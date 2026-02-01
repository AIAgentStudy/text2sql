"""
키워드 기반 SQL 쿼리 안전 검증기 (1단계)

위험한 SQL 키워드(UPDATE, DELETE, INSERT 등)를 감지하여 차단합니다.
"""

import re
from dataclasses import dataclass, field

# 위험 키워드 목록 (대문자)
DANGEROUS_KEYWORDS: frozenset[str] = frozenset(
    {
        "UPDATE",
        "DELETE",
        "INSERT",
        "DROP",
        "ALTER",
        "TRUNCATE",
        "GRANT",
        "REVOKE",
        "CREATE",
        "MODIFY",
        "EXEC",
        "EXECUTE",
    }
)

# 허용되는 시작 키워드
ALLOWED_START_KEYWORDS: frozenset[str] = frozenset(
    {
        "SELECT",
        "WITH",  # CTE
    }
)

# 문자열 리터럴 패턴 (제거용)
STRING_LITERAL_PATTERN = re.compile(r"'[^']*'|\"[^\"]*\"")

# SQL 주석 패턴 (제거용)
COMMENT_PATTERN = re.compile(r"--.*?$|/\*.*?\*/", re.MULTILINE | re.DOTALL)


@dataclass
class KeywordValidationResult:
    """키워드 검증 결과"""

    is_valid: bool
    """검증 통과 여부"""

    detected_keywords: list[str] = field(default_factory=list)
    """감지된 위험 키워드 목록"""

    error_message: str | None = None
    """에러 메시지 (한국어)"""


def _remove_string_literals(query: str) -> str:
    """문자열 리터럴 제거"""
    return STRING_LITERAL_PATTERN.sub(" ", query)


def _remove_comments(query: str) -> str:
    """SQL 주석 제거"""
    return COMMENT_PATTERN.sub(" ", query)


def _normalize_query(query: str) -> str:
    """쿼리 정규화 (공백 정리, 대문자 변환)"""
    # 주석 제거
    query = _remove_comments(query)
    # 문자열 리터럴 제거
    query = _remove_string_literals(query)
    # 공백 정규화
    query = " ".join(query.split())
    # 대문자 변환
    return query.upper()


def _extract_keywords(normalized_query: str) -> list[str]:
    """정규화된 쿼리에서 SQL 키워드 추출"""
    # 단어 경계로 분리
    word_pattern = re.compile(r"\b([A-Z_]+)\b")
    return word_pattern.findall(normalized_query)


def _detect_dangerous_keywords(keywords: list[str]) -> list[str]:
    """위험 키워드 감지"""
    detected = []
    for keyword in keywords:
        if keyword in DANGEROUS_KEYWORDS:
            if keyword not in detected:
                detected.append(keyword)
    return detected


def _check_start_keyword(normalized_query: str) -> bool:
    """쿼리가 허용된 키워드로 시작하는지 확인"""
    stripped = normalized_query.strip()
    if not stripped:
        return False

    for keyword in ALLOWED_START_KEYWORDS:
        if stripped.startswith(keyword):
            return True
    return False


def _generate_error_message(detected_keywords: list[str]) -> str:
    """한국어 에러 메시지 생성"""
    if not detected_keywords:
        return "조회 쿼리만 허용됩니다. SELECT로 시작하는 쿼리를 작성해주세요."

    keyword_names = {
        "UPDATE": "데이터 수정(UPDATE)",
        "DELETE": "데이터 삭제(DELETE)",
        "INSERT": "데이터 삽입(INSERT)",
        "DROP": "테이블/데이터베이스 삭제(DROP)",
        "ALTER": "스키마 변경(ALTER)",
        "TRUNCATE": "테이블 비우기(TRUNCATE)",
        "GRANT": "권한 부여(GRANT)",
        "REVOKE": "권한 회수(REVOKE)",
        "CREATE": "테이블/객체 생성(CREATE)",
        "MODIFY": "데이터 수정(MODIFY)",
        "EXEC": "프로시저 실행(EXEC)",
        "EXECUTE": "프로시저 실행(EXECUTE)",
    }

    names = [keyword_names.get(k, k) for k in detected_keywords]

    if len(names) == 1:
        return f"조회 요청만 가능합니다. {names[0]} 작업은 지원되지 않습니다."
    else:
        return f"조회 요청만 가능합니다. 다음 작업은 지원되지 않습니다: {', '.join(names)}"


def validate_query_keywords(query: str) -> KeywordValidationResult:
    """
    SQL 쿼리의 키워드를 검증합니다 (1단계 검증).

    Args:
        query: 검증할 SQL 쿼리

    Returns:
        KeywordValidationResult: 검증 결과

    검증 규칙:
    1. 빈 쿼리 거부
    2. SELECT 또는 WITH로 시작해야 함
    3. 위험 키워드(UPDATE, DELETE 등) 포함 시 거부
    """
    # 빈 쿼리 체크
    if not query or not query.strip():
        return KeywordValidationResult(
            is_valid=False,
            detected_keywords=[],
            error_message="쿼리가 비어있습니다.",
        )

    # 쿼리 정규화
    normalized = _normalize_query(query)

    # 빈 쿼리 체크 (정규화 후)
    if not normalized.strip():
        return KeywordValidationResult(
            is_valid=False,
            detected_keywords=[],
            error_message="쿼리가 비어있습니다.",
        )

    # 키워드 추출
    keywords = _extract_keywords(normalized)

    # 위험 키워드 감지
    detected = _detect_dangerous_keywords(keywords)

    if detected:
        return KeywordValidationResult(
            is_valid=False,
            detected_keywords=detected,
            error_message=_generate_error_message(detected),
        )

    # 시작 키워드 확인
    if not _check_start_keyword(normalized):
        return KeywordValidationResult(
            is_valid=False,
            detected_keywords=[],
            error_message="조회 쿼리만 허용됩니다. SELECT로 시작하는 쿼리를 작성해주세요.",
        )

    # 모든 검증 통과
    return KeywordValidationResult(
        is_valid=True,
        detected_keywords=[],
        error_message=None,
    )
