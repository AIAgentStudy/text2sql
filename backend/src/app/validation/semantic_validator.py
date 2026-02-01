"""
시맨틱 기반 SQL 쿼리 검증기

3단계 검증: LLM을 사용하여 쿼리의 의도와 안전성을 분석합니다.
"""

import logging
from dataclasses import dataclass

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

logger = logging.getLogger(__name__)


VALIDATION_SYSTEM_PROMPT = """당신은 SQL 쿼리 보안 분석가입니다.
주어진 SQL 쿼리가 안전한 조회 쿼리인지 분석해주세요.

## 안전한 쿼리 (SAFE)
- 데이터를 읽기만 하는 SELECT 쿼리
- 집계, 필터링, 정렬, 조인 등 일반적인 조회 작업

## 위험한 쿼리 (UNSAFE)
- 시스템 테이블 접근 (pg_catalog, information_schema 등의 민감한 정보)
- 권한 상승 시도
- SQL 인젝션 패턴 (1=1, OR 1=1, 주석을 이용한 쿼리 조작 등)
- 대량 데이터 추출 시도 (LIMIT 없는 큰 테이블 전체 조회)
- UNION을 이용한 의심스러운 데이터 결합
- 서브쿼리를 통한 민감 정보 접근
- 의도적으로 복잡하게 작성된 쿼리 (난독화)

## 응답 형식
- 안전한 경우: "SAFE"
- 위험한 경우: "UNSAFE: [이유]"

반드시 SAFE 또는 UNSAFE로 시작하는 한 줄 응답만 해주세요."""


@dataclass
class SemanticValidationResult:
    """시맨틱 검증 결과"""

    is_valid: bool
    """검증 통과 여부"""

    reason: str
    """검증 결과 이유"""

    confidence: float
    """검증 신뢰도 (0.0 ~ 1.0)"""

    error_message: str
    """사용자에게 표시할 에러 메시지"""


class SemanticValidator:
    """
    LLM 기반 시맨틱 쿼리 검증기

    LLM을 사용하여 쿼리의 의도와 잠재적 위험을 분석합니다.
    키워드/스키마 검증을 통과한 쿼리에 대해 추가적인 보안 검사를 수행합니다.
    """

    def __init__(
        self,
        llm: BaseChatModel,
        strict_mode: bool = True,
    ) -> None:
        """
        검증기 초기화

        Args:
            llm: LangChain 호환 LLM 인스턴스
            strict_mode: True면 불확실한 경우 차단, False면 허용
        """
        self._llm = llm
        self._strict_mode = strict_mode

    async def validate(self, query: str) -> SemanticValidationResult:
        """
        SQL 쿼리의 시맨틱 유효성 검증

        Args:
            query: 검증할 SQL 쿼리

        Returns:
            SemanticValidationResult: 검증 결과
        """
        if not query or not query.strip():
            return SemanticValidationResult(
                is_valid=False,
                reason="쿼리가 비어있습니다.",
                confidence=1.0,
                error_message="쿼리가 비어있습니다.",
            )

        try:
            # LLM에게 쿼리 분석 요청
            messages = [
                SystemMessage(content=VALIDATION_SYSTEM_PROMPT),
                HumanMessage(content=f"다음 SQL 쿼리를 분석해주세요:\n\n```sql\n{query}\n```"),
            ]

            response = await self._llm.ainvoke(messages)
            response_text = response.content.strip()

            logger.debug(f"시맨틱 검증 응답: {response_text}")

            # 응답 파싱
            return self._parse_response(response_text)

        except Exception as e:
            logger.error(f"시맨틱 검증 중 오류 발생: {e}")

            if self._strict_mode:
                # Strict 모드: 오류 시 차단
                return SemanticValidationResult(
                    is_valid=False,
                    reason=f"검증 중 오류 발생: {str(e)}",
                    confidence=0.0,
                    error_message="쿼리 검증 중 문제가 발생했습니다. 잠시 후 다시 시도해주세요.",
                )
            else:
                # Lenient 모드: 오류 시 허용 (로깅은 함)
                return SemanticValidationResult(
                    is_valid=True,
                    reason="검증 건너뜀 (오류 발생)",
                    confidence=0.0,
                    error_message="",
                )

    def _parse_response(self, response_text: str) -> SemanticValidationResult:
        """
        LLM 응답 파싱

        Args:
            response_text: LLM 응답 텍스트

        Returns:
            SemanticValidationResult: 파싱된 결과
        """
        upper_response = response_text.upper()

        if upper_response.startswith("SAFE"):
            return SemanticValidationResult(
                is_valid=True,
                reason="안전한 조회 쿼리",
                confidence=0.9,
                error_message="",
            )

        if upper_response.startswith("UNSAFE"):
            # 이유 추출
            reason = response_text
            if ":" in response_text:
                reason = response_text.split(":", 1)[1].strip()

            return SemanticValidationResult(
                is_valid=False,
                reason=reason,
                confidence=0.9,
                error_message=self._generate_user_message(reason),
            )

        # 불명확한 응답 처리
        logger.warning(f"불명확한 시맨틱 검증 응답: {response_text}")

        if self._strict_mode:
            return SemanticValidationResult(
                is_valid=False,
                reason="검증 결과 불명확",
                confidence=0.5,
                error_message="쿼리 안전성을 확인할 수 없습니다. 다시 시도해주세요.",
            )
        else:
            return SemanticValidationResult(
                is_valid=True,
                reason="검증 결과 불명확 (허용됨)",
                confidence=0.5,
                error_message="",
            )

    def _generate_user_message(self, reason: str) -> str:
        """
        사용자 친화적 에러 메시지 생성

        Args:
            reason: 차단 이유

        Returns:
            사용자 메시지
        """
        # 기술적 이유를 사용자 친화적으로 변환
        reason_lower = reason.lower()

        if "시스템 테이블" in reason_lower or "system table" in reason_lower:
            return "시스템 정보에는 접근할 수 없습니다."

        if "인젝션" in reason_lower or "injection" in reason_lower:
            return "보안상의 이유로 이 쿼리는 실행할 수 없습니다."

        if "대량" in reason_lower or "전체 조회" in reason_lower:
            return "너무 많은 데이터를 요청하셨습니다. 조건을 추가해주세요."

        if "union" in reason_lower:
            return "이 형태의 쿼리는 지원되지 않습니다."

        # 기본 메시지
        return "보안 검증에 실패했습니다. 질문을 다시 작성해주세요."


# 빠른 검증을 위한 패턴 기반 사전 필터
SUSPICIOUS_PATTERNS = [
    # SQL 인젝션 패턴
    r"\bor\s+1\s*=\s*1\b",
    r"\band\s+1\s*=\s*1\b",
    r"'\s*or\s+'.*'\s*=\s*'",
    r"--\s*$",
    r";\s*--",
    # 시스템 테이블 접근
    r"\bpg_catalog\b",
    r"\bpg_shadow\b",
    r"\bpg_roles\b",
    r"\binformation_schema\b",
    # 위험한 함수
    r"\bpg_read_file\b",
    r"\bpg_ls_dir\b",
    r"\blo_import\b",
    r"\blo_export\b",
]


def quick_pattern_check(query: str) -> tuple[bool, str]:
    """
    빠른 패턴 기반 사전 검사

    LLM 호출 전에 명확히 위험한 패턴을 빠르게 감지합니다.

    Args:
        query: 검사할 쿼리

    Returns:
        (안전 여부, 위험 시 이유)
    """
    import re

    query_lower = query.lower()

    for pattern in SUSPICIOUS_PATTERNS:
        if re.search(pattern, query_lower):
            return False, f"의심스러운 패턴 감지: {pattern}"

    return True, ""
