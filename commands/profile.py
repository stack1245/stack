"""프로필 관리 명령어"""
from __future__ import annotations

from discord import Option
from discord.ext import commands
import discord
from datetime import datetime
from utils.constants import COLORS
from zoneinfo import ZoneInfo
KST = ZoneInfo("Asia/Seoul")
class ProfileCommands(commands.Cog):
    """프로필 관리 명령어"""
    def __init__(self, bot: discord.Bot) -> None:
        """초기화"""
        self.bot = bot
        self.data_manager = bot.data_manager
    @discord.slash_command(name="프로필등록", description="프로필을 등록하거나 수정합니다")
    async def register_profile(
        self,
        ctx: discord.ApplicationContext,
        닉네임: str = Option(str, description="표시될 닉네임 또는 이름", required=True),
        출생년도: str = Option(str, description="출생년도 (예: 2008 또는 08)", required=True),
        성별: str = Option(str, description="성별", choices=["남", "여", "기타", "비공개"], required=True),
        지역: str = Option(str, description="거주 지역 (예: 서울, 부산 등)", required=True),
        유저: discord.Member = Option(discord.Member, description="프로필을 설정할 유저 (관리자 전용)", required=False, default=None)
    ):
        target_user = 유저 if 유저 else ctx.author
        if target_user.id != ctx.author.id and not ctx.author.guild_permissions.administrator:
            await ctx.respond("다른 유저의 프로필을 수정하려면 관리자 권한이 필요합니다.", ephemeral=True)
            return
        user_id = str(target_user.id)
        username = str(target_user)
        success = await self.data_manager.register_profile(
            user_id=user_id,
            username=username,
            display_name=닉네임,
            birth_year=출생년도,
            gender=성별,
            region=지역
        )
        if success:
            is_self = target_user.id == ctx.author.id
            title = "프로필 등록 완료" if is_self else f"{target_user.display_name}님의 프로필 등록 완료"
            embed = discord.Embed(
                title=title,
                description="프로필이 성공적으로 등록되었습니다!",
                color=COLORS["SUCCESS"],
                timestamp=datetime.now(KST)
            )
            if not is_self:
                embed.add_field(name="대상 유저", value=target_user.mention, inline=False)
            embed.add_field(name="닉네임", value=닉네임, inline=True)
            embed.add_field(name="출생년도", value=출생년도, inline=True)
            embed.add_field(name="성별", value=성별, inline=True)
            embed.add_field(name="지역", value=지역, inline=True)
            embed.set_footer(text=f"등록자: {ctx.author}")
            await ctx.respond(embed=embed)
        else:
            await ctx.respond("프로필 등록 중 오류가 발생했습니다.", ephemeral=True)
    @discord.slash_command(name="프로필목록", description="등록된 모든 유저의 프로필 목록을 조회합니다")
    async def list_profiles(self, ctx: discord.ApplicationContext) -> None:
        await ctx.defer()
        profiles = await self.data_manager.get_all_profiles()
        if not profiles:
            await ctx.respond("등록된 프로필이 없습니다.", ephemeral=True)
            return
        items_per_page = 15
        total_pages = (len(profiles) - 1) // items_per_page + 1
        embeds = []
        for page in range(total_pages):
            start_idx = page * items_per_page
            end_idx = min(start_idx + items_per_page, len(profiles))
            page_profiles = profiles[start_idx:end_idx]
            embed = discord.Embed(
            title="등록된 프로필 목록",
                color=COLORS["INFO"],
                timestamp=datetime.now(KST)
            )
            profile_list = []
            for i, profile in enumerate(page_profiles, start=start_idx + 1):
                user_mention = f"<@{profile['user_id']}>"
                display_name = profile['display_name']
                profile_list.append(f"{i}. **{display_name}** - {user_mention}")
            embed.add_field(
                name="유저 목록",
                value="\n".join(profile_list),
                inline=False
            )
            if total_pages > 1:
                embed.set_footer(text=f"페이지 {page + 1}/{total_pages}")
            embeds.append(embed)
        if len(embeds) == 1:
            await ctx.respond(embed=embeds[0])
        else:
            await ctx.respond(embed=embeds[0])
    @discord.slash_command(name="정보", description="유저의 프로필 정보를 조회합니다")
    async def get_info(
        self,
        ctx: discord.ApplicationContext,
        유저: discord.Member = Option(discord.Member, description="정보를 조회할 유저", required=False, default=None)
    ):
        target_user = 유저 if 유저 else ctx.author
        user_id = str(target_user.id)
        profile = await self.data_manager.get_profile(user_id)
        if not profile:
            await ctx.respond(f"{target_user.mention}님의 등록된 프로필이 없습니다.", ephemeral=True)
            return
        embed = discord.Embed(
            title=f"{profile['display_name']}님의 프로필",
            color=COLORS["INFO"],
            timestamp=datetime.now(KST)
        )
        embed.set_thumbnail(url=target_user.display_avatar.url)
        embed.add_field(name="디스코드", value=f"<@{user_id}>", inline=False)
        embed.add_field(name="닉네임", value=profile['display_name'], inline=True)
        embed.add_field(name="출생년도", value=profile['birth_year'], inline=True)
        embed.add_field(name="성별", value=profile['gender'], inline=True)
        embed.add_field(name="지역", value=profile['region'], inline=True)
        if ctx.author.guild_permissions.administrator:
            admin_info = await self.data_manager.get_admin_info(user_id)
            if admin_info:
                embed.add_field(name="\u200b", value="**━━━ 관리자 전용 정보 ━━━**", inline=False)
                embed.add_field(name="경고 횟수", value=f"{admin_info['warning_count']}회", inline=True)
                memo = admin_info['admin_memo'] if admin_info['admin_memo'] else "없음"
                embed.add_field(name="관리자 메모", value=memo, inline=False)
        if profile.get('registered_at'):
            registered_time = profile['registered_at'].split('T')[0]
            embed.set_footer(text=f"등록일: {registered_time}")
        await ctx.respond(embed=embed)
def setup(bot: discord.Bot):
    """명령어 로드"""
    bot.add_cog(ProfileCommands(bot))
