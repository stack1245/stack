"""상수 정의"""
from __future__ import annotations
from pathlib import Path

__all__ = [
    "DATA_DIR",
    "COLORS",
    "DEFAULT_ACTIVITY_NAME",
    "AUTO_SAVE_INTERVAL",
    "DEFAULT_SETTINGS",
]

# 경로
DATA_DIR = Path(__file__).parent.parent / "data"

# 색상
COLORS = {
    "ERROR": 0xE74C3C,
    "SUCCESS": 0x2ECC71,
    "INFO": 0x3498DB,
    "WARNING": 0xF39C12,
    "NEUTRAL": 0x95A5A6,
}

# 봇 설정
DEFAULT_ACTIVITY_NAME = "기록 남기는 중..."
AUTO_SAVE_INTERVAL: int = 300  # 5분

# 기본 설정
DEFAULT_SETTINGS = {
    "log_channel_id": None,
}
