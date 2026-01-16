"""메시지 삭제 명령어"""
from __future__ import annotations

from discord import Option
from discord.ext import commands
import discord
from datetime import datetime
from utils.constants import COLORS
from zoneinfo import ZoneInfo
KST = ZoneInfo("Asia/Seoul")


class DeleteCommand(commands.Cog):
    """메시지 삭제 명령어"""
    def __init__(self, bot: discord.Bot) -> None:
        """초기화"""
        self.bot = bot

    @discord.slash_command(name="메시지삭제", description="특정 메시지를 삭제합니다")
    @commands.has_permissions(administrator=True)
    async def delete_message(
        self,
        ctx: discord.ApplicationContext,
        메시지id: str = Option(str, description="삭제할 메시지의 ID", required=True)
    ):
        await ctx.defer(ephemeral=True)
        try:
            message_id = int(메시지id)
            try:
                message = await ctx.channel.fetch_message(message_id)
            except discord.NotFound:
                embed = discord.Embed(
                    title="오류",
                    description="해당 메시지를 찾을 수 없습니다.",
                    color=COLORS["ERROR"],
                    timestamp=datetime.now(KST)
                )
                await ctx.respond(embed=embed, ephemeral=True)
                return

            deleted_by = message.author.mention
            await message.delete()
            
            embed = discord.Embed(
                title="메시지 삭제 완료",
                description=f"메시지가 삭제되었습니다.",
                color=COLORS["SUCCESS"],
                timestamp=datetime.now(KST)
            )
            embed.add_field(name="메시지 작성자", value=deleted_by, inline=True)
            embed.add_field(name="채널", value=ctx.channel.mention, inline=True)
            embed.add_field(name="실행자", value=ctx.author.mention, inline=True)
            embed.set_footer(text=f"처리자: {ctx.author}")
            await ctx.respond(embed=embed, ephemeral=True)
        except ValueError:
            embed = discord.Embed(
                title="오류",
                description="유효한 메시지 ID가 아닙니다.",
                color=COLORS["ERROR"],
                timestamp=datetime.now(KST)
            )
            await ctx.respond(embed=embed, ephemeral=True)
        except discord.Forbidden:
            await ctx.respond("메시지를 삭제할 권한이 없습니다.", ephemeral=True)
        except discord.HTTPException as e:
            await ctx.respond(f"메시지 삭제 중 오류가 발생했습니다: {e}", ephemeral=True)


def setup(bot: discord.Bot):
    """명령어 로드"""
    bot.add_cog(DeleteCommand(bot))
