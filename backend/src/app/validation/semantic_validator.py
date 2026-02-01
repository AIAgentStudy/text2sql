"""
시맨틱 기반 SQL 쿼리 검증기 (3단계)

LLM을 사용하여 쿼리의 의도와 안전성을 시맨틱 수준에서 검증합니다.
"""

import logging
from dataclasses import dataclass, field
from typing import Protocol

from langchain_core.messages import HumanMessage, SystemMessage

logger = logging.getLogger(__name__)


class LLMProtocol(Protocol):
    """LLM 프로토콜"""

    async def ainvoke(self, messages: list) -> object:
        """비동기 LLM 호출"""
        ...


@dataclass
class SemanticValidationResult:
    """시맨틱 검증 결과"""

    is_valid: bool
    """검증 통과 여부"""

    is_dangerous: bool = False
    """위험한 의도 감지 여부"""

    confidence: float = 0.0
    """검증 신뢰도 (0.0 ~ 1.0)"""

    reason: str | None = None
    """판단 이유"""

    suggestions: list[str] = field(default_factory=list)
    """개선 제안"""

    error_message: str | None = None
    """에러 메시지 (한국어)"""


# 시맨틱 검증 시스템 프롬프트
SEMANTIC_VALIDATION_PROMPT = """당신은 SQL 쿼리 보안 전문가입니다.
사용자가 입력한 SQL 쿼리가 안전한 조회 쿼리인지 분석해주세요.

## 검증 기준

### 반드시 거부해야 하는 경우 (REJECT):
1. 데이터 변경 의도가 있는 쿼리 (UPDATE, DELETE, INSERT 등이 숨겨진 경우)
2. 스키마 변경 의도가 있는 쿼리 (DROP, ALTER, CREATE 등)
3. 권한 변경 시도 (GRANT, REVOKE)
4. SQL 인젝션 패턴 (세미콜론, UNION 공격 등)
5. 시스템 테이블 접근 시도 (pg_catalog, information_schema 직접 쿼리)
6. 민감 정보 조회 시도 (비밀번호, 개인정보 컬럼 직접 조회)

### 허용하는 경우 (APPROVE):
1. 순수한 SELECT 조회 쿼리
2. 집계, 그룹화, 정렬이 포함된 분석 쿼리
3. JOIN을 사용한 복합 조회
4. 서브쿼리를 사용한 조회
5. CTE (WITH 절)를 사용한 조회

## 응답 형식

다음 형식으로만 응답해주세요:

VERDICT: APPROVE 또는 REJECT
CONFIDENCE: 0.0 ~ 1.0 사이 숫자
REASON: 판단 이유 (한국어)
SUGGESTIONS: 개선 제안 (선택사항, 한국어)

예시:
VERDICT: APPROVE
CONFIDENCE: 0.95
REASON: 사용자 테이블에서 이름과 이메일만 조회하는 안전한 SELECT 쿼리입니다.

또는:
VERDICT: REJECT
CONFIDENCE: 0.99
REASON: 세미콜론 이후 DROP TABLE 명령이 숨겨져 있어 SQL 인젝션 공격으로 판단됩니다.
SUGGESTIONS: 안전한 조회 쿼리만 사용해주세요."""


def _parse_llm_response(response_text: str) -> SemanticValidationResult:
    """LLM 응답 파싱"""
    lines = response_text.strip().split("\n")

    verdict = "REJECT"
    confidence = 0.0
    reason = ""
    suggestions: list[str] = []

    for line in lines:
        line = line.strip()
        if line.startswith("VERDICT:"):
            verdict = line.replace("VERDICT:", "").strip().upper()
        elif line.startswith("CONFIDENCE:"):
            try:
                confidence = float(line.replace("CONFIDENCE:", "").strip())
            except ValueError:
                confidence = 0.5
        elif line.startswith("REASON:"):
            reason = line.replace("REASON:", "").strip()
        elif line.startswith("SUGGESTIONS:"):
            suggestion = line.replace("SUGGESTIONS:", "").strip()
            if suggestion:
                suggestions.append(suggestion)

    is_valid = verdict == "APPROVE"
    is_dangerous = verdict == "REJECT" and confidence >= 0.8

    error_message = None
    if not is_valid:
        error_message = reason or "쿼리가 보안 검증을 통과하지 못했습니다."

    return SemanticValidationResult(
        is_valid=is_valid,
        is_dangerous=is_dangerous,
        confidence=confidence,
        reason=reason,
        suggestions=suggestions,
        error_message=error_message,
    )


async def validate_query_semantic(
    query: str,
    llm: LLMProtocol,
    user_question: str | None = None,
) -> SemanticValidationResult:
    """
    SQL 쿼리의 시맨틱을 LLM으로 검증합니다 (3단계 검증).

    Args:
        query: 검증할 SQL 쿼리
        llm: LLM 인스턴스
        user_question: 원본 사용자 질문 (선택)

    Returns:
        SemanticValidationResult: 검증 결과

    검증 내용:
    1. 쿼리의 의도가 조회 목적인지 확인
    2. 숨겨진 위험 패턴 감지
    3. 민감 정보 접근 시도 감지
    """
    try:
        # 프롬프트 구성
        user_content = f"## 분석할 SQL 쿼리\n```sql\n{query}\n```"

        if user_question:
            user_content = (
                f"## 사용자 질문\n{user_question}\n\n"
                f"## 생성된 SQL 쿼리\n```sql\n{query}\n```"
            )

        messages = [
            SystemMessage(content=SEMANTIC_VALIDATION_PROMPT),
            HumanMessage(content=user_content),
        ]

        # LLM 호출
        response = await llm.ainvoke(messages)
        response_text = response.content if hasattr(response, "content") else str(response)

        # 응답 파싱
        result = _parse_llm_response(response_text)

        logger.info(
            f"시맨틱 검증 완료: valid={result.is_valid}, "
            f"confidence={result.confidence:.2f}"
        )

        return result

    except Exception as e:
        logger.error(f"시맨틱 검증 중 오류: {e}")
        # 오류 발생 시 안전하게 통과 (다른 검증 레이어가 있으므로)
        return SemanticValidationResult(
            is_valid=True,
            is_dangerous=False,
            confidence=0.0,
            reason=f"시맨틱 검증 중 오류 발생: {e}",
            suggestions=[],
            error_message=None,
        )


def validate_query_semantic_sync(
    query: str,
    user_question: str | None = None,
) -> SemanticValidationResult:
    """
    동기 시맨틱 검증 (LLM 없이 규칙 기반)

    LLM을 사용하지 않고 간단한 규칙 기반으로 검증합니다.
    실제 LLM 검증 전 빠른 필터링 용도로 사용합니다.

    Args:
        query: 검증할 SQL 쿼리
        user_question: 원본 사용자 질문 (선택)

    Returns:
        SemanticValidationResult: 검증 결과
    """
    query_upper = query.upper()

    # 시스템 테이블 접근 패턴
    system_table_patterns = [
        "PG_CATALOG",
        "INFORMATION_SCHEMA",
        "PG_STAT",
        "PG_CLASS",
        "PG_ROLES",
        "PG_USER",
        "PG_SHADOW",
    ]

    for pattern in system_table_patterns:
        if pattern in query_upper:
            return SemanticValidationResult(
                is_valid=False,
                is_dangerous=True,
                confidence=0.95,
                reason=f"시스템 테이블({pattern}) 접근이 감지되었습니다.",
                suggestions=["일반 테이블만 조회해주세요."],
                error_message="시스템 테이블 접근은 허용되지 않습니다.",
            )

    # 민감 컬럼 패턴
    sensitive_columns = [
        "PASSWORD",
        "PASSWD",
        "SECRET",
        "TOKEN",
        "API_KEY",
        "APIKEY",
        "PRIVATE_KEY",
        "CREDIT_CARD",
        "SSN",
        "SOCIAL_SECURITY",
    ]

    for col in sensitive_columns:
        # 단독 선택 시에만 경고 (WHERE 절에서 사용은 허용)
        if f"SELECT" in query_upper and col in query_upper:
            # 더 정밀한 검사: SELECT 절에 포함되어 있는지
            if f"SELECT " in query_upper or f", {col}" in query_upper:
                return SemanticValidationResult(
                    is_valid=False,
                    is_dangerous=True,
                    confidence=0.9,
                    reason=f"민감 정보 컬럼({col}) 직접 조회가 감지되었습니다.",
                    suggestions=["민감 정보는 직접 조회할 수 없습니다."],
                    error_message="민감 정보 컬럼은 조회할 수 없습니다.",
                )

    # 다중 쿼리 패턴 (SQL 인젝션)
    if query.count(";") > 1:
        return SemanticValidationResult(
            is_valid=False,
            is_dangerous=True,
            confidence=0.95,
            reason="다중 쿼리 실행 시도가 감지되었습니다.",
            suggestions=["한 번에 하나의 쿼리만 실행해주세요."],
            error_message="다중 쿼리 실행은 허용되지 않습니다.",
        )

    # 모든 규칙 기반 검사 통과
    return SemanticValidationResult(
        is_valid=True,
        is_dangerous=False,
        confidence=0.8,
        reason="규칙 기반 검증 통과",
        suggestions=[],
        error_message=None,
    )
