from discord.ext import commands
from utils.database import DatabaseManager
from utils.anilist import AniListAPI
from utils.embed_creator import EmbedCreator
from utils.logger import log_command, log_error
from typing import Optional, Any
import traceback

class BaseCog(commands.Cog):
    """Base cog class with common functionality"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = DatabaseManager()
        self.anilist = AniListAPI()
        self.embed_creator = EmbedCreator()
        
    async def cog_unload(self) -> None:
        """Clean up resources when cog is unloaded"""
        await self.anilist.close()
        self.db.close()
    
    async def cog_before_invoke(self, ctx: commands.Context) -> None:
        """Log command usage before execution"""
        log_command(
            ctx.command.name,
            ctx.author.id,
            ctx.guild.id if ctx.guild else 0
        )
    
    async def cog_after_invoke(self, ctx: commands.Context) -> None:
        """Handle any cleanup after command execution"""
        pass
    
    async def cog_command_error(self, ctx: commands.Context, error: Exception) -> None:
        """Handle command errors"""
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(
                embed=self.embed_creator.create_error_embed(
                    "Permission Error",
                    "You don't have permission to use this command."
                )
            )
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(
                embed=self.embed_creator.create_error_embed(
                    "Missing Argument",
                    f"Required argument missing: {error.param.name}"
                )
            )
        elif isinstance(error, commands.BadArgument):
            await ctx.send(
                embed=self.embed_creator.create_error_embed(
                    "Invalid Argument",
                    str(error)
                )
            )
        else:
            log_error(error, ctx.command.name if ctx.command else None)
            await ctx.send(
                embed=self.embed_creator.create_error_embed(
                    "Error",
                    "An unexpected error occurred. Please try again later."
                )
            )
            
    async def handle_api_response(
        self,
        ctx: commands.Context,
        title: str,
        success_message: Optional[str] = None
    ) -> Optional[Any]:
        """Handle AniList API response with error handling"""
        try:
            anime_data = await self.anilist.fetch_anime_details(title)
            if not anime_data:
                await ctx.send(
                    embed=self.embed_creator.create_error_embed(
                        "Not Found",
                        f"Could not find anime with title **{title}** on AniList."
                    )
                )
                return None
                
            if success_message:
                await ctx.send(
                    embed=self.embed_creator.create_success_embed(
                        "Success",
                        success_message
                    )
                )
            
            return self.anilist.format_anime_data(anime_data)
            
        except Exception as e:
            log_error(e)
            await ctx.send(
                embed=self.embed_creator.create_error_embed(
                    "API Error",
                    "An error occurred while fetching anime details."
                )
            )
            return None
            
    async def confirm_action(
        self,
        ctx: commands.Context,
        title: str,
        description: str,
        timeout: float = 30.0
    ) -> bool:
        """Get user confirmation for an action"""
        message = await ctx.send(
            embed=self.embed_creator.create_confirmation_embed(title, description)
        )
        
        await message.add_reaction("✅")
        await message.add_reaction("❌")
        
        def check(reaction, user):
            return (
                user == ctx.author
                and str(reaction.emoji) in ["✅", "❌"]
                and reaction.message.id == message.id
            )
        
        try:
            reaction, _ = await self.bot.wait_for(
                "reaction_add",
                timeout=timeout,
                check=check
            )
            return str(reaction.emoji) == "✅"
        except TimeoutError:
            await ctx.send(
                embed=self.embed_creator.create_error_embed(
                    "Timeout",
                    "Confirmation timed out."
                )
            )
            return False 