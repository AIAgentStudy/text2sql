"""
LangGraph 시각화 유틸리티

그래프 구조를 PNG 이미지 또는 Mermaid 다이어그램으로 내보냅니다.
"""

import logging
from pathlib import Path

from app.agent.graph import build_graph

logger = logging.getLogger(__name__)


def get_graph_mermaid() -> str:
    """
    그래프를 Mermaid 다이어그램 형식으로 반환

    Returns:
        Mermaid 다이어그램 문자열
    """
    graph = build_graph()
    compiled = graph.compile()
    return compiled.get_graph().draw_mermaid()


def get_graph_png() -> bytes:
    """
    그래프를 PNG 바이트로 반환

    Returns:
        PNG 이미지 바이트
    """
    graph = build_graph()
    compiled = graph.compile()
    return compiled.get_graph().draw_mermaid_png()


def save_graph_png(output_path: str | Path = "langgraph_structure.png") -> Path:
    """
    그래프를 PNG 파일로 저장

    Args:
        output_path: 출력 파일 경로

    Returns:
        저장된 파일 경로
    """
    output_path = Path(output_path)
    png_data = get_graph_png()
    output_path.write_bytes(png_data)
    logger.info(f"그래프 이미지 저장: {output_path}")
    return output_path


if __name__ == "__main__":
    # CLI 실행: python -m app.agent.visualization
    path = save_graph_png()
    print(f"그래프 저장됨: {path}")
