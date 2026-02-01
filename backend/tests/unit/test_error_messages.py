"""
에러 메시지 생성 단위 테스트

모든 에러 코드에 대해 적절한 한국어 메시지가 생성되는지 테스트합니다.
"""

import pytest

from app.errors.messages import (
    get_error_message,
    get_error_suggestion,
    format_error_response,
    ErrorCode,
    ERROR_MESSAGES,
)


class TestErrorMessages:
    """에러 메시지 테스트"""

    def test_all_error_codes_have_messages(self) -> None:
        """모든 에러 코드에 대해 메시지가 정의되어 있는지 확인"""
        for code in ErrorCode:
            message = get_error_message(code)
            assert message is not None
            assert len(message) > 0
            assert isinstance(message, str)

    def test_error_messages_are_in_korean(self) -> None:
        """에러 메시지가 한국어인지 확인"""
        for code in ErrorCode:
            message = get_error_message(code)
            # 한글이 포함되어 있는지 확인
            has_korean = any('\uac00' <= char <= '\ud7a3' for char in message)
            assert has_korean, f"{code}의 메시지에 한글이 없습니다: {message}"

    def test_dangerous_query_message(self) -> None:
        """위험한 쿼리 에러 메시지"""
        message = get_error_message(ErrorCode.DANGEROUS_QUERY)
        assert "조회" in message or "수정" in message

    def test_query_timeout_message(self) -> None:
        """쿼리 타임아웃 에러 메시지"""
        message = get_error_message(ErrorCode.QUERY_TIMEOUT)
        assert "시간" in message or "타임아웃" in message

    def test_schema_not_found_message(self) -> None:
        """스키마 없음 에러 메시지"""
        message = get_error_message(ErrorCode.SCHEMA_NOT_FOUND)
        assert "테이블" in message or "스키마" in message

    def test_session_expired_message(self) -> None:
        """세션 만료 에러 메시지"""
        message = get_error_message(ErrorCode.SESSION_EXPIRED)
        assert "세션" in message or "만료" in message

    def test_database_connection_error_message(self) -> None:
        """DB 연결 오류 메시지"""
        message = get_error_message(ErrorCode.DATABASE_CONNECTION_ERROR)
        assert "데이터" in message or "연결" in message

    def test_empty_result_message(self) -> None:
        """빈 결과 메시지"""
        message = get_error_message(ErrorCode.EMPTY_RESULT)
        assert "결과" in message or "없습니다" in message


class TestErrorSuggestions:
    """에러 제안 테스트"""

    def test_suggestions_exist_for_recoverable_errors(self) -> None:
        """복구 가능한 에러에 대해 제안이 있는지 확인"""
        recoverable_codes = [
            ErrorCode.QUERY_TIMEOUT,
            ErrorCode.EMPTY_RESULT,
            ErrorCode.QUERY_GENERATION_ERROR,
            ErrorCode.AMBIGUOUS_QUERY,
        ]
        for code in recoverable_codes:
            suggestion = get_error_suggestion(code)
            assert suggestion is not None
            assert len(suggestion) > 0

    def test_timeout_suggestion(self) -> None:
        """타임아웃 제안"""
        suggestion = get_error_suggestion(ErrorCode.QUERY_TIMEOUT)
        assert "조건" in suggestion or "구체적" in suggestion

    def test_empty_result_suggestion(self) -> None:
        """빈 결과 제안"""
        suggestion = get_error_suggestion(ErrorCode.EMPTY_RESULT)
        assert "조건" in suggestion or "다른" in suggestion

    def test_ambiguous_query_suggestion(self) -> None:
        """모호한 쿼리 제안"""
        suggestion = get_error_suggestion(ErrorCode.AMBIGUOUS_QUERY)
        assert "구체적" in suggestion or "명확" in suggestion


class TestFormatErrorResponse:
    """에러 응답 포맷팅 테스트"""

    def test_format_includes_code(self) -> None:
        """응답에 에러 코드가 포함되는지 확인"""
        response = format_error_response(ErrorCode.DANGEROUS_QUERY)
        assert "code" in response
        assert response["code"] == ErrorCode.DANGEROUS_QUERY.value

    def test_format_includes_message(self) -> None:
        """응답에 메시지가 포함되는지 확인"""
        response = format_error_response(ErrorCode.QUERY_TIMEOUT)
        assert "message" in response
        assert len(response["message"]) > 0

    def test_format_includes_suggestion_when_available(self) -> None:
        """제안이 있을 때 응답에 포함되는지 확인"""
        response = format_error_response(ErrorCode.EMPTY_RESULT)
        assert "suggestion" in response

    def test_format_with_context(self) -> None:
        """컨텍스트가 포함된 포맷팅"""
        response = format_error_response(
            ErrorCode.SCHEMA_NOT_FOUND,
            context={"table_name": "unknown_table"},
        )
        assert "message" in response


class TestErrorMessageTemplates:
    """에러 메시지 템플릿 테스트"""

    def test_template_substitution(self) -> None:
        """템플릿 변수 치환"""
        message = get_error_message(
            ErrorCode.SCHEMA_NOT_FOUND,
            table_name="users",
        )
        # 테이블명이 메시지에 포함되어야 함
        assert "users" in message or "테이블" in message

    def test_missing_template_variable_handled(self) -> None:
        """누락된 템플릿 변수 처리"""
        # 변수 없이 호출해도 에러가 발생하지 않아야 함
        message = get_error_message(ErrorCode.SCHEMA_NOT_FOUND)
        assert isinstance(message, str)


class TestErrorCodeEnum:
    """에러 코드 Enum 테스트"""

    def test_all_codes_are_strings(self) -> None:
        """모든 에러 코드가 문자열인지 확인"""
        for code in ErrorCode:
            assert isinstance(code.value, str)

    def test_codes_are_uppercase(self) -> None:
        """에러 코드가 대문자인지 확인"""
        for code in ErrorCode:
            assert code.value == code.value.upper()

    def test_no_duplicate_codes(self) -> None:
        """중복된 에러 코드가 없는지 확인"""
        values = [code.value for code in ErrorCode]
        assert len(values) == len(set(values))
