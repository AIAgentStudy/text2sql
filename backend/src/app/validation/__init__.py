"""
SQL 쿼리 검증 모듈

3단계 점진적 검증을 통해 안전한 쿼리만 실행되도록 합니다.

1단계: 키워드 검증 (keyword_validator)
2단계: 스키마 검증 (schema_validator)
3단계: 시맨틱 검증 (semantic_validator)
"""

from app.validation.keyword_validator import (
    DANGEROUS_KEYWORDS,
    KeywordValidationResult,
    validate_query_keywords,
)
from app.validation.schema_validator import (
    SchemaValidationResult,
    validate_query_schema,
)
from app.validation.semantic_validator import (
    SemanticValidationResult,
    validate_query_semantic,
    validate_query_semantic_sync,
)

__all__ = [
    # 키워드 검증
    "DANGEROUS_KEYWORDS",
    "KeywordValidationResult",
    "validate_query_keywords",
    # 스키마 검증
    "SchemaValidationResult",
    "validate_query_schema",
    # 시맨틱 검증
    "SemanticValidationResult",
    "validate_query_semantic",
    "validate_query_semantic_sync",
]
