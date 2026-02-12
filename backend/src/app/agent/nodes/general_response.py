"""
일반 대화 응답 노드

데이터베이스 조회와 무관한 일반적인 질문에 대해 답변합니다.
"""

import logging

from langchain_core.messages import SystemMessage, HumanMessage

from app.agent.decorators import with_debug_timing
from app.agent.state import Text2SQLAgentState, update_response
from app.llm.factory import get_chat_model
from app.config import get_settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """당신은 회사나 데이터를 분석해주는 친절한 AI 어시스턴트입니다.
사용자의 일반적인 질문(인사, 정체성, 가벼운 대화 등)에 대해 자연스럽고 친절하게 답변해주세요.

## 답변 가이드라인
1. **정체성**:
   - 당신은 기업 데이터를 분석하여 인사이트를 제공하는 "Text2SQL AI 에이전트"입니다.
   - 복잡한 SQL 쿼리 없이도 자연어로 질문하면 데이터를 찾아준다는 점을 강조하세요.

2. **기능 안내**:
   - 사용자가 무엇을 할 수 있는지 물어보면, "매출 현황", "재고 조회", "고객 분석" 등을 할 수 있다고 예시를 들어 설명해주세요.
   - 예: "저는 회사의 매출 데이터나 재고 현황을 분석해드릴 수 있어요. '지난달 매출 보여줘'라고 물어보세요!"

3. **일상 대화**:
   - 인사나 안부에는 밝고 긍정적으로 답해주세요.
   - "점심 메뉴 추천" 같은 질문에는 재치 있게 답변하되, 본업(데이터 분석)으로 자연스럽게 유도해보세요.
     (예: "점심 메뉴 고르는 건 어렵죠! 하지만 메뉴별 판매 데이터를 분석해드릴 순 있답니다. 농담이에요, 맛있는 거 드세요!")

4. **형식**:
   - 답변은 한국어로 간결하고 명확하게 작성하세요.
   - 이모지를 적절히 사용하여 친근감을 주세요.
"""


@with_debug_timing("general_response")
async def general_response_node(state: Text2SQLAgentState) -> dict[str, object]:
    """
    일반 대화 응답 노드

    LLM을 사용하여 일반적인 질문에 대한 답변을 생성합니다.

    Args:
        state: 현재 에이전트 상태

    Returns:
        업데이트할 상태 딕셔너리
    """
    settings = get_settings()
    user_question = state["input"]["user_question"]
    llm_provider = state["input"]["llm_provider"]

    logger.info(f"일반 대화 응답 생성 시작 - 질문: {user_question[:50]}...")

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
        content = str(response.content)

        logger.info("일반 대화 응답 생성 완료")

        return {
            "response": update_response(
                state,
                final_response=content,
                response_format="summary",  # 텍스트 형식으로 표시
                user_approved=True  # 일반 대화는 별도 승인 절차 없음
            )
        }

    except Exception as e:
        logger.error(f"일반 대화 응답 실패: {e}")
        return {
            "response": update_response(
                state,
                final_response="죄송합니다. 잠시 문제가 발생했어요. 다시 말씀해 주시겠어요?",
                response_format="error"
            )
        }
