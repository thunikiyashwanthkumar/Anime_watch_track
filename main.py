import discord
from discord.ext import commands
from pymongo import MongoClient
from datetime import datetime
import random
import os
import requests
from discord import Embed
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
DBSTR = os.getenv('DBSTR')
DCBOT = os.getenv('DCBOT')

# Check if environment variables are set
if not DBSTR or not DCBOT:
    print("Error: Environment variables 'DBSTR' and 'DCBOT' are required.")
    exit(1)

# Initialize the bot with AutoShardedBot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.AutoShardedBot(command_prefix="!", intents=intents)

# MongoDB connection
MONGO_URI = DBSTR  # Use the environment variable directly
client = MongoClient(MONGO_URI)
db = client.anime_watchlist  # Database name
collection = db.anime  # Collection name

# Constants
VALID_STATUSES = ["Watching", "Completed", "To Watch"]
ITEMS_PER_PAGE = 5  # Number of items per page for pagination
ANILIST_API_URL = "https://graphql.anilist.co"

# Helper function to check for missing arguments
def check_missing_args(**kwargs):
    missing_args = [arg for arg, value in kwargs.items() if value is None]
    return missing_args

# Fetch anime details from AniList API
def fetch_anime_details(title: str):
    query = """
    query ($search: String) {
      Media(search: $search, type: ANIME) {
        title {
          romaji
          english
          native
        }
        description
        episodes
        status
        genres
        averageScore
        siteUrl
        coverImage {
          large
        }
      }
    }
    """
    variables = {"search": title}
    response = requests.post(ANILIST_API_URL, json={"query": query, "variables": variables})
    if response.status_code == 200:
        return response.json()["data"]["Media"]
    else:
        return None

# Add Anime using AniList API
@bot.command()
async def add_anime(ctx, title: str = None, status: str = None, preference: str = None):
    missing_args = check_missing_args(title=title, status=status, preference=preference)
    if missing_args:
        await ctx.send(f"Missing arguments: **{', '.join(missing_args)}**. Usage: `!add_anime \"Title\" \"Status\" \"Preference\"`")
        return

    # Validate status
    if status not in VALID_STATUSES:
        await ctx.send(f"Invalid status: **{status}**. Valid statuses are: {', '.join(VALID_STATUSES)}.")
        return

    # Fetch anime details from AniList API
    anime_details = fetch_anime_details(title)
    if not anime_details:
        await ctx.send(f"Could not find anime with title **{title}** on AniList.")
        return

    # Check for duplicate title
    if collection.find_one({"title": anime_details["title"]["romaji"]}):
        await ctx.send(f"**{anime_details['title']['romaji']}** already exists in the watchlist.")
        return

    anime = {
        "title": anime_details["title"]["romaji"],
        "status": status,
        "preference": preference,
        "total_episodes": anime_details["episodes"],
        "episodes_watched": 0,
        "source_link": anime_details["siteUrl"],
        "is_favorite": False,
        "start_date": None,
        "completion_date": None
    }
    collection.insert_one(anime)
    await ctx.send(f"Added **{anime_details['title']['romaji']}** to the watchlist!")

# Delete Anime (with confirmation)
@bot.command()
async def delete_anime(ctx, title: str = None):
    if not title:
        await ctx.send("Missing argument: **title**. Usage: `!delete_anime \"Title\"`")
        return

    anime = collection.find_one({"title": title})
    if not anime:
        await ctx.send(f"**{title}** not found in the watchlist.")
        return

    if anime["is_favorite"]:
        await ctx.send(f"**{title}** is marked as a favorite and cannot be deleted.")
        return

    # Confirmation message
    confirm_msg = await ctx.send(f"Are you sure you want to delete **{title}**? React with ✅ to confirm or ❌ to cancel.")
    await confirm_msg.add_reaction("✅")
    await confirm_msg.add_reaction("❌")

    def check(reaction, user):
        return user == ctx.author and str(reaction.emoji) in ["✅", "❌"]

    try:
        reaction, _ = await bot.wait_for("reaction_add", timeout=30.0, check=check)
        if str(reaction.emoji) == "✅":
            collection.delete_one({"title": title})
            await ctx.send(f"Deleted **{title}** from the watchlist!")
        else:
            await ctx.send("Deletion canceled.")
    except Exception:
        await ctx.send("Confirmation timed out. Deletion canceled.")

# Update Status
@bot.command()
async def update_status(ctx, title: str = None, new_status: str = None):
    missing_args = check_missing_args(title=title, new_status=new_status)
    if missing_args:
        await ctx.send(f"Missing arguments: **{', '.join(missing_args)}**. Usage: `!update_status \"Title\" \"NewStatus\"`")
        return

    if new_status not in VALID_STATUSES:
        await ctx.send(f"Invalid status: **{new_status}**. Valid statuses are: {', '.join(VALID_STATUSES)}.")
        return

    update_data = {"status": new_status}
    if new_status == "Watching":
        update_data["start_date"] = datetime.now().strftime('%Y-%m-%d')
    elif new_status == "Completed":
        update_data["completion_date"] = datetime.now().strftime('%Y-%m-%d')
    collection.update_one({"title": title}, {"$set": update_data})
    await ctx.send(f"Updated **{title}** status to **{new_status}**!")

# Update Progress
@bot.command()
async def update_progress(ctx, title: str = None, episodes_watched: int = None):
    missing_args = check_missing_args(title=title, episodes_watched=episodes_watched)
    if missing_args:
        await ctx.send(f"Missing arguments: **{', '.join(missing_args)}**. Usage: `!update_progress \"Title\" EpisodesWatched`")
        return

    anime = collection.find_one({"title": title})
    if not anime:
        await ctx.send(f"**{title}** not found in the watchlist.")
        return

    if episodes_watched < 0 or episodes_watched > anime["total_episodes"]:
        await ctx.send(f"Invalid episodes watched: **{episodes_watched}**. Must be between 0 and {anime['total_episodes']}.")
        return

    progress_percentage = (episodes_watched / anime["total_episodes"]) * 100
    collection.update_one({"title": title}, {"$set": {"episodes_watched": episodes_watched}})
    if episodes_watched >= anime["total_episodes"]:
        collection.update_one({"title": title}, {"$set": {"status": "Completed", "completion_date": datetime.now().strftime('%Y-%m-%d')}})
    await ctx.send(f"Updated **{title}** progress to **{episodes_watched}/{anime['total_episodes']}** ({progress_percentage:.2f}%)!")

# Mark/Unmark Favorite
@bot.command()
async def toggle_favorite(ctx, title: str = None):
    if not title:
        await ctx.send("Missing argument: **title**. Usage: `!toggle_favorite \"Title\"`")
        return

    anime = collection.find_one({"title": title})
    if not anime:
        await ctx.send(f"**{title}** not found in the watchlist.")
        return

    new_favorite_status = not anime["is_favorite"]
    collection.update_one({"title": title}, {"$set": {"is_favorite": new_favorite_status}})
    await ctx.send(f"Toggled favorite status for **{title}** to **{'Favorite' if new_favorite_status else 'Not Favorite'}**!")

# Search Anime (with enhanced functionality)
@bot.command()
async def search_anime(ctx, title: str = None):
    if not title:
        await ctx.send("Missing argument: **title**. Usage: `!search_anime \"Title\"`")
        return

    anime_details = fetch_anime_details(title)
    if not anime_details:
        await ctx.send(f"Could not find anime with title **{title}** on AniList.")
        return

    embed = Embed(title=anime_details["title"]["romaji"], color=0x00ff00)
    embed.set_thumbnail(url=anime_details["coverImage"]["large"])
    embed.add_field(name="Status", value=anime_details["status"], inline=True)
    embed.add_field(name="Episodes", value=anime_details["episodes"], inline=True)
    embed.add_field(name="Genres", value=", ".join(anime_details["genres"]), inline=False)
    embed.add_field(name="Average Score", value=anime_details["averageScore"], inline=True)
    embed.add_field(name="AniList Link", value=anime_details["siteUrl"], inline=False)
    embed.description = anime_details["description"]
    await ctx.send(embed=embed)

# List All Anime (with pagination)
@bot.command()
async def list_anime(ctx):
    results = list(collection.find())
    if not results:
        await ctx.send("No anime in the watchlist.")
        return

    total_pages = (len(results) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
    current_page = 0

    def create_embed(page):
        embed = Embed(title="Anime Watchlist", color=0x00ff00)
        start_index = page * ITEMS_PER_PAGE
        end_index = start_index + ITEMS_PER_PAGE
        for anime in results[start_index:end_index]:
            embed.add_field(name=anime["title"], value=f"Status: {anime['status']}, Progress: {anime['episodes_watched']}/{anime['total_episodes']}", inline=False)
        embed.set_footer(text=f"Page {page + 1}/{total_pages}")
        return embed

    message = await ctx.send(embed=create_embed(current_page))
    await message.add_reaction("⬅️")
    await message.add_reaction("➡️")

    def check(reaction, user):
        return user == ctx.author and str(reaction.emoji) in ["⬅️", "➡️"]

    while True:
        try:
            reaction, _ = await bot.wait_for("reaction_add", timeout=60.0, check=check)
            if str(reaction.emoji) == "➡️" and current_page < total_pages - 1:
                current_page += 1
            elif str(reaction.emoji) == "⬅️" and current_page > 0:
                current_page -= 1
            await message.edit(embed=create_embed(current_page))
            await message.remove_reaction(reaction.emoji, ctx.author)
        except Exception:
            break

# Show Favorite Anime (with pagination)
@bot.command()
async def show_favorites(ctx):
    results = list(collection.find({"is_favorite": True}))
    if not results:
        await ctx.send("No favorite anime found.")
        return

    total_pages = (len(results) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
    current_page = 0

    def create_embed(page):
        embed = Embed(title="Favorite Anime", color=0x00ff00)
        start_index = page * ITEMS_PER_PAGE
        end_index = start_index + ITEMS_PER_PAGE
        for anime in results[start_index:end_index]:
            embed.add_field(name=anime["title"], value=f"Status: {anime['status']}, Progress: {anime['episodes_watched']}/{anime['total_episodes']}", inline=False)
        embed.set_footer(text=f"Page {page + 1}/{total_pages}")
        return embed

    message = await ctx.send(embed=create_embed(current_page))
    await message.add_reaction("⬅️")
    await message.add_reaction("➡️")

    def check(reaction, user):
        return user == ctx.author and str(reaction.emoji) in ["⬅️", "➡️"]

    while True:
        try:
            reaction, _ = await bot.wait_for("reaction_add", timeout=60.0, check=check)
            if str(reaction.emoji) == "➡️" and current_page < total_pages - 1:
                current_page += 1
            elif str(reaction.emoji) == "⬅️" and current_page > 0:
                current_page -= 1
            await message.edit(embed=create_embed(current_page))
            await message.remove_reaction(reaction.emoji, ctx.author)
        except Exception:
            break

# Pick Random Anime (with filters)
@bot.command()
async def random_anime(ctx, preference: str = None):
    query = {"status": {"$in": ["To Watch", "Watching"]}}
    if preference:
        query["preference"] = {"$regex": preference, "$options": "i"}

    results = list(collection.find(query))
    if results:
        anime = random.choice(results)
        anime_details = fetch_anime_details(anime["title"])
        if anime_details:
            embed = Embed(title="Random Anime Suggestion", color=0x00ff00)
            embed.set_thumbnail(url=anime_details["coverImage"]["large"])
            embed.add_field(name="Title", value=anime_details["title"]["romaji"], inline=False)
            embed.add_field(name="Status", value=anime["status"], inline=True)
            embed.add_field(name="Progress", value=f"{anime['episodes_watched']}/{anime['total_episodes']}", inline=True)
            embed.add_field(name="Preference", value=anime["preference"], inline=True)
            embed.add_field(name="AniList Link", value=anime_details["siteUrl"], inline=False)
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"**{anime['title']}** details could not be fetched from AniList.")
    else:
        await ctx.send("No anime found matching your filters.")

# View Anime Details (with rich embed)
@bot.command()
async def anime_details(ctx, title: str = None):
    if not title:
        await ctx.send("Missing argument: **title**. Usage: `!anime_details \"Title\"`")
        return

    anime = collection.find_one({"title": title})
    if not anime:
        await ctx.send(f"**{title}** not found in the watchlist.")
        return

    anime_details = fetch_anime_details(title)
    if not anime_details:
        await ctx.send(f"Could not find anime with title **{title}** on AniList.")
        return

    embed = Embed(title=anime_details["title"]["romaji"], color=0x00ff00)
    embed.set_thumbnail(url=anime_details["coverImage"]["large"])
    embed.add_field(name="Status", value=anime["status"], inline=True)
    embed.add_field(name="Preference", value=anime["preference"], inline=True)
    embed.add_field(name="Progress", value=f"{anime['episodes_watched']}/{anime['total_episodes']}", inline=True)
    embed.add_field(name="AniList Link", value=anime_details["siteUrl"], inline=False)
    embed.add_field(name="Favorite", value="Yes" if anime["is_favorite"] else "No", inline=True)
    embed.add_field(name="Start Date", value=anime["start_date"] or "N/A", inline=True)
    embed.add_field(name="Completion Date", value=anime["completion_date"] or "N/A", inline=True)
    embed.description = anime_details["description"]
    await ctx.send(embed=embed)

# Run the bot
bot.run(DCBOT)