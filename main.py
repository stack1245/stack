import discord
from discord.ext import commands
from discord import Option, SlashCommandGroup
from datetime import datetime
import config
from database import Database


intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = discord.Bot(intents=intents)
db = Database(config.DATABASE_PATH)


@bot.event
async def on_ready():
    await db.init_db()
    print(f"[{bot.user.name}] 준비 완료")


@bot.slash_command(name="프로필등록", description="프로필을 등록하거나 수정합니다")
async def register_profile(
    ctx: discord.ApplicationContext,
    닉네임: str = Option(str, description="표시될 닉네임 또는 이름", required=True),
    출생년도: str = Option(str, description="출생년도 (예: 2008 또는 08)", required=True),
    성별: str = Option(str, description="성별", choices=["남", "여", "기타", "비공개"], required=True),
    지역: str = Option(str, description="거주 지역 (예: 서울, 부산 등)", required=True),
    유저: discord.Member = Option(discord.Member, description="프로필을 설정할 유저 (관리자 전용)", required=False, default=None)
):
    target_user = 유저 if 유저 else ctx.author
    
    if target_user.id != ctx.author.id and not ctx.author.guild_permissions.administrator:
        await ctx.respond("❌ 다른 유저의 프로필을 수정하려면 관리자 권한이 필요합니다.", ephemeral=True)
        return
    
    user_id = str(target_user.id)
    username = str(target_user)
    
    success = await db.register_profile(
        user_id=user_id,
        username=username,
        display_name=닉네임,
        birth_year=출생년도,
        gender=성별,
        region=지역
    )
    
    if success:
        is_self = target_user.id == ctx.author.id
        title = "✅ 프로필 등록 완료" if is_self else f"✅ {target_user.display_name}님의 프로필 등록 완료"
        
        embed = discord.Embed(
            title=title,
            description="프로필이 성공적으로 등록되었습니다!",
            color=discord.Color.green(),
            timestamp=datetime.now()
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
        await ctx.respond("❌ 프로필 등록 중 오류가 발생했습니다.", ephemeral=True)


@bot.slash_command(name="정보", description="유저의 프로필 정보를 조회합니다")
async def get_info(
    ctx: discord.ApplicationContext,
    유저: discord.Member = Option(discord.Member, description="정보를 조회할 유저", required=False, default=None)
):
    target_user = 유저 if 유저 else ctx.author
    user_id = str(target_user.id)
    
    profile = await db.get_profile(user_id)
    
    if not profile:
        await ctx.respond(f"❌ {target_user.mention}님의 등록된 프로필이 없습니다.", ephemeral=True)
        return
    
    embed = discord.Embed(
        title=f"📋 {profile['display_name']}님의 프로필",
        color=discord.Color.blue(),
        timestamp=datetime.now()
    )
    
    embed.set_thumbnail(url=target_user.display_avatar.url)
    embed.add_field(name="👤 디스코드", value=f"<@{user_id}>", inline=False)
    embed.add_field(name="✏️ 닉네임", value=profile['display_name'], inline=True)
    embed.add_field(name="🎂 출생년도", value=profile['birth_year'], inline=True)
    embed.add_field(name="⚧ 성별", value=profile['gender'], inline=True)
    embed.add_field(name="📍 지역", value=profile['region'], inline=True)
    
    if ctx.author.guild_permissions.administrator:
        admin_info = await db.get_admin_info(user_id)
        if admin_info:
            embed.add_field(name="\u200b", value="**━━━ 관리자 전용 정보 ━━━**", inline=False)
            embed.add_field(name="⚠️ 경고 횟수", value=f"{admin_info['warning_count']}회", inline=True)
            memo = admin_info['admin_memo'] if admin_info['admin_memo'] else "없음"
            embed.add_field(name="📝 관리자 메모", value=memo, inline=False)
    
    if profile.get('registered_at'):
        registered_time = profile['registered_at'].split('T')[0]
        embed.set_footer(text=f"등록일: {registered_time}")
    
    await ctx.respond(embed=embed)


admin = SlashCommandGroup("관리", "관리자 전용 명령어")


@admin.command(name="경고추가", description="[관리자] 유저에게 경고를 추가합니다")
@commands.has_permissions(administrator=True)
async def add_warning(
    ctx: discord.ApplicationContext,
    유저: discord.Member = Option(discord.Member, description="경고를 추가할 유저", required=True),
    횟수: int = Option(int, description="추가할 경고 횟수", required=False, default=1, min_value=1)
):
    user_id = str(유저.id)
    
    profile = await db.get_profile(user_id)
    if not profile:
        await ctx.respond(f"❌ {유저.mention}님은 등록된 프로필이 없습니다.", ephemeral=True)
        return
    
    success = await db.add_warning(user_id, 횟수)
    
    if success:
        admin_info = await db.get_admin_info(user_id)
        total_warnings = admin_info['warning_count'] if admin_info else 0
        
        embed = discord.Embed(
            title="⚠️ 경고 추가",
            description=f"{유저.mention}님에게 경고 {횟수}회가 추가되었습니다.",
            color=discord.Color.orange(),
            timestamp=datetime.now()
        )
        embed.add_field(name="총 경고 횟수", value=f"{total_warnings}회", inline=False)
        embed.set_footer(text=f"처리자: {ctx.author}")
        await ctx.respond(embed=embed)
    else:
        await ctx.respond("❌ 경고 추가 중 오류가 발생했습니다.", ephemeral=True)


@admin.command(name="경고제거", description="[관리자] 유저의 경고를 제거합니다")
@commands.has_permissions(administrator=True)
async def remove_warning(
    ctx: discord.ApplicationContext,
    유저: discord.Member = Option(discord.Member, description="경고를 제거할 유저", required=True),
    횟수: int = Option(int, description="제거할 경고 횟수", required=False, default=1, min_value=1)
):
    user_id = str(유저.id)
    
    profile = await db.get_profile(user_id)
    if not profile:
        await ctx.respond(f"❌ {유저.mention}님은 등록된 프로필이 없습니다.", ephemeral=True)
        return
    
    success = await db.remove_warning(user_id, 횟수)
    
    if success:
        admin_info = await db.get_admin_info(user_id)
        total_warnings = admin_info['warning_count'] if admin_info else 0
        
        embed = discord.Embed(
            title="✅ 경고 제거",
            description=f"{유저.mention}님의 경고 {횟수}회가 제거되었습니다.",
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        embed.add_field(name="남은 경고 횟수", value=f"{total_warnings}회", inline=False)
        embed.set_footer(text=f"처리자: {ctx.author}")
        await ctx.respond(embed=embed)
    else:
        await ctx.respond("❌ 경고 제거 중 오류가 발생했습니다.", ephemeral=True)


@admin.command(name="메모작성", description="[관리자] 유저에 대한 관리자 메모를 작성합니다")
@commands.has_permissions(administrator=True)
async def set_memo(
    ctx: discord.ApplicationContext,
    유저: discord.Member = Option(discord.Member, description="메모를 작성할 유저", required=True),
    메모: str = Option(str, description="작성할 메모 내용", required=True)
):
    user_id = str(유저.id)
    
    profile = await db.get_profile(user_id)
    if not profile:
        await ctx.respond(f"❌ {유저.mention}님은 등록된 프로필이 없습니다.", ephemeral=True)
        return
    
    success = await db.set_admin_memo(user_id, 메모)
    
    if success:
        embed = discord.Embed(
            title="📝 메모 작성 완료",
            description=f"{유저.mention}님에 대한 메모가 작성되었습니다.",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        embed.add_field(name="메모 내용", value=메모, inline=False)
        embed.set_footer(text=f"작성자: {ctx.author}")
        await ctx.respond(embed=embed, ephemeral=True)
    else:
        await ctx.respond("❌ 메모 작성 중 오류가 발생했습니다.", ephemeral=True)


@admin.command(name="로그채널설정", description="[관리자] 로그를 보낼 채널을 설정합니다")
@commands.has_permissions(administrator=True)
async def set_log_channel(
    ctx: discord.ApplicationContext,
    채널: discord.TextChannel = Option(discord.TextChannel, description="로그를 보낼 채널", required=True)
):
    guild_id = str(ctx.guild.id)
    channel_id = str(채널.id)
    
    success = await db.set_log_channel(guild_id, channel_id)
    
    if success:
        embed = discord.Embed(
            title="✅ 로그 채널 설정 완료",
            description=f"로그가 {채널.mention} 채널로 전송됩니다.",
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        embed.set_footer(text=f"설정자: {ctx.author}")
        await ctx.respond(embed=embed, ephemeral=True)
    else:
        await ctx.respond("❌ 로그 채널 설정 중 오류가 발생했습니다.", ephemeral=True)


@admin.command(name="청소", description="[관리자] 채널의 메시지를 삭제합니다")
@commands.has_permissions(administrator=True)
async def clear_messages(
    ctx: discord.ApplicationContext,
    개수: int = Option(int, description="삭제할 메시지 개수", required=True, min_value=1, max_value=100),
    유저: discord.Member = Option(discord.Member, description="특정 유저의 메시지만 삭제", required=False, default=None)
):
    await ctx.defer(ephemeral=True)
    
    try:
        if 유저:
            # 특정 유저의 메시지만 삭제
            def check_user(m):
                return m.author.id == 유저.id
            
            deleted = await ctx.channel.purge(limit=개수, check=check_user)
            
            embed = discord.Embed(
                title="🧹 메시지 청소 완료",
                description=f"{유저.mention}님의 메시지 {len(deleted)}개가 삭제되었습니다.",
                color=discord.Color.green(),
                timestamp=datetime.now()
            )
        else:
            # 모든 메시지 삭제
            deleted = await ctx.channel.purge(limit=개수)
            
            embed = discord.Embed(
                title="🧹 메시지 청소 완료",
                description=f"{len(deleted)}개의 메시지가 삭제되었습니다.",
                color=discord.Color.green(),
                timestamp=datetime.now()
            )
        
        embed.add_field(name="채널", value=ctx.channel.mention, inline=True)
        embed.add_field(name="실행자", value=ctx.author.mention, inline=True)
        embed.set_footer(text=f"처리자: {ctx.author}")
        
        await ctx.respond(embed=embed, ephemeral=True)
        
    except discord.Forbidden:
        await ctx.respond("❌ 메시지를 삭제할 권한이 없습니다.", ephemeral=True)
    except discord.HTTPException as e:
        await ctx.respond(f"❌ 메시지 삭제 중 오류가 발생했습니다: {e}", ephemeral=True)


bot.add_application_command(admin)


async def send_log(guild: discord.Guild, embed: discord.Embed):
    """로그 채널에 embed 전송"""
    try:
        guild_id = str(guild.id)
        log_channel_id = await db.get_log_channel(guild_id)
        
        if log_channel_id:
            channel = guild.get_channel(int(log_channel_id))
            if channel:
                await channel.send(embed=embed)
    except Exception as e:
        print(f"[로그 전송 오류] {e}")


@bot.event
async def on_member_join(member: discord.Member):
    """유저 입장 로그"""
    embed = discord.Embed(
        title="📥 유저 입장",
        description=f"{member.mention}님이 서버에 입장했습니다.",
        color=discord.Color.green(),
        timestamp=datetime.now()
    )
    embed.add_field(name="유저", value=f"{member} ({member.id})", inline=False)
    embed.add_field(name="계정 생성일", value=member.created_at.strftime("%Y-%m-%d %H:%M"), inline=True)
    embed.set_thumbnail(url=member.display_avatar.url)
    
    await send_log(member.guild, embed)


@bot.event
async def on_member_remove(member: discord.Member):
    """유저 퇴장 로그"""
    embed = discord.Embed(
        title="📤 유저 퇴장",
        description=f"{member.mention}님이 서버에서 퇴장했습니다.",
        color=discord.Color.red(),
        timestamp=datetime.now()
    )
    embed.add_field(name="유저", value=f"{member} ({member.id})", inline=False)
    if member.joined_at:
        embed.add_field(name="서버 가입일", value=member.joined_at.strftime("%Y-%m-%d %H:%M"), inline=True)
    embed.set_thumbnail(url=member.display_avatar.url)
    
    await send_log(member.guild, embed)


@bot.event
async def on_message_delete(message: discord.Message):
    """메시지 삭제 로그"""
    if message.author.bot or not message.guild:
        return
    
    embed = discord.Embed(
        title="🗑️ 메시지 삭제",
        description=f"{message.author.mention}님의 메시지가 삭제되었습니다.",
        color=discord.Color.orange(),
        timestamp=datetime.now()
    )
    embed.add_field(name="작성자", value=f"{message.author} ({message.author.id})", inline=False)
    embed.add_field(name="채널", value=message.channel.mention, inline=True)
    
    content = message.content[:1000] if message.content else "_내용 없음_"
    embed.add_field(name="삭제된 내용", value=content, inline=False)
    
    if message.attachments:
        attachments_info = "\n".join([f"[{att.filename}]({att.url})" for att in message.attachments[:5]])
        embed.add_field(name="첨부파일", value=attachments_info, inline=False)
    
    embed.set_thumbnail(url=message.author.display_avatar.url)
    
    await send_log(message.guild, embed)


@bot.event
async def on_application_command_error(ctx: discord.ApplicationContext, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.respond("❌ 이 명령어를 사용할 권한이 없습니다.", ephemeral=True)
    else:
        print(f"[오류] {error}")
        await ctx.respond("❌ 명령어 실행 중 오류가 발생했습니다.", ephemeral=True)


if __name__ == "__main__":
    if not config.BOT_TOKEN:
        print("[오류] DISCORD_BOT_TOKEN이 설정되지 않았습니다. .env 파일을 확인해주세요.")
    else:
        bot.run(config.BOT_TOKEN)
