import aiosqlite
from datetime import datetime
from typing import Optional, Dict, Any


class Database:
    def __init__(self, db_path: str = "data.db"):
        self.db_path = db_path
    
    async def init_db(self):
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
            
            await db.commit()
    
    async def register_profile(self, user_id: str, username: str, display_name: str, 
                               birth_year: str, gender: str, region: str) -> bool:
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
            print(f"[DB 오류] 프로필 등록: {e}")
            return False
    
    async def get_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute(
                    "SELECT * FROM user_profiles WHERE user_id = ?", (user_id,)
                )
                row = await cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            print(f"[DB 오류] 프로필 조회: {e}")
            return None
    
    async def get_admin_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute(
                    "SELECT * FROM admin_info WHERE user_id = ?", (user_id,)
                )
                row = await cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            print(f"[DB 오류] 관리자 정보 조회: {e}")
            return None
    
    async def add_warning(self, user_id: str, count: int = 1) -> bool:
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
            print(f"[DB 오류] 경고 추가: {e}")
            return False
    
    async def remove_warning(self, user_id: str, count: int = 1) -> bool:
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
            print(f"[DB 오류] 경고 제거: {e}")
            return False
    
    async def set_admin_memo(self, user_id: str, memo: str) -> bool:
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
            print(f"[DB 오류] 메모 작성: {e}")
            return False
    
    async def set_log_channel(self, guild_id: str, channel_id: str) -> bool:
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
            print(f"[DB 오류] 로그 채널 설정: {e}")
            return False
    
    async def get_log_channel(self, guild_id: str) -> Optional[str]:
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    "SELECT log_channel_id FROM server_settings WHERE guild_id = ?", (guild_id,)
                )
                row = await cursor.fetchone()
                return row[0] if row else None
        except Exception as e:
            print(f"[DB 오류] 로그 채널 조회: {e}")
            return None
    
    async def get_all_profiles(self) -> list[Dict[str, Any]]:
        """등록된 모든 프로필 조회"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute(
                    "SELECT * FROM user_profiles ORDER BY display_name ASC"
                )
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            print(f"[DB 오류] 전체 프로필 조회: {e}")
            return []
