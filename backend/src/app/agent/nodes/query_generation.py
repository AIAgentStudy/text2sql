"""
쿼리 생성 노드

LLM을 사용하여 자연어 질문을 SQL 쿼리로 변환합니다.
"""

import logging
import uuid

from langchain_core.messages import HumanMessage, SystemMessage

from app.agent.state import Text2SQLAgentState
from app.config import get_settings
from app.llm.factory import get_chat_model

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """당신은 PostgreSQL 데이터베이스 전문가입니다.
사용자의 자연어 질문을 SQL SELECT 쿼리로 변환하는 것이 당신의 임무입니다.

## 규칙
1. 반드시 SELECT 문만 생성하세요. UPDATE, DELETE, INSERT, DROP 등은 절대 사용하지 마세요.
2. 주어진 스키마에 있는 테이블과 컬럼만 사용하세요.
3. 한국어 질문을 정확히 이해하고 적절한 SQL로 변환하세요.
4. 결과는 사용자가 이해하기 쉽게 정렬하세요.
5. 집계 함수 사용 시 적절한 GROUP BY를 포함하세요.
6. 날짜 관련 질문은 PostgreSQL 날짜 함수를 사용하세요.

## 출력 형식
다음 형식으로 정확히 응답하세요:

SQL:
```sql
여기에 SQL 쿼리
```

설명:
여기에 이 쿼리가 무엇을 조회하는지 한국어로 설명

## 데이터베이스 스키마
{schema}
"""


async def query_generation_node(state: Text2SQLAgentState) -> dict[str, object]:
    """
    쿼리 생성 노드

    LLM을 사용하여 자연어 질문을 SQL 쿼리로 변환합니다.

    Args:
        state: 현재 에이전트 상태

    Returns:
        업데이트할 상태 딕셔너리
    """
    settings = get_settings()
    attempt = state.get("generation_attempt", 0) + 1

    logger.info(
        f"쿼리 생성 시작 - 질문: {state['user_question'][:50]}... (시도 {attempt})"
    )

    # 최대 시도 횟수 확인
    if attempt > settings.max_generation_attempts:
        logger.warning(f"최대 생성 시도 횟수 초과: {attempt}")
        return {
            "generation_attempt": attempt,
            "execution_error": "쿼리를 생성할 수 없습니다. 질문을 다시 확인해주세요.",
        }

    try:
        # LLM 모델 가져오기
        llm = get_chat_model()

        # 시스템 프롬프트 구성
        system_prompt = SYSTEM_PROMPT.format(schema=state["database_schema"])

        # 대화 맥락 구성
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=state["user_question"]),
        ]

        # LLM 호출
        response = await llm.ainvoke(messages)
        response_text = str(response.content)

        # 응답 파싱
        sql_query, explanation = _parse_llm_response(response_text)

        if not sql_query:
            logger.warning("SQL 쿼리 파싱 실패")
            return {
                "generation_attempt": attempt,
                "generated_query": "",
                "query_explanation": "",
                "execution_error": "쿼리를 생성하지 못했습니다.",
            }

        # 쿼리 ID 생성
        query_id = str(uuid.uuid4())

        logger.info(f"쿼리 생성 완료 - ID: {query_id}")

        return {
            "generation_attempt": attempt,
            "generated_query": sql_query,
            "query_explanation": explanation,
            "query_id": query_id,
            "execution_error": None,
        }

    except Exception as e:
        logger.error(f"쿼리 생성 실패: {e}")
        return {
            "generation_attempt": attempt,
            "generated_query": "",
            "query_explanation": "",
            "execution_error": f"쿼리 생성 중 오류가 발생했습니다: {e}",
        }


def _parse_llm_response(response: str) -> tuple[str, str]:
    """
    LLM 응답에서 SQL 쿼리와 설명을 추출합니다.

    Args:
        response: LLM 응답 텍스트

    Returns:
        (SQL 쿼리, 설명) 튜플
    """
    sql_query = ""
    explanation = ""

    # SQL 블록 추출
    if "```sql" in response:
        try:
            sql_start = response.index("```sql") + 6
            sql_end = response.index("```", sql_start)
            sql_query = response[sql_start:sql_end].strip()
        except ValueError:
            pass
    elif "```" in response:
        # sql 태그 없이 코드 블록만 있는 경우
        try:
            sql_start = response.index("```") + 3
            sql_end = response.index("```", sql_start)
            sql_query = response[sql_start:sql_end].strip()
        except ValueError:
            pass

    # 설명 추출
    if "설명:" in response:
        try:
            explanation_start = response.index("설명:") + 3
            explanation = response[explanation_start:].strip()
            # 다음 섹션이 있으면 자르기
            if "```" in explanation:
                explanation = explanation[: explanation.index("```")].strip()
        except ValueError:
            pass
    elif sql_query:
        # 설명이 없으면 SQL 이후의 텍스트를 설명으로 사용
        if "```" in response:
            try:
                after_sql = response.split("```")[-1].strip()
                if after_sql:
                    explanation = after_sql
            except Exception:
                pass

    # 기본 설명
    if not explanation and sql_query:
        explanation = "요청하신 데이터를 조회합니다."

    return sql_query, explanation
