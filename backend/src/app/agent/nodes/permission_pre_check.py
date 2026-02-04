"""
권한 사전 검사 노드

쿼리 생성 전에 사용자 질문이 접근 불가 테이블을 필요로 하는지 판단합니다.
Fast model을 사용하여 최소 토큰으로 권한 위반 여부를 체크합니다.
"""

import logging

from langchain_core.messages import HumanMessage, SystemMessage

from app.agent.state import Text2SQLAgentState
from app.database.schema import get_database_schema
from app.llm.factory import get_fast_model

logger = logging.getLogger(__name__)

PERMISSION_CHECK_PROMPT = """당신은 SQL 데이터베이스 권한 검사기입니다.

사용자의 질문이 아래 "접근 불가 테이블" 목록의 데이터를 필요로 하는지 판단하세요.

## 접근 가능 테이블
{accessible_tables}

## 접근 불가 테이블
{inaccessible_tables}

## 규칙
- 질문이 접근 불가 테이블의 데이터를 필요로 하면 "YES"만 출력
- 질문이 접근 가능 테이블만으로 답할 수 있으면 "NO"만 출력
- 반드시 YES 또는 NO 중 하나만 출력"""


def _format_table_list(table_names: list[str], table_descriptions: dict[str, str]) -> str:
    """테이블 이름과 설명을 포맷팅"""
    lines = []
    for name in sorted(table_names):
        desc = table_descriptions.get(name, "")
        if desc:
            lines.append(f"- {name}: {desc}")
        else:
            lines.append(f"- {name}")
    return "\n".join(lines) if lines else "(없음)"


async def permission_pre_check_node(state: Text2SQLAgentState) -> dict[str, object]:
    """
    권한 사전 검사 노드

    쿼리 생성 전에 사용자 질문이 접근 불가 테이블을 필요로 하는지
    fast model로 판단하여, 권한 위반 시 즉시 에러를 반환합니다.

    Args:
        state: 현재 에이전트 상태

    Returns:
        업데이트할 상태 딕셔너리
    """
    user_roles = state.get("user_roles", [])
    accessible_tables = state.get("accessible_tables", [])

    # admin은 모든 테이블 접근 가능 → 스킵
    if "admin" in user_roles:
        logger.debug("admin 사용자 - 권한 사전 검사 스킵")
        return {}

    # 접근 가능 테이블 정보가 없으면 스킵 (기존 validation에서 처리)
    if not accessible_tables:
        logger.debug("accessible_tables 없음 - 권한 사전 검사 스킵")
        return {}

    try:
        # 전체 스키마 조회 (캐시됨)
        schema = await get_database_schema()

        # 전체 테이블 목록에서 접근 불가 테이블 추출
        all_table_names = {table.name for table in schema.tables}
        accessible_lower = {t.lower() for t in accessible_tables}
        inaccessible_tables = {
            name for name in all_table_names
            if name.lower() not in accessible_lower
        }

        # 접근 불가 테이블이 없으면 스킵
        if not inaccessible_tables:
            logger.debug("접근 불가 테이블 없음 - 권한 사전 검사 스킵")
            return {}

        # 테이블 설명 맵 생성 (프롬프트용)
        table_descriptions = {
            table.name: table.description or ""
            for table in schema.tables
        }

        # 프롬프트 구성
        prompt = PERMISSION_CHECK_PROMPT.format(
            accessible_tables=_format_table_list(
                list(accessible_lower & all_table_names), table_descriptions
            ),
            inaccessible_tables=_format_table_list(
                list(inaccessible_tables), table_descriptions
            ),
        )

        user_question = state.get("user_question", "")

        # fast model로 권한 체크
        llm_provider = state.get("llm_provider", "openai")
        llm = get_fast_model(provider_type=llm_provider)

        response = await llm.ainvoke([
            SystemMessage(content=prompt),
            HumanMessage(content=user_question),
        ])

        answer = response.content.strip().upper()
        logger.info(f"권한 사전 검사 결과: {answer}")

        if answer.startswith("YES"):
            logger.warning(
                f"권한 사전 검사 차단 - 사용자 질문이 접근 불가 테이블 필요: "
                f"roles={user_roles}, question={user_question[:100]}"
            )
            return {
                "execution_error": "해당 데이터에 대한 접근 권한이 없습니다. 관리자에게 문의하세요.",
            }

        # NO 또는 기타 응답 → 통과
        return {}

    except Exception as e:
        # fail-open: LLM 호출 실패 시 통과 (기존 validation에서 잡힘)
        logger.warning(f"권한 사전 검사 중 오류 발생, 통과 처리: {e}")
        return {}
