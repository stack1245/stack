"""서버 이벤트 로그"""
from __future__ import annotations
import logging
import discord
from discord.ext import commands
from datetime import datetime
from zoneinfo import ZoneInfo

from utils.constants import COLORS

logger = logging.getLogger(__name__)
KST = ZoneInfo("Asia/Seoul")


class EventLogger(commands.Cog):
    """서버 이벤트 로그"""
    
    def __init__(self, bot: discord.Bot):
        self.bot = bot
        self.data_manager = bot.data_manager
    
    async def send_log(self, guild: discord.Guild, embed: discord.Embed) -> None:
        """로그 채널에 embed 전송"""
        try:
            guild_id = str(guild.id)
            log_channel_id = await self.data_manager.get_log_channel(guild_id)
            
            if log_channel_id:
                channel = guild.get_channel(int(log_channel_id))
                if channel:
                    await channel.send(embed=embed)
        except Exception as e:
            logger.error(f"로그 전송 실패: {e}")
    
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """유저 입장 로그"""
        embed = discord.Embed(
            title="유저 입장",
            description=f"{member.mention}님이 서버에 입장했습니다.",
            color=COLORS["SUCCESS"],
            timestamp=datetime.now(KST)
        )
        embed.add_field(name="유저", value=f"{member} ({member.id})", inline=False)
        embed.add_field(name="계정 생성일", value=member.created_at.astimezone(KST).strftime("%Y-%m-%d %H:%M"), inline=True)
        embed.set_thumbnail(url=member.display_avatar.url)
        
        await self.send_log(member.guild, embed)
    
    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        """유저 퇴장 로그"""
        embed = discord.Embed(
            title="유저 퇴장",
            description=f"{member.mention}님이 서버에서 퇴장했습니다.",
            color=COLORS["ERROR"],
            timestamp=datetime.now(KST)
        )
        embed.add_field(name="유저", value=f"{member} ({member.id})", inline=False)
        if member.joined_at:
            embed.add_field(name="서버 가입일", value=member.joined_at.astimezone(KST).strftime("%Y-%m-%d %H:%M"), inline=True)
        embed.set_thumbnail(url=member.display_avatar.url)
        
        await self.send_log(member.guild, embed)
    
    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        """메시지 삭제 로그"""
        if message.author.bot or not message.guild:
            return
        
        deleter = None
        try:
            async for entry in message.guild.audit_logs(limit=5, action=discord.AuditLogAction.message_delete):
                if entry.target.id == message.author.id and (discord.utils.utcnow() - entry.created_at).total_seconds() < 3:
                    deleter = entry.user
                    break
        except (discord.Forbidden, discord.HTTPException):
            pass
        
        if deleter and deleter.id != message.author.id:
            embed = discord.Embed(
                title="메시지 삭제 (관리자)",
                description=f"{message.author.mention}님의 메시지가 {deleter.mention}님에 의해 삭제되었습니다.",
                color=COLORS["ERROR"],
                timestamp=datetime.now(KST)
            )
            embed.add_field(name="작성자", value=f"{message.author} ({message.author.id})", inline=True)
            embed.add_field(name="삭제자", value=f"{deleter} ({deleter.id})", inline=True)
        else:
            embed = discord.Embed(
                title="메시지 삭제",
                description=f"{message.author.mention}님의 메시지가 삭제되었습니다.",
                color=COLORS["WARNING"],
                timestamp=datetime.now(KST)
            )
            embed.add_field(name="작성자", value=f"{message.author} ({message.author.id})", inline=False)
        
        embed.add_field(name="채널", value=message.channel.mention, inline=True)
        
        content = message.content[:1000] if message.content else "_내용 없음_"
        embed.add_field(name="삭제된 내용", value=content, inline=False)
        
        if message.attachments:
            attachments_info = "\n".join([f"[{att.filename}]({att.url})" for att in message.attachments[:5]])
            embed.add_field(name="첨부파일", value=attachments_info, inline=False)
        
        embed.set_thumbnail(url=message.author.display_avatar.url)
        
        await self.send_log(message.guild, embed)
    
    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        """메시지 수정 로그"""
        if before.author.bot or not before.guild:
            return
        
        if before.content == after.content:
            return
        
        embed = discord.Embed(
            title="메시지 수정",
            description=f"{before.author.mention}님이 메시지를 수정했습니다.",
            color=COLORS["INFO"],
            timestamp=datetime.now(KST)
        )
        embed.add_field(name="작성자", value=f"{before.author} ({before.author.id})", inline=False)
        embed.add_field(name="채널", value=before.channel.mention, inline=True)
        
        before_content = before.content[:1000] if before.content else "_내용 없음_"
        embed.add_field(name="수정 전", value=before_content, inline=False)
        
        after_content = after.content[:1000] if after.content else "_내용 없음_"
        embed.add_field(name="수정 후", value=after_content, inline=False)
        
        embed.add_field(name="메시지 링크", value=f"[바로가기]({after.jump_url})", inline=False)
        
        embed.set_thumbnail(url=before.author.display_avatar.url)
        
        await self.send_log(before.guild, embed)


def setup(bot: discord.Bot):
    bot.add_cog(EventLogger(bot))
