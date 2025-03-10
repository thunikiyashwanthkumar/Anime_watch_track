from pymongo import MongoClient
import os
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# Get MongoDB connection string
MONGODB_URI = os.getenv('DBSTR')
if not MONGODB_URI:
    print("Error: DBSTR environment variable not found")
    exit(1)

# Connect to MongoDB
client = MongoClient(MONGODB_URI)
db = client.anime_watchlist

# User ID to add anime for
USER_ID = 1187780807331430410

def import_user():
    """Create or update user in the database"""
    try:
        user_data = {
            "user_id": USER_ID,
            "username": "roronoazoro20_dev",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        # Upsert user (insert if not exists, update if exists)
        db.users.update_one(
            {"user_id": USER_ID},
            {"$set": user_data},
            upsert=True
        )
        print(f"✅ User setup complete for ID: {USER_ID}")
        return True
    except Exception as e:
        print(f"❌ Error setting up user: {str(e)}")
        return False

def import_watchlist():
    """Import anime list for the user"""
    if not import_user():
        return
    
    success_count = 0
    error_count = 0
    
    # Clear existing anime list for this user
    try:
        result = db.anime_lists.delete_many({"user_id": USER_ID})
        print(f"Cleared {result.deleted_count} existing entries")
    except Exception as e:
        print(f"❌ Error clearing existing entries: {str(e)}")
        return
    
    # Watchlist data
    watchlist_data = {
        "Watching": [
            {"title": "Attack on Titan Season 3", "total_episodes": 12, "source_link": "https://myanimelist.net/anime/35760"},
            {"title": "Attack on Titan Season 2", "total_episodes": 12, "source_link": "https://myanimelist.net/anime/25777"},
            {"title": "Demon Slayer: Kimetsu no Yaiba", "total_episodes": 26, "source_link": "https://myanimelist.net/anime/38000"},
            {"title": "One Piece", "total_episodes": 0, "source_link": "https://myanimelist.net/anime/21"}
        ],
        "Plan to Watch": [
            {"title": "Naruto", "total_episodes": 220, "source_link": "https://myanimelist.net/anime/20"},
            {"title": "Pokémon", "total_episodes": 0, "source_link": "https://myanimelist.net/anime/527"},
            {"title": "Pokémon Evolutions", "total_episodes": 8, "source_link": "https://myanimelist.net/anime/49730"}
        ]
    }
    
    # Process all anime
    for status, anime_list in watchlist_data.items():
        for anime in anime_list:
            try:
                # Prepare document
                document = {
                    "user_id": USER_ID,
                    "title": anime["title"],
                    "status": "To Watch" if status == "Plan to Watch" else status,
                    "episodes_watched": 0,
                    "total_episodes": anime["total_episodes"],
                    "source_link": anime["source_link"],
                    "is_favorite": False,
                    "notes": "",
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
                
                # Insert into MongoDB
                db.anime_lists.insert_one(document)
                print(f"✅ Added: {anime['title']}")
                success_count += 1
                
            except Exception as e:
                print(f"❌ Error adding {anime['title']}: {str(e)}")
                error_count += 1
    
    print("\nImport Summary:")
    print(f"Successfully Added: {success_count}")
    print(f"Failed to Add: {error_count}")
    print(f"Total Anime: {success_count + error_count}")

if __name__ == "__main__":
    import_watchlist() 