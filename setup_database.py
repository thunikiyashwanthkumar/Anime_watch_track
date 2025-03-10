from pymongo import MongoClient, ASCENDING
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get MongoDB connection string
MONGODB_URI = os.getenv('DBSTR')
if not MONGODB_URI:
    print("Error: DBSTR environment variable not found")
    exit(1)

def setup_database():
    # Connect to MongoDB
    client = MongoClient(MONGODB_URI)
    
    # Create/Get database
    db = client.anime_watchlist
    
    # Create collections
    users = db.users
    anime_lists = db.anime_lists
    
    try:
        # Drop existing collections to start fresh
        db.users.drop()
        db.anime_lists.drop()
        print("Dropped existing collections")
        
        # Create indexes for users collection
        users.create_index([("user_id", ASCENDING)], unique=True)
        users.create_index([("username", ASCENDING)])
        print("Created indexes for users collection")
        
        # Create indexes for anime_lists collection
        anime_lists.create_index([("user_id", ASCENDING), ("title", ASCENDING)], unique=True)
        anime_lists.create_index([("user_id", ASCENDING), ("status", ASCENDING)])
        anime_lists.create_index([("user_id", ASCENDING), ("is_favorite", ASCENDING)])
        print("Created indexes for anime_lists collection")
        
        # Create schema validation for anime_lists
        db.command({
            "collMod": "anime_lists",
            "validator": {
                "$jsonSchema": {
                    "bsonType": "object",
                    "required": ["user_id", "title", "status", "episodes_watched", "total_episodes"],
                    "properties": {
                        "user_id": {"bsonType": "long"},
                        "title": {"bsonType": "string"},
                        "status": {
                            "enum": ["Watching", "Completed", "To Watch", "Dropped"]
                        },
                        "episodes_watched": {"bsonType": "int"},
                        "total_episodes": {"bsonType": "int"},
                        "source_link": {"bsonType": "string"},
                        "is_favorite": {"bsonType": "bool"},
                        "preference": {"bsonType": "string"},
                        "mal_id": {"bsonType": "int"},
                        "watchListType": {"bsonType": "int"},
                        "notes": {"bsonType": "string"},
                        "start_date": {"bsonType": "date"},
                        "completion_date": {"bsonType": "date"},
                        "rating": {
                            "bsonType": "int",
                            "minimum": 0,
                            "maximum": 10
                        }
                    }
                }
            }
        })
        print("Added schema validation for anime_lists collection")
        
        print("\n✅ Database setup completed successfully!")
        print("\nCollections created:")
        print("1. users - Stores user information")
        print("2. anime_lists - Stores anime entries for each user")
        
        print("\nIndexes created:")
        print("- Unique index on user_id in users collection")
        print("- Unique compound index on user_id and title in anime_lists")
        print("- Index on user_id and status in anime_lists")
        print("- Index on user_id and is_favorite in anime_lists")
        
    except Exception as e:
        print(f"\n❌ Error setting up database: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    setup_database() 