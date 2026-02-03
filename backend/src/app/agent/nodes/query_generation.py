"""
쿼리 생성 노드

LLM을 사용하여 자연어 질문을 SQL 쿼리로 변환합니다.
대화 맥락을 활용하여 연속 질문을 처리합니다.
"""

import logging
import re
import uuid

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

from app.agent.state import Text2SQLAgentState
from app.config import get_settings
from app.errors.messages import get_ambiguous_query_help, is_ambiguous_query
from app.llm.factory import get_chat_model

logger = logging.getLogger(__name__)

# 맥락 참조 패턴 (한국어)
CONTEXT_REFERENCE_PATTERNS = [
    r"그중에",
    r"그\s*중에서",
    r"거기서",
    r"거기에서",
    r"위에서",
    r"이전\s*(결과|데이터|것)",
    r"방금\s*(그|저|그것|거)",
    r"아까\s*(그|저|그것)",
    r"그\s*(데이터|결과|것)",
    r"저\s*(데이터|결과|것)",
    r"말한\s*것",
    r"보여준\s*것",
    r"조회한\s*것",
]

# 리셋 명령어 패턴
RESET_COMMAND_PATTERNS = [
    r"^처음부터\s*다시$",
    r"^다시\s*시작$",
    r"^새로운\s*대화$",
    r"^리셋$",
    r"^초기화$",
    r"^대화\s*초기화$",
    r"^세션\s*초기화$",
    r"^새\s*대화$",
]

FEW_SHOT_EXAMPLES = """
## 예시

질문: "지역별 총 매출"
```sql
SELECT c.region AS "지역", COALESCE(SUM(o.amount), 0) AS "총매출액"
FROM orders o INNER JOIN customers c ON c.id = o.customer_id
GROUP BY c.region ORDER BY "총매출액" DESC;
```

질문: "이번 달 매출 상위 5개 상품"
```sql
SELECT p.name AS "상품명", COALESCE(SUM(oi.quantity), 0) AS "판매수량"
FROM order_items oi INNER JOIN products p ON p.id = oi.product_id
INNER JOIN orders o ON o.id = oi.order_id
WHERE o.order_date >= DATE_TRUNC('month', CURRENT_DATE)
GROUP BY p.id, p.name ORDER BY "판매수량" DESC LIMIT 5;
```
"""

SYSTEM_PROMPT = """당신은 PostgreSQL 데이터베이스 전문가입니다.
사용자의 자연어 질문을 SQL SELECT 쿼리로 변환하는 것이 당신의 임무입니다.

## 규칙
1. 반드시 SELECT 문만 생성하세요. UPDATE, DELETE, INSERT, DROP 등은 절대 사용하지 마세요.
2. 주어진 스키마에 있는 테이블과 컬럼만 사용하세요.
3. 한국어 질문을 정확히 이해하고 적절한 SQL로 변환하세요.
4. 결과는 사용자가 이해하기 쉽게 정렬하세요.
5. 집계 함수 사용 시 적절한 GROUP BY를 포함하세요.
6. 날짜 관련 질문은 PostgreSQL 날짜 함수를 사용하세요.
7. 한국어 텍스트 검색 시 ILIKE와 '%패턴%'을 사용하세요.
   예: '강남' 검색 → WHERE name ILIKE '%강남%' (정확한 값을 알 수 없으므로 부분 일치 사용)
8. 지역명, 제품명, 고객명 등 텍스트 컬럼 필터링은 항상 ILIKE를 우선 고려하세요.
9. 집계 쿼리에서 명시적 정렬 요청이 없으면 집계 값 기준 내림차순(DESC)으로 정렬하세요.
10. 항상 명시적 JOIN 문법을 사용하세요 (INNER JOIN, LEFT JOIN). WHERE절 조인 금지.
11. 집계 결과 컬럼에는 반드시 한국어 AS 별칭을 부여하세요 (예: SUM(amount) AS "총매출액").
12. 집계 함수 사용 시 COALESCE로 NULL을 0 또는 기본값으로 처리하세요.

{few_shot_examples}

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

CONTEXT_AWARE_SYSTEM_PROMPT = """당신은 PostgreSQL 데이터베이스 전문가입니다.
사용자의 자연어 질문을 SQL SELECT 쿼리로 변환하는 것이 당신의 임무입니다.

## 대화 맥락
사용자와의 이전 대화 내용을 참고하여 현재 질문을 이해하세요.
"그중에", "거기서", "이전 결과에서" 같은 표현은 이전 질문/결과를 참조합니다.

## 이전 대화
{conversation_history}

## 규칙
1. 반드시 SELECT 문만 생성하세요. UPDATE, DELETE, INSERT, DROP 등은 절대 사용하지 마세요.
2. 주어진 스키마에 있는 테이블과 컬럼만 사용하세요.
3. 이전 대화 맥락을 활용하여 현재 질문을 정확히 이해하세요.
4. "그중에", "거기서" 등의 표현은 이전 쿼리 결과를 필터링하는 것입니다.
5. 이전 쿼리의 조건을 유지하면서 새로운 조건을 추가하세요.
6. 한국어 텍스트 검색 시 ILIKE와 '%패턴%'을 사용하세요.
   예: '강남' 검색 → WHERE name ILIKE '%강남%' (정확한 값을 알 수 없으므로 부분 일치 사용)
7. 지역명, 제품명, 고객명 등 텍스트 컬럼 필터링은 항상 ILIKE를 우선 고려하세요.
8. 집계 쿼리에서 명시적 정렬 요청이 없으면 집계 값 기준 내림차순(DESC)으로 정렬하세요.
9. 항상 명시적 JOIN 문법을 사용하세요 (INNER JOIN, LEFT JOIN). WHERE절 조인 금지.
10. 집계 결과 컬럼에는 반드시 한국어 AS 별칭을 부여하세요 (예: SUM(amount) AS "총매출액").
11. 집계 함수 사용 시 COALESCE로 NULL을 0 또는 기본값으로 처리하세요.

{few_shot_examples}

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


def detect_context_reference(question: str) -> bool:
    """
    질문에서 이전 대화 맥락 참조 감지

    Args:
        question: 사용자 질문

    Returns:
        맥락 참조 여부
    """
    question_lower = question.lower().strip()

    for pattern in CONTEXT_REFERENCE_PATTERNS:
        if re.search(pattern, question_lower):
            return True

    return False


def is_reset_command(question: str) -> bool:
    """
    리셋 명령어인지 확인

    Args:
        question: 사용자 입력

    Returns:
        리셋 명령어 여부
    """
    question_normalized = question.strip()

    for pattern in RESET_COMMAND_PATTERNS:
        if re.match(pattern, question_normalized, re.IGNORECASE):
            return True

    return False


def build_context_aware_prompt(
    current_question: str,
    message_history: list[BaseMessage],
    schema: str,
) -> str:
    """
    대화 맥락을 포함한 프롬프트 생성

    Args:
        current_question: 현재 질문
        message_history: 이전 대화 히스토리
        schema: 데이터베이스 스키마

    Returns:
        맥락이 포함된 프롬프트
    """
    if not message_history:
        return SYSTEM_PROMPT.format(schema=schema, few_shot_examples=FEW_SHOT_EXAMPLES)

    # 대화 히스토리 포맷팅
    history_lines = []
    for msg in message_history[-6:]:  # 최근 6개 메시지만
        if isinstance(msg, HumanMessage):
            history_lines.append(f"사용자: {msg.content}")
        elif isinstance(msg, AIMessage):
            # AI 응답에서 SQL 쿼리 부분만 추출
            content = str(msg.content)
            if "```sql" in content:
                try:
                    sql_start = content.index("```sql") + 6
                    sql_end = content.index("```", sql_start)
                    sql = content[sql_start:sql_end].strip()
                    history_lines.append(f"생성된 쿼리: {sql}")
                except ValueError:
                    history_lines.append(f"어시스턴트: {content[:200]}")
            else:
                history_lines.append(f"어시스턴트: {content[:200]}")

    conversation_history = "\n".join(history_lines)

    return CONTEXT_AWARE_SYSTEM_PROMPT.format(
        conversation_history=conversation_history,
        schema=schema,
        few_shot_examples=FEW_SHOT_EXAMPLES,
    )


def format_messages_for_llm(
    message_history: list[BaseMessage],
    current_question: str,
    system_prompt: str,
) -> list[BaseMessage]:
    """
    LLM 호출을 위한 메시지 목록 구성

    Args:
        message_history: 이전 대화 히스토리
        current_question: 현재 질문
        system_prompt: 시스템 프롬프트

    Returns:
        LLM에 전달할 메시지 목록
    """
    messages: list[BaseMessage] = [SystemMessage(content=system_prompt)]

    # 이전 대화 히스토리 추가 (최근 4개까지)
    for msg in message_history[-4:]:
        messages.append(msg)

    # 현재 질문 추가
    messages.append(HumanMessage(content=current_question))

    return messages


async def query_generation_node(state: Text2SQLAgentState) -> dict[str, object]:
    """
    쿼리 생성 노드

    LLM을 사용하여 자연어 질문을 SQL 쿼리로 변환합니다.
    대화 맥락을 활용하여 연속 질문을 처리합니다.

    Args:
        state: 현재 에이전트 상태

    Returns:
        업데이트할 상태 딕셔너리
    """
    settings = get_settings()
    attempt = state.get("generation_attempt", 0) + 1
    user_question = state["user_question"]
    message_history = state.get("messages", [])

    # 접근 가능한 테이블이 없으면 LLM 호출 없이 즉시 에러 반환 (이중 안전장치)
    accessible_tables = state.get("accessible_tables", [])
    if accessible_tables is not None and len(accessible_tables) == 0:
        logger.warning("접근 가능한 테이블이 없음 - LLM 호출 생략")
        return {
            "generation_attempt": attempt,
            "generated_query": "",
            "query_explanation": "",
            "execution_error": "접근 권한이 없습니다. 요청하신 데이터에 대한 조회 권한이 부여되지 않았습니다.",
        }

    logger.info(
        f"쿼리 생성 시작 - 질문: {user_question[:50]}... (시도 {attempt})"
    )

    # 리셋 명령어 확인
    if is_reset_command(user_question):
        logger.info("리셋 명령어 감지 - 세션 초기화")
        return {
            "generation_attempt": attempt,
            "generated_query": "",
            "query_explanation": "",
            "execution_error": None,
            "final_response": "대화가 초기화되었습니다. 새로운 질문을 해주세요.",
            "response_format": "summary",
            # 메시지 히스토리 초기화는 세션 매니저에서 처리
        }

    # 맥락 참조 감지
    has_context_reference = detect_context_reference(user_question)

    # 맥락 참조가 있는데 히스토리가 없으면 안내
    if has_context_reference and not message_history:
        logger.info("맥락 참조 있으나 히스토리 없음")
        return {
            "generation_attempt": attempt,
            "generated_query": "",
            "query_explanation": "",
            "execution_error": "이전 대화 내용이 없습니다. 먼저 조회할 데이터를 알려주세요.\n\n예: '지난달 매출을 보여줘'",
        }

    # 모호한 쿼리 감지 (맥락 참조가 없는 경우에만)
    if attempt == 1 and not has_context_reference and is_ambiguous_query(user_question):
        logger.info("모호한 쿼리 감지")
        help_text = get_ambiguous_query_help()
        return {
            "generation_attempt": attempt,
            "generated_query": "",
            "query_explanation": "",
            "execution_error": help_text,
        }

    # 최대 시도 횟수 확인
    if attempt > settings.max_generation_attempts:
        logger.warning(f"최대 생성 시도 횟수 초과: {attempt}")
        return {
            "generation_attempt": attempt,
            "execution_error": "쿼리를 생성할 수 없습니다. 질문을 다시 확인해주세요.",
        }

    try:
        # LLM 모델 가져오기 (state에서 선택한 provider 사용)
        llm_provider = state.get("llm_provider", "openai")
        llm = get_chat_model(provider_type=llm_provider)

        # 맥락 인식 프롬프트 생성
        if has_context_reference and message_history:
            logger.info("맥락 인식 모드로 쿼리 생성")
            system_prompt = build_context_aware_prompt(
                current_question=user_question,
                message_history=message_history,
                schema=state["database_schema"],
            )
        else:
            system_prompt = SYSTEM_PROMPT.format(
                schema=state["database_schema"],
                few_shot_examples=FEW_SHOT_EXAMPLES,
            )

        # 메시지 구성
        messages = format_messages_for_llm(
            message_history=message_history if has_context_reference else [],
            current_question=user_question,
            system_prompt=system_prompt,
        )

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

        # 메시지 히스토리에 현재 대화 추가
        updated_messages = list(message_history)
        updated_messages.append(HumanMessage(content=user_question))
        updated_messages.append(AIMessage(content=response_text))

        return {
            "generation_attempt": attempt,
            "generated_query": sql_query,
            "query_explanation": explanation,
            "query_id": query_id,
            "execution_error": None,
            "messages": updated_messages,
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
