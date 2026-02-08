"""
디버그 컨텍스트 유틸리티

노드별 타이밍 측정, 에러 체인 추적, 재시도 기록 등
디버깅 및 관찰성을 위한 유틸리티 함수들을 제공합니다.
"""

import logging
import time
import uuid
from typing import Any

from app.agent.state import (
    DebugContext,
    ErrorEntry,
    NodeTiming,
    RetryRecord,
)

logger = logging.getLogger(__name__)


def create_debug_context(trace_id: str | None = None) -> DebugContext:
    """
    새 디버그 컨텍스트 생성

    Args:
        trace_id: 추적 ID (선택, 미제공 시 UUID 생성)

    Returns:
        DebugContext: 초기화된 디버그 컨텍스트
    """
    return DebugContext(
        trace_id=trace_id or str(uuid.uuid4()),
        node_timings=[],
        error_chain=[],
        current_node="",
        retry_history=[],
    )


def start_node_timing(debug: DebugContext, node_name: str) -> DebugContext:
    """
    노드 시작 시간 기록

    Args:
        debug: 현재 디버그 컨텍스트
        node_name: 노드 이름

    Returns:
        DebugContext: 업데이트된 디버그 컨텍스트
    """
    timing = NodeTiming(
        node_name=node_name,
        start_time=time.time(),
        end_time=None,
        duration_ms=None,
    )

    # 기존 타이밍 목록에 추가
    new_timings = list(debug["node_timings"])
    new_timings.append(timing)

    return DebugContext(
        trace_id=debug["trace_id"],
        node_timings=new_timings,
        error_chain=debug["error_chain"],
        current_node=node_name,
        retry_history=debug["retry_history"],
    )


def end_node_timing(debug: DebugContext, node_name: str) -> DebugContext:
    """
    노드 종료 시간 및 소요 시간 기록

    Args:
        debug: 현재 디버그 컨텍스트
        node_name: 노드 이름

    Returns:
        DebugContext: 업데이트된 디버그 컨텍스트
    """
    end_time = time.time()
    new_timings = []

    for timing in debug["node_timings"]:
        if timing["node_name"] == node_name and timing["end_time"] is None:
            # 매칭되는 타이밍 업데이트
            duration_ms = (end_time - timing["start_time"]) * 1000
            new_timing = NodeTiming(
                node_name=timing["node_name"],
                start_time=timing["start_time"],
                end_time=end_time,
                duration_ms=duration_ms,
            )
            new_timings.append(new_timing)

            # 로그 출력
            logger.debug(
                f"[{debug['trace_id'][:8]}] Node '{node_name}' completed in {duration_ms:.2f}ms"
            )
        else:
            new_timings.append(timing)

    return DebugContext(
        trace_id=debug["trace_id"],
        node_timings=new_timings,
        error_chain=debug["error_chain"],
        current_node="",  # 현재 노드 클리어
        retry_history=debug["retry_history"],
    )


def add_error_entry(
    debug: DebugContext,
    node_name: str,
    error: Exception | str,
    context: dict[str, Any] | None = None,
) -> DebugContext:
    """
    에러 체인에 에러 항목 추가

    Args:
        debug: 현재 디버그 컨텍스트
        node_name: 에러 발생 노드
        error: 에러 객체 또는 에러 메시지
        context: 추가 컨텍스트 정보

    Returns:
        DebugContext: 업데이트된 디버그 컨텍스트
    """
    error_entry = ErrorEntry(
        node_name=node_name,
        error_type=type(error).__name__ if isinstance(error, Exception) else "Error",
        error_message=str(error),
        timestamp=time.time(),
        context=context or {},
    )

    # 에러 로그 출력
    logger.error(
        f"[{debug['trace_id'][:8]}] Error in '{node_name}': {error_entry['error_type']} - {error_entry['error_message']}"
    )

    # 기존 에러 체인에 추가
    new_error_chain = list(debug["error_chain"])
    new_error_chain.append(error_entry)

    return DebugContext(
        trace_id=debug["trace_id"],
        node_timings=debug["node_timings"],
        error_chain=new_error_chain,
        current_node=debug["current_node"],
        retry_history=debug["retry_history"],
    )


def add_retry_record(
    debug: DebugContext,
    node_name: str,
    attempt: int,
    reason: str,
) -> DebugContext:
    """
    재시도 기록 추가

    Args:
        debug: 현재 디버그 컨텍스트
        node_name: 재시도 발생 노드
        attempt: 시도 횟수
        reason: 재시도 사유

    Returns:
        DebugContext: 업데이트된 디버그 컨텍스트
    """
    retry_record = RetryRecord(
        node_name=node_name,
        attempt=attempt,
        reason=reason,
        timestamp=time.time(),
    )

    # 재시도 로그 출력
    logger.info(
        f"[{debug['trace_id'][:8]}] Retry in '{node_name}': attempt {attempt} - {reason}"
    )

    # 기존 재시도 히스토리에 추가
    new_retry_history = list(debug["retry_history"])
    new_retry_history.append(retry_record)

    return DebugContext(
        trace_id=debug["trace_id"],
        node_timings=debug["node_timings"],
        error_chain=debug["error_chain"],
        current_node=debug["current_node"],
        retry_history=new_retry_history,
    )


def get_total_execution_time_ms(debug: DebugContext) -> float:
    """
    전체 실행 시간 계산 (밀리초)

    Args:
        debug: 디버그 컨텍스트

    Returns:
        float: 전체 실행 시간 (밀리초)
    """
    total_ms = 0.0
    for timing in debug["node_timings"]:
        if timing["duration_ms"] is not None:
            total_ms += timing["duration_ms"]
    return total_ms


def get_node_timing_summary(debug: DebugContext) -> dict[str, float]:
    """
    노드별 실행 시간 요약

    Args:
        debug: 디버그 컨텍스트

    Returns:
        dict: 노드 이름 -> 실행 시간(ms) 매핑
    """
    summary = {}
    for timing in debug["node_timings"]:
        if timing["duration_ms"] is not None:
            node_name = timing["node_name"]
            # 동일 노드가 여러 번 실행될 수 있으므로 합산
            summary[node_name] = summary.get(node_name, 0.0) + timing["duration_ms"]
    return summary


def get_error_summary(debug: DebugContext) -> list[dict[str, Any]]:
    """
    에러 체인 요약

    Args:
        debug: 디버그 컨텍스트

    Returns:
        list: 에러 요약 목록
    """
    return [
        {
            "node": entry["node_name"],
            "type": entry["error_type"],
            "message": entry["error_message"],
        }
        for entry in debug["error_chain"]
    ]


def format_debug_report(debug: DebugContext) -> str:
    """
    디버그 리포트 포맷팅 (로깅/디버깅용)

    Args:
        debug: 디버그 컨텍스트

    Returns:
        str: 포맷팅된 디버그 리포트
    """
    lines = [
        f"=== Debug Report ===",
        f"Trace ID: {debug['trace_id']}",
        "",
        "Node Timings:",
    ]

    timing_summary = get_node_timing_summary(debug)
    for node_name, duration_ms in timing_summary.items():
        lines.append(f"  - {node_name}: {duration_ms:.2f}ms")

    total_ms = get_total_execution_time_ms(debug)
    lines.append(f"  Total: {total_ms:.2f}ms")

    if debug["error_chain"]:
        lines.append("")
        lines.append("Errors:")
        for entry in debug["error_chain"]:
            lines.append(
                f"  - [{entry['node_name']}] {entry['error_type']}: {entry['error_message']}"
            )

    if debug["retry_history"]:
        lines.append("")
        lines.append("Retries:")
        for record in debug["retry_history"]:
            lines.append(
                f"  - [{record['node_name']}] Attempt {record['attempt']}: {record['reason']}"
            )

    lines.append("===================")
    return "\n".join(lines)


def merge_debug_update(
    current_debug: DebugContext,
    update: dict[str, Any],
) -> DebugContext:
    """
    디버그 컨텍스트 업데이트 병합

    노드에서 반환된 부분 업데이트를 현재 디버그 컨텍스트에 병합합니다.

    Args:
        current_debug: 현재 디버그 컨텍스트
        update: 병합할 업데이트

    Returns:
        DebugContext: 병합된 디버그 컨텍스트
    """
    return DebugContext(
        trace_id=update.get("trace_id", current_debug["trace_id"]),
        node_timings=update.get("node_timings", current_debug["node_timings"]),
        error_chain=update.get("error_chain", current_debug["error_chain"]),
        current_node=update.get("current_node", current_debug["current_node"]),
        retry_history=update.get("retry_history", current_debug["retry_history"]),
    )
