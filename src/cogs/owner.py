from discord.ext import commands
from .base_cog import BaseCog
from config.config import OWNER_IDS
import discord
from typing import Optional
import sys
import os
from pathlib import Path

class OwnerCog(BaseCog):
    """Owner-only commands for bot management"""

    async def cog_check(self, ctx: commands.Context) -> bool:
        """Check if the user is a bot owner"""
        return ctx.author.id in OWNER_IDS

    @commands.command(name="shutdown", aliases=["sd"], help="Shutdown the bot (Owner only)")
    async def shutdown(self, ctx):
        """Safely shuts down the bot"""
        await ctx.send("⚠️ Shutting down bot...")
        await self.bot.close()

    @commands.command(name="reload", aliases=["rl"], help="Reload a cog (Owner only)")
    async def reload(self, ctx, cog: str):
        """Reload a specific cog"""
        try:
            await self.bot.reload_extension(f"src.cogs.{cog}")
            await ctx.send(f"✅ Successfully reloaded `{cog}` cog!")
        except Exception as e:
            await ctx.send(f"❌ Error reloading `{cog}` cog: {str(e)}")

    @commands.command(name="load", aliases=["l"], help="Load a cog (Owner only)")
    async def load(self, ctx, cog: str):
        """Load a specific cog"""
        try:
            await self.bot.load_extension(f"src.cogs.{cog}")
            await ctx.send(f"✅ Successfully loaded `{cog}` cog!")
        except Exception as e:
            await ctx.send(f"❌ Error loading `{cog}` cog: {str(e)}")

    @commands.command(name="unload", aliases=["ul"], help="Unload a cog (Owner only)")
    async def unload(self, ctx, cog: str):
        """Unload a specific cog"""
        try:
            await self.bot.unload_extension(f"src.cogs.{cog}")
            await ctx.send(f"✅ Successfully unloaded `{cog}` cog!")
        except Exception as e:
            await ctx.send(f"❌ Error unloading `{cog}` cog: {str(e)}")

    @commands.command(name="setstatus", aliases=["ss"], help="Change bot status (Owner only)")
    async def setstatus(self, ctx, *, status: str):
        """Change the bot's status message"""
        try:
            await self.bot.change_presence(activity=discord.Game(name=status))
            await ctx.send(f"✅ Status changed to: **{status}**")
        except Exception as e:
            await ctx.send(f"❌ Error changing status: {str(e)}")

    @commands.command(name="broadcast", aliases=["dc"], help="Send a message to all servers (Owner only)")
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

    @commands.command(name="serverlist", aliases=["sl"], help="List all servers (Owner only)")
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

    @commands.command(name="leaveserver", aliases=["ls"], help="Leave a server (Owner only)")
    async def leaveserver(self, ctx, guild_id: int):
        """Leave a specific server by ID"""
        guild = self.bot.get_guild(guild_id)
        if guild:
            await guild.leave()
            await ctx.send(f"✅ Left server: **{guild.name}**")
        else:
            await ctx.send("❌ Server not found!")

    @commands.command(name="maintenance", aliases=["main"], help="Toggle maintenance mode (Owner only)")
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

    @commands.command(name="stats", aliases=["st"], help="Show bot statistics (Owner only)")
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

    @commands.command(name="setprefix", aliases=["p"], help="Change the bot's command prefix (Owner only)")
    async def setprefix(self, ctx, new_prefix: str):
        """Change the bot's command prefix
        
        Usage: {prefix}setprefix <new_prefix>
        Example: {prefix}setprefix !
        """
        try:
            # Update the prefix in the config first
            import os
            from pathlib import Path
            
            # Update the .env file
            env_path = Path(__file__).parent.parent.parent / '.env'
            
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
            
            # Update the prefix in memory
            import sys
            sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            global PREFIX
            from src.config.config import PREFIX
            PREFIX = new_prefix
            
            # Create a new prefix getter function
            async def new_prefix_getter(bot, message):
                prefixes = [new_prefix]
                prefixes.extend([f'<@!{bot.user.id}> ', f'<@{bot.user.id}> '])
                if message.author.id in OWNER_IDS:
                    prefixes.append('?')
                return prefixes
            
            # Update the bot's command prefix
            self.bot.command_prefix = new_prefix_getter
            
            # Update bot's status to show new prefix
            await self.bot.change_presence(
                activity=discord.Game(name=f"AniTrack | {new_prefix}help")
            )
            
            # Force update help command
            self.bot.help_command.context = ctx
            
            await ctx.send(f"✅ Command prefix updated to: `{new_prefix}`")
            
        except Exception as e:
            await ctx.send(f"❌ Error changing prefix: {str(e)}")
            raise e  # Re-raise to see the full error in logs

    @commands.command(name="servermute", aliases=["sm"], help="Mute a user across all servers (Owner only)")
    async def servermute(self, ctx, user_id: int, *, reason: str = "No reason provided"):
        """Mute a user in all mutual servers"""
        try:
            user = await self.bot.fetch_user(user_id)
            if not user:
                await ctx.send("❌ User not found!")
                return

            success_count = 0
            fail_count = 0
            
            for guild in self.bot.guilds:
                try:
                    member = await guild.fetch_member(user_id)
                    if member:
                        # Find or create muted role
                        muted_role = discord.utils.get(guild.roles, name="Muted")
                        if not muted_role:
                            # Create muted role with no permissions
                            permissions = discord.Permissions()
                            permissions.update(send_messages=False, speak=False)
                            muted_role = await guild.create_role(name="Muted", permissions=permissions)
                            
                            # Update channel permissions for muted role
                            for channel in guild.channels:
                                await channel.set_permissions(muted_role, send_messages=False, speak=False)
                        
                        await member.add_roles(muted_role, reason=reason)
                        success_count += 1
                except Exception as e:
                    fail_count += 1
                    continue

            embed = discord.Embed(
                title="🔇 Server Mute Results",
                color=discord.Color.orange()
            )
            embed.add_field(name="User", value=f"{user} (ID: {user.id})", inline=False)
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Success", value=f"Muted in {success_count} servers", inline=True)
            embed.add_field(name="Failed", value=f"Failed in {fail_count} servers", inline=True)
            
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ Error: {str(e)}")

    @commands.command(name="serverunmute", aliases=["sum"], help="Unmute a user across all servers (Owner only)")
    async def serverunmute(self, ctx, user_id: int, *, reason: str = "No reason provided"):
        """Unmute a user in all mutual servers"""
        try:
            user = await self.bot.fetch_user(user_id)
            if not user:
                await ctx.send("❌ User not found!")
                return

            success_count = 0
            fail_count = 0
            
            for guild in self.bot.guilds:
                try:
                    member = await guild.fetch_member(user_id)
                    if member:
                        muted_role = discord.utils.get(guild.roles, name="Muted")
                        if muted_role and muted_role in member.roles:
                            await member.remove_roles(muted_role, reason=reason)
                            success_count += 1
                except Exception as e:
                    fail_count += 1
                    continue

            embed = discord.Embed(
                title="🔊 Server Unmute Results",
                color=discord.Color.green()
            )
            embed.add_field(name="User", value=f"{user} (ID: {user.id})", inline=False)
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Success", value=f"Unmuted in {success_count} servers", inline=True)
            embed.add_field(name="Failed", value=f"Failed in {fail_count} servers", inline=True)
            
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ Error: {str(e)}")

    @commands.command(name="serverban", aliases=["sb"], help="Ban a user from all servers (Owner only)")
    async def serverban(self, ctx, user_id: int, *, reason: str = "No reason provided"):
        """Ban a user from all mutual servers"""
        try:
            user = await self.bot.fetch_user(user_id)
            if not user:
                await ctx.send("❌ User not found!")
                return

            success_count = 0
            fail_count = 0
            
            for guild in self.bot.guilds:
                try:
                    member = await guild.fetch_member(user_id)
                    if member:
                        await guild.ban(user, reason=reason)
                        success_count += 1
                except Exception as e:
                    fail_count += 1
                    continue

            embed = discord.Embed(
                title="🔨 Server Ban Results",
                color=discord.Color.red()
            )
            embed.add_field(name="User", value=f"{user} (ID: {user.id})", inline=False)
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Success", value=f"Banned in {success_count} servers", inline=True)
            embed.add_field(name="Failed", value=f"Failed in {fail_count} servers", inline=True)
            
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ Error: {str(e)}")

    @commands.command(name="serverunban", aliases=["sub"], help="Unban a user from all servers (Owner only)")
    async def serverunban(self, ctx, user_id: int, *, reason: str = "No reason provided"):
        """Unban a user from all mutual servers"""
        try:
            user = await self.bot.fetch_user(user_id)
            if not user:
                await ctx.send("❌ User not found!")
                return

            success_count = 0
            fail_count = 0
            
            for guild in self.bot.guilds:
                try:
                    bans = [ban.user.id async for ban in guild.bans()]
                    if user_id in bans:
                        await guild.unban(user, reason=reason)
                        success_count += 1
                except Exception as e:
                    fail_count += 1
                    continue

            embed = discord.Embed(
                title="🔓 Server Unban Results",
                color=discord.Color.green()
            )
            embed.add_field(name="User", value=f"{user} (ID: {user.id})", inline=False)
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Success", value=f"Unbanned in {success_count} servers", inline=True)
            embed.add_field(name="Failed", value=f"Failed in {fail_count} servers", inline=True)
            
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ Error: {str(e)}")

    @commands.command(name="guildinvites", aliases=["gl"], help="List invite links for all servers (Owner only)")
    async def guildinvites(self, ctx):
        """Generate and list invite links for all servers"""
        embed = discord.Embed(
            title="🔗 Server Invite Links",
            description="Generating invite links for all servers...",
            color=discord.Color.blue()
        )
        message = await ctx.send(embed=embed)
        
        results = []
        for guild in self.bot.guilds:
            try:
                # Try to get the system channel or first text channel
                invite_channel = guild.system_channel or next(
                    (channel for channel in guild.text_channels 
                     if channel.permissions_for(guild.me).create_instant_invite),
                    None
                )
                
                if invite_channel:
                    # Create an invite that never expires
                    invite = await invite_channel.create_invite(
                        reason=f"Invite requested by {ctx.author}",
                        max_age=0
                    )
                    results.append({
                        "name": guild.name,
                        "success": True,
                        "invite": invite.url,
                        "members": guild.member_count
                    })
                else:
                    results.append({
                        "name": guild.name,
                        "success": False,
                        "error": "No suitable channel found"
                    })
            except Exception as e:
                results.append({
                    "name": guild.name,
                    "success": False,
                    "error": str(e)
                })
        
        # Create new embed with results
        embed = discord.Embed(
            title="🔗 Server Invite Links",
            color=discord.Color.blue()
        )
        
        for result in results:
            if result["success"]:
                value = f"Members: {result['members']}\nInvite: {result['invite']}"
            else:
                value = f"Error: {result['error']}"
            
            embed.add_field(
                name=result["name"],
                value=value,
                inline=False
            )
        
        embed.set_footer(text=f"Total Servers: {len(self.bot.guilds)}")
        await message.edit(embed=embed)

    @commands.command(name="importlist", aliases=["iml"], help="Import anime list for a user (Owner only)")
    async def importlist(self, ctx, user_id: int):
        """Import anime watchlist for a specific user"""
        try:
            user = await self.bot.fetch_user(user_id)
            if not user:
                await ctx.send("❌ User not found!")
                return

            # Watchlist data
            watchlist_data = {
                "Watching": [
                    {"title": "Attack on Titan Season 3", "status": "Watching", "episodes_watched": 0, "total_episodes": 12, "source_link": "https://myanimelist.net/anime/35760", "is_favorite": False},
                    {"title": "Attack on Titan Season 2", "status": "Watching", "episodes_watched": 0, "total_episodes": 12, "source_link": "https://myanimelist.net/anime/25777", "is_favorite": False},
                    {"title": "Demon Slayer: Kimetsu no Yaiba", "status": "Watching", "episodes_watched": 0, "total_episodes": 26, "source_link": "https://myanimelist.net/anime/38000", "is_favorite": False},
                    {"title": "One Piece", "status": "Watching", "episodes_watched": 0, "total_episodes": 0, "source_link": "https://myanimelist.net/anime/21", "is_favorite": False}
                ],
                "Plan to Watch": [
                    {"title": "Naruto", "status": "Plan to Watch", "episodes_watched": 0, "total_episodes": 220, "source_link": "https://myanimelist.net/anime/20", "is_favorite": False},
                    {"title": "Pokémon", "status": "Plan to Watch", "episodes_watched": 0, "total_episodes": 0, "source_link": "https://myanimelist.net/anime/527", "is_favorite": False},
                    {"title": "Pokémon Evolutions", "status": "Plan to Watch", "episodes_watched": 0, "total_episodes": 8, "source_link": "https://myanimelist.net/anime/49730", "is_favorite": False}
                ]
            }

            success_count = 0
            error_count = 0
            
            # Process Watching anime
            for anime in watchlist_data["Watching"]:
                try:
                    await self.db.add_anime(
                        user_id=user_id,
                        title=anime["title"],
                        status=anime["status"],
                        episodes_watched=anime["episodes_watched"],
                        total_episodes=anime["total_episodes"],
                        source_link=anime["source_link"],
                        is_favorite=anime["is_favorite"]
                    )
                    success_count += 1
                except Exception as e:
                    error_count += 1
                    print(f"Error adding {anime['title']}: {str(e)}")

            # Process Plan to Watch anime
            for anime in watchlist_data["Plan to Watch"]:
                try:
                    await self.db.add_anime(
                        user_id=user_id,
                        title=anime["title"],
                        status="To Watch",  # Convert "Plan to Watch" to "To Watch"
                        episodes_watched=anime["episodes_watched"],
                        total_episodes=anime["total_episodes"],
                        source_link=anime["source_link"],
                        is_favorite=anime["is_favorite"]
                    )
                    success_count += 1
                except Exception as e:
                    error_count += 1
                    print(f"Error adding {anime['title']}: {str(e)}")

            embed = discord.Embed(
                title="📥 Watchlist Import Results",
                color=discord.Color.green()
            )
            embed.add_field(name="User", value=f"{user} (ID: {user.id})", inline=False)
            embed.add_field(name="Successfully Added", value=str(success_count), inline=True)
            embed.add_field(name="Failed to Add", value=str(error_count), inline=True)
            embed.add_field(name="Total Anime", value=str(success_count + error_count), inline=True)
            
            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"❌ Error importing watchlist: {str(e)}")

async def setup(bot):
    await bot.add_cog(OwnerCog(bot))
    return True 