"""
쿼리 검증 노드

3단계 점진적 검증을 통해 생성된 SQL 쿼리의 안전성을 검증합니다.
"""

import logging

from app.agent.state import Text2SQLAgentState
from app.config import get_settings
from app.database.schema import get_database_schema
from app.llm.factory import get_chat_model
from app.validation.keyword_validator import validate_query_keywords
from app.validation.schema_validator import validate_query_schema
from app.validation.semantic_validator import (
    validate_query_semantic,
    validate_query_semantic_sync,
)

logger = logging.getLogger(__name__)


async def query_validation_node(state: Text2SQLAgentState) -> dict[str, object]:
    """
    쿼리 검증 노드

    3단계 점진적 검증을 수행합니다:
    1단계: 키워드 검증 (위험 키워드 감지)
    2단계: 스키마 검증 (테이블/컬럼 존재 확인)
    3단계: 시맨틱 검증 (LLM 기반 의도 분석)

    Args:
        state: 현재 에이전트 상태

    Returns:
        업데이트할 상태 딕셔너리
    """
    settings = get_settings()
    generated_query = state.get("generated_query", "")

    logger.info(f"쿼리 검증 시작 - 쿼리: {generated_query[:100]}...")

    # 쿼리가 없으면 검증 스킵
    if not generated_query:
        logger.warning("검증할 쿼리가 없습니다.")
        return {
            "is_query_valid": False,
            "validation_errors": ["검증할 쿼리가 없습니다."],
            "execution_error": "쿼리가 생성되지 않았습니다.",
        }

    validation_errors: list[str] = []

    # === 1단계: 키워드 검증 ===
    logger.debug("1단계: 키워드 검증 시작")
    keyword_result = validate_query_keywords(generated_query)

    if not keyword_result.is_valid:
        logger.warning(
            f"키워드 검증 실패: {keyword_result.detected_keywords}"
        )
        validation_errors.append(
            f"[키워드] {keyword_result.error_message}"
        )
        return {
            "is_query_valid": False,
            "validation_errors": validation_errors,
            "execution_error": keyword_result.error_message,
        }

    logger.debug("1단계: 키워드 검증 통과")

    # === 2단계: 스키마 검증 ===
    logger.debug("2단계: 스키마 검증 시작")

    try:
        # 스키마 가져오기 (캐시 사용)
        schema = await get_database_schema()
        schema_result = validate_query_schema(generated_query, schema)

        if not schema_result.is_valid:
            logger.warning(
                f"스키마 검증 실패: tables={schema_result.invalid_tables}, "
                f"columns={schema_result.invalid_columns}"
            )
            validation_errors.append(
                f"[스키마] {schema_result.error_message}"
            )
            return {
                "is_query_valid": False,
                "validation_errors": validation_errors,
                "execution_error": schema_result.error_message,
            }

        logger.debug(
            f"2단계: 스키마 검증 통과 - 참조 테이블: {schema_result.referenced_tables}"
        )

    except Exception as e:
        logger.error(f"스키마 검증 중 오류: {e}")
        # 스키마 조회 실패 시에도 검증 계속 진행
        logger.warning("스키마 검증을 건너뜁니다.")

    # === 3단계: 시맨틱 검증 ===
    logger.debug("3단계: 시맨틱 검증 시작")

    # 먼저 규칙 기반 검증
    sync_result = validate_query_semantic_sync(
        generated_query,
        state.get("user_question"),
    )

    if not sync_result.is_valid:
        logger.warning(f"시맨틱 검증 실패 (규칙 기반): {sync_result.reason}")
        validation_errors.append(
            f"[시맨틱] {sync_result.error_message}"
        )
        return {
            "is_query_valid": False,
            "validation_errors": validation_errors,
            "execution_error": sync_result.error_message,
        }

    # LLM 기반 검증 (선택적)
    if settings.enable_semantic_validation:
        try:
            llm = get_chat_model()
            async_result = await validate_query_semantic(
                generated_query,
                llm,
                state.get("user_question"),
            )

            if not async_result.is_valid and async_result.is_dangerous:
                logger.warning(
                    f"시맨틱 검증 실패 (LLM): {async_result.reason}"
                )
                validation_errors.append(
                    f"[시맨틱] {async_result.error_message}"
                )
                return {
                    "is_query_valid": False,
                    "validation_errors": validation_errors,
                    "execution_error": async_result.error_message,
                }

            logger.debug(
                f"3단계: 시맨틱 검증 통과 - 신뢰도: {async_result.confidence:.2f}"
            )

        except Exception as e:
            logger.warning(f"LLM 시맨틱 검증 중 오류 (건너뜀): {e}")
    else:
        logger.debug("3단계: 시맨틱 검증 통과 (규칙 기반)")

    # === 모든 검증 통과 ===
    logger.info("쿼리 검증 완료 - 모든 단계 통과")

    return {
        "is_query_valid": True,
        "validation_errors": [],
        "execution_error": None,
    }


async def should_retry_generation(state: Text2SQLAgentState) -> bool:
    """
    검증 실패 시 쿼리 재생성 여부 결정

    Args:
        state: 현재 에이전트 상태

    Returns:
        재생성 필요 여부
    """
    settings = get_settings()
    attempt = state.get("generation_attempt", 0)

    # 최대 재시도 횟수 확인
    if attempt >= settings.max_generation_attempts:
        logger.info(f"최대 재시도 횟수({settings.max_generation_attempts}) 도달")
        return False

    # 검증 오류가 있는 경우
    validation_errors = state.get("validation_errors", [])
    if validation_errors:
        # 스키마 오류는 재시도해도 해결되지 않을 가능성 높음
        for error in validation_errors:
            if "[스키마]" in error:
                logger.info("스키마 오류는 재시도로 해결되지 않음")
                return False

        # 키워드 오류도 마찬가지
        for error in validation_errors:
            if "[키워드]" in error:
                logger.info("키워드 오류는 재시도로 해결되지 않음")
                return False

        # 시맨틱 오류는 재시도 가능
        return True

    return False
