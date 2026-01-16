"""반응 역할 목록 조회"""
from __future__ import annotations
import discord

from utils.constants import COLORS
from . import reaction_group


@reaction_group.command(
    name="목록",
    description="현재 설정된 모든 반응 역할 목록을 확인합니다"
)
async def list_reactions(ctx: discord.ApplicationContext):
    """모든 반응설정 목록 조회"""
    all_reactions = await ctx.bot.data_manager.get_all_reaction_roles()
        
        if not all_reactions:
            await ctx.respond("❌ 등록된 반응 역할 설정이 없습니다.", ephemeral=True)
            return
        
        by_channel = {}
        for reaction_id, data in all_reactions.items():
            channel_id = data["channel_id"]
            if channel_id not in by_channel:
                by_channel[channel_id] = []
            by_channel[channel_id].append((reaction_id, data))
        
        embed = discord.Embed(
            title="📋 반응 역할 설정 목록",
            color=COLORS["INFO"]
        )
        
        for channel_id, reactions in by_channel.items():
            channel = ctx.bot.get_channel(channel_id)
            channel_name = channel.mention if channel else f"<#{channel_id}>"
            
            lines = []
            for reaction_id, data in reactions:
                role = ctx.guild.get_role(data["role_id"])
                role_name = role.mention if role else f"<@&{data['role_id']}>"
                
                lines.append(
                    f"**ID:** `{reaction_id}` | "
                    f"{data['emoji']} → {role_name}\n"
                    f"└ 메시지: `{data['message_id']}`"
                )
            
            field_value = "\n\n".join(lines)
            if len(field_value) > 1024:
                field_value = field_value[:1021] + "..."
            
            embed.add_field(
                name=f"📌 채널: {channel_name}",
                value=field_value,
                inline=False
            )
        
        if len(embed.fields) > 25:
            embed.description = "⚠️ 설정이 너무 많아 일부만 표시됩니다."
            embed.fields = embed.fields[:25]
        
        embed.set_footer(text=f"총 {len(all_reactions)}개의 반응 역할 설정")
        await ctx.respond(embed=embed, ephemeral=True)
