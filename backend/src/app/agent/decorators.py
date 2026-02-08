"""
에이전트 노드 데코레이터

노드 함수를 래핑하여 자동 타이밍 측정, 에러 체인 추적 등의
디버깅 기능을 제공하는 데코레이터들을 정의합니다.
"""

import functools
import logging
import time
from typing import Any, Callable

from app.agent.state import (
    DebugContext,
    ErrorEntry,
    NodeTiming,
    Text2SQLAgentState,
)

logger = logging.getLogger(__name__)


def with_debug_timing(node_name: str) -> Callable:
    """
    노드 함수에 자동 타이밍 및 에러 추적을 추가하는 데코레이터

    - 노드 시작/종료 시간 자동 기록
    - 예외 발생 시 에러 체인에 자동 추가
    - debug 컨텍스트가 없어도 안전하게 동작

    Args:
        node_name: 노드 이름 (로깅 및 타이밍 기록용)

    Returns:
        데코레이터 함수

    Usage:
        @with_debug_timing("query_execution")
        async def query_execution_node(state: Text2SQLAgentState) -> dict:
            ...
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(state: Text2SQLAgentState) -> dict[str, Any]:
            start_time = time.time()
            trace_id = ""

            # debug 컨텍스트 안전하게 추출
            try:
                debug = state.get("debug", {})
                trace_id = debug.get("trace_id", "")[:8] if debug else ""
            except (KeyError, TypeError, AttributeError):
                pass

            logger.debug(f"[{trace_id}] Node '{node_name}' started")

            try:
                # 실제 노드 함수 실행
                result = await func(state)

                # 타이밍 정보 추가
                end_time = time.time()
                duration_ms = (end_time - start_time) * 1000

                logger.debug(
                    f"[{trace_id}] Node '{node_name}' completed in {duration_ms:.2f}ms"
                )

                # 결과에 debug 업데이트 추가
                result = _add_timing_to_result(
                    result=result,
                    state=state,
                    node_name=node_name,
                    start_time=start_time,
                    end_time=end_time,
                    duration_ms=duration_ms,
                )

                return result

            except Exception as e:
                # 에러 발생 시 타이밍 및 에러 정보 기록
                end_time = time.time()
                duration_ms = (end_time - start_time) * 1000

                logger.error(
                    f"[{trace_id}] Node '{node_name}' failed after {duration_ms:.2f}ms: {e}"
                )

                # 에러 정보를 포함한 결과 생성
                error_result = _create_error_result(
                    state=state,
                    node_name=node_name,
                    error=e,
                    start_time=start_time,
                    end_time=end_time,
                    duration_ms=duration_ms,
                )

                # 예외를 다시 발생시키지 않고 에러 상태 반환
                # (LangGraph가 에러 처리를 하도록 함)
                raise

        return wrapper

    return decorator


def _add_timing_to_result(
    result: dict[str, Any],
    state: Text2SQLAgentState,
    node_name: str,
    start_time: float,
    end_time: float,
    duration_ms: float,
) -> dict[str, Any]:
    """결과에 타이밍 정보 추가"""
    if result is None:
        result = {}

    # 현재 debug 컨텍스트 가져오기
    try:
        current_debug = state.get("debug", {})
        if not current_debug:
            return result

        # 새 타이밍 항목 생성
        new_timing = NodeTiming(
            node_name=node_name,
            start_time=start_time,
            end_time=end_time,
            duration_ms=duration_ms,
        )

        # 기존 타이밍 목록에 추가
        existing_timings = list(current_debug.get("node_timings", []))
        existing_timings.append(new_timing)

        # debug 업데이트 생성
        debug_update = DebugContext(
            trace_id=current_debug.get("trace_id", ""),
            node_timings=existing_timings,
            error_chain=current_debug.get("error_chain", []),
            current_node="",
            retry_history=current_debug.get("retry_history", []),
        )

        # 결과에 debug 업데이트 추가
        result["debug"] = debug_update

    except (KeyError, TypeError, AttributeError) as e:
        logger.warning(f"Failed to add timing info: {e}")

    return result


def _create_error_result(
    state: Text2SQLAgentState,
    node_name: str,
    error: Exception,
    start_time: float,
    end_time: float,
    duration_ms: float,
) -> dict[str, Any]:
    """에러 발생 시 결과 생성"""
    result = {}

    try:
        current_debug = state.get("debug", {})
        if not current_debug:
            return result

        # 타이밍 항목
        new_timing = NodeTiming(
            node_name=node_name,
            start_time=start_time,
            end_time=end_time,
            duration_ms=duration_ms,
        )

        # 에러 항목
        error_entry = ErrorEntry(
            node_name=node_name,
            error_type=type(error).__name__,
            error_message=str(error),
            timestamp=end_time,
            context={},
        )

        # 기존 목록에 추가
        existing_timings = list(current_debug.get("node_timings", []))
        existing_timings.append(new_timing)

        existing_errors = list(current_debug.get("error_chain", []))
        existing_errors.append(error_entry)

        # debug 업데이트 생성
        debug_update = DebugContext(
            trace_id=current_debug.get("trace_id", ""),
            node_timings=existing_timings,
            error_chain=existing_errors,
            current_node=node_name,
            retry_history=current_debug.get("retry_history", []),
        )

        result["debug"] = debug_update

    except (KeyError, TypeError, AttributeError) as e:
        logger.warning(f"Failed to create error result: {e}")

    return result


def with_retry_tracking(node_name: str) -> Callable:
    """
    재시도 추적을 위한 데코레이터

    generation_attempt 등의 재시도 필드를 모니터링하고
    debug 컨텍스트에 재시도 기록을 추가합니다.

    Args:
        node_name: 노드 이름

    Returns:
        데코레이터 함수
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(state: Text2SQLAgentState) -> dict[str, Any]:
            # 현재 시도 횟수 추출
            try:
                current_attempt = state.get("generation", {}).get("generation_attempt", 0)
            except (KeyError, TypeError, AttributeError):
                current_attempt = 0

            # 실제 함수 실행
            result = await func(state)

            # 결과에서 새 시도 횟수 확인
            new_attempt = None
            if isinstance(result, dict):
                # nested 구조에서 확인
                if "generation" in result and isinstance(result["generation"], dict):
                    new_attempt = result["generation"].get("generation_attempt")
                # flat 구조에서 확인 (하위 호환성)
                elif "generation_attempt" in result:
                    new_attempt = result["generation_attempt"]

            # 재시도 발생 시 기록
            if new_attempt is not None and new_attempt > current_attempt:
                result = _add_retry_to_result(
                    result=result,
                    state=state,
                    node_name=node_name,
                    attempt=new_attempt,
                    reason="Validation failed, regenerating",
                )

            return result

        return wrapper

    return decorator


def _add_retry_to_result(
    result: dict[str, Any],
    state: Text2SQLAgentState,
    node_name: str,
    attempt: int,
    reason: str,
) -> dict[str, Any]:
    """결과에 재시도 기록 추가"""
    from app.agent.state import RetryRecord

    try:
        current_debug = state.get("debug", {})
        if not current_debug:
            return result

        # 새 재시도 기록
        retry_record = RetryRecord(
            node_name=node_name,
            attempt=attempt,
            reason=reason,
            timestamp=time.time(),
        )

        # 기존 재시도 목록에 추가
        existing_retries = list(current_debug.get("retry_history", []))
        existing_retries.append(retry_record)

        # debug 업데이트가 이미 있으면 병합
        if "debug" in result:
            result["debug"]["retry_history"] = existing_retries
        else:
            result["debug"] = DebugContext(
                trace_id=current_debug.get("trace_id", ""),
                node_timings=current_debug.get("node_timings", []),
                error_chain=current_debug.get("error_chain", []),
                current_node=current_debug.get("current_node", ""),
                retry_history=existing_retries,
            )

        logger.info(f"Retry recorded: {node_name} attempt {attempt}")

    except (KeyError, TypeError, AttributeError) as e:
        logger.warning(f"Failed to add retry record: {e}")

    return result
