"""경고 추가 명령어"""
from __future__ import annotations

from discord import Option
from discord.ext import commands
import discord
from datetime import datetime
from utils.constants import COLORS
from zoneinfo import ZoneInfo
KST = ZoneInfo("Asia/Seoul")
class AddWarningCommand(commands.Cog):
    """경고 추가 명령어"""
    def __init__(self, bot: discord.Bot) -> None:
        """초기화"""
        self.bot = bot
        self.data_manager = bot.data_manager
    @discord.slash_command(name="경고추가", description="유저에게 경고를 추가합니다")
    @commands.has_permissions(administrator=True)
    async def add_warning(
        self,
        ctx: discord.ApplicationContext,
        유저: discord.Member = Option(discord.Member, description="경고를 추가할 유저", required=True),
        횟수: int = Option(int, description="추가할 경고 횟수", required=False, default=1, min_value=1)
    ):
        user_id = str(유저.id)
        profile = await self.data_manager.get_profile(user_id)
        if not profile:
            await ctx.respond(f"{유저.mention}님은 등록된 프로필이 없습니다.", ephemeral=True)
            return
        success = await self.data_manager.add_warning(user_id, 횟수)
        if success:
            admin_info = await self.data_manager.get_admin_info(user_id)
            total_warnings = admin_info['warning_count'] if admin_info else 0
            embed = discord.Embed(
                title="경고 추가",
                description=f"{유저.mention}님에게 경고 {횟수}회가 추가되었습니다.",
                color=COLORS["WARNING"],
                timestamp=datetime.now(KST)
            )
            embed.add_field(name="총 경고 횟수", value=f"{total_warnings}회", inline=False)
            embed.set_footer(text=f"처리자: {ctx.author}")
            await ctx.respond(embed=embed)
        else:
            await ctx.respond("경고 추가 중 오류가 발생했습니다.", ephemeral=True)
def setup(bot: discord.Bot):
    """명령어 로드"""
    bot.add_cog(AddWarningCommand(bot))
