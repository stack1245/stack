"""Stack Bot - 사용자 프로필 및 서버 관리 봇"""
from __future__ import annotations
import logging
import os
import discord
from dotenv import load_dotenv

from utils.extension_loader import ExtensionLoader
from utils.data_manager import DataManager
from utils.constants import DEFAULT_ACTIVITY_NAME
from utils.graceful_shutdown import setup_graceful_shutdown, register_shutdown_callback
from utils.logging_config import configure_logging

load_dotenv()
configure_logging()
logger = logging.getLogger(__name__)


class StackBot(discord.Bot):
    """Stack Bot - 프로필 및 서버 관리"""
    
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.messages = True
        intents.guilds = True
        
        super().__init__(intents=intents)
        
        self.data_manager = DataManager(self)
        self.extension_loader = ExtensionLoader(self, "Stack")
    
    async def on_ready(self):
        """봇 준비 완료"""
        await self.data_manager.init_db()
        
        activity = discord.Activity(type=discord.ActivityType.playing, name=DEFAULT_ACTIVITY_NAME)
        await self.change_presence(activity=activity, status=discord.Status.online)
        
        self.extension_loader.load_all_extensions()
        
        print(f"[{self.user.name}] 준비 완료")
    
    async def on_application_command_error(self, ctx: discord.ApplicationContext, error):
        """명령어 오류 처리"""
        if isinstance(error, discord.ext.commands.MissingPermissions):
            await ctx.respond("이 명령어를 사용할 권한이 없습니다.", ephemeral=True)
        else:
            logger.error(f"명령어 오류: {error}")
            await ctx.respond("명령어 실행 중 오류가 발생했습니다.", ephemeral=True)


def main():
    """메인 진입점"""
    setup_graceful_shutdown()
    
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        print("[오류] 토큰이 설정되지 않았습니다. .env 파일을 확인해주세요.")
        return
    
    bot = StackBot()
    bot.run(token)


if __name__ == "__main__":
    main()
