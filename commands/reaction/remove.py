"""반응 역할 제거"""
from __future__ import annotations
import discord
from discord.ext import commands

from utils.constants import COLORS
from . import reaction_group


class RemoveReaction(commands.Cog):
    """반응 역할 제거"""
    
    def __init__(self, bot: discord.Bot):
        self.bot = bot
    
    @reaction_group.command(
        name="제거",
        description="반응설정 ID로 반응 역할 설정을 제거합니다"
    )
    async def remove_reaction(
        self,
        ctx: discord.ApplicationContext,
        reaction_id: str = discord.Option(str, description="반응설정 ID (/반응 목록에서 확인)")
    ):
        """반응설정 ID로 매핑 제거"""
        reaction_data = await self.bot.data_manager.get_reaction_role_by_id(reaction_id)
        
        if not reaction_data:
            await ctx.respond(
                f"❌ 반응설정 ID `{reaction_id}`를 찾을 수 없습니다.\n"
                f"`/반응 목록` 명령어로 유효한 ID를 확인하세요.",
                ephemeral=True
            )
            return
        
        message_id = reaction_data["message_id"]
        channel_id = reaction_data["channel_id"]
        emoji = reaction_data["emoji"]
        role_id = reaction_data["role_id"]
        
        try:
            channel = self.bot.get_channel(channel_id)
            if channel:
                message = await channel.fetch_message(message_id)
                await message.clear_reaction(emoji)
        except Exception:
            pass
        
        if await self.bot.data_manager.remove_reaction_by_id(reaction_id):
            role = ctx.guild.get_role(role_id) if ctx.guild else None
            role_name = role.mention if role else f"<@&{role_id}>"
            
            embed = discord.Embed(
                title="✅ 반응 역할 설정 제거 완료",
                description=(
                    f"**반응설정 ID:** `{reaction_id}`\n"
                    f"**메시지 ID:** `{message_id}`\n"
                    f"**반응:** {emoji}\n"
                    f"**역할:** {role_name}\n\n"
                    f"해당 반응은 더 이상 역할을 지급하지 않습니다."
                ),
                color=COLORS["SUCCESS"]
            )
            await ctx.respond(embed=embed, ephemeral=True)
        else:
            await ctx.respond("❌ 반응설정 제거에 실패했습니다.", ephemeral=True)
