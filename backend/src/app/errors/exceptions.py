"""
커스텀 예외 클래스 정의

Text2SQL Agent에서 사용하는 모든 예외를 정의합니다.
"""

from abc import ABC, abstractmethod
from typing import Literal


class Text2SQLError(Exception, ABC):
    """Text2SQL 에이전트 기본 예외 클래스"""

    @property
    @abstractmethod
    def code(self) -> str:
        """에러 코드"""
        ...

    @property
    @abstractmethod
    def user_message(self) -> str:
        """사용자에게 표시할 메시지 (한국어)"""
        ...

    @property
    @abstractmethod
    def severity(self) -> Literal["user", "system", "security"]:
        """에러 심각도"""
        ...


class DangerousQueryError(Text2SQLError):
    """위험한 쿼리 감지 시 발생하는 예외"""

    def __init__(self, keyword: str) -> None:
        self.keyword = keyword
        super().__init__(f"위험한 키워드 감지: {keyword}")

    @property
    def code(self) -> str:
        return "DANGEROUS_QUERY"

    @property
    def user_message(self) -> str:
        return "조회 요청만 가능합니다. 데이터 수정은 지원되지 않습니다."

    @property
    def severity(self) -> Literal["user", "system", "security"]:
        return "security"


class QueryTimeoutError(Text2SQLError):
    """쿼리 실행 타임아웃 시 발생하는 예외"""

    def __init__(self, timeout_ms: int) -> None:
        self.timeout_ms = timeout_ms
        super().__init__(f"쿼리 타임아웃: {timeout_ms}ms 초과")

    @property
    def code(self) -> str:
        return "QUERY_TIMEOUT"

    @property
    def user_message(self) -> str:
        return "쿼리 실행 시간이 너무 깁니다. 더 구체적인 조건을 추가해주세요."

    @property
    def severity(self) -> Literal["user", "system", "security"]:
        return "user"


class QueryValidationError(Text2SQLError):
    """쿼리 검증 실패 시 발생하는 예외"""

    def __init__(self, message: str, layer: str = "unknown") -> None:
        self.layer = layer
        self._message = message
        super().__init__(f"쿼리 검증 실패 ({layer}): {message}")

    @property
    def code(self) -> str:
        return f"VALIDATION_ERROR_{self.layer.upper()}"

    @property
    def user_message(self) -> str:
        return self._message

    @property
    def severity(self) -> Literal["user", "system", "security"]:
        return "user"


class SchemaNotFoundError(Text2SQLError):
    """스키마를 찾을 수 없을 때 발생하는 예외"""

    def __init__(self, table_name: str | None = None) -> None:
        self.table_name = table_name
        if table_name:
            message = f'테이블 "{table_name}"을(를) 찾을 수 없습니다.'
        else:
            message = "데이터베이스 스키마를 불러올 수 없습니다."
        super().__init__(message)

    @property
    def code(self) -> str:
        return "SCHEMA_NOT_FOUND"

    @property
    def user_message(self) -> str:
        if self.table_name:
            return f'테이블 "{self.table_name}"을(를) 찾을 수 없습니다. 테이블 이름을 확인해주세요.'
        return "데이터베이스 스키마를 불러올 수 없습니다. 잠시 후 다시 시도해주세요."

    @property
    def severity(self) -> Literal["user", "system", "security"]:
        return "user"


class SessionNotFoundError(Text2SQLError):
    """세션을 찾을 수 없을 때 발생하는 예외"""

    def __init__(self, session_id: str) -> None:
        self.session_id = session_id
        super().__init__(f"세션을 찾을 수 없음: {session_id}")

    @property
    def code(self) -> str:
        return "SESSION_NOT_FOUND"

    @property
    def user_message(self) -> str:
        return "세션이 만료되었거나 존재하지 않습니다. 새로운 대화를 시작해주세요."

    @property
    def severity(self) -> Literal["user", "system", "security"]:
        return "user"


class SessionExpiredError(Text2SQLError):
    """세션이 만료되었을 때 발생하는 예외"""

    def __init__(self, session_id: str) -> None:
        self.session_id = session_id
        super().__init__(f"세션 만료: {session_id}")

    @property
    def code(self) -> str:
        return "SESSION_EXPIRED"

    @property
    def user_message(self) -> str:
        return "세션이 만료되었습니다. 새로운 대화를 시작해주세요."

    @property
    def severity(self) -> Literal["user", "system", "security"]:
        return "user"


class DatabaseConnectionError(Text2SQLError):
    """데이터베이스 연결 오류 시 발생하는 예외"""

    def __init__(self, detail: str = "") -> None:
        self.detail = detail
        super().__init__(f"데이터베이스 연결 오류: {detail}")

    @property
    def code(self) -> str:
        return "DATABASE_CONNECTION_ERROR"

    @property
    def user_message(self) -> str:
        return "현재 데이터를 가져올 수 없습니다. 잠시 후 다시 시도해주세요."

    @property
    def severity(self) -> Literal["user", "system", "security"]:
        return "system"


class LLMError(Text2SQLError):
    """LLM 호출 오류 시 발생하는 예외"""

    def __init__(self, provider: str, detail: str = "") -> None:
        self.provider = provider
        self.detail = detail
        super().__init__(f"LLM 오류 ({provider}): {detail}")

    @property
    def code(self) -> str:
        return "LLM_ERROR"

    @property
    def user_message(self) -> str:
        return "질문을 처리하는 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."

    @property
    def severity(self) -> Literal["user", "system", "security"]:
        return "system"


class QueryGenerationError(Text2SQLError):
    """쿼리 생성 실패 시 발생하는 예외"""

    def __init__(self, message: str = "") -> None:
        self._message = message or "쿼리를 생성할 수 없습니다."
        super().__init__(self._message)

    @property
    def code(self) -> str:
        return "QUERY_GENERATION_ERROR"

    @property
    def user_message(self) -> str:
        return "죄송합니다. 질문을 이해하지 못했어요. '지난달 매출은?' 처럼 구체적으로 질문해 주세요."

    @property
    def severity(self) -> Literal["user", "system", "security"]:
        return "user"


class EmptyResultError(Text2SQLError):
    """결과가 비어있을 때 발생하는 예외 (정보 제공용)"""

    def __init__(self) -> None:
        super().__init__("결과 없음")

    @property
    def code(self) -> str:
        return "EMPTY_RESULT"

    @property
    def user_message(self) -> str:
        return "조건에 맞는 데이터가 없습니다."

    @property
    def severity(self) -> Literal["user", "system", "security"]:
        return "user"
