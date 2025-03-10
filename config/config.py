import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bot Configuration
DCBOT = os.getenv('DCBOT')  # Bot Token
DBSTR = os.getenv('DBSTR')  # MongoDB Connection String
PREFIX = os.getenv('PREFIX', ',')  # Command Prefix, defaults to ',' if not set
DESCRIPTION = os.getenv('DESCRIPTION', 'An Anime Tracking Discord Bot')  # Bot description
OWNER_IDS = [int(id.strip()) for id in os.getenv('OWNER_IDS', '').split(',') if id.strip()]  # List of owner IDs

# Validate required environment variables
if not DCBOT:
    raise ValueError("Bot token (DCBOT) not found in environment variables")
if not DBSTR:
    raise ValueError("MongoDB connection string (DBSTR) not found in environment variables")
if not OWNER_IDS:
    raise ValueError("No owner IDs (OWNER_IDS) found in environment variables")

# Bot Settings
BOT_SETTINGS = {
    'command_prefix': PREFIX,
    'owner_ids': set(OWNER_IDS),
    'case_insensitive': True,
    'description': DESCRIPTION
}

# Database Settings
DB_SETTINGS = {
    'uri': DBSTR,
    'database': 'anime_watchlist',
    'collections': {
        'users': 'users',
        'anime_lists': 'anime_lists'
    }
}

# API Tokens
DISCORD_TOKEN = DCBOT
MONGODB_URI = DBSTR

# Database Configuration
DB_NAME = DB_SETTINGS['database']
COLLECTION_NAME = DB_SETTINGS['collections']['anime_lists']

# AniList API
ANILIST_API_URL = "https://graphql.anilist.co"

# Anime Status Configuration
VALID_STATUSES = ["Watching", "Completed", "To Watch"]

# Pagination Configuration
ITEMS_PER_PAGE = 5
PAGINATION_TIMEOUT = 60.0  # seconds

# Embed Configuration
EMBED_COLOR = 0x00ff00
EMBED_FOOTER = "Anime Watch Track Bot"

# Logging Configuration
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_FILE = 'logs/bot.log'
LOG_LEVEL = 'INFO'

# Error Messages
ERRORS = {
    "missing_args": "Missing arguments: **{args}**. Usage: `{usage}`",
    "invalid_status": "Invalid status: **{status}**. Valid statuses are: {valid_statuses}.",
    "not_found": "**{title}** not found in the watchlist.",
    "already_exists": "**{title}** already exists in the watchlist.",
    "api_error": "Could not find anime with title **{title}** on AniList.",
    "invalid_episodes": "Invalid episodes watched: **{episodes}**. Must be between 0 and {total}."
}

# Success Messages
SUCCESS = {
    "anime_added": "Added **{title}** to the watchlist!",
    "anime_deleted": "Deleted **{title}** from the watchlist!",
    "status_updated": "Updated **{title}** status to **{status}**!",
    "progress_updated": "Updated **{title}** progress to **{progress}/{total}** ({percentage:.2f}%)!",
    "favorite_toggled": "Toggled favorite status for **{title}** to **{status}**!"
} 