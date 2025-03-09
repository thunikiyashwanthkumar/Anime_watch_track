# Anime Watch Track Bot

A Discord bot for tracking your anime watchlist using the AniList API.

## Features

- Track anime you're watching, plan to watch, or have completed
- Search for anime using AniList's database
- Mark favorites and track progress
- View detailed information about anime
- Paginated lists with reactions for navigation
- Proper error handling and logging
- MongoDB integration for data persistence

## Requirements

- Python 3.8 or higher
- MongoDB database
- Discord Bot Token
- Dependencies listed in requirements.txt

## Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd anime-watch-track
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
# On Windows
venv\Scripts\activate
# On Unix or MacOS
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the root directory with the following content:
```env
# Database Configuration
DBSTR=your_mongodb_connection_string

# Discord Bot Token
DCBOT=your_discord_bot_token

# Bot Configuration
OWNER_IDS=your_discord_user_id  # Comma-separated for multiple owners

# Logging Configuration
LOG_LEVEL=INFO
```

5. Run the bot:
```bash
python src/bot.py
```

## Commands

- `!add_anime <title> <status> <preference>` - Add an anime to your watchlist
- `!delete_anime <title>` - Delete an anime from your watchlist
- `!update_status <title> <new_status>` - Update the watching status
- `!update_progress <title> <episodes>` - Update watched episodes
- `!toggle_favorite <title>` - Toggle favorite status
- `!search_anime <title>` - Search for anime information
- `!list_anime` - List all anime in your watchlist
- `!show_favorites` - Show your favorite anime
- `!random_anime [preference]` - Get a random anime suggestion
- `!anime_details <title>` - View detailed information about an anime

## Project Structure

```
anime-watch-track/
├── src/
│   ├── bot.py
│   └── cogs/
│       ├── base_cog.py
│       └── [feature_cogs].py
├── utils/
│   ├── database.py
│   ├── anilist.py
│   ├── embed_creator.py
│   └── logger.py
├── config/
│   └── config.py
├── logs/
│   └── bot.log
├── requirements.txt
├── .env
└── README.md
```

## Contributing

1. Fork the repository
2. Create a new branch for your feature
3. Commit your changes
4. Push to your branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [discord.py](https://github.com/Rapptz/discord.py)
- [AniList API](https://anilist.gitbook.io/anilist-apiv2-docs/)
- [MongoDB](https://www.mongodb.com/) 