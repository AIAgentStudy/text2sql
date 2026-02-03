"""
스키마 조회 노드

데이터베이스 스키마를 조회하고 LLM에 전달할 형식으로 변환합니다.
사용자 권한에 따라 접근 가능한 테이블만 포함합니다.
"""

import logging

from app.agent.state import Text2SQLAgentState
from app.database.schema import format_schema_for_llm, get_database_schema
from app.models.entities import DatabaseSchema

logger = logging.getLogger(__name__)


def filter_schema_by_accessible_tables(
    schema: DatabaseSchema,
    accessible_tables: list[str],
) -> DatabaseSchema:
    """
    접근 가능한 테이블만 포함하도록 스키마 필터링

    Args:
        schema: 전체 데이터베이스 스키마
        accessible_tables: 접근 가능한 테이블 목록

    Returns:
        필터링된 스키마
    """
    if not accessible_tables:
        # 접근 가능한 테이블이 없으면 빈 스키마 반환
        return DatabaseSchema(tables=[], last_updated_at=schema.last_updated_at)

    # 접근 가능한 테이블만 필터링
    filtered_tables = [
        table for table in schema.tables
        if table.name.lower() in [t.lower() for t in accessible_tables]
    ]

    return DatabaseSchema(tables=filtered_tables, last_updated_at=schema.last_updated_at)


async def schema_retrieval_node(state: Text2SQLAgentState) -> dict[str, object]:
    """
    스키마 조회 노드

    데이터베이스 스키마를 조회하고 상태를 업데이트합니다.
    사용자 권한에 따라 접근 가능한 테이블만 포함합니다.

    Args:
        state: 현재 에이전트 상태

    Returns:
        업데이트할 상태 딕셔너리
    """
    logger.info(f"스키마 조회 시작 - 세션: {state['session_id']}")

    try:
        # 스키마 조회 (캐시 사용)
        schema = await get_database_schema()

        # 사용자 권한에 따라 스키마 필터링
        accessible_tables = state.get("accessible_tables", [])
        if accessible_tables:
            schema = filter_schema_by_accessible_tables(schema, accessible_tables)
            logger.info(f"권한에 따라 스키마 필터링 - 접근 가능: {len(accessible_tables)}개 테이블")

        # LLM 프롬프트용 문자열로 변환
        schema_str = format_schema_for_llm(schema)

        # 테이블 목록 추출
        table_names = [table.name for table in schema.tables]

        logger.info(f"스키마 조회 완료 - {len(table_names)}개 테이블")

        return {
            "database_schema": schema_str,
            "relevant_tables": table_names,
        }

    except Exception as e:
        logger.error(f"스키마 조회 실패: {e}")
        return {
            "database_schema": "",
            "relevant_tables": [],
            "execution_error": f"스키마를 불러올 수 없습니다: {e}",
        }
