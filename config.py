import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID", 815027847789936711))
ADMIN_ROLE_ID = int(os.getenv("ADMIN_ROLE_ID", 0))
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID", 0))
DB_PATH = "data/verificacoes.db"
WEB_HOST = os.getenv("WEB_HOST", "0.0.0.0")
WEB_PORT = int(os.getenv("WEB_PORT", 8000))
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")
