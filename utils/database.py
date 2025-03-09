from typing import Optional, Dict, List, Any
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import PyMongoError
import logging
from config.config import MONGODB_URI, DB_NAME, COLLECTION_NAME

logger = logging.getLogger(__name__)

class DatabaseManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance.initialize()
        return cls._instance
    
    def initialize(self):
        """Initialize database connection"""
        try:
            self.client: MongoClient = MongoClient(MONGODB_URI)
            self.db: Database = self.client[DB_NAME]
            self.collection: Collection = self.db[COLLECTION_NAME]
            # Create compound index for user_id and title
            self.collection.create_index([("user_id", 1), ("title", 1)], unique=True)
            logger.info("Successfully connected to MongoDB")
        except PyMongoError as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            raise

    def close(self):
        """Close database connection"""
        try:
            self.client.close()
            logger.info("MongoDB connection closed")
        except Exception as e:
            logger.error(f"Error closing MongoDB connection: {str(e)}")

    async def add_anime(self, user_id: int, anime_data: Dict[str, Any]) -> bool:
        """Add a new anime to the database for specific user"""
        try:
            # Add user_id to anime data
            anime_data["user_id"] = user_id
            if not self.collection.find_one({"user_id": user_id, "title": anime_data["title"]}):
                self.collection.insert_one(anime_data)
                return True
            return False
        except PyMongoError as e:
            logger.error(f"Error adding anime: {str(e)}")
            raise

    async def get_anime(self, user_id: int, title: str) -> Optional[Dict[str, Any]]:
        """Get anime by title for specific user"""
        try:
            return self.collection.find_one({"user_id": user_id, "title": title})
        except PyMongoError as e:
            logger.error(f"Error getting anime: {str(e)}")
            raise

    async def update_anime(self, user_id: int, title: str, update_data: Dict[str, Any]) -> bool:
        """Update anime data for specific user"""
        try:
            result = self.collection.update_one(
                {"user_id": user_id, "title": title},
                {"$set": update_data}
            )
            return result.modified_count > 0
        except PyMongoError as e:
            logger.error(f"Error updating anime: {str(e)}")
            raise

    async def delete_anime(self, user_id: int, title: str) -> bool:
        """Delete anime from database for specific user"""
        try:
            result = self.collection.delete_one({"user_id": user_id, "title": title})
            return result.deleted_count > 0
        except PyMongoError as e:
            logger.error(f"Error deleting anime: {str(e)}")
            raise

    async def get_all_anime(self, user_id: int, query: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Get all anime matching the query for specific user"""
        try:
            base_query = {"user_id": user_id}
            if query:
                base_query.update(query)
            return list(self.collection.find(base_query))
        except PyMongoError as e:
            logger.error(f"Error getting anime list: {str(e)}")
            raise

    async def get_favorites(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all favorite anime for specific user"""
        return await self.get_all_anime(user_id, {"is_favorite": True}) 