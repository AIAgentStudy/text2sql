"""
응답 포맷팅 노드

쿼리 결과를 사용자 친화적인 형식으로 변환합니다.
"""

import logging

from app.agent.state import Text2SQLAgentState

logger = logging.getLogger(__name__)


async def response_formatting_node(state: Text2SQLAgentState) -> dict[str, object]:
    """
    응답 포맷팅 노드

    쿼리 결과를 사용자에게 표시할 형식으로 변환합니다.

    Args:
        state: 현재 에이전트 상태

    Returns:
        업데이트할 상태 딕셔너리
    """
    response_format = state.get("response_format", "table")

    logger.info(f"응답 포맷팅 - 형식: {response_format}")

    # 에러 응답
    if response_format == "error" or state.get("execution_error"):
        error_message = state.get("execution_error", "알 수 없는 오류가 발생했습니다.")
        return {
            "final_response": _format_error_response(error_message),
            "response_format": "error",
        }

    # 빈 결과 응답
    total_count = state.get("total_row_count", 0)
    if total_count == 0:
        return {
            "final_response": _format_empty_response(state.get("user_question", "")),
            "response_format": "summary",
        }

    # 테이블 형식 응답
    rows = state.get("query_result", [])
    columns = state.get("result_columns", [])
    execution_time = state.get("execution_time_ms", 0)

    return {
        "final_response": _format_table_response(
            rows=rows,
            columns=columns,
            total_count=total_count,
            execution_time=execution_time,
        ),
        "response_format": "table",
    }


def _format_error_response(error_message: str) -> str:
    """에러 응답 포맷팅"""
    return f"❌ 오류가 발생했습니다.\n\n{error_message}"


def _format_empty_response(question: str) -> str:
    """빈 결과 응답 포맷팅"""
    return "📭 조건에 맞는 데이터가 없습니다.\n\n" "질문을 다시 확인하거나 조건을 변경해보세요."


def _format_table_response(
    rows: list[dict[str, object]],
    columns: list[str],
    total_count: int,
    execution_time: int,
) -> str:
    """테이블 형식 응답 포맷팅"""
    # 결과 요약
    summary = f"✅ 조회 완료! {total_count}건의 데이터를 찾았습니다. ({execution_time}ms)"

    # 마크다운 테이블 생성 (최대 10행만 미리보기)
    preview_rows = rows[:10]
    has_more = len(rows) > 10

    if not columns:
        columns = list(preview_rows[0].keys()) if preview_rows else []

    # 테이블 헤더
    header = "| " + " | ".join(columns) + " |"
    separator = "|" + "|".join(["---"] * len(columns)) + "|"

    # 테이블 행
    table_rows = []
    for row in preview_rows:
        values = [_format_cell_value(row.get(col, "")) for col in columns]
        table_rows.append("| " + " | ".join(values) + " |")

    table = "\n".join([header, separator] + table_rows)

    # 추가 행 안내
    if has_more:
        table += f"\n\n... 그 외 {total_count - 10}건의 데이터가 더 있습니다."

    return f"{summary}\n\n{table}"


def _format_cell_value(value: object) -> str:
    """셀 값 포맷팅"""
    if value is None:
        return "-"
    if isinstance(value, bool):
        return "예" if value else "아니오"
    if isinstance(value, float):
        # 큰 숫자는 천 단위 구분
        if abs(value) >= 1000:
            return f"{value:,.2f}"
        return f"{value:.2f}"
    if isinstance(value, int):
        if abs(value) >= 1000:
            return f"{value:,}"
        return str(value)

    # 문자열 처리
    str_value = str(value)
    # 너무 긴 문자열은 자르기
    if len(str_value) > 50:
        return str_value[:47] + "..."
    return str_value
