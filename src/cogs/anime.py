from discord.ext import commands
from .base_cog import BaseCog
from datetime import datetime
from config.config import VALID_STATUSES, ITEMS_PER_PAGE, ERRORS, SUCCESS, PREFIX
from discord import SelectOption, Interaction, ButtonStyle, TextStyle
from discord.ui import Select, View, Button, TextInput, Modal
import discord

class EpisodeModal(Modal):
    def __init__(self, title, current, total):
        super().__init__(title=f"Update Episodes - {title}")
        self.episodes = TextInput(
            label=f"Episodes watched (Current: {current}/{total})",
            placeholder=f"Enter a number between 0 and {total}",
            default=str(current),
            required=True,
            min_length=1,
            max_length=4
        )
        self.add_item(self.episodes)

class AnimeControlPanel(View):
    def __init__(self, cog, anime_data, watchlist_data, user_id):
        super().__init__(timeout=180)  # 3 minutes timeout
        self.cog = cog
        self.anime_data = anime_data
        self.watchlist_data = watchlist_data
        self.user_id = user_id
        
        # Status row
        self.add_item(Button(
            label="Watching",
            style=ButtonStyle.primary if watchlist_data["status"] == "Watching" else ButtonStyle.secondary,
            emoji="👀",
            custom_id="status_watching"
        ))
        self.add_item(Button(
            label="Completed",
            style=ButtonStyle.primary if watchlist_data["status"] == "Completed" else ButtonStyle.secondary,
            emoji="✅",
            custom_id="status_completed"
        ))
        self.add_item(Button(
            label="To Watch",
            style=ButtonStyle.primary if watchlist_data["status"] == "To Watch" else ButtonStyle.secondary,
            emoji="📝",
            custom_id="status_towatch"
        ))
        
        # Action row
        self.add_item(Button(
            label="Update Episodes",
            style=ButtonStyle.primary,
            emoji="🎬",
            custom_id="update_episodes"
        ))
        self.add_item(Button(
            label="Toggle Favorite",
            style=ButtonStyle.danger if watchlist_data.get("is_favorite") else ButtonStyle.secondary,
            emoji="⭐",
            custom_id="toggle_favorite"
        ))
        
        # Info row
        self.add_item(Button(
            label="View Details",
            style=ButtonStyle.secondary,
            emoji="ℹ️",
            custom_id="view_details"
        ))
        self.add_item(Button(
            label="Delete",
            style=ButtonStyle.danger,
            emoji="🗑️",
            custom_id="delete",
            disabled=watchlist_data.get("is_favorite", False)
        ))
        
        # Reload button
        self.add_item(Button(
            label="Reload",
            style=ButtonStyle.success,
            emoji="🔄",
            custom_id="reload"
        ))
        
        # Add button callbacks
        for child in self.children:
            if isinstance(child, Button):
                child.callback = self.button_callback

    async def button_callback(self, interaction: Interaction):
        custom_id = interaction.data["custom_id"]
        title = self.anime_data["title"]
        
        if custom_id == "reload":
            # Fetch fresh data from both API and database
            anime_data = await self.cog.handle_api_response(interaction, title)
            if not anime_data:
                return
            
            watchlist_data = await self.cog.db.get_anime(self.user_id, title)
            if not watchlist_data:
                await interaction.response.send_message(
                    f"**{title}** was not found in your watchlist!",
                    ephemeral=True
                )
                return
            
            # Update stored data
            self.anime_data = anime_data
            self.watchlist_data = watchlist_data
            
            # Update embed and view
            embed = self.cog.embed_creator.create_status_embed(anime_data, watchlist_data)
            await interaction.response.edit_message(embed=embed, view=self)
            return
        
        elif custom_id.startswith("status_"):
            status = custom_id.split("_")[1].title()
            update_data = {"status": status}
            
            if status == "Watching" and not self.watchlist_data.get("start_date"):
                update_data["start_date"] = datetime.now().strftime('%Y-%m-%d')
            elif status == "Completed":
                update_data["completion_date"] = datetime.now().strftime('%Y-%m-%d')
            
            await self.cog.db.update_anime(self.user_id, title, update_data)
            await interaction.response.send_message(
                f"Updated status of **{title}** to **{status}**",
                ephemeral=True
            )
        
        elif custom_id == "update_episodes":
            modal = EpisodeModal(
                title,
                self.watchlist_data.get('episodes_watched', 0),
                self.anime_data.get('episodes', '?')
            )
            
            async def modal_callback(interaction: Interaction):
                try:
                    episodes = int(modal.episodes.value)
                    if 0 <= episodes <= self.anime_data['episodes']:
                        await self.cog.db.update_anime(self.user_id, title, {"episodes_watched": episodes})
                        
                        # Update status if needed
                        if episodes == self.anime_data['episodes']:
                            await self.cog.db.update_anime(self.user_id, title, {
                                "status": "Completed",
                                "completion_date": datetime.now().strftime('%Y-%m-%d')
                            })
                        elif episodes > 0 and self.watchlist_data['status'] == "To Watch":
                            await self.cog.db.update_anime(self.user_id, title, {
                                "status": "Watching",
                                "start_date": datetime.now().strftime('%Y-%m-%d')
                            })
                        
                        await interaction.response.send_message(
                            f"Updated progress of **{title}** to **{episodes}/{self.anime_data['episodes']}** episodes",
                            ephemeral=True
                        )
                    else:
                        await interaction.response.send_message(
                            f"Invalid episode number! Must be between 0 and {self.anime_data['episodes']}",
                            ephemeral=True
                        )
                except ValueError:
                    await interaction.response.send_message(
                        "Please enter a valid number!",
                        ephemeral=True
                    )
            
            modal.callback = modal_callback
            await interaction.response.send_modal(modal)
            return
        
        elif custom_id == "toggle_favorite":
            new_status = not self.watchlist_data.get("is_favorite", False)
            await self.cog.db.update_anime(self.user_id, title, {"is_favorite": new_status})
            await interaction.response.send_message(
                f"**{title}** is {'now' if new_status else 'no longer'} marked as favorite!",
                ephemeral=True
            )
        
        elif custom_id == "view_details":
            embed = self.cog.embed_creator.create_anime_details_embed(
                self.anime_data,
                self.watchlist_data
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        
        elif custom_id == "delete":
            if self.watchlist_data.get("is_favorite"):
                await interaction.response.send_message(
                    f"Cannot delete **{title}** because it's marked as favorite!",
                    ephemeral=True
                )
                return
            
            # Create confirmation view
            confirm_view = View(timeout=30)
            
            async def confirm_callback(i: Interaction):
                await self.cog.db.delete_anime(self.user_id, title)
                await i.response.send_message(
                    f"Deleted **{title}** from your watchlist!",
                    ephemeral=True
                )
            
            async def cancel_callback(i: Interaction):
                await i.response.send_message(
                    f"Cancelled deletion of **{title}**",
                    ephemeral=True
                )
            
            confirm_button = Button(label="Confirm Delete", style=ButtonStyle.danger, emoji="✅")
            cancel_button = Button(label="Cancel", style=ButtonStyle.secondary, emoji="❌")
            
            confirm_button.callback = confirm_callback
            cancel_button.callback = cancel_callback
            
            confirm_view.add_item(confirm_button)
            confirm_view.add_item(cancel_button)
            
            await interaction.response.send_message(
                f"Are you sure you want to delete **{title}**?",
                view=confirm_view,
                ephemeral=True
            )
        
        # Update the watchlist data and refresh buttons
        self.watchlist_data = await self.cog.db.get_anime(self.user_id, title)
        for child in self.children:
            if isinstance(child, Button):
                if child.custom_id.startswith("status_"):
                    status = child.custom_id.split("_")[1].title()
                    child.style = ButtonStyle.primary if self.watchlist_data["status"] == status else ButtonStyle.secondary
                elif child.custom_id == "toggle_favorite":
                    child.style = ButtonStyle.danger if self.watchlist_data.get("is_favorite") else ButtonStyle.secondary
                elif child.custom_id == "delete":
                    child.disabled = self.watchlist_data.get("is_favorite", False)
        
        try:
            await interaction.message.edit(view=self)
        except:
            pass

class AnimeSelect(Select):
    def __init__(self, anime_list):
        options = []
        for idx, anime in enumerate(anime_list):
            # Create a unique value by combining title with index
            unique_value = f"{anime['title']}|{idx}"
            options.append(
                SelectOption(
                    label=anime["title"][:100],  # Discord has 100 char limit for labels
                    description=f"{anime['status']} - {anime.get('episodes_watched', 0)}/{anime.get('total_episodes', '?')} eps",
                    value=unique_value,
                    emoji="⭐" if anime.get("is_favorite") else "📺"
                )
            )
        
        super().__init__(
            placeholder="Select an anime to manage...",
            min_values=1,
            max_values=1,
            options=options
        )

class AnimeView(View):
    def __init__(self, cog, anime_list, user_id):
        super().__init__(timeout=60)
        self.cog = cog
        self.anime_list = anime_list
        self.user_id = user_id
        
        # Add select menu
        self.select = AnimeSelect(anime_list)
        self.select.callback = self.select_callback
        self.add_item(self.select)

    async def select_callback(self, interaction: Interaction):
        # Extract title from the unique value
        anime_title = self.select.values[0].split("|")[0]
        anime = next((a for a in self.anime_list if a["title"] == anime_title), None)
        
        if anime:
            # Get fresh data
            anime_data = await self.cog.handle_api_response(interaction, anime_title)
            if not anime_data:
                return
            
            # Create and show control panel
            control_panel = AnimeControlPanel(self.cog, anime_data, anime, self.user_id)
            embed = self.cog.embed_creator.create_status_embed(anime_data, anime)
            
            await interaction.response.send_message(
                embed=embed,
                view=control_panel,
                ephemeral=True
            )

class AddAnimeView(View):
    def __init__(self, cog, anime_data, user_id):
        super().__init__(timeout=180)  # 3 minutes timeout
        self.cog = cog
        self.anime_data = anime_data
        self.user_id = user_id
        self.status = None
        self.rating = None
        self.start_date = datetime.now().strftime('%Y-%m-%d')  # Set default date to today
        self.is_favorite = False
        self.completion_date = None
        
        # Status dropdown with emojis
        self.status_select = Select(
            placeholder="Select status...",
            options=[
                SelectOption(label="Watching", emoji="👀", value="Watching", description="Currently watching this anime"),
                SelectOption(label="Completed", emoji="✅", value="Completed", description="Finished watching this anime"),
                SelectOption(label="To Watch", emoji="📝", value="To Watch", description="Plan to watch this anime"),
                SelectOption(label="On Hold", emoji="⏸️", value="On Hold", description="Temporarily paused watching"),
                SelectOption(label="Dropped", emoji="⛔", value="Dropped", description="Stopped watching")
            ],
            custom_id="status_select"
        )
        
        # Rating dropdown
        self.rating_select = Select(
            placeholder="Rate this anime...",
            options=[
                SelectOption(label="★★★★★", value="5", description="Masterpiece"),
                SelectOption(label="★★★★☆", value="4", description="Great"),
                SelectOption(label="★★★☆☆", value="3", description="Good"),
                SelectOption(label="★★☆☆☆", value="2", description="Fair"),
                SelectOption(label="★☆☆☆☆", value="1", description="Poor")
            ],
            custom_id="rating_select"
        )
        
        # Add components
        self.add_item(self.status_select)
        self.add_item(self.rating_select)
        self.add_item(Button(
            label="Set Start Date",
            style=ButtonStyle.secondary,
            emoji="📅",
            custom_id="set_date"
        ))
        self.add_item(Button(
            label="Mark as Favorite",
            style=ButtonStyle.secondary,
            emoji="⭐",
            custom_id="toggle_favorite"
        ))
        self.add_item(Button(
            label="Confirm Add",
            style=ButtonStyle.success,
            emoji="✅",
            custom_id="confirm",
            disabled=True,
            row=4
        ))
        self.add_item(Button(
            label="Cancel",
            style=ButtonStyle.danger,
            emoji="❌",
            custom_id="cancel",
            row=4
        ))
        
        # Add callbacks
        self.status_select.callback = self.status_callback
        self.rating_select.callback = self.rating_callback
        for child in self.children:
            if isinstance(child, Button):
                child.callback = self.button_callback

    def update_confirm_button(self):
        # Enable confirm button if status is set
        for child in self.children:
            if isinstance(child, Button) and child.custom_id == "confirm":
                child.disabled = not self.status

    async def status_callback(self, interaction: Interaction):
        try:
            # Get the selected status
            self.status = interaction.data["values"][0]
            
            # Update dates based on status
            if self.status == "Completed":
                self.completion_date = datetime.now().strftime('%Y-%m-%d')
            elif self.status == "Watching":
                self.start_date = datetime.now().strftime('%Y-%m-%d')
            
            # Enable confirm button if status is set
            self.update_confirm_button()
            
            # Get status emoji
            status_emojis = {
                "Watching": "👀",
                "Completed": "✅",
                "To Watch": "📝",
                "On Hold": "⏸️",
                "Dropped": "⛔"
            }
            emoji = status_emojis.get(self.status, "")
            
            # Send feedback message
            await interaction.response.send_message(
                f"{emoji} Status set to **{self.status}**",
                ephemeral=True
            )
            
            # Update view
            await interaction.message.edit(view=self)
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error setting status: {str(e)}",
                ephemeral=True
            )

    async def rating_callback(self, interaction: Interaction):
        try:
            # Get the selected rating
            self.rating = interaction.data["values"][0]
            stars = "★" * int(self.rating) + "☆" * (5 - int(self.rating))
            
            # Get rating description
            rating_descriptions = {
                "5": "Masterpiece",
                "4": "Great",
                "3": "Good",
                "2": "Fair",
                "1": "Poor"
            }
            description = rating_descriptions.get(self.rating, "")
            
            # Send feedback message
            await interaction.response.send_message(
                f"⭐ Rating set to **{stars}** - {description}",
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error setting rating: {str(e)}",
                ephemeral=True
            )

    async def button_callback(self, interaction: Interaction):
        custom_id = interaction.data["custom_id"]
        
        if custom_id == "set_date":
            # Create date modal
            modal = Modal(title="Set Start Date")
            date_input = TextInput(
                label="Start Date (YYYY-MM-DD)",
                placeholder="e.g., 2024-03-15",
                default=self.start_date,
                required=True,
                min_length=10,
                max_length=10
            )
            modal.add_item(date_input)
            
            await interaction.response.send_modal(modal)
            
            try:
                # Wait for modal submission
                modal_interaction = await modal.wait_for_submit(timeout=300.0)
                if modal_interaction:
                    date_str = modal_interaction.data["components"][0]["components"][0]["value"]
                    try:
                        # Validate date format
                        input_date = datetime.strptime(date_str, '%Y-%m-%d')
                        
                        # Check if date is in the future
                        if input_date > datetime.now():
                            await modal_interaction.response.send_message(
                                "⚠️ Cannot set a future date!",
                                ephemeral=True
                            )
                            return
                        
                        # Update the date
                        self.start_date = date_str
                        await modal_interaction.response.send_message(
                            f"📅 Start date set to **{self.start_date}**",
                            ephemeral=True
                        )
                    except ValueError:
                        await modal_interaction.response.send_message(
                            "❌ Invalid date format! Please use YYYY-MM-DD",
                            ephemeral=True
                        )
            except TimeoutError:
                await interaction.followup.send(
                    "❌ Date input timed out",
                    ephemeral=True
                )
            return
        
        elif custom_id == "toggle_favorite":
            await interaction.response.defer(ephemeral=True)
            button = [child for child in self.children if child.custom_id == "toggle_favorite"][0]
            button.style = ButtonStyle.danger if button.style == ButtonStyle.secondary else ButtonStyle.secondary
            self.is_favorite = button.style == ButtonStyle.danger
            await interaction.edit_original_response(
                content=f"{'⭐ Marked as favorite!' if self.is_favorite else '❌ Removed from favorites'}",
                view=self
            )
            return
        
        elif custom_id == "confirm":
            if not self.status:
                await interaction.response.send_message(
                    "❌ Please select a status first!",
                    ephemeral=True
                )
                return
            
            await interaction.response.defer()
            
            # Prepare anime data for database with automatic date handling
            anime_entry = {
                "title": self.anime_data["title"],
                "status": self.status,
                "rating": int(self.rating) if self.rating else None,
                "total_episodes": self.anime_data["episodes"],
                "episodes_watched": 0,
                "source_link": self.anime_data["site_url"],
                "is_favorite": self.is_favorite,
                "start_date": self.start_date,  # Always include start_date
                "completion_date": datetime.now().strftime('%Y-%m-%d') if self.status == "Completed" else None
            }
            
            # Add to database
            await self.cog.db.add_anime(self.user_id, anime_entry)
            
            # Send success message
            embed = self.cog.embed_creator.create_anime_details_embed(
                self.anime_data,
                anime_entry
            )
            await interaction.edit_original_response(
                content="✅ Anime added successfully!",
                embed=embed,
                view=None
            )
        
        elif custom_id == "cancel":
            await interaction.response.defer()
            await interaction.edit_original_response(
                content="❌ Add anime cancelled.",
                embed=None,
                view=None
            )

class AnimeCog(BaseCog):
    """Commands for managing your anime watchlist"""

    @commands.command(name="add_anime", aliases=["add"], help="Add an anime to your watchlist")
    async def add_anime(self, ctx, *, title=None):
        """Add an anime to your watchlist interactively
        
        Usage: {PREFIX}add "Title"
        Shows an interactive menu to:
        - Select status (👀 Watching, ✅ Completed, 📝 To Watch, ⏸️ On Hold, ⛔ Dropped)
        - Rate the anime (★★★★★)
        - Set start date (optional)
        - Mark as favorite (optional)
        """
        if not title:
            await ctx.send(embed=self.embed_creator.create_error_embed(
                "Missing Arguments",
                f"Usage: {PREFIX}add \"Title\"\n"
                f"Example: {PREFIX}add \"Naruto\""
            ))
            return

        try:
            # Fetch anime details from AniList
            anime_data = await self.handle_api_response(ctx, title)
            if not anime_data:
                return

            # Check if anime already exists for this user
            existing = await self.db.get_anime(ctx.author.id, anime_data["title"])
            if existing:
                await ctx.send(embed=self.embed_creator.create_error_embed(
                    "Already Exists",
                    f"**{anime_data['title']}** is already in your watchlist!"
                ))
                return

            # Show anime details and add options
            embed = self.embed_creator.create_anime_details_embed(
                anime_data,
                None
            )
            view = AddAnimeView(self, anime_data, ctx.author.id)  # Pass user_id to AddAnimeView
            await ctx.send(
                content="Found anime! Please fill in the details:",
                embed=embed,
                view=view
            )

        except Exception as e:
            await self.cog_command_error(ctx, e)

    @commands.command(name="delete_anime", help="Delete an anime from your watchlist")
    async def delete_anime(self, ctx, *, title=None):
        """Delete an anime from your watchlist
        
        Usage: {prefix}delete_anime "Title"
        Requires confirmation before deletion
        Cannot delete favorite anime
        """
        if not title:
            await ctx.send(embed=self.embed_creator.create_error_embed(
                "Missing Title",
                f"Usage: {PREFIX}delete_anime \"Title\""
            ))
            return

        try:
            # Get anime from database for this user
            anime = await self.db.get_anime(ctx.author.id, title)
            if not anime:
                await ctx.send(embed=self.embed_creator.create_error_embed(
                    "Not Found",
                    f"**{title}** not found in your watchlist!"
                ))
                return

            if anime["is_favorite"]:
                await ctx.send(embed=self.embed_creator.create_error_embed(
                    "Cannot Delete",
                    f"**{title}** is marked as favorite and cannot be deleted!"
                ))
                return

            # Get confirmation
            confirmed = await self.confirm_action(
                ctx,
                "Confirm Deletion",
                f"Are you sure you want to delete **{title}** from your watchlist?"
            )

            if confirmed:
                await self.db.delete_anime(ctx.author.id, title)
                await ctx.send(embed=self.embed_creator.create_success_embed(
                    "Deleted",
                    f"**{title}** has been deleted from your watchlist!"
                ))

        except Exception as e:
            await self.cog_command_error(ctx, e)

    @commands.command(name="list_anime", help="List all anime in your watchlist")
    async def list_anime(self, ctx):
        """List all anime in your watchlist
        
        Usage: {prefix}list_anime
        Shows a paginated list of all anime with status, progress, and preferences
        Use ⬅️ ➡️ reactions to navigate pages
        """
        try:
            anime_list = await self.db.get_all_anime(ctx.author.id)
            if not anime_list:
                await ctx.send(embed=self.embed_creator.create_error_embed(
                    "Empty Watchlist",
                    f"Your watchlist is empty! Use {PREFIX}add_anime to add some anime."
                ))
                return

            total_pages = (len(anime_list) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
            page = 0

            # Sort anime list by status and favorite
            anime_list.sort(key=lambda x: (
                not x.get('is_favorite', False),  # Favorites first
                {'Watching': 0, 'To Watch': 1, 'Completed': 2}.get(x.get('status', ''), 3),  # Sort by status
                x['title'].lower()  # Then alphabetically
            ))

            embed = self.embed_creator.create_list_embed(
                f"📺 Your Anime Watchlist ({len(anime_list)} total)",  # Updated to say "Your"
                anime_list,
                page,
                total_pages,
                ITEMS_PER_PAGE
            )
            message = await ctx.send(embed=embed)

            # Add navigation reactions
            await message.add_reaction("⬅️")
            await message.add_reaction("➡️")

            def check(reaction, user):
                return (
                    user == ctx.author
                    and str(reaction.emoji) in ["⬅️", "➡️"]
                    and reaction.message.id == message.id
                )

            while True:
                try:
                    reaction, user = await self.bot.wait_for(
                        "reaction_add",
                        timeout=60.0,
                        check=check
                    )

                    if str(reaction.emoji) == "➡️" and page < total_pages - 1:
                        page += 1
                    elif str(reaction.emoji) == "⬅️" and page > 0:
                        page -= 1

                    embed = self.embed_creator.create_list_embed(
                        f"📺 Your Anime Watchlist ({len(anime_list)} total)",
                        anime_list,
                        page,
                        total_pages,
                        ITEMS_PER_PAGE
                    )
                    await message.edit(embed=embed)
                    await message.remove_reaction(reaction, user)

                except TimeoutError:
                    # Remove reactions after timeout
                    try:
                        await message.clear_reactions()
                    except:
                        pass
                    break

        except Exception as e:
            await self.cog_command_error(ctx, e)

    @commands.command(name="update_status", help="Update the status of an anime")
    async def update_status(self, ctx, *, args=None):
        """Update the status of an anime
        
        Usage: {prefix}update_status "Title" "New Status"
        Status must be one of: Watching, Completed, To Watch
        """
        if not args:
            await ctx.send(embed=self.embed_creator.create_error_embed(
                "Missing Arguments",
                f"Usage: {PREFIX}update_status \"Title\" \"New Status\""
            ))
            return

        try:
            parts = args.split('"')
            parts = [p.strip() for p in parts if p.strip()]
            
            if len(parts) < 2:
                await ctx.send(embed=self.embed_creator.create_error_embed(
                    "Missing Arguments",
                    f"Please provide all arguments in quotes: {PREFIX}update_status \"Title\" \"New Status\""
                ))
                return

            title, new_status = parts[:2]

            if new_status not in VALID_STATUSES:
                await ctx.send(embed=self.embed_creator.create_error_embed(
                    "Invalid Status",
                    f"Status must be one of: {', '.join(VALID_STATUSES)}"
                ))
                return

            anime = await self.db.get_anime(ctx.author.id, title)
            if not anime:
                await ctx.send(embed=self.embed_creator.create_error_embed(
                    "Not Found",
                    f"**{title}** not found in your watchlist!"
                ))
                return

            update_data = {"status": new_status}
            
            # Update dates based on status
            if new_status == "Watching" and not anime.get("start_date"):
                update_data["start_date"] = datetime.now().strftime('%Y-%m-%d')
            elif new_status == "Completed":
                update_data["completion_date"] = datetime.now().strftime('%Y-%m-%d')

            await self.db.update_anime(ctx.author.id, title, update_data)
            
            # Fetch updated anime data
            updated_anime = await self.db.get_anime(ctx.author.id, title)
            anime_data = await self.handle_api_response(ctx, title)
            
            await ctx.send(embed=self.embed_creator.create_anime_details_embed(
                anime_data,
                updated_anime
            ))

        except Exception as e:
            await self.cog_command_error(ctx, e)

    @commands.command(name="toggle_favorite", help="Toggle favorite status of an anime")
    async def toggle_favorite(self, ctx, *, title=None):
        """Toggle whether an anime is marked as favorite
        
        Usage: {prefix}toggle_favorite "Title"
        """
        if not title:
            await ctx.send(embed=self.embed_creator.create_error_embed(
                "Missing Title",
                f"Usage: {PREFIX}toggle_favorite \"Title\""
            ))
            return

        try:
            anime = await self.db.get_anime(ctx.author.id, title)
            if not anime:
                await ctx.send(embed=self.embed_creator.create_error_embed(
                    "Not Found",
                    f"**{title}** not found in your watchlist!"
                ))
                return

            new_status = not anime["is_favorite"]
            await self.db.update_anime(ctx.author.id, title, {"is_favorite": new_status})
            
            await ctx.send(embed=self.embed_creator.create_success_embed(
                "Favorite Updated",
                f"**{title}** is {'now' if new_status else 'no longer'} marked as favorite!"
            ))

        except Exception as e:
            await self.cog_command_error(ctx, e)

    @commands.command(name="search_anime", help="Search for an anime on AniList")
    async def search_anime(self, ctx, *, title=None):
        """Search for an anime on AniList
        
        Usage: {prefix}search_anime "Title"
        Shows detailed information about the anime
        """
        if not title:
            await ctx.send(embed=self.embed_creator.create_error_embed(
                "Missing Title",
                f"Usage: {PREFIX}search_anime \"Title\""
            ))
            return

        try:
            anime_data = await self.handle_api_response(ctx, title)
            if anime_data:
                # Check if anime is in watchlist
                watchlist_data = await self.db.get_anime(ctx.author.id, anime_data["title"])
                await ctx.send(embed=self.embed_creator.create_anime_details_embed(
                    anime_data,
                    watchlist_data
                ))

        except Exception as e:
            await self.cog_command_error(ctx, e)

    @commands.command(name="status", help="Show detailed status of an anime")
    async def status(self, ctx, *, title=None):
        """Show detailed status view of an anime with progress bars and quick actions
        
        Usage: {prefix}status "Title"
        Shows progress bars, status, and quick actions
        Use reactions to perform actions:
        🎬 - Update progress
        📝 - Change status
        ⭐ - Toggle favorite
        ℹ️ - View details
        """
        if not title:
            await ctx.send(embed=self.embed_creator.create_error_embed(
                "Missing Title",
                f"Usage: {PREFIX}status \"Title\""
            ))
            return

        try:
            # Get anime from database and API
            watchlist_data = await self.db.get_anime(ctx.author.id, title)
            if not watchlist_data:
                await ctx.send(embed=self.embed_creator.create_error_embed(
                    "Not Found",
                    f"**{title}** not found in your watchlist!"
                ))
                return

            anime_data = await self.handle_api_response(ctx, title)
            if not anime_data:
                return

            # Create and send status embed
            embed = self.embed_creator.create_status_embed(anime_data, watchlist_data)
            message = await ctx.send(embed=embed)

            # Add reaction controls
            reactions = ["🎬", "📝", "⭐", "ℹ️"]
            for reaction in reactions:
                await message.add_reaction(reaction)

            def check(reaction, user):
                return (
                    user == ctx.author
                    and str(reaction.emoji) in reactions
                    and reaction.message.id == message.id
                )

            while True:
                try:
                    reaction, user = await self.bot.wait_for(
                        "reaction_add",
                        timeout=60.0,
                        check=check
                    )

                    emoji = str(reaction.emoji)
                    if emoji == "🎬":
                        # Update progress
                        await message.clear_reactions()
                        await ctx.send(f"How many episodes have you watched? (Current: {watchlist_data['episodes_watched']}/{anime_data['episodes']})")
                        
                        def check_msg(m):
                            return m.author == ctx.author and m.channel == ctx.channel and m.content.isdigit()
                        
                        try:
                            msg = await self.bot.wait_for("message", timeout=30.0, check=check_msg)
                            episodes = int(msg.content)
                            
                            if 0 <= episodes <= anime_data['episodes']:
                                await self.db.update_anime(ctx.author.id, title, {"episodes_watched": episodes})
                                # Update status if completed
                                if episodes == anime_data['episodes']:
                                    await self.db.update_anime(ctx.author.id, title, {
                                        "status": "Completed",
                                        "completion_date": datetime.now().strftime('%Y-%m-%d')
                                    })
                                # Update status if started watching
                                elif episodes > 0 and watchlist_data['status'] == "To Watch":
                                    await self.db.update_anime(ctx.author.id, title, {
                                        "status": "Watching",
                                        "start_date": datetime.now().strftime('%Y-%m-%d')
                                    })
                                
                                # Refresh the status view
                                watchlist_data = await self.db.get_anime(ctx.author.id, title)
                                embed = self.embed_creator.create_status_embed(anime_data, watchlist_data)
                                await message.edit(embed=embed)
                                for reaction in reactions:
                                    await message.add_reaction(reaction)
                            else:
                                await ctx.send("Invalid episode number!")
                        except TimeoutError:
                            await ctx.send("Progress update cancelled.")

                    elif emoji == "📝":
                        # Change status
                        status_msg = await ctx.send(
                            f"Current status: {watchlist_data['status']}\n"
                            f"React to change status:\n"
                            f"👀 - Watching\n"
                            f"✅ - Completed\n"
                            f"📝 - To Watch"
                        )
                        
                        status_reactions = {"👀": "Watching", "✅": "Completed", "📝": "To Watch"}
                        for react in status_reactions.keys():
                            await status_msg.add_reaction(react)
                            
                        def check_status(r, u):
                            return (
                                u == ctx.author
                                and str(r.emoji) in status_reactions
                                and r.message.id == status_msg.id
                            )
                            
                        try:
                            reaction, user = await self.bot.wait_for(
                                "reaction_add",
                                timeout=30.0,
                                check=check_status
                            )
                            
                            new_status = status_reactions[str(reaction.emoji)]
                            update_data = {"status": new_status}
                            
                            if new_status == "Watching" and not watchlist_data.get("start_date"):
                                update_data["start_date"] = datetime.now().strftime('%Y-%m-%d')
                            elif new_status == "Completed":
                                update_data["completion_date"] = datetime.now().strftime('%Y-%m-%d')
                                
                            await self.db.update_anime(ctx.author.id, title, update_data)
                            await status_msg.delete()
                            
                            # Refresh the status view
                            watchlist_data = await self.db.get_anime(ctx.author.id, title)
                            embed = self.embed_creator.create_status_embed(anime_data, watchlist_data)
                            await message.edit(embed=embed)
                        except TimeoutError:
                            await status_msg.delete()
                            await ctx.send("Status update cancelled.")

                    elif emoji == "⭐":
                        # Toggle favorite
                        new_status = not watchlist_data["is_favorite"]
                        await self.db.update_anime(ctx.author.id, title, {"is_favorite": new_status})
                        
                        # Refresh the status view
                        watchlist_data = await self.db.get_anime(ctx.author.id, title)
                        embed = self.embed_creator.create_status_embed(anime_data, watchlist_data)
                        await message.edit(embed=embed)

                    elif emoji == "ℹ️":
                        # Show detailed view
                        await message.clear_reactions()
                        await ctx.send(embed=self.embed_creator.create_anime_details_embed(
                            anime_data,
                            watchlist_data
                        ))
                        break

                    await message.remove_reaction(reaction, user)

                except TimeoutError:
                    await message.clear_reactions()
                    break

        except Exception as e:
            await self.cog_command_error(ctx, e)

    @commands.command(name="manage", help="Manage your anime list with dropdown menus")
    async def manage(self, ctx):
        """Manage your anime list using dropdown menus
        
        Usage: {prefix}manage
        Shows dropdown menus to:
        - Update anime status
        - Delete anime from list
        """
        try:
            anime_list = await self.db.get_all_anime(ctx.author.id)
            if not anime_list:
                await ctx.send(embed=self.embed_creator.create_error_embed(
                    "Empty Watchlist",
                    f"Your watchlist is empty! Use {PREFIX}add_anime to add some anime."
                ))
                return

            # Sort anime list
            anime_list.sort(key=lambda x: (
                not x.get('is_favorite', False),
                {'Watching': 0, 'To Watch': 1, 'Completed': 2}.get(x.get('status', ''), 3),
                x['title'].lower()
            ))

            view = AnimeView(self, anime_list, ctx.author.id)  # Pass user_id to AnimeView
            await ctx.send(
                "Select an anime to manage:",
                view=view
            )

        except Exception as e:
            await self.cog_command_error(ctx, e)

async def setup(bot):
    await bot.add_cog(AnimeCog(bot))
    return True 