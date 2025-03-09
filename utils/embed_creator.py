from typing import List, Dict, Any, Optional
from discord import Embed
from config.config import EMBED_COLOR, EMBED_FOOTER

class EmbedCreator:
    @staticmethod
    def create_help_embed(title: str, description: str) -> Embed:
        """Create an embed for help messages"""
        embed = Embed(title=title, description=description, color=EMBED_COLOR)
        embed.set_footer(text=EMBED_FOOTER)
        return embed

    @staticmethod
    def create_anime_details_embed(anime_data: Dict[str, Any], watchlist_data: Optional[Dict[str, Any]] = None) -> Embed:
        """Create an embed for anime details"""
        embed = Embed(
            title=anime_data["title"],
            description=anime_data.get("description", "No description available"),
            color=EMBED_COLOR
        )
        
        # Set thumbnail
        if anime_data.get("cover_image"):
            embed.set_thumbnail(url=anime_data["cover_image"])
        
        # Set banner image if available
        if anime_data.get("banner_image"):
            embed.set_image(url=anime_data["banner_image"])
        
        # Basic anime information
        embed.add_field(name="Episodes", value=anime_data.get("episodes", "Unknown"), inline=True)
        embed.add_field(name="Score", value=f"{anime_data.get('average_score', 'N/A')}/100", inline=True)
        embed.add_field(name="Genres", value=", ".join(anime_data.get("genres", ["Unknown"])), inline=False)
        
        # Add watchlist information if available
        if watchlist_data:
            embed.add_field(
                name="Watch Status",
                value=f"Status: {watchlist_data.get('status', 'Unknown')}\n"
                      f"Progress: {watchlist_data.get('episodes_watched', 0)}/{anime_data.get('episodes', '?')}\n"
                      f"Favorite: {'Yes' if watchlist_data.get('is_favorite') else 'No'}",
                inline=False
            )
            
            # Add dates if available
            if watchlist_data.get("start_date"):
                embed.add_field(name="Started", value=watchlist_data["start_date"], inline=True)
            if watchlist_data.get("completion_date"):
                embed.add_field(name="Completed", value=watchlist_data["completion_date"], inline=True)
        
        # Add additional information
        if anime_data.get("studios"):
            embed.add_field(name="Studios", value=", ".join(anime_data["studios"]), inline=False)
        
        # Add season information if available
        if anime_data.get("season") and anime_data.get("year"):
            embed.add_field(
                name="Season",
                value=f"{anime_data['season']} {anime_data['year']}",
                inline=True
            )
        
        # Add AniList link
        if anime_data.get("site_url"):
            embed.add_field(name="AniList Link", value=anime_data["site_url"], inline=False)
        
        embed.set_footer(text=EMBED_FOOTER)
        return embed

    @staticmethod
    def create_list_embed(
        title: str,
        anime_list: List[Dict[str, Any]],
        page: int,
        total_pages: int,
        items_per_page: int
    ) -> Embed:
        """Create an embed for listing anime"""
        embed = Embed(title=title, color=EMBED_COLOR)
        
        start_idx = page * items_per_page
        end_idx = start_idx + items_per_page
        current_items = anime_list[start_idx:end_idx]

        # Status emojis
        status_emoji = {
            "Watching": "👀",
            "Completed": "✅",
            "To Watch": "📝"
        }
        
        for anime in current_items:
            # Create title with status emoji
            status = anime.get('status', 'Unknown')
            emoji = status_emoji.get(status, "❓")
            title_text = f"{emoji} {anime['title']}"
            if anime.get('is_favorite'):
                title_text = f"⭐ {title_text}"

            # Create organized info field
            progress = f"{anime.get('episodes_watched', 0)}/{anime.get('total_episodes', '?')}"
            info = [
                f"**Status:** {status}",
                f"**Progress:** {progress} episodes",
                f"**Preference:** {anime.get('preference', 'Not set')}"
            ]
            
            # Add dates if available
            if anime.get('start_date'):
                info.append(f"**Started:** {anime['start_date']}")
            if anime.get('completion_date'):
                info.append(f"**Completed:** {anime['completion_date']}")

            embed.add_field(
                name=title_text,
                value="\n".join(info),
                inline=False
            )
        
        if not current_items:
            embed.add_field(
                name="No Anime Found",
                value="Your watchlist is empty! Use the add_anime command to add some anime.",
                inline=False
            )

        embed.set_footer(text=f"{EMBED_FOOTER} | Page {page + 1}/{total_pages}")
        return embed

    @staticmethod
    def create_error_embed(title: str, description: str) -> Embed:
        """Create an embed for error messages"""
        embed = Embed(title=title, description=description, color=0xFF0000)
        embed.set_footer(text=EMBED_FOOTER)
        return embed

    @staticmethod
    def create_success_embed(title: str, description: str) -> Embed:
        """Create an embed for success messages"""
        embed = Embed(title=title, description=description, color=EMBED_COLOR)
        embed.set_footer(text=EMBED_FOOTER)
        return embed

    @staticmethod
    def create_confirmation_embed(title: str, description: str) -> Embed:
        """Create an embed for confirmation messages"""
        embed = Embed(title=title, description=description, color=0xFFA500)
        embed.set_footer(text=f"{EMBED_FOOTER} | React with ✅ to confirm or ❌ to cancel")
        return embed

    @staticmethod
    def create_status_embed(anime_data: Dict[str, Any], watchlist_data: Dict[str, Any]) -> Embed:
        """Create a status embed with progress bars and quick actions"""
        embed = Embed(title=f"📺 {anime_data['title']}", color=EMBED_COLOR)
        
        # Calculate progress percentage
        episodes_watched = watchlist_data.get('episodes_watched', 0)
        total_episodes = anime_data.get('episodes', 0)
        progress_percent = (episodes_watched / total_episodes * 100) if total_episodes > 0 else 0
        
        # Create progress bar (20 segments)
        filled = '█' * int(progress_percent / 5)
        empty = '░' * (20 - int(progress_percent / 5))
        progress_bar = f"{filled}{empty} {progress_percent:.1f}%"
        
        # Progress section
        embed.add_field(
            name="📊 Progress",
            value=f"```\n{progress_bar}\n{episodes_watched}/{total_episodes} episodes```",
            inline=False
        )
        
        # Status section with emoji indicators
        status = watchlist_data.get('status', 'Unknown')
        status_emoji = {
            "Watching": "👀",
            "Completed": "✅",
            "To Watch": "📝"
        }.get(status, "❓")
        
        embed.add_field(
            name=f"{status_emoji} Status",
            value=f"```\n{status}```",
            inline=True
        )
        
        # Score section
        score = anime_data.get('average_score', 0)
        score_bar = '█' * int(score / 5) + '░' * (20 - int(score / 5))
        embed.add_field(
            name="⭐ Score",
            value=f"```\n{score_bar} {score}/100```",
            inline=True
        )
        
        # Quick actions section
        actions = [
            "🎬 Update Progress",
            "📝 Change Status",
            "⭐ Toggle Favorite",
            "ℹ️ View Details"
        ]
        embed.add_field(
            name="Quick Actions",
            value="\n".join(actions),
            inline=False
        )
        
        # Additional info
        info_lines = []
        if watchlist_data.get('start_date'):
            info_lines.append(f"Started: {watchlist_data['start_date']}")
        if watchlist_data.get('completion_date'):
            info_lines.append(f"Completed: {watchlist_data['completion_date']}")
        if watchlist_data.get('preference'):
            info_lines.append(f"Note: {watchlist_data['preference']}")
        
        if info_lines:
            embed.add_field(
                name="📌 Additional Info",
                value="\n".join(info_lines),
                inline=False
            )
        
        # Set thumbnail if available
        if anime_data.get("cover_image"):
            embed.set_thumbnail(url=anime_data["cover_image"])
        
        embed.set_footer(text=f"{EMBED_FOOTER} | Use reactions to perform actions")
        return embed 