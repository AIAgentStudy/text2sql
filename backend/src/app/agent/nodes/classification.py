"""
의도 분류 노드

사용자의 질문이 데이터베이스 조회(Text2SQL)가 필요한지, 일반적인 대화인지 분류합니다.
"""

import logging
from typing import Literal

from langchain_core.messages import SystemMessage, HumanMessage

from app.agent.decorators import with_debug_timing
from app.agent.state import Text2SQLAgentState, update_input
from app.llm.factory import get_chat_model
from app.config import get_settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """당신은 사용자의 질문 의도를 분류하는 AI 어시스턴트입니다.
사용자의 질문이 데이터베이스에서 데이터를 조회하거나 분석해야 하는 질문(text2sql)인지, 아니면 인사, 잡담, 일반적인 지식 질문 등(general)인지 분류해주세요.

## 분류 기준
1. **text2sql**: 
   - 데이터베이스 조회가 필요한 질문
   - 매출, 고객, 주문, 상품, 재고 등 비즈니스 데이터 관련 질문
   - "보여줘", "알려줘", "조회해줘", "찾아줘" 등으로 끝나면서 데이터 관련 내용을 묻는 경우
   - 예: "지난달 매출 얼마야?", "가장 많이 팔린 상품은?", "서울 지역 고객 수 알려줘"

2. **general**:
   - 데이터베이스 조회와 관련 없는 일반적인 질문
   - 인사 ("안녕", "반가워")
   - 정체성 질문 ("너는 누구야?", "무슨 일을 해?")
   - 일반 지식 ("오늘 날씨 어때?", "점심 메뉴 추천해줘")
   - 단순한 감사 표현 ("고마워", "수고했어")

## 출력 형식
오직 다음 단어 중 하나만 출력하세요:
- text2sql
- general
"""


@with_debug_timing("classification")
async def classification_node(state: Text2SQLAgentState) -> dict[str, object]:
    """
    의도 분류 노드

    사용자 질문의 의도를 분석하여 intent 상태를 업데이트합니다.

    Args:
        state: 현재 에이전트 상태

    Returns:
        업데이트할 상태 딕셔너리
    """
    settings = get_settings()
    user_question = state["input"]["user_question"]
    llm_provider = state["input"]["llm_provider"]

    logger.info(f"의도 분류 시작 - 질문: {user_question[:50]}...")

    try:
        # LLM 모델 가져오기
        llm = get_chat_model(provider_type=llm_provider)

        # 메시지 구성
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=user_question),
        ]

        # LLM 호출
        response = await llm.ainvoke(messages)
        content = str(response.content).strip().lower()

        # 결과 파싱
        if "text2sql" in content:
            intent = "text2sql"
        else:
            intent = "general"

        logger.info(f"의도 분류 완료: {intent}")

        return {
            "input": update_input(state, intent=intent)
        }

    except Exception as e:
        logger.error(f"의도 분류 실패: {e}")
        # 에러 발생 시 기본적으로 text2sql로 처리 (안전장치)
        return {
            "input": update_input(state, intent="text2sql")
        }
