import discord
from discord.ext import commands
import asyncio
import sys
import traceback
from pathlib import Path
import os
from dotenv import load_dotenv

# Add src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

# Load environment variables
load_dotenv()

from config.config import PREFIX, DESCRIPTION, DISCORD_TOKEN, OWNER_IDS
from utils.logger import logger, log_startup, log_shutdown

async def get_prefix(bot, message):
    """Get the command prefix for a message
    
    This function allows for:
    1. Using mentions as a prefix (e.g. @bot help)
    2. Using the configured prefix
    3. Owner can use ? as a prefix
    """
    # Get base prefixes
    prefixes = [PREFIX]
    
    # Add bot mention as a prefix
    prefixes.extend([f'<@!{bot.user.id}> ', f'<@{bot.user.id}> '])
    
    # Add ? prefix for bot owners
    if message.author.id in OWNER_IDS:
        prefixes.append('?')
    
    return prefixes

class AnimeBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        
        super().__init__(
            command_prefix=get_prefix,
            description=DESCRIPTION,
            intents=intents,
            case_insensitive=True
        )
        
    async def setup_hook(self) -> None:
        """Load extensions and perform any additional setup"""
        # Load all cogs
        await self.load_extensions()
        
    async def load_extensions(self) -> None:
        """Load all extensions from the cogs directory"""
        cogs_dir = Path(__file__).parent / "src" / "cogs"
        for file in cogs_dir.glob("*.py"):
            if file.name != "base_cog.py" and not file.name.startswith("_"):
                extension = f"src.cogs.{file.stem}"
                try:
                    await self.load_extension(extension)
                    logger.info(f"Loaded extension: {extension}")
                except Exception as e:
                    logger.error(f"Failed to load extension {extension}: {str(e)}")
                    traceback.print_exc()
    
    async def on_ready(self):
        """Called when the bot is ready"""
        log_startup()
        logger.info(f"Logged in as {self.user.name} (ID: {self.user.id})")
        logger.info(f"Connected to {len(self.guilds)} guilds")
        
        # Set custom status
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name=f"anime | {PREFIX}help"
        )
        await self.change_presence(activity=activity)
    
    async def on_command_error(self, ctx: commands.Context, error: Exception):
        """Global error handler for commands"""
        if isinstance(error, commands.CommandNotFound):
            return  # Ignore command not found errors
            
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(f"You don't have permission to use this command.")
            return
            
        if isinstance(error, commands.NoPrivateMessage):
            await ctx.send("This command cannot be used in private messages.")
            return
            
        # Log unexpected errors
        logger.error(f"Unexpected error in command {ctx.command}: {str(error)}")
        traceback.print_exception(type(error), error, error.__traceback__)
    
    async def close(self) -> None:
        """Clean up and close the bot"""
        log_shutdown()
        await super().close()

def main():
    """Main entry point for the bot"""
    try:
        bot = AnimeBot()
        asyncio.run(bot.start(DISCORD_TOKEN))
    except KeyboardInterrupt:
        print("\nBot shutdown requested...")
        logger.info("Bot stopped by keyboard interrupt")
    except Exception as e:
        print(f"Error: {str(e)}")
        logger.error(f"Fatal error: {str(e)}")
        traceback.print_exception(type(e), e, e.__traceback__)
        sys.exit(1)

if __name__ == "__main__":
    main()