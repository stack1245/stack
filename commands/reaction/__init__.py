"""그룹 명령어 동적 로더"""
from __future__ import annotations
import discord
import importlib
from pathlib import Path


# 공유 그룹 정의
reaction_group = discord.SlashCommandGroup(
    name="반응",
    description="역할 반응 관리 명령어",
    default_member_permissions=discord.Permissions(administrator=True)
)


def setup(bot: discord.Bot):
    """현재 폴더의 모든 명령어를 동적으로 로드"""
    current_dir = Path(__file__).parent
    
    # 현재 디렉토리의 모든 .py 파일 탐색
    for file_path in current_dir.glob("*.py"):
        # __init__.py는 제외
        if file_path.name.startswith("__"):
            continue
        
        # 모듈명 생성 (예: commands.reaction.add)
        module_name = f"commands.{current_dir.name}.{file_path.stem}"
        
        try:
            # 모듈 동적 import (명령어가 데코레이터에 의해 자동으로 그룹에 추가됨)
            importlib.import_module(module_name)
        except Exception as e:
            print(f"⚠️ {module_name} 로드 실패: {e}")
    
    # 그룹을 bot에 추가
    bot.add_application_command(reaction_group)