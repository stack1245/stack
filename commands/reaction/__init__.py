"""그룹 명령어 동적 로더"""
from __future__ import annotations
import discord
from discord.ext import commands
import importlib
import inspect
from pathlib import Path


# 공유 그룹 정의
reaction_group = discord.SlashCommandGroup(
    name="반응",
    description="역할 반응 관리 명령어",
    default_member_permissions=discord.Permissions(administrator=True)
)


def setup(bot: discord.Bot):
    """현재 폴더의 모든 Cog를 동적으로 로드"""
    current_dir = Path(__file__).parent
    
    # 현재 디렉토리의 모든 .py 파일 탐색
    for file_path in current_dir.glob("*.py"):
        # __init__.py는 제외
        if file_path.name.startswith("__"):
            continue
        
        # 모듈명 생성 (예: commands.group.sub_command)
        module_name = f"commands.{current_dir.name}.{file_path.stem}"
        
        try:
            # 모듈 동적 import
            module = importlib.import_module(module_name)
            
            # 모듈 내의 모든 Cog 클래스 탐색 및 로드
            for name, obj in inspect.getmembers(module, inspect.isclass):
                # Cog인지 확인 (obj가 실제 클래스이고, commands.Cog의 서브클래스인지)
                try:
                    if obj is not commands.Cog and issubclass(obj, commands.Cog):
                        bot.add_cog(obj(bot))
                except (TypeError, AttributeError):
                    # issubclass가 실패하면 무시
                    continue
        except Exception as e:
            print(f"⚠️ {module_name} 로드 실패: {e}")
    
    # 그룹을 bot에 추가
    bot.add_application_command(reaction_group)