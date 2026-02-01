"""
키워드 기반 SQL 쿼리 검증기

1단계 검증: 위험한 SQL 키워드를 감지하여 데이터 변경 쿼리를 차단합니다.
"""

import re
from dataclasses import dataclass

# 위험한 SQL 키워드 목록
# DML (Data Manipulation Language)
# DDL (Data Definition Language)
# DCL (Data Control Language)
# 실행 명령
DANGEROUS_KEYWORDS: tuple[str, ...] = (
    # DML - 데이터 조작
    "UPDATE",
    "DELETE",
    "INSERT",
    "TRUNCATE",
    "MERGE",
    "UPSERT",
    # DDL - 스키마 변경
    "DROP",
    "ALTER",
    "CREATE",
    "RENAME",
    # DCL - 권한 제어
    "GRANT",
    "REVOKE",
    # 실행 명령
    "EXEC",
    "EXECUTE",
    "CALL",
    # PostgreSQL 특수 명령
    "COPY",
    "VACUUM",
    "ANALYZE",
    "REINDEX",
    "CLUSTER",
    "REFRESH",
    # 트랜잭션 제어 (읽기 전용 환경에서는 불필요)
    "COMMIT",
    "ROLLBACK",
    "SAVEPOINT",
    # 세션/설정 변경
    "SET",
    "RESET",
    "LOAD",
)


@dataclass
class KeywordValidationResult:
    """키워드 검증 결과"""

    is_valid: bool
    """검증 통과 여부"""

    detected_keywords: list[str]
    """감지된 위험 키워드 목록"""

    error_message: str
    """사용자에게 표시할 에러 메시지"""


class KeywordValidator:
    """
    키워드 기반 SQL 쿼리 검증기

    위험한 SQL 키워드를 감지하여 데이터 변경 쿼리를 사전에 차단합니다.
    이 검증은 가장 빠르게 수행되며, 의심스러운 쿼리를 조기에 차단합니다.
    """

    def __init__(self, additional_keywords: list[str] | None = None) -> None:
        """
        검증기 초기화

        Args:
            additional_keywords: 추가로 차단할 키워드 목록
        """
        self._keywords = set(DANGEROUS_KEYWORDS)
        if additional_keywords:
            self._keywords.update(kw.upper() for kw in additional_keywords)

        # 키워드 매칭용 정규식 패턴 생성
        # 단어 경계를 사용하여 부분 매칭 방지 (예: "SELECTED"에서 "SELECT" 매칭 안함)
        keywords_pattern = "|".join(re.escape(kw) for kw in self._keywords)
        self._pattern = re.compile(
            rf"\b({keywords_pattern})\b",
            re.IGNORECASE,
        )

    def validate(self, query: str) -> KeywordValidationResult:
        """
        SQL 쿼리에서 위험한 키워드 검사

        Args:
            query: 검사할 SQL 쿼리

        Returns:
            KeywordValidationResult: 검증 결과
        """
        # 빈 쿼리 처리
        if not query or not query.strip():
            return KeywordValidationResult(
                is_valid=False,
                detected_keywords=[],
                error_message="쿼리가 비어있습니다.",
            )

        # 주석 제거 (-- 스타일과 /* */ 스타일 모두)
        cleaned_query = self._remove_comments(query)

        # 문자열 리터럴 내 키워드는 무시 (고급 처리)
        # 간단한 구현에서는 전체 쿼리를 검사
        # 보수적 접근: 문자열 내 키워드도 일단 검사 (안전을 위해)

        # 위험 키워드 검색
        matches = self._pattern.findall(cleaned_query)
        detected = list(set(kw.upper() for kw in matches))

        if detected:
            return KeywordValidationResult(
                is_valid=False,
                detected_keywords=detected,
                error_message=self._generate_error_message(detected),
            )

        # SELECT로 시작하는지 확인 (추가 안전장치)
        normalized = cleaned_query.strip().upper()
        if not normalized.startswith(("SELECT", "WITH")):
            return KeywordValidationResult(
                is_valid=False,
                detected_keywords=[],
                error_message="조회(SELECT) 쿼리만 허용됩니다.",
            )

        return KeywordValidationResult(
            is_valid=True,
            detected_keywords=[],
            error_message="",
        )

    def _remove_comments(self, query: str) -> str:
        """
        SQL 쿼리에서 주석 제거

        Args:
            query: 원본 쿼리

        Returns:
            주석이 제거된 쿼리
        """
        # -- 스타일 주석 제거
        query = re.sub(r"--[^\n]*", "", query)
        # /* */ 스타일 주석 제거
        query = re.sub(r"/\*[\s\S]*?\*/", "", query)
        return query

    def _generate_error_message(self, keywords: list[str]) -> str:
        """
        사용자 친화적 에러 메시지 생성

        Args:
            keywords: 감지된 키워드 목록

        Returns:
            에러 메시지
        """
        if len(keywords) == 1:
            return f"조회 요청만 가능합니다. 데이터 수정({keywords[0]})은 지원되지 않습니다."
        else:
            keywords_str = ", ".join(keywords)
            return f"조회 요청만 가능합니다. 데이터 수정({keywords_str})은 지원되지 않습니다."

    def is_safe_keyword(self, keyword: str) -> bool:
        """
        특정 키워드가 안전한지 확인

        Args:
            keyword: 확인할 키워드

        Returns:
            안전 여부
        """
        return keyword.upper() not in self._keywords

    def get_dangerous_keywords(self) -> set[str]:
        """
        등록된 모든 위험 키워드 반환

        Returns:
            위험 키워드 집합
        """
        return self._keywords.copy()


# 모듈 레벨 싱글톤 인스턴스
_default_validator: KeywordValidator | None = None


def get_keyword_validator() -> KeywordValidator:
    """기본 키워드 검증기 인스턴스 반환"""
    global _default_validator
    if _default_validator is None:
        _default_validator = KeywordValidator()
    return _default_validator
