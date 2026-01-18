"""Stack Bot - 사용자 프로필 및 서버 관리 봇"""
from __future__ import annotations
import asyncio
import os

import discord
from dotenv import load_dotenv

from utils.extension_loader import ExtensionLoader
from utils.data_manager import DataManager
from utils.constants import DEFAULT_ACTIVITY_NAME, COLORS
from utils.graceful_shutdown import setup_graceful_shutdown, register_shutdown_callback
from utils.logging_config import configure_logging

load_dotenv()
configure_logging()

import logging
logger = logging.getLogger(__name__)


class AuthenticationView(discord.ui.View):
    """인증 버튼 View"""

    def __init__(self, bot: discord.Bot, guild_id: int, role_id: int) -> None:
        super().__init__(timeout=300)
        self.bot = bot
        self.guild_id = guild_id
        self.role_id = role_id

    @discord.ui.button(label="프로필 입력", style=discord.ButtonStyle.primary)
    async def authenticate(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ) -> None:
        """프로필 입력 모달 표시"""
        modal = AuthenticationModal(self.bot, self.guild_id, self.role_id)
        await interaction.response.send_modal(modal)


class AuthenticationModal(discord.ui.Modal):
    """인증 프로필 입력 모달"""

    def __init__(self, bot: discord.Bot, guild_id: int, role_id: int) -> None:
        super().__init__(title="역할 인증 프로필")
        self.bot = bot
        self.guild_id = guild_id
        self.role_id = role_id

        self.add_item(
            discord.ui.InputText(
                label="닉네임",
                placeholder="사용할 닉네임을 입력하세요",
                required=True,
                max_length=50
            )
        )

        self.add_item(
            discord.ui.InputText(
                label="출생년도",
                placeholder="예: 2000",
                required=True,
                max_length=4
            )
        )

        self.add_item(
            discord.ui.InputText(
                label="성별",
                placeholder="예: 남/여",
                required=True,
                max_length=10
            )
        )

        self.add_item(
            discord.ui.InputText(
                label="지역",
                placeholder="예: 서울",
                required=True,
                max_length=50
            )
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        """모달 제출 시 역할 지급"""
        await interaction.response.defer(ephemeral=True)

        user_id = str(interaction.user.id)
        username = self.children[0].value.strip()
        birth_year = self.children[1].value.strip()
        gender = self.children[2].value.strip()
        region = self.children[3].value.strip()

        try:
            success = await self.bot.data_manager.register_profile(
                user_id, username, username, birth_year, gender, region
            )

            if not success:
                await interaction.followup.send(
                    embed=discord.Embed(
                        description="프로필 등록에 실패했습니다.",
                        color=COLORS["ERROR"]
                    ),
                    ephemeral=True
                )
                return

            guild = self.bot.get_guild(self.guild_id)
            if not guild:
                await interaction.followup.send(
                    embed=discord.Embed(
                        description="서버를 찾을 수 없습니다.",
                        color=COLORS["ERROR"]
                    ),
                    ephemeral=True
                )
                return

            member = guild.get_member(interaction.user.id)
            if not member:
                await interaction.followup.send(
                    embed=discord.Embed(
                        description="서버에서 사용자를 찾을 수 없습니다.",
                        color=COLORS["ERROR"]
                    ),
                    ephemeral=True
                )
                return

            role = guild.get_role(self.role_id)
            if not role:
                await interaction.followup.send(
                    embed=discord.Embed(
                        description="역할을 찾을 수 없습니다.",
                        color=COLORS["ERROR"]
                    ),
                    ephemeral=True
                )
                return

            if role not in member.roles:
                await member.add_roles(role)

            await interaction.followup.send(
                embed=discord.Embed(
                    description=f"**{username}**님의 인증이 완료되었습니다.",
                    color=COLORS["SUCCESS"]
                ),
                ephemeral=True
            )
        except discord.Forbidden:
            await interaction.followup.send(
                embed=discord.Embed(
                    description="역할 지급 권한이 없습니다.",
                    color=COLORS["ERROR"]
                ),
                ephemeral=True
            )
            logger.error(f"역할 지급 권한 없음: {self.role_id}")
        except Exception as e:
            await interaction.followup.send(
                embed=discord.Embed(
                    description="인증 처리 중 오류가 발생했습니다.",
                    color=COLORS["ERROR"]
                ),
                ephemeral=True
            )
            logger.error(f"인증 처리 실패: {e}")


class StackBot(discord.Bot):
    """프로필 및 서버 관리 봇"""

    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.guilds = True
        intents.reactions = True

        super().__init__(intents=intents)

        self.data_manager = DataManager(self)
        self.extension_loader = ExtensionLoader(self)
        self._initialized = False

    async def on_ready(self) -> None:
        """봇 준비 완료"""
        if self._initialized or not self.user:
            return

        try:
            # 데이터베이스 초기화
            await self.data_manager.init_db()
            
            # 명령어 로드
            self.extension_loader.load_all_extensions("commands")
            
            # 로드 실패시만 로그
            if self.extension_loader.failed_extensions:
                for ext_name, error in self.extension_loader.failed_extensions.items():
                    logger.error(f"명령어 로드 실패: {ext_name}\n{error}")
            
            # 명령어 동기화
            await self.sync_commands()
            
            self._initialized = True
            print(f"[{self.user.name}] 준비 완료")
            
        except Exception as e:
            logger.error(f"봇 초기화 실패: {e}", exc_info=e)
            await self.close()
            return

        # 활동 상태 설정
        try:
            await self.change_presence(
                activity=discord.Activity(
                    type=discord.ActivityType.competing,
                    name=DEFAULT_ACTIVITY_NAME
                )
            )
        except Exception as e:
            logger.error(f"상태 변경 실패: {e}")

    async def on_application_command_error(
        self, ctx: discord.ApplicationContext, error: discord.DiscordException
    ) -> None:
        """명령어 오류 처리"""
        logger.error(f"명령어 오류: {ctx.command.name if ctx.command else 'unknown'} - {error}")

        try:
            if not ctx.response.is_done():
                await ctx.respond(f"오류가 발생했습니다: {error}", ephemeral=True)
        except Exception:
            pass

    async def close(self) -> None:
        """봇 종료 처리"""
        await super().close()

    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent) -> None:
        """이모지 추가 시 프로필 입력 모달 표시"""
        if payload.user_id == self.user.id:
            return

        if not await self.data_manager.is_reaction_message(payload.message_id):
            return

        emoji = str(payload.emoji)
        role_id = await self.data_manager.get_role_for_reaction(payload.message_id, emoji)

        if not role_id:
            return

        try:
            # 캐시에서 먼저 찾기, 없으면 API에서 조회
            user = self.get_user(payload.user_id)
            if not user:
                try:
                    user = await self.fetch_user(payload.user_id)
                except discord.NotFound:
                    logger.warning(f"사용자를 찾을 수 없음: {payload.user_id}")
                    return

            embed = discord.Embed(
                description="인증을 진행하려면 아래 버튼을 클릭하여 프로필 정보를 입력해주세요.",
                color=COLORS["INFO"]
            )
            view = AuthenticationView(self, payload.guild_id, role_id)
            await user.send(embed=embed, view=view)
        except discord.Forbidden:
            logger.warning(f"DM 전송 실패 (권한 부족): {payload.user_id} - 사용자가 DM을 차단했을 수 있습니다.")
        except discord.HTTPException as e:
            logger.error(f"DM 전송 실패 (HTTP 오류): {payload.user_id} - {e.status}: {e.text}")
        except Exception as e:
            logger.error(f"DM 전송 실패: {payload.user_id} - {type(e).__name__}: {e}")

    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent) -> None:
        """이모지 제거 시 역할 회수"""
        if payload.user_id == self.user.id:
            return

        if not await self.data_manager.is_reaction_message(payload.message_id):
            return

        emoji = str(payload.emoji)
        role_id = await self.data_manager.get_role_for_reaction(payload.message_id, emoji)

        if not role_id:
            return

        try:
            guild = self.get_guild(payload.guild_id)
            if not guild:
                return

            member = guild.get_member(payload.user_id)
            if not member:
                return

            role = guild.get_role(role_id)
            if not role:
                logger.warning(f"역할을 찾을 수 없음: {role_id}")
                return

            if role in member.roles:
                await member.remove_roles(role)
        except discord.Forbidden:
            logger.error(f"역할 회수 권한 없음: {role_id}")
        except Exception as e:
            logger.error(f"역할 회수 실패: {e}")


def main() -> None:
    """봇 실행"""
    import sys
    
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        logger.error("DISCORD_TOKEN 미설정")
        return

    bot = StackBot()

    def shutdown_handler() -> None:
        asyncio.create_task(bot.close())

    register_shutdown_callback(shutdown_handler)
    setup_graceful_shutdown()

    try:
        bot.run(token)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
