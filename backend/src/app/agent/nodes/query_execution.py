"""
쿼리 실행 노드

검증된 SQL 쿼리를 안전하게 실행하고 결과를 반환합니다.
"""

import logging

from app.agent.state import Text2SQLAgentState
from app.database.executor import execute_safe_query

logger = logging.getLogger(__name__)


async def query_execution_node(state: Text2SQLAgentState) -> dict[str, object]:
    """
    쿼리 실행 노드

    검증된 SQL 쿼리를 실행하고 결과를 상태에 저장합니다.

    Args:
        state: 현재 에이전트 상태

    Returns:
        업데이트할 상태 딕셔너리
    """
    query = state.get("generated_query", "")

    if not query:
        logger.warning("실행할 쿼리가 없습니다")
        return {
            "execution_error": "실행할 쿼리가 없습니다.",
            "response_format": "error",
        }

    logger.info(f"쿼리 실행 시작 - 쿼리: {query[:100]}...")

    try:
        # 안전한 쿼리 실행
        result = await execute_safe_query(query)

        # 결과 처리
        rows = result.rows
        columns = [col.name for col in result.columns]
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
            "query_result": rows,
            "result_columns": columns,
            "total_row_count": total_count,
            "execution_time_ms": execution_time,
            "execution_error": None,
            "response_format": response_format,
        }

    except Exception as e:
        logger.error(f"쿼리 실행 실패: {e}")
        return {
            "query_result": [],
            "result_columns": [],
            "total_row_count": 0,
            "execution_time_ms": 0,
            "execution_error": str(e),
            "response_format": "error",
        }
