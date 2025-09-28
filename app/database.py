import hashlib
import json
import os
from datetime import datetime
from typing import Any, Dict, Optional

from pymongo import ASCENDING, AsyncMongoClient, IndexModel


class Database:
    client: Optional[AsyncMongoClient] = None
    database = None

db = Database()

async def get_database():
    return db.database

async def connect_to_mongo():
    """Create database connection"""
    mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    database_name = os.getenv("DATABASE_NAME", "image_processing_db")

    db.client = AsyncMongoClient(mongodb_url)
    db.database = db.client[database_name]

    # Create indexes for efficient querying
    collection = db.database[os.getenv("COLLECTION_NAME", "image_results")]
    indexes = [
        IndexModel([("image_hash", ASCENDING)], unique=True),
        IndexModel([("created_at", ASCENDING)]),
    ]
    await collection.create_indexes(indexes)

    print("Connected to MongoDB")

async def close_mongo_connection():
    """Close database connection"""
    if db.client:
        db.client.close()

def calculate_image_hash(image_data: bytes) -> str:
    """Calculate SHA-256 hash of image data"""
    return hashlib.sha256(image_data).hexdigest()

async def get_cached_result(image_hash: str) -> Optional[Dict[Any, Any]]:
    """Get cached processing result by image hash"""
    database = await get_database()
    collection = database[os.getenv("COLLECTION_NAME", "image_results")]

    result = await collection.find_one({"image_hash": image_hash})
    return result

async def save_processing_result(
    image_hash: str,
    filename: str,
    processing_result: Dict[Any, Any],
    processing_time: float
) -> bool:
    """Save processing result to database"""
    database = await get_database()
    collection = database[os.getenv("COLLECTION_NAME", "image_results")]

    document = {
        "image_hash": image_hash,
        "filename": filename,
        "result": processing_result,
        "processing_time": processing_time,
        "created_at": datetime.utcnow(),
        "cache_hit": False
    }

    try:
        await collection.insert_one(document)
        return True
    except Exception as e:
        print(f"Error saving to database: {e}")
        return False

async def log_request(
    endpoint: str,
    image_hash: str,
    filename: str,
    cache_hit: bool,
    processing_time: float,
    status: str = "success"
) -> bool:
    """Log API request details"""
    database = await get_database()
    collection = database["request_logs"]

    log_entry = {
        "endpoint": endpoint,
        "image_hash": image_hash,
        "filename": filename,
        "cache_hit": cache_hit,
        "processing_time": processing_time,
        "status": status,
        "timestamp": datetime.utcnow()
    }

    try:
        await collection.insert_one(log_entry)
        return True
    except Exception as e:
        print(f"Error logging request: {e}")
        return False