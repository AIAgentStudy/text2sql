"""
쿼리 실행 노드

검증된 SQL 쿼리를 안전하게 실행하고 결과를 반환합니다.
"""

import logging

from app.agent.decorators import with_debug_timing
from app.agent.state import Text2SQLAgentState
from app.database.executor import execute_safe_query

logger = logging.getLogger(__name__)


@with_debug_timing("query_execution")
async def query_execution_node(state: Text2SQLAgentState) -> dict[str, object]:
    """
    쿼리 실행 노드

    검증된 SQL 쿼리를 실행하고 결과를 상태에 저장합니다.

    Args:
        state: 현재 에이전트 상태

    Returns:
        업데이트할 상태 딕셔너리
    """
    # Nested 구조에서 값 추출
    query = state["generation"]["generated_query"]

    if not query:
        logger.warning("실행할 쿼리가 없습니다")
        return {
            "execution": {
                "execution_error": "실행할 쿼리가 없습니다.",
            },
            "response": {
                "response_format": "error",
            },
        }

    # 최종 권한 체크 (defense-in-depth)
    accessible_tables = state["auth"]["accessible_tables"]
    if accessible_tables:
        from app.auth.permissions import extract_tables_from_query

        referenced_tables = extract_tables_from_query(query)
        accessible_lower = [t.lower() for t in accessible_tables]
        unauthorized = [
            t for t in referenced_tables if t.lower() not in accessible_lower
        ]
        if unauthorized:
            logger.warning(
                f"실행 단계에서 권한 없는 테이블 접근 차단: {unauthorized}"
            )
            return {
                "execution": {
                    "query_result": [],
                    "result_columns": [],
                    "total_row_count": 0,
                    "execution_time_ms": 0,
                    "execution_error": f"접근 권한이 없는 테이블이 포함되어 있습니다: {', '.join(unauthorized)}",
                },
                "response": {
                    "response_format": "error",
                },
            }

    logger.info(f"쿼리 실행 시작 - 쿼리: {query[:100]}...")

    try:
        # 안전한 쿼리 실행
        result = await execute_safe_query(query)

        # 결과 처리
        rows = result.rows
        columns = [
            {"name": col.name, "data_type": col.data_type, "is_nullable": col.is_nullable}
            for col in result.columns
        ]
        total_count = result.total_row_count
        execution_time = result.execution_time_ms

        logger.info(
            f"쿼리 실행 완료 - {total_count}행, {execution_time}ms"
        )

        # 결과 형식 결정
        if total_count == 0:
            response_format = "summary"  # 빈 결과
        else:
            response_format = "table"

        return {
            "execution": {
                "query_result": rows,
                "result_columns": columns,
                "total_row_count": total_count,
                "execution_time_ms": execution_time,
                "execution_error": None,
            },
            "response": {
                "response_format": response_format,
            },
        }

    except Exception as e:
        logger.error(f"쿼리 실행 실패: {e}")
        return {
            "execution": {
                "query_result": [],
                "result_columns": [],
                "total_row_count": 0,
                "execution_time_ms": 0,
                "execution_error": str(e),
            },
            "response": {
                "response_format": "error",
            },
        }
