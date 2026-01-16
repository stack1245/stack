"""역할 인증 메시지 생성"""
from __future__ import annotations
import discord
from discord.ext import commands

from utils.constants import COLORS
from . import reaction_group


class SetupModal(discord.ui.Modal):
    """역할 인증 메시지 생성 모달"""
    
    def __init__(self):
        super().__init__(title="역할 인증 메시지 생성")
        
        self.add_item(
            discord.ui.InputText(
                label="제목",
                placeholder="임베드 제목 (선택사항)",
                required=False,
                max_length=256
            )
        )
        
        self.add_item(
            discord.ui.InputText(
                label="내용",
                placeholder="임베드 내용을 입력하세요",
                style=discord.InputTextStyle.long,
                required=True,
                max_length=4000
            )
        )
    
    async def callback(self, interaction: discord.Interaction):
        """모달 제출 처리"""
        title = self.children[0].value.strip() or None
        description = self.children[1].value
        
        embed = discord.Embed(
            description=description,
            color=COLORS["INFO"]
        )
        
        if title:
            embed.title = title
        
        await interaction.response.send_message(
            embed=discord.Embed(
                description="역할 인증 메시지가 생성되었습니다.",
                color=COLORS["SUCCESS"]
            ),
            ephemeral=True
        )
        await interaction.channel.send(embed=embed)


@reaction_group.command(
    name="메시지생성",
    description="역할 인증 메시지를 생성합니다"
)
async def setup_message(ctx: discord.ApplicationContext):
    """역할 인증 메시지 생성 모달 열기"""
    modal = SetupModal()
    await ctx.send_modal(modal)
