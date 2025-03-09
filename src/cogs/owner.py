from discord.ext import commands
from .base_cog import BaseCog
from config.config import OWNER_IDS
import discord
from typing import Optional
import sys
import os

class OwnerCog(BaseCog):
    """Owner-only commands for bot management"""

    async def cog_check(self, ctx: commands.Context) -> bool:
        """Check if the user is a bot owner"""
        return ctx.author.id in OWNER_IDS

    @commands.command(name="shutdown", help="Shutdown the bot (Owner only)")
    async def shutdown(self, ctx):
        """Safely shuts down the bot"""
        await ctx.send("⚠️ Shutting down bot...")
        await self.bot.close()

    @commands.command(name="reload", help="Reload a cog (Owner only)")
    async def reload(self, ctx, cog: str):
        """Reload a specific cog"""
        try:
            await self.bot.reload_extension(f"src.cogs.{cog}")
            await ctx.send(f"✅ Successfully reloaded `{cog}` cog!")
        except Exception as e:
            await ctx.send(f"❌ Error reloading `{cog}` cog: {str(e)}")

    @commands.command(name="load", help="Load a cog (Owner only)")
    async def load(self, ctx, cog: str):
        """Load a specific cog"""
        try:
            await self.bot.load_extension(f"src.cogs.{cog}")
            await ctx.send(f"✅ Successfully loaded `{cog}` cog!")
        except Exception as e:
            await ctx.send(f"❌ Error loading `{cog}` cog: {str(e)}")

    @commands.command(name="unload", help="Unload a cog (Owner only)")
    async def unload(self, ctx, cog: str):
        """Unload a specific cog"""
        try:
            await self.bot.unload_extension(f"src.cogs.{cog}")
            await ctx.send(f"✅ Successfully unloaded `{cog}` cog!")
        except Exception as e:
            await ctx.send(f"❌ Error unloading `{cog}` cog: {str(e)}")

    @commands.command(name="setstatus", help="Change bot status (Owner only)")
    async def setstatus(self, ctx, *, status: str):
        """Change the bot's status message"""
        try:
            await self.bot.change_presence(activity=discord.Game(name=status))
            await ctx.send(f"✅ Status changed to: **{status}**")
        except Exception as e:
            await ctx.send(f"❌ Error changing status: {str(e)}")

    @commands.command(name="broadcast", help="Send a message to all servers (Owner only)")
    async def broadcast(self, ctx, *, message: str):
        """Broadcast a message to all servers the bot is in"""
        try:
            for guild in self.bot.guilds:
                try:
                    # Try to find a suitable channel to send the message
                    channel = next((ch for ch in guild.text_channels if ch.permissions_for(guild.me).send_messages), None)
                    if channel:
                        embed = discord.Embed(
                            title="📢 Bot Announcement",
                            description=message,
                            color=discord.Color.blue()
                        )
                        embed.set_footer(text=f"From: {ctx.author}")
                        await channel.send(embed=embed)
                except Exception as e:
                    await ctx.send(f"❌ Failed to send to {guild.name}: {str(e)}")
            
            await ctx.send("✅ Broadcast complete!")
        except Exception as e:
            await ctx.send(f"❌ Error broadcasting message: {str(e)}")

    @commands.command(name="serverlist", help="List all servers (Owner only)")
    async def serverlist(self, ctx):
        """Show list of servers the bot is in"""
        embed = discord.Embed(
            title="🌐 Server List",
            color=discord.Color.blue()
        )
        
        for guild in self.bot.guilds:
            embed.add_field(
                name=guild.name,
                value=f"ID: {guild.id}\nMembers: {guild.member_count}\nOwner: {guild.owner}",
                inline=False
            )
        
        await ctx.send(embed=embed)

    @commands.command(name="leaveserver", help="Leave a server (Owner only)")
    async def leaveserver(self, ctx, guild_id: int):
        """Leave a specific server by ID"""
        guild = self.bot.get_guild(guild_id)
        if guild:
            await guild.leave()
            await ctx.send(f"✅ Left server: **{guild.name}**")
        else:
            await ctx.send("❌ Server not found!")

    @commands.command(name="maintenance", help="Toggle maintenance mode (Owner only)")
    async def maintenance(self, ctx, mode: bool = None):
        """Toggle or set maintenance mode"""
        current_mode = getattr(self.bot, "maintenance_mode", False)
        new_mode = not current_mode if mode is None else mode
        
        self.bot.maintenance_mode = new_mode
        status = discord.Status.dnd if new_mode else discord.Status.online
        
        await self.bot.change_presence(
            status=status,
            activity=discord.Game("🛠️ Maintenance" if new_mode else "Anime Watch Track")
        )
        
        await ctx.send(f"{'🛠️' if new_mode else '✅'} Maintenance mode: **{'ON' if new_mode else 'OFF'}**")

    @commands.command(name="stats", help="Show bot statistics (Owner only)")
    async def stats(self, ctx):
        """Show detailed bot statistics"""
        embed = discord.Embed(
            title="📊 Bot Statistics",
            color=discord.Color.blue()
        )
        
        # General stats
        total_users = sum(guild.member_count for guild in self.bot.guilds)
        embed.add_field(name="Servers", value=str(len(self.bot.guilds)), inline=True)
        embed.add_field(name="Users", value=str(total_users), inline=True)
        embed.add_field(name="Latency", value=f"{round(self.bot.latency * 1000)}ms", inline=True)
        
        # Database stats
        try:
            total_anime = len(await self.db.get_all_anime(None))  # Get all anime across all users
            embed.add_field(name="Total Anime Entries", value=str(total_anime), inline=True)
        except Exception:
            embed.add_field(name="Total Anime Entries", value="Error fetching", inline=True)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(OwnerCog(bot))
    return True 