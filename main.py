import asyncio
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get bot token from environment variables
TOKEN = os.getenv('DCBOT')
if not TOKEN:
    print("Error: Environment variable 'DCBOT' not found. Please check your .env file.")
    sys.exit(1)

# Add src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

# Import the bot from src
from bot import AnimeBot

def main():
    """Main entry point for the bot"""
    try:
        # Create and run bot instance
        bot = AnimeBot()
        asyncio.run(bot.start(TOKEN))
    except KeyboardInterrupt:
        print("\nBot shutdown requested...")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()