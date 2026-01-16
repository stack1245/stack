"""SQLite 데이터베이스 기반 데이터 관리"""
from __future__ import annotations
import logging
import aiosqlite
from datetime import datetime
from pathlib import Path
from typing import Any
import discord

from .constants import DATA_DIR, DEFAULT_SETTINGS

logger = logging.getLogger(__name__)


class DataManager:
    """SQLite 기반 데이터 관리"""
    
    def __init__(self, bot: discord.Bot):
        self.bot = bot
        self.db_path = DATA_DIR / "stack_bot.db"
        DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    async def init_db(self) -> None:
        """데이터베이스 초기화"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS user_profiles (
                        user_id TEXT PRIMARY KEY,
                        username TEXT NOT NULL,
                        display_name TEXT,
                        birth_year TEXT,
                        gender TEXT,
                        region TEXT,
                        registered_at TEXT,
                        updated_at TEXT
                    )
                """)
                
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS admin_info (
                        user_id TEXT PRIMARY KEY,
                        warning_count INTEGER DEFAULT 0,
                        admin_memo TEXT,
                        updated_at TEXT,
                        FOREIGN KEY (user_id) REFERENCES user_profiles (user_id)
                    )
                """)
                
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS server_settings (
                        guild_id TEXT PRIMARY KEY,
                        log_channel_id TEXT,
                        updated_at TEXT
                    )
                """)
                
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS reaction_roles (
                        reaction_id TEXT PRIMARY KEY,
                        message_id TEXT NOT NULL,
                        channel_id TEXT NOT NULL,
                        emoji TEXT NOT NULL,
                        role_id TEXT NOT NULL,
                        created_at TEXT
                    )
                """)
                
                await db.execute("""
                    CREATE INDEX IF NOT EXISTS idx_reaction_message 
                    ON reaction_roles(message_id)
                """)
                
                await db.commit()
        except Exception as e:
            logger.error(f"데이터베이스 초기화 실패: {e}")
    
    async def register_profile(
        self, user_id: str, username: str, display_name: str, 
        birth_year: str, gender: str, region: str
    ) -> bool:
        """프로필 등록"""
        try:
            now = datetime.now().isoformat()
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    "SELECT user_id FROM user_profiles WHERE user_id = ?", (user_id,)
                )
                existing = await cursor.fetchone()
                
                if existing:
                    await db.execute("""
                        UPDATE user_profiles 
                        SET username = ?, display_name = ?, birth_year = ?, 
                            gender = ?, region = ?, updated_at = ?
                        WHERE user_id = ?
                    """, (username, display_name, birth_year, gender, region, now, user_id))
                else:
                    await db.execute("""
                        INSERT INTO user_profiles 
                        (user_id, username, display_name, birth_year, gender, region, registered_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (user_id, username, display_name, birth_year, gender, region, now, now))
                    
                    await db.execute("""
                        INSERT INTO admin_info (user_id, warning_count, admin_memo, updated_at)
                        VALUES (?, 0, '', ?)
                    """, (user_id, now))
                
                await db.commit()
                return True
        except Exception as e:
            logger.error(f"프로필 등록 실패: {e}")
            return False
    
    async def get_profile(self, user_id: str) -> dict[str, Any] | None:
        """프로필 조회"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute(
                    "SELECT * FROM user_profiles WHERE user_id = ?", (user_id,)
                )
                row = await cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"프로필 조회 실패: {e}")
            return None
    
    async def get_all_profiles(self) -> list[dict[str, Any]]:
        """전체 프로필 조회"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute(
                    "SELECT * FROM user_profiles ORDER BY display_name ASC"
                )
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"전체 프로필 조회 실패: {e}")
            return []
    
    async def get_admin_info(self, user_id: str) -> dict[str, Any] | None:
        """관리자 정보 조회"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute(
                    "SELECT * FROM admin_info WHERE user_id = ?", (user_id,)
                )
                row = await cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"관리자 정보 조회 실패: {e}")
            return None
    
    async def add_warning(self, user_id: str, count: int = 1) -> bool:
        """경고 추가"""
        try:
            now = datetime.now().isoformat()
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    UPDATE admin_info 
                    SET warning_count = warning_count + ?, updated_at = ?
                    WHERE user_id = ?
                """, (count, now, user_id))
                await db.commit()
                return True
        except Exception as e:
            logger.error(f"경고 추가 실패: {e}")
            return False
    
    async def remove_warning(self, user_id: str, count: int = 1) -> bool:
        """경고 제거"""
        try:
            now = datetime.now().isoformat()
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    UPDATE admin_info 
                    SET warning_count = MAX(0, warning_count - ?), updated_at = ?
                    WHERE user_id = ?
                """, (count, now, user_id))
                await db.commit()
                return True
        except Exception as e:
            logger.error(f"경고 제거 실패: {e}")
            return False
    
    async def set_admin_memo(self, user_id: str, memo: str) -> bool:
        """관리자 메모 작성"""
        try:
            now = datetime.now().isoformat()
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    UPDATE admin_info 
                    SET admin_memo = ?, updated_at = ?
                    WHERE user_id = ?
                """, (memo, now, user_id))
                await db.commit()
                return True
        except Exception as e:
            logger.error(f"메모 작성 실패: {e}")
            return False
    
    async def set_log_channel(self, guild_id: str, channel_id: str) -> bool:
        """로그 채널 설정"""
        try:
            now = datetime.now().isoformat()
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    "SELECT guild_id FROM server_settings WHERE guild_id = ?", (guild_id,)
                )
                existing = await cursor.fetchone()
                
                if existing:
                    await db.execute("""
                        UPDATE server_settings 
                        SET log_channel_id = ?, updated_at = ?
                        WHERE guild_id = ?
                    """, (channel_id, now, guild_id))
                else:
                    await db.execute("""
                        INSERT INTO server_settings (guild_id, log_channel_id, updated_at)
                        VALUES (?, ?, ?)
                    """, (guild_id, channel_id, now))
                
                await db.commit()
                return True
        except Exception as e:
            logger.error(f"로그 채널 설정 실패: {e}")
            return False
    
    async def get_log_channel(self, guild_id: str) -> str | None:
        """로그 채널 조회"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    "SELECT log_channel_id FROM server_settings WHERE guild_id = ?", (guild_id,)
                )
                row = await cursor.fetchone()
                return row[0] if row else None
        except Exception as e:
            logger.error(f"로그 채널 조회 실패: {e}")
            return None
    
    async def add_reaction_role(
        self,
        message_id: int,
        channel_id: int,
        emoji: str,
        role_id: int
    ) -> str:
        """이모지-역할 매핑 추가"""
        try:
            import random
            while True:
                reaction_id = ''.join(random.choices('0123456789ABCDEF', k=6))
                async with aiosqlite.connect(self.db_path) as db:
                    cursor = await db.execute(
                        "SELECT reaction_id FROM reaction_roles WHERE reaction_id = ?",
                        (reaction_id,)
                    )
                    if not await cursor.fetchone():
                        break
            
            now = datetime.now().isoformat()
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT INTO reaction_roles 
                    (reaction_id, message_id, channel_id, emoji, role_id, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (reaction_id, str(message_id), str(channel_id), emoji, str(role_id), now))
                await db.commit()
                return reaction_id
        except Exception as e:
            logger.error(f"반응 역할 추가 실패: {e}")
            return ""
    
    async def remove_reaction_by_id(self, reaction_id: str) -> bool:
        """반응설정 ID로 매핑 제거"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    "DELETE FROM reaction_roles WHERE reaction_id = ?",
                    (reaction_id,)
                )
                await db.commit()
                return True
        except Exception as e:
            logger.error(f"반응 역할 제거 실패: {e}")
            return False
    
    async def get_all_reaction_roles(self) -> dict[str, dict]:
        """모든 반응설정 조회"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute("SELECT * FROM reaction_roles")
                rows = await cursor.fetchall()
                
                result = {}
                for row in rows:
                    result[row['reaction_id']] = {
                        'message_id': int(row['message_id']),
                        'channel_id': int(row['channel_id']),
                        'emoji': row['emoji'],
                        'role_id': int(row['role_id'])
                    }
                return result
        except Exception as e:
            logger.error(f"반응 역할 목록 조회 실패: {e}")
            return {}
    
    async def get_reaction_role_by_id(self, reaction_id: str) -> dict | None:
        """반응설정 ID로 조회"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute(
                    "SELECT * FROM reaction_roles WHERE reaction_id = ?",
                    (reaction_id,)
                )
                row = await cursor.fetchone()
                if row:
                    return {
                        'message_id': int(row['message_id']),
                        'channel_id': int(row['channel_id']),
                        'emoji': row['emoji'],
                        'role_id': int(row['role_id'])
                    }
                return None
        except Exception as e:
            logger.error(f"반응 역할 조회 실패: {e}")
            return None
    
    async def get_role_for_reaction(self, message_id: int, emoji: str) -> int | None:
        """이모지에 해당하는 역할 ID 조회"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    "SELECT role_id FROM reaction_roles WHERE message_id = ? AND emoji = ?",
                    (str(message_id), emoji)
                )
                row = await cursor.fetchone()
                return int(row[0]) if row else None
        except Exception as e:
            logger.error(f"역할 조회 실패: {e}")
            return None
    
    async def is_reaction_message(self, message_id: int) -> bool:
        """역할 인증 메시지인지 확인"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    "SELECT COUNT(*) FROM reaction_roles WHERE message_id = ?",
                    (str(message_id),)
                )
                row = await cursor.fetchone()
                return row[0] > 0 if row else False
        except Exception as e:
            logger.error(f"메시지 확인 실패: {e}")
            return False
