"""
LangGraph 시각화 엔드포인트

그래프 구조를 시각화하여 반환합니다.
"""

import logging

from fastapi import APIRouter
from fastapi.responses import Response

from app.agent.visualization import get_graph_mermaid, get_graph_png

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/graph/png",
    summary="그래프 PNG 이미지",
    description="LangGraph 워크플로우 구조를 PNG 이미지로 반환합니다.",
    responses={200: {"content": {"image/png": {}}}},
)
async def get_graph_image() -> Response:
    """LangGraph 구조를 PNG 이미지로 반환"""
    png_data = get_graph_png()
    return Response(content=png_data, media_type="image/png")


@router.get(
    "/graph/mermaid",
    summary="그래프 Mermaid 다이어그램",
    description="LangGraph 워크플로우 구조를 Mermaid 형식으로 반환합니다.",
)
async def get_graph_mermaid_text() -> dict[str, str]:
    """LangGraph 구조를 Mermaid 텍스트로 반환"""
    mermaid_text = get_graph_mermaid()
    return {"mermaid": mermaid_text}
