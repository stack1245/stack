"""메시지 청소 명령어"""
from __future__ import annotations

from discord import Option
from discord.ext import commands
import discord
from datetime import datetime
from utils.constants import COLORS
from zoneinfo import ZoneInfo
KST = ZoneInfo("Asia/Seoul")
class ClearCommand(commands.Cog):
    """메시지 청소 명령어"""
    def __init__(self, bot: discord.Bot) -> None:
        """초기화"""
        self.bot = bot
    @discord.slash_command(name="청소", description="채널의 메시지를 삭제합니다")
    @commands.has_permissions(administrator=True)
    async def clear_messages(
        self,
        ctx: discord.ApplicationContext,
        개수: int = Option(int, description="삭제할 메시지 개수", required=True, min_value=1, max_value=100),
        유저: discord.Member = Option(discord.Member, description="특정 유저의 메시지만 삭제", required=False, default=None)
    ):
        await ctx.defer(ephemeral=True)
        try:
            if 유저:
                messages_to_delete = []
                search_limit = 1000
                async for message in ctx.channel.history(limit=search_limit):
                    if message.author.id == 유저.id:
                        messages_to_delete.append(message)
                        if len(messages_to_delete) >= 개수:
                            break
                if messages_to_delete:
                    await ctx.channel.delete_messages(messages_to_delete)
                    deleted_count = len(messages_to_delete)
                else:
                    deleted_count = 0
                embed = discord.Embed(
                    title="메시지 청소 완료",
                    description=f"{유저.mention}님의 메시지 {deleted_count}개가 삭제되었습니다.",
                    color=COLORS["SUCCESS"],
                    timestamp=datetime.now(KST)
                )
                if deleted_count < 개수:
                    embed.add_field(
                        name="알림",
                        value=f"최근 {search_limit}개 메시지 중 {deleted_count}개만 찾았습니다.",
                        inline=False
                    )
            else:
                deleted = await ctx.channel.purge(limit=개수)
                embed = discord.Embed(
                    title="메시지 청소 완료",
                    description=f"{len(deleted)}개의 메시지가 삭제되었습니다.",
                    color=COLORS["SUCCESS"],
                    timestamp=datetime.now(KST)
                )
            embed.add_field(name="채널", value=ctx.channel.mention, inline=True)
            embed.add_field(name="실행자", value=ctx.author.mention, inline=True)
            embed.set_footer(text=f"처리자: {ctx.author}")
            await ctx.respond(embed=embed, ephemeral=True)
        except discord.Forbidden:
            await ctx.respond("메시지를 삭제할 권한이 없습니다.", ephemeral=True)
        except discord.HTTPException as e:
            await ctx.respond(f"메시지 삭제 중 오류가 발생했습니다: {e}", ephemeral=True)
def setup(bot: discord.Bot):
    """명령어 로드"""
    bot.add_cog(ClearCommand(bot))
