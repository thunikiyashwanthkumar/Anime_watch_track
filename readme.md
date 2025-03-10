# AniTrack Discord Bot

A powerful Discord bot for tracking your anime watchlist using the AniList API. Keep track of your favorite anime, manage your watchlist, and share your progress with your server members.

## 🌟 Features

### Anime Management
- Track anime with different statuses (Watching, Completed, Plan to Watch)
- Update watching progress and episode counts
- Mark favorites and manage your personal anime list
- Search anime using AniList's extensive database
- Get detailed information about any anime
- Import anime lists (owner-only feature)

### User Interface
- Modern embed-based responses
- Reaction-based navigation for lists
- Intuitive command structure
- Customizable command prefix
- Detailed help menus for all commands

### Administrative Features
- Server management commands for bot owners
- Maintenance mode for updates
- Cross-server moderation capabilities
- Detailed bot statistics
- Server invite management
- Broadcast announcements to all servers

### Technical Features
- MongoDB integration for reliable data persistence
- Proper error handling and logging
- Asynchronous command processing
- Modular cog-based structure
- Environment-based configuration

## 📋 Requirements

- Python 3.8 or higher
- MongoDB database
- Discord Bot Token
- Dependencies from requirements.txt

## 🚀 Quick Start

1. **Clone the repository:**
```bash
git clone <repository-url>
cd anime-watch-track
```

2. **Set up Python environment:**
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Unix/MacOS
source venv/bin/activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Configure the bot:**
Create a `.env` file in the root directory:
```env
# Required Settings
DCBOT=your_discord_bot_token
DBSTR=your_mongodb_connection_string
OWNER_IDS=your_discord_user_id  # Comma-separated for multiple owners
PREFIX=!  # Default command prefix

# Optional Settings
LOG_LEVEL=INFO
MAINTENANCE_MODE=false
```

5. **Start the bot:**
```bash
python src/bot.py
```

## 🎯 Commands

### Anime Commands
- `.add_anime <title>` - Add an anime to your watchlist
- `.delete_anime <title>` - Remove an anime from your watchlist
- `.list_anime` - View your anime list
- `.update_status <title> <status>` - Update watching status
- `.update_progress <title> <episodes>` - Update episode progress
- `.toggle_favorite <title>` - Toggle favorite status
- `.search_anime <title>` - Search for anime
- `.status <title>` - Show detailed anime status

### Owner Commands
- `.setprefix <prefix>` - Change command prefix
- `.maintenance` - Toggle maintenance mode
- `.broadcast <message>` - Send announcement to all servers
- `.stats` - View bot statistics
- `.serverlist` - List all servers
- `.importlist <user_id>` - Import anime list for a user
- `.shutdown` - Safely shut down the bot

### Moderation Commands
- `.servermute <user_id>` - Mute user across all servers
- `.serverban <user_id>` - Ban user from all servers
- `.serverunmute <user_id>` - Unmute user across all servers
- `.serverunban <user_id>` - Unban user from all servers

## 📁 Project Structure

```
anime-watch-track/
├── src/
│   ├── bot.py              # Main bot file
│   ├── cogs/
│   │   ├── base_cog.py    # Base cog class
│   │   ├── owner.py       # Owner commands
│   │   ├── anime.py       # Anime commands
│   │   └── moderation.py  # Moderation commands
│   └── utils/
│       ├── database.py    # MongoDB interactions
│       ├── anilist.py     # AniList API wrapper
│       └── logger.py      # Logging configuration
├── config/
│   └── config.py          # Configuration management
├── logs/
│   └── bot.log           # Log files
├── requirements.txt      # Python dependencies
├── .env                 # Environment variables
└── README.md           # Documentation
```

## 🔧 Configuration

### Environment Variables
- `DCBOT`: Discord bot token
- `DBSTR`: MongoDB connection string
- `OWNER_IDS`: Bot owner Discord IDs
- `PREFIX`: Default command prefix
- `LOG_LEVEL`: Logging level (DEBUG/INFO/WARNING/ERROR)
- `MAINTENANCE_MODE`: Maintenance mode state

### Database Setup
1. Create a MongoDB database
2. Add connection string to `.env`
3. Collections will be created automatically

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [discord.py](https://github.com/Rapptz/discord.py) - Discord API wrapper
- [AniList API](https://anilist.gitbook.io/anilist-apiv2-docs/) - Anime database API
- [MongoDB](https://www.mongodb.com/) - Database system
- [motor](https://motor.readthedocs.io/) - Async MongoDB driver

## 📫 Support

If you encounter any issues or have questions, please:
1. Check the existing issues
2. Create a new issue with detailed information
3. Join our support server [Coming Soon]

## 🤖 Invite the Bot

You can add AniTrack to your Discord server using the following link:

```
https://discord.com/api/oauth2/authorize?client_id=YOUR_BOT_CLIENT_ID&permissions=1374389534790&scope=bot
```
### Required Permissions
The bot needs the following permissions to function properly:
- Manage Roles (for moderation features)
- Manage Messages (for message cleanup)
- Send Messages & Embeds (for responses)
- Add Reactions (for navigation)
- Read Message History (for context)
- View Channels (for basic functionality)
- Attach Files (for exporting lists)
- Use External Emojis (for better UI) 