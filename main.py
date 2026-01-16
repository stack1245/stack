"""Stack Bot - 사용자 프로필 및 서버 관리 봇"""
from __future__ import annotations
import asyncio
import logging
import os
from typing import Optional

import discord
from dotenv import load_dotenv

from utils.extension_loader import ExtensionLoader
from utils.data_manager import DataManager
from utils.constants import AUTO_SAVE_INTERVAL, DEFAULT_ACTIVITY_NAME, COLORS
from utils.graceful_shutdown import setup_graceful_shutdown, register_shutdown_callback
from utils.logging_config import configure_logging

load_dotenv()
configure_logging()
logger = logging.getLogger(__name__)


class AuthenticationView(discord.ui.View):
    """인증 버튼 View"""

    def __init__(self, bot: discord.Bot, guild_id: int, role_id: int) -> None:
        super().__init__(timeout=None)
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
                max_length=1
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
        self._commands_loaded = False
        self._auto_save_task: Optional[asyncio.Task] = None

    async def on_ready(self) -> None:
        """봇 준비 완료"""
        if not self.user:
            return

        if not self._commands_loaded:
            try:
                await self.data_manager.init_db()
                self.extension_loader.load_all_extensions("commands")
                await self.sync_commands()
                self._commands_loaded = True
                print(f"[{self.user.name}] 준비 완료")
            except Exception as e:
                logger.error(f"초기화 실패: {e}")
                return

        try:
            await self.change_presence(
                activity=discord.Activity(
                    type=discord.ActivityType.competing,
                    name=DEFAULT_ACTIVITY_NAME
                )
            )
        except Exception as e:
            logger.error(f"상태 변경 실패: {e}")

        if not self._auto_save_task:
            self._auto_save_task = self.loop.create_task(self._auto_save_loop())

    async def _auto_save_loop(self) -> None:
        """주기적 데이터 저장"""
        await self.wait_until_ready()
        while not self.is_closed():
            await asyncio.sleep(AUTO_SAVE_INTERVAL)
            try:
                await self.data_manager.save_data()
            except Exception as e:
                logger.error(f"자동 저장 실패: {e}")

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
        if self._auto_save_task:
            self._auto_save_task.cancel()

        try:
            await self.data_manager.close()
        except Exception as e:
            logger.error(f"종료 시 저장 실패: {e}")

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
            user = self.get_user(payload.user_id)
            if not user:
                return

            embed = discord.Embed(
                description="인증을 진행하려면 아래 버튼을 클릭하여 프로필 정보를 입력해주세요.",
                color=COLORS["INFO"]
            )
            view = AuthenticationView(self, payload.guild_id, role_id)
            await user.send(embed=embed, view=view)
        except discord.Forbidden:
            logger.error(f"DM 전송 실패: {payload.user_id}")
        except Exception as e:
            logger.error(f"모달 표시 실패: {e}")

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
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        logger.error("DISCORD_TOKEN이 설정되지 않았습니다.")
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
