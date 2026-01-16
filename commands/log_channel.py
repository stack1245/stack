"""로그 채널 설정 명령어"""
from __future__ import annotations

from discord import Option
from discord.ext import commands
import discord
from datetime import datetime
from utils.constants import COLORS
from zoneinfo import ZoneInfo
KST = ZoneInfo("Asia/Seoul")
class LogChannelCommand(commands.Cog):
    """로그 채널 설정 명령어"""
    def __init__(self, bot: discord.Bot) -> None:
        """초기화"""
        self.bot = bot
        self.data_manager = bot.data_manager
    @discord.slash_command(name="로그채널설정", description="로그를 보낼 채널을 설정합니다")
    @commands.has_permissions(administrator=True)
    async def set_log_channel(
        self,
        ctx: discord.ApplicationContext,
        채널: discord.TextChannel = Option(discord.TextChannel, description="로그를 보낼 채널", required=True)
    ):
        guild_id = str(ctx.guild.id)
        channel_id = str(채널.id)
        success = await self.data_manager.set_log_channel(guild_id, channel_id)
        if success:
            embed = discord.Embed(
                title="로그 채널 설정 완료",
                description=f"로그가 {채널.mention} 채널로 전송됩니다.",
                color=COLORS["SUCCESS"],
                timestamp=datetime.now(KST)
            )
            embed.set_footer(text=f"설정자: {ctx.author}")
            await ctx.respond(embed=embed, ephemeral=True)
        else:
            await ctx.respond("로그 채널 설정 중 오류가 발생했습니다.", ephemeral=True)
def setup(bot: discord.Bot):
    """명령어 로드"""
    bot.add_cog(LogChannelCommand(bot))
