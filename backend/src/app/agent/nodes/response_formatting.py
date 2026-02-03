"""
응답 포맷팅 노드

쿼리 결과를 사용자 친화적인 형식으로 변환합니다.
"""

import logging

from app.agent.state import Text2SQLAgentState
from app.errors.messages import (
    ErrorCode,
    get_error_message,
    get_error_suggestion,
    get_ambiguous_query_help,
)

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

    # 사용자가 취소한 경우
    if state.get("user_approved") is False:
        return {
            "final_response": _format_cancelled_response(),
            "response_format": "summary",
        }

    # 에러 응답
    if response_format == "error" or state.get("execution_error"):
        error_message = state.get("execution_error", "")
        validation_errors = state.get("validation_errors", [])

        return {
            "final_response": _format_error_response(
                error_message,
                validation_errors,
                state.get("user_question", ""),
            ),
            "response_format": "error",
        }

    # 빈 결과 응답
    total_count = state.get("total_row_count", 0)
    if total_count == 0:
        return {
            "final_response": _format_empty_response(
                state.get("user_question", ""),
                state.get("generated_query", ""),
            ),
            "response_format": "summary",
        }

    # 테이블 형식 응답
    rows = state.get("query_result", [])
    raw_columns = state.get("result_columns", [])
    columns = [col["name"] if isinstance(col, dict) else col for col in raw_columns]
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


def _format_cancelled_response() -> str:
    """취소 응답 포맷팅"""
    return "쿼리 실행이 취소되었습니다. 다른 질문을 해주세요."


def _format_error_response(
    error_message: str,
    validation_errors: list[str],
    user_question: str,
) -> str:
    """
    에러 응답 포맷팅

    에러 유형에 따라 적절한 사용자 친화적 메시지를 생성합니다.
    """
    # 검증 오류가 있는 경우
    if validation_errors:
        main_error = validation_errors[0]
        response_parts = [f"요청을 처리할 수 없습니다.\n\n{main_error}"]

        # 위험 쿼리 관련 오류
        if "조회" in main_error or "수정" in main_error:
            suggestion = get_error_suggestion(ErrorCode.DANGEROUS_QUERY)
            if suggestion:
                response_parts.append(f"\n💡 {suggestion}")

        return "\n".join(response_parts)

    # 타임아웃 오류
    if "타임아웃" in error_message or "시간" in error_message:
        message = get_error_message(ErrorCode.QUERY_TIMEOUT)
        suggestion = get_error_suggestion(ErrorCode.QUERY_TIMEOUT)
        return f"{message}\n\n💡 {suggestion}"

    # 연결 오류
    if "연결" in error_message or "connection" in error_message.lower():
        return get_error_message(ErrorCode.DATABASE_CONNECTION_ERROR)

    # 스키마/테이블 오류
    if "테이블" in error_message or "찾을 수 없" in error_message:
        return f"요청하신 데이터를 찾을 수 없습니다.\n\n{error_message}"

    # 모호한 질문
    if "이해" in error_message or "모호" in error_message:
        help_text = get_ambiguous_query_help()
        return help_text

    # 일반 오류
    if error_message:
        return f"요청을 처리할 수 없습니다.\n\n{error_message}"

    return get_error_message(ErrorCode.INTERNAL_ERROR)


def _format_empty_response(question: str, query: str) -> str:
    """
    빈 결과 응답 포맷팅

    결과가 없는 이유와 함께 도움말을 제공합니다.
    """
    message = get_error_message(ErrorCode.EMPTY_RESULT)
    suggestion = get_error_suggestion(ErrorCode.EMPTY_RESULT)

    response_parts = [message]

    if suggestion:
        response_parts.append(f"\n💡 {suggestion}")

    # 실행된 쿼리 정보 제공 (디버깅용)
    if query:
        response_parts.append(f"\n\n실행된 쿼리:\n```sql\n{query}\n```")

    return "\n".join(response_parts)


def _format_table_response(
    rows: list[dict[str, object]],
    columns: list[str],
    total_count: int,
    execution_time: int,
) -> str:
    """테이블 형식 응답 포맷팅"""
    # 결과 요약
    summary = f"조회 완료! {total_count:,}건의 데이터를 찾았습니다. ({execution_time}ms)"

    # 마크다운 테이블 생성 (최대 10행만 미리보기)
    preview_rows = rows[:10]
    has_more = len(rows) > 10

    if not columns:
        columns = list(preview_rows[0].keys()) if preview_rows else []

    if not columns:
        return summary

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
        remaining = total_count - 10
        table += f"\n\n... 그 외 {remaining:,}건의 데이터가 더 있습니다."

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
    # 파이프 문자 이스케이프 (마크다운 테이블 호환)
    return str_value.replace("|", "\\|")
