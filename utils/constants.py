"""상수 정의"""
from __future__ import annotations
from pathlib import Path
from datetime import datetime

__all__ = [
    "DATA_DIR",
    "COLORS",
    "DEFAULT_ACTIVITY_NAME",
    "AUTO_SAVE_INTERVAL",
    "DEFAULT_SETTINGS",
    "GENDER_ROLES",
    "AGE_ROLES",
    "calculate_age",
    "get_age_category",
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

# 자동 역할 지급 설정
GENDER_ROLES = {
    "남": 1460659275494981908,
    "여": 1460659352435298463,
}

AGE_ROLES = {
    "adult": 1460660230151999601,      # 성인 (19세 이상)
    "minor": 1460660192206389453,       # 미성년자 (18세 이하)
}


def calculate_age(birth_year: str) -> int:
    """출생년도에서 나이 계산 (만 나이)"""
    try:
        # 출생년도가 2자리 또는 4자리인지 확인
        year = int(birth_year)
        if year < 100:
            # 2자리 숫자인 경우, 2000년대 기준
            year = 2000 + year if year <= 30 else 1900 + year
        
        current_year = datetime.now().year
        age = current_year - year
        return age
    except (ValueError, TypeError):
        return 0


def get_age_category(birth_year: str) -> str:
    """나이 카테고리 반환 (adult 또는 minor)"""
    age = calculate_age(birth_year)
    return "adult" if age >= 19 else "minor"
