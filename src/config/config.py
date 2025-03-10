import os
from dotenv import load_dotenv
import json
from pathlib import Path

# Load environment variables
load_dotenv()

# Bot configuration
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
PREFIX = os.getenv('PREFIX', '!')  # Default prefix is ! if not set
DESCRIPTION = "A Discord bot to track your anime watchlist"
OWNER_IDS = [int(id.strip()) for id in os.getenv('OWNER_IDS', '').split(',') if id.strip()]

# Constants
VALID_STATUSES = ["Watching", "Completed", "To Watch", "On Hold", "Dropped"]
ITEMS_PER_PAGE = 10

# Response messages
ERRORS = {
    "NOT_FOUND": "Anime not found in your watchlist!",
    "ALREADY_EXISTS": "This anime is already in your watchlist!",
    "INVALID_STATUS": f"Invalid status! Must be one of: {', '.join(VALID_STATUSES)}",
    "MISSING_TITLE": "Please provide an anime title!",
    "MISSING_STATUS": "Please provide a status!",
    "PERMISSION_DENIED": "You don't have permission to use this command!",
}

SUCCESS = {
    "ADDED": "Anime added to your watchlist!",
    "DELETED": "Anime deleted from your watchlist!",
    "UPDATED": "Anime updated in your watchlist!",
}

async def update_prefix(new_prefix: str) -> None:
    """Update the bot's command prefix in the .env file
    
    Args:
        new_prefix: The new prefix to set
    """
    try:
        env_path = Path('.env')
        
        # Read current .env content
        if env_path.exists():
            with open(env_path, 'r') as f:
                lines = f.readlines()
        else:
            lines = []
        
        # Find and update PREFIX line, or add it if not found
        prefix_updated = False
        for i, line in enumerate(lines):
            if line.startswith('PREFIX='):
                lines[i] = f'PREFIX={new_prefix}\n'
                prefix_updated = True
                break
        
        if not prefix_updated:
            lines.append(f'PREFIX={new_prefix}\n')
        
        # Write back to .env
        with open(env_path, 'w') as f:
            f.writelines(lines)
        
        # Update the global PREFIX variable
        global PREFIX
        PREFIX = new_prefix
        
    except Exception as e:
        raise Exception(f"Failed to update prefix: {str(e)}") 