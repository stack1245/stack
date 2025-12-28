import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("DISCORD_TOKEN")
DATABASE_PATH = "stack_bot.db"
LOG_CHANNEL_ID = None  # 로그 채널 ID (런타임에 설정됨)
