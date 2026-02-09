"""
쿼리 검증 노드

LangGraph 워크플로우에서 생성된 SQL 쿼리의 안전성을 검증합니다.
3단계 점진적 검증을 수행합니다:
1. 키워드 검증 (가장 빠름)
2. 스키마 검증
3. 시맨틱 검증 (LLM 사용)
"""

import logging
from dataclasses import dataclass
from typing import Literal

from langchain_core.language_models import BaseChatModel

from app.agent.decorators import with_debug_timing
from app.agent.state import Text2SQLAgentState, update_execution, update_generation, update_validation
from app.database.schema import get_database_schema
from app.errors.exceptions import DangerousQueryError, QueryValidationError
from app.llm.factory import get_llm
from app.models.entities import DatabaseSchema
from app.validation.keyword_validator import KeywordValidator, get_keyword_validator
from app.validation.schema_validator import SchemaValidator
from app.validation.semantic_validator import (
    SemanticValidator,
    quick_pattern_check,
)

logger = logging.getLogger(__name__)

# 최대 재시도 횟수
MAX_VALIDATION_RETRIES = 3


@dataclass
class ValidationPipelineResult:
    """검증 파이프라인 결과"""

    is_valid: bool
    """검증 통과 여부"""

    blocked_at_layer: Literal["keyword", "schema", "semantic"] | None
    """차단된 검증 단계 (None이면 모두 통과)"""

    error_message: str
    """에러 메시지"""

    details: dict[str, object]
    """상세 정보"""


async def validate_query_pipeline(
    query: str,
    schema: DatabaseSchema,
    llm: BaseChatModel | None = None,
    skip_semantic: bool = False,
) -> ValidationPipelineResult:
    """
    3단계 쿼리 검증 파이프라인 실행

    각 단계에서 실패하면 즉시 반환하여 불필요한 검증을 방지합니다.

    Args:
        query: 검증할 SQL 쿼리
        schema: 데이터베이스 스키마
        llm: 시맨틱 검증용 LLM (None이면 건너뜀)
        skip_semantic: True면 시맨틱 검증 건너뜀

    Returns:
        ValidationPipelineResult: 검증 결과
    """
    logger.info(f"쿼리 검증 파이프라인 시작: {query[:100]}...")

    # 1단계: 키워드 검증 (가장 빠름)
    logger.debug("1단계: 키워드 검증")
    keyword_validator = get_keyword_validator()
    keyword_result = keyword_validator.validate(query)

    if not keyword_result.is_valid:
        logger.warning(f"키워드 검증 실패: {keyword_result.detected_keywords}")
        return ValidationPipelineResult(
            is_valid=False,
            blocked_at_layer="keyword",
            error_message=keyword_result.error_message,
            details={
                "detected_keywords": keyword_result.detected_keywords,
            },
        )

    # 2단계: 스키마 검증
    logger.debug("2단계: 스키마 검증")
    schema_validator = SchemaValidator(schema)
    schema_result = schema_validator.validate(query)

    if not schema_result.is_valid:
        logger.warning(
            f"스키마 검증 실패: 테이블={schema_result.invalid_tables}, "
            f"컬럼={schema_result.invalid_columns}"
        )
        return ValidationPipelineResult(
            is_valid=False,
            blocked_at_layer="schema",
            error_message=schema_result.error_message,
            details={
                "invalid_tables": schema_result.invalid_tables,
                "invalid_columns": schema_result.invalid_columns,
            },
        )

    # 3단계: 시맨틱 검증 (LLM 사용)
    if skip_semantic or llm is None:
        logger.debug("시맨틱 검증 건너뜀")
        return ValidationPipelineResult(
            is_valid=True,
            blocked_at_layer=None,
            error_message="",
            details={"skipped_semantic": True},
        )

    # 빠른 패턴 검사 (LLM 호출 전)
    pattern_safe, pattern_reason = quick_pattern_check(query)
    if not pattern_safe:
        logger.warning(f"패턴 검사 실패: {pattern_reason}")
        return ValidationPipelineResult(
            is_valid=False,
            blocked_at_layer="semantic",
            error_message="보안상의 이유로 이 쿼리는 실행할 수 없습니다.",
            details={"pattern_check_failed": pattern_reason},
        )

    logger.debug("3단계: 시맨틱 검증")
    semantic_validator = SemanticValidator(llm)
    semantic_result = await semantic_validator.validate(query)

    if not semantic_result.is_valid:
        logger.warning(f"시맨틱 검증 실패: {semantic_result.reason}")
        return ValidationPipelineResult(
            is_valid=False,
            blocked_at_layer="semantic",
            error_message=semantic_result.error_message,
            details={
                "semantic_reason": semantic_result.reason,
                "confidence": semantic_result.confidence,
            },
        )

    logger.info("쿼리 검증 통과")
    return ValidationPipelineResult(
        is_valid=True,
        blocked_at_layer=None,
        error_message="",
        details={},
    )


@with_debug_timing("query_validation")
async def query_validation_node(
    state: Text2SQLAgentState,
) -> dict[str, object]:
    """
    쿼리 검증 LangGraph 노드

    생성된 쿼리를 3단계 검증 파이프라인으로 검증합니다.
    검증 실패 시 에러 메시지와 함께 재생성을 트리거합니다.

    Args:
        state: 현재 에이전트 상태

    Returns:
        업데이트된 상태 필드
    """
    # Nested 구조에서 값 추출
    generated_query = state["generation"]["generated_query"]
    generation_attempt = state["generation"]["generation_attempt"]

    logger.info(
        f"쿼리 검증 노드 실행 (시도 {generation_attempt}/{MAX_VALIDATION_RETRIES})"
    )

    # 쿼리가 없는 경우
    if not generated_query:
        logger.warning("검증할 쿼리 없음")
        return {
            "validation": update_validation(state, is_query_valid=False, validation_errors=["쿼리가 생성되지 않았습니다."]),
        }

    try:
        # 스키마 가져오기
        schema = await get_database_schema()

        # LLM 가져오기 (시맨틱 검증용)
        # 빠른 모델 사용, state에서 선택한 provider 사용
        llm_provider = state["input"]["llm_provider"]
        llm = get_llm(provider_type=llm_provider, use_fast_model=True)

        # 검증 파이프라인 실행
        result = await validate_query_pipeline(
            query=generated_query,
            schema=schema,
            llm=llm,
            skip_semantic=False,
        )

        if result.is_valid:
            # 권한 검증: accessible_tables에 포함되지 않은 테이블 참조 차단
            accessible_tables = state["auth"]["accessible_tables"]
            if accessible_tables:
                from app.auth.permissions import extract_tables_from_query

                referenced_tables = extract_tables_from_query(generated_query)
                accessible_lower = [t.lower() for t in accessible_tables]
                unauthorized = [
                    t for t in referenced_tables if t.lower() not in accessible_lower
                ]
                if unauthorized:
                    logger.warning(f"권한 없는 테이블 접근 시도: {unauthorized}")
                    return {
                        "validation": update_validation(state, is_query_valid=False, validation_errors=[f"접근 권한이 없는 테이블이 포함되어 있습니다: {', '.join(unauthorized)}"]),
                    }

            return {
                "validation": update_validation(state, is_query_valid=True, validation_errors=[]),
            }
        else:
            # 검증 실패
            error_messages = [result.error_message]

            # 재시도 가능 여부 확인
            if generation_attempt < MAX_VALIDATION_RETRIES:
                # 재생성을 위한 힌트 추가
                if result.blocked_at_layer == "keyword":
                    error_messages.append(
                        "힌트: SELECT 문만 사용하여 쿼리를 생성하세요."
                    )
                elif result.blocked_at_layer == "schema":
                    error_messages.append(
                        f"힌트: 유효한 테이블과 컬럼을 사용하세요. "
                        f"오류: {result.details}"
                    )
                elif result.blocked_at_layer == "semantic":
                    error_messages.append("힌트: 더 간단하고 명확한 쿼리를 생성하세요.")

            return {
                "validation": update_validation(state, is_query_valid=False, validation_errors=error_messages),
                "generation": update_generation(state, generation_attempt=generation_attempt + 1),
            }

    except DangerousQueryError as e:
        logger.warning(f"위험한 쿼리 감지: {e}")
        return {
            "validation": update_validation(state, is_query_valid=False, validation_errors=[e.user_message]),
            "execution": update_execution(state, execution_error=e.user_message),
        }

    except QueryValidationError as e:
        logger.warning(f"쿼리 검증 오류: {e}")
        return {
            "validation": update_validation(state, is_query_valid=False, validation_errors=[e.user_message]),
            "generation": update_generation(state, generation_attempt=generation_attempt + 1),
        }

    except Exception as e:
        logger.error(f"쿼리 검증 중 예외 발생: {e}", exc_info=True)
        return {
            "validation": update_validation(state, is_query_valid=False, validation_errors=["쿼리 검증 중 문제가 발생했습니다. 다시 시도해주세요."]),
            "generation": update_generation(state, generation_attempt=generation_attempt + 1),
        }


def should_retry_generation(state: Text2SQLAgentState) -> bool:
    """
    쿼리 재생성 여부 결정

    Args:
        state: 현재 에이전트 상태

    Returns:
        재생성 필요 여부
    """
    is_valid = state["validation"]["is_query_valid"]
    attempt = state["generation"]["generation_attempt"]

    if is_valid:
        return False

    if attempt >= MAX_VALIDATION_RETRIES:
        logger.warning(f"최대 재시도 횟수({MAX_VALIDATION_RETRIES}) 도달")
        return False

    return True
