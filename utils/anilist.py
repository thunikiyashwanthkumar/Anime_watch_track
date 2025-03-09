import aiohttp
import logging
from typing import Optional, Dict, Any
import asyncio
from config.config import ANILIST_API_URL

logger = logging.getLogger(__name__)

class AniListAPI:
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self._rate_limit_lock = asyncio.Lock()
        self._last_request_time = 0
        self.rate_limit_delay = 1  # Minimum delay between requests in seconds

    async def _init_session(self):
        """Initialize aiohttp session if not exists"""
        if self.session is None:
            self.session = aiohttp.ClientSession()

    async def close(self):
        """Close the aiohttp session"""
        if self.session:
            await self.session.close()
            self.session = None

    async def _handle_rate_limit(self):
        """Handle rate limiting for API requests"""
        async with self._rate_limit_lock:
            current_time = asyncio.get_event_loop().time()
            time_since_last_request = current_time - self._last_request_time
            if time_since_last_request < self.rate_limit_delay:
                await asyncio.sleep(self.rate_limit_delay - time_since_last_request)
            self._last_request_time = asyncio.get_event_loop().time()

    async def fetch_anime_details(self, title: str) -> Optional[Dict[str, Any]]:
        """Fetch anime details from AniList API"""
        query = """
        query ($search: String) {
          Media(search: $search, type: ANIME) {
            id
            title {
              romaji
              english
              native
            }
            description
            episodes
            duration
            status
            genres
            averageScore
            popularity
            siteUrl
            startDate {
              year
              month
              day
            }
            endDate {
              year
              month
              day
            }
            coverImage {
              large
            }
            bannerImage
            studios {
              nodes {
                name
              }
            }
            seasonYear
            season
          }
        }
        """
        
        try:
            await self._init_session()
            await self._handle_rate_limit()
            
            async with self.session.post(
                ANILIST_API_URL,
                json={"query": query, "variables": {"search": title}}
            ) as response:
                if response.status == 429:  # Too Many Requests
                    retry_after = int(response.headers.get('Retry-After', '60'))
                    logger.warning(f"Rate limited by AniList API. Retrying after {retry_after} seconds")
                    await asyncio.sleep(retry_after)
                    return await self.fetch_anime_details(title)
                
                if response.status != 200:
                    logger.error(f"AniList API error: Status {response.status}")
                    return None
                
                data = await response.json()
                
                if "errors" in data:
                    logger.error(f"AniList API returned errors: {data['errors']}")
                    return None
                
                return data.get("data", {}).get("Media")
                
        except aiohttp.ClientError as e:
            logger.error(f"Error fetching anime details: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in fetch_anime_details: {str(e)}")
            return None

    def format_anime_data(self, api_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format API response data into a consistent structure"""
        return {
            "title": api_data["title"]["romaji"],
            "english_title": api_data["title"]["english"],
            "native_title": api_data["title"]["native"],
            "description": api_data["description"],
            "episodes": api_data["episodes"],
            "status": api_data["status"],
            "genres": api_data["genres"],
            "average_score": api_data["averageScore"],
            "popularity": api_data["popularity"],
            "site_url": api_data["siteUrl"],
            "cover_image": api_data["coverImage"]["large"],
            "banner_image": api_data["bannerImage"],
            "studios": [studio["name"] for studio in api_data["studios"]["nodes"]],
            "year": api_data["seasonYear"],
            "season": api_data["season"]
        } 