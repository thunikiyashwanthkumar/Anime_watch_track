import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bot Configuration
PREFIX = ","
DESCRIPTION = "An Anime Tracking Discord Bot"
OWNER_IDS = [int(id.strip()) for id in os.getenv('OWNER_IDS', '').split(',') if id.strip()]

# API Tokens
DISCORD_TOKEN = os.getenv('DCBOT')
MONGODB_URI = os.getenv('DBSTR')

# Database Configuration
DB_NAME = "anime_watchlist"
COLLECTION_NAME = "anime"

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