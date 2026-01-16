"""관리자 메모 작성 명령어"""
from __future__ import annotations

from discord import Option
from discord.ext import commands
import discord
from datetime import datetime
from utils.constants import COLORS
from zoneinfo import ZoneInfo
KST = ZoneInfo("Asia/Seoul")
class MemoCommand(commands.Cog):
    """관리자 메모 작성 명령어"""
    def __init__(self, bot: discord.Bot) -> None:
        """초기화"""
        self.bot = bot
        self.data_manager = bot.data_manager
    @discord.slash_command(name="메모", description="유저에 대한 관리자 메모를 작성합니다")
    @commands.has_permissions(administrator=True)
    async def set_memo(
        self,
        ctx: discord.ApplicationContext,
        유저: discord.Member = Option(discord.Member, description="메모를 작성할 유저", required=True),
        메모: str = Option(str, description="작성할 메모 내용", required=True)
    ):
        user_id = str(유저.id)
        profile = await self.data_manager.get_profile(user_id)
        if not profile:
            await ctx.respond(f"{유저.mention}님은 등록된 프로필이 없습니다.", ephemeral=True)
            return
        success = await self.data_manager.set_admin_memo(user_id, 메모)
        if success:
            embed = discord.Embed(
                title="메모 작성 완료",
                description=f"{유저.mention}님에 대한 메모가 작성되었습니다.",
                color=COLORS["INFO"],
                timestamp=datetime.now(KST)
            )
            embed.add_field(name="메모 내용", value=메모, inline=False)
            embed.set_footer(text=f"작성자: {ctx.author}")
            await ctx.respond(embed=embed, ephemeral=True)
        else:
            await ctx.respond("메모 작성 중 오류가 발생했습니다.", ephemeral=True)
def setup(bot: discord.Bot):
    """명령어 로드"""
    bot.add_cog(MemoCommand(bot))
