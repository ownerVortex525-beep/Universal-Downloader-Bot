import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bot Configuration
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHANNEL_ID = int(os.getenv('CHANNEL_ID', '0')) if os.getenv('CHANNEL_ID') else None
ADMIN_IDS = [int(x.strip()) for x in os.getenv('ADMIN_IDS', '').split(',') if x.strip()]

# Database
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///bot.db')

# File limits
MAX_FILE_SIZE_MB = int(os.getenv('MAX_FILE_SIZE', 50))
RATE_LIMIT = int(os.getenv('RATE_LIMIT', 10))

# Debug
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'