import asyncio
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from config import MONGO_DB_URI

class DatabaseManager:
    def __init__(self):
        self.mongo_uri = MONGO_DB_URI
        self.client = None
        self.db = None
        self.async_client = None
        self.async_db = None
        self.setup_database()
    
    def setup_database(self):
        """Setup synchronous MongoDB connection"""
        try:
            self.client = MongoClient(self.mongo_uri)
            self.db = self.client.ytdownloader
            self.videos_collection = self.db.videos
            logging.info("Connected to MongoDB Atlas successfully")
        except Exception as e:
            logging.error(f"Failed to connect to MongoDB: {str(e)}")
            raise
    
    async def setup_async_database(self):
        """Setup asynchronous MongoDB connection"""
        try:
            self.async_client = AsyncIOMotorClient(self.mongo_uri)
            self.async_db = self.async_client.ytdownloader
            self.async_videos_collection = self.async_db.videos
            logging.info("Connected to MongoDB Atlas async successfully")
        except Exception as e:
            logging.error(f"Failed to connect to MongoDB async: {str(e)}")
            raise
    
    def find_video_by_url(self, video_url):
        """Find video data by URL - sync version"""
        try:
            # Extract video ID from URL
            video_id = self.extract_video_id(video_url)
            if not video_id:
                return None
            
            result = self.videos_collection.find_one({"video_id": video_id})
            return result
        except Exception as e:
            logging.error(f"Error finding video: {str(e)}")
            return None
    
    async def find_video_by_url_async(self, video_url):
        """Find video data by URL - async version"""
        try:
            if not self.async_client:
                await self.setup_async_database()
            
            video_id = self.extract_video_id(video_url)
            if not video_id:
                return None
            
            result = await self.async_videos_collection.find_one({"video_id": video_id})
            return result
        except Exception as e:
            logging.error(f"Error finding video async: {str(e)}")
            return None
    
    def save_video_data(self, video_data):
        """Save video data to MongoDB - sync version"""
        try:
            # Upsert based on video_id
            result = self.videos_collection.update_one(
                {"video_id": video_data["video_id"]},
                {"$set": video_data},
                upsert=True
            )
            logging.info(f"Video data saved: {video_data['video_id']}")
            return True
        except Exception as e:
            logging.error(f"Error saving video data: {str(e)}")
            return False
    
    async def save_video_data_async(self, video_data):
        """Save video data to MongoDB - async version"""
        try:
            if not self.async_client:
                await self.setup_async_database()
            
            result = await self.async_videos_collection.update_one(
                {"video_id": video_data["video_id"]},
                {"$set": video_data},
                upsert=True
            )
            logging.info(f"Video data saved async: {video_data['video_id']}")
            return True
        except Exception as e:
            logging.error(f"Error saving video data async: {str(e)}")
            return False
    
    def extract_video_id(self, url):
        """Extract YouTube video ID from URL"""
        import re
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)',
            r'youtube\.com\/v\/([^&\n?#]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    def get_stats(self):
        """Get database statistics"""
        try:
            total_videos = self.videos_collection.count_documents({})
            video_count = self.videos_collection.count_documents({"video_telegram_url": {"$exists": True}})
            audio_count = self.videos_collection.count_documents({"audio_telegram_url": {"$exists": True}})
            
            return {
                "total_videos": total_videos,
                "videos_with_telegram_video": video_count,
                "videos_with_telegram_audio": audio_count
            }
        except Exception as e:
            logging.error(f"Error getting stats: {str(e)}")
            return {"total_videos": 0, "videos_with_telegram_video": 0, "videos_with_telegram_audio": 0}

# Global database instance
db_manager = DatabaseManager()