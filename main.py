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
    
    # 커스텀 활동 설정
    activity = discord.Activity(type=discord.ActivityType.playing, name="기록 남기는 중...")
    await bot.change_presence(activity=activity, status=discord.Status.online)
    
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


@bot.slash_command(name="프로필목록", description="등록된 모든 유저의 프로필 목록을 조회합니다")
async def list_profiles(ctx: discord.ApplicationContext):
    await ctx.defer()
    
    profiles = await db.get_all_profiles()
    
    if not profiles:
        await ctx.respond("❌ 등록된 프로필이 없습니다.", ephemeral=True)
        return
    
    # 페이지당 15명씩 표시
    items_per_page = 15
    total_pages = (len(profiles) - 1) // items_per_page + 1
    
    embeds = []
    for page in range(total_pages):
        start_idx = page * items_per_page
        end_idx = min(start_idx + items_per_page, len(profiles))
        page_profiles = profiles[start_idx:end_idx]
        
        embed = discord.Embed(
            title="📋 등록된 프로필 목록",
            description=f"총 {len(profiles)}명의 프로필이 등록되어 있습니다.",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        
        # 프로필 목록 작성
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
    
    # 페이지가 1개면 그냥 전송, 여러 개면 페이지네이션 사용
    if len(embeds) == 1:
        await ctx.respond(embed=embeds[0])
    else:
        # 간단한 페이지네이션: 첫 페이지만 표시
        await ctx.respond(embed=embeds[0])


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
            # 특정 유저의 메시지만 정확히 개수만큼 삭제
            messages_to_delete = []
            search_limit = 1000  # 최대 탐색할 메시지 수
            
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
                title="🧹 메시지 청소 완료",
                description=f"{유저.mention}님의 메시지 {deleted_count}개가 삭제되었습니다.",
                color=discord.Color.green(),
                timestamp=datetime.now()
            )
            
            if deleted_count < 개수:
                embed.add_field(
                    name="⚠️ 알림", 
                    value=f"최근 {search_limit}개 메시지 중 {deleted_count}개만 찾았습니다.", 
                    inline=False
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
    
    # Audit Log를 확인하여 삭제자 찾기
    deleter = None
    try:
        async for entry in message.guild.audit_logs(limit=5, action=discord.AuditLogAction.message_delete):
            if entry.target.id == message.author.id and (discord.utils.utcnow() - entry.created_at).total_seconds() < 3:
                deleter = entry.user
                break
    except (discord.Forbidden, discord.HTTPException):
        pass
    
    # 삭제자가 작성자와 다른 경우 (타인이 삭제)
    if deleter and deleter.id != message.author.id:
        embed = discord.Embed(
            title="🗑️ 메시지 삭제 (관리자)",
            description=f"{message.author.mention}님의 메시지가 {deleter.mention}님에 의해 삭제되었습니다.",
            color=discord.Color.red(),
            timestamp=datetime.now()
        )
        embed.add_field(name="작성자", value=f"{message.author} ({message.author.id})", inline=True)
        embed.add_field(name="삭제자", value=f"{deleter} ({deleter.id})", inline=True)
    else:
        # 작성자 본인이 삭제
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
async def on_message_edit(before: discord.Message, after: discord.Message):
    """메시지 수정 로그"""
    if before.author.bot or not before.guild:
        return
    
    # 내용이 실제로 변경되지 않은 경우 무시 (embed 업데이트 등)
    if before.content == after.content:
        return
    
    embed = discord.Embed(
        title="✏️ 메시지 수정",
        description=f"{before.author.mention}님이 메시지를 수정했습니다.",
        color=discord.Color.blue(),
        timestamp=datetime.now()
    )
    embed.add_field(name="작성자", value=f"{before.author} ({before.author.id})", inline=False)
    embed.add_field(name="채널", value=before.channel.mention, inline=True)
    
    # 수정 전 내용
    before_content = before.content[:1000] if before.content else "_내용 없음_"
    embed.add_field(name="수정 전", value=before_content, inline=False)
    
    # 수정 후 내용
    after_content = after.content[:1000] if after.content else "_내용 없음_"
    embed.add_field(name="수정 후", value=after_content, inline=False)
    
    # 메시지 링크 추가
    embed.add_field(name="메시지 링크", value=f"[바로가기]({after.jump_url})", inline=False)
    
    embed.set_thumbnail(url=before.author.display_avatar.url)
    
    await send_log(before.guild, embed)


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
