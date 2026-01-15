"""안전한 종료 처리"""
from __future__ import annotations
import signal
import sys
from typing import Callable

__all__ = ["register_shutdown_callback", "setup_graceful_shutdown"]

_callbacks: list[Callable[[], None]] = []
_active = False


def register_shutdown_callback(cb: Callable[[], None]) -> None:
    """종료 시 실행할 콜백 등록"""
    _callbacks.append(cb)


def _run_callbacks() -> None:
    """모든 콜백 실행"""
    for cb in _callbacks:
        try:
            cb()
        except Exception as e:
            print(f"[Shutdown] 콜백 실행 오류: {e}")


def _signal_handler(signum: int, frame) -> None:
    """시그널 핸들러"""
    global _active
    if _active:
        return
    _active = True
    
    print("\n[Shutdown] 종료 신호 수신, 안전하게 종료합니다...")
    _run_callbacks()
    sys.exit(0)


def setup_graceful_shutdown() -> None:
    """SIGINT/SIGTERM 핸들러 설정"""
    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)
