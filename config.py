import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("DISCORD_BOT")
DATABASE_PATH = "user_profiles.db"
