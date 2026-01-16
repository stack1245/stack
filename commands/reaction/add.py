"""반응 역할 설정"""
from __future__ import annotations
import discord
from discord.ext import commands

from utils.constants import COLORS
from . import reaction_group


class AddReaction(commands.Cog):
    """반응 역할 설정"""
    
    def __init__(self, bot: discord.Bot):
        self.bot = bot
    
    @reaction_group.command(
        name="설정",
        description="메시지에 반응 역할을 설정합니다"
    )
    async def add_reaction(
        self,
        ctx: discord.ApplicationContext,
        message_id: str = discord.Option(str, description="메시지 ID"),
        role: discord.Role = discord.Option(discord.Role, description="지급할 역할"),
        reaction: str = discord.Option(str, description="반응 (이모지)", default="✅")
    ):
        """반응 역할 설정"""
        try:
            msg_id = int(message_id)
        except ValueError:
            await ctx.respond("❌ 올바른 메시지 ID를 입력하세요.", ephemeral=True)
            return
        
        try:
            message = await ctx.channel.fetch_message(msg_id)
        except discord.NotFound:
            await ctx.respond("❌ 메시지를 찾을 수 없습니다.", ephemeral=True)
            return
        except discord.HTTPException as e:
            await ctx.respond(f"❌ 메시지를 가져올 수 없습니다: {e}", ephemeral=True)
            return
        
        try:
            await message.add_reaction(reaction)
        except discord.HTTPException as e:
            await ctx.respond(f"❌ 반응을 추가할 수 없습니다: {e}", ephemeral=True)
            return
        
        reaction_id = await self.bot.data_manager.add_reaction_role(
            msg_id,
            ctx.channel.id,
            reaction,
            role.id
        )
        
        embed = discord.Embed(
            title="✅ 반응 역할 설정 완료",
            description=(
                f"**반응설정 ID:** `{reaction_id}`\n"
                f"**메시지 ID:** `{message_id}`\n"
                f"**반응:** {reaction}\n"
                f"**역할:** {role.mention}\n\n"
                f"해당 반응을 누르면 프로필 입력 모달이 표시되며,\n"
                f"프로필 정보를 모두 입력하면 역할이 지급됩니다.\n"
                f"반응을 제거하면 역할이 회수됩니다."
            ),
            color=COLORS["SUCCESS"]
        )
        await ctx.respond(embed=embed, ephemeral=True)
