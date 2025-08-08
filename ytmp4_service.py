import base64
import json
import requests
import requests.adapters
import threading
import time
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
from Crypto.Cipher import AES
from database import db_manager
from telegram_service import telegram_service

class OptimizedYtmp4Service:
    def __init__(self, cache_manager):
        self.hex_key = "C5D58EF67A7584E4A29F6C35BBC4EB12"
        self.cache_manager = cache_manager
        self.session = requests.Session()
        # Configure session with connection pooling
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=20,
            pool_maxsize=20,
            max_retries=3
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        self._lock = threading.Lock()

    def hex_to_bytes(self, hex_str):
        return bytes.fromhex(hex_str)

    def b64_to_bytes(self, b64):
        return base64.b64decode(b64.replace("\n", "").replace(" ", ""))

    def decrypt(self, b64_encrypted):
        try:
            raw = self.hex_to_bytes(self.hex_key)
            data = self.b64_to_bytes(b64_encrypted)
            iv = data[:16]
            cipher_data = data[16:]
            cipher = AES.new(raw, AES.MODE_CBC, iv)
            decrypted = cipher.decrypt(cipher_data)
            decrypted = decrypted.rstrip(b"\x00")
            
            # Clean the decrypted data before JSON parsing
            decrypted_str = decrypted.decode("utf-8")
            # Remove any extra characters that might cause JSON parsing issues
            decrypted_str = decrypted_str.strip()
            
            # Try to find the JSON part if there's extra data
            json_start = decrypted_str.find('{')
            json_end = decrypted_str.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = decrypted_str[json_start:json_end]
                return json.loads(json_str)
            else:
                return json.loads(decrypted_str)
                
        except json.JSONDecodeError as e:
            logging.error(f"JSON decode error: {str(e)}")
            if 'decrypted_str' in locals():
                logging.error(f"Decrypted data: {decrypted_str[:500]}...")  # Log first 500 chars
            raise Exception("Failed to parse decrypted data")

    def get_cdn(self):
        """Get CDN with caching for faster subsequent requests"""
        cache_key = "current_cdn"
        cdn = self.cache_manager.get(cache_key)
        
        if cdn:
            return cdn
            
        retries = 3  # Reduced retries for faster response
        while retries:
            try:
                r = self.session.get("https://media.savetube.me/api/random-cdn", timeout=3)
                cdn = r.json().get("cdn")
                if cdn:
                    # Cache CDN for 5 minutes
                    self.cache_manager.set(cache_key, cdn, ttl=300)
                    return cdn
            except Exception as e:
                logging.warning(f"CDN fetch attempt failed: {str(e)}")
                retries -= 1
                time.sleep(0.5)  # Short delay between retries
        
        raise Exception("CDN fetch failed after retries")

    def get_info(self, url):
        """Get video info with MongoDB and Telegram caching"""
        # Step 1: Check MongoDB first (fastest)
        video_data = db_manager.find_video_by_url(url)
        if video_data:
            logging.info("Returning video info from MongoDB")
            return {
                "title": video_data["title"],
                "duration": video_data["duration"],
                "thumbnail": video_data["thumbnail"],
                "key": video_data["key"],
                "video_id": video_data["video_id"]
            }
        
        # Step 2: Check in-memory cache
        cache_key = f"info_{hash(url)}"
        cached_info = self.cache_manager.get(cache_key)
        if cached_info:
            logging.info("Returning cached video info")
            return cached_info
            
        # Step 3: Fetch from external API
        cdn = self.get_cdn()
        try:
            r = self.session.post(f"https://{cdn}/v2/info", 
                                json={"url": url}, 
                                timeout=8)
            res = r.json()
            
            if not res.get("status"):
                raise Exception(res.get("message", "Failed to fetch video info"))
            
            decrypted = self.decrypt(res["data"])
            video_id = db_manager.extract_video_id(url)
            
            info = {
                "title": decrypted["title"],
                "duration": decrypted["durationLabel"],
                "thumbnail": decrypted["thumbnail"],
                "key": decrypted["key"],
                "video_id": video_id
            }
            
            # Save to MongoDB for future use
            video_data = {
                "video_id": video_id,
                "title": decrypted["title"],
                "duration": decrypted["durationLabel"],
                "thumbnail": decrypted["thumbnail"],
                "key": decrypted["key"],
                "url": url,
                "created_at": time.time()
            }
            db_manager.save_video_data(video_data)
            
            # Cache info for 1 hour
            self.cache_manager.set(cache_key, info, ttl=3600)
            return info
            
        except Exception as e:
            logging.error(f"Error getting video info: {str(e)}")
            raise

    def get_best_quality_download(self, key, video_id=None):
        """Get highest quality video download with Telegram caching"""
        # Step 1: Check MongoDB for Telegram URL first (super fast)
        if video_id:
            video_data = db_manager.videos_collection.find_one({"video_id": video_id})
            if video_data and video_data.get("video_telegram_url"):
                logging.info("Returning video from Telegram channel")
                return video_data["video_telegram_url"], video_data.get("video_quality", "HD")
        
        # Step 2: Check in-memory cache
        cache_key = f"video_{key}"
        cached_result = self.cache_manager.get(cache_key)
        if cached_result:
            logging.info("Returning cached video download URL")
            return cached_result
            
        # Step 3: Fetch from external API
        qualities = ["1080", "720", "480", "360"]
        
        def check_quality(quality):
            try:
                cdn = self.get_cdn()
                r = self.session.post(f"https://{cdn}/download", json={
                    "downloadType": "video",
                    "quality": quality,
                    "key": key
                }, timeout=8)
                
                if r.status_code == 200:
                    res = r.json()
                    if res.get("status") and res["data"].get("downloadUrl"):
                        return res["data"]["downloadUrl"], quality
                return None
            except Exception as e:
                logging.warning(f"Quality {quality} check failed: {str(e)}")
                return None

        # Try qualities in priority order
        for quality in qualities:
            logging.info(f"Trying video quality: {quality}p")
            result = check_quality(quality)
            if result:
                download_url, found_quality = result
                logging.info(f"Successfully found {found_quality}p video quality")
                
                # Cache for 30 minutes
                self.cache_manager.set(cache_key, (download_url, found_quality), ttl=1800)
                
                # Background upload to Telegram (fire and forget)
                if video_id:
                    logging.info(f"Starting background upload for video {video_id}")
                    self.background_upload_to_telegram(video_id, download_url, 'video', found_quality)
                
                return download_url, found_quality
        
        raise Exception("No HD video download URL found - all qualities failed")

    def get_best_audio_download(self, key, video_id=None):
        """Get highest quality audio download with Telegram caching"""
        # Step 1: Check MongoDB for Telegram URL first (super fast)
        if video_id:
            video_data = db_manager.videos_collection.find_one({"video_id": video_id})
            if video_data and video_data.get("audio_telegram_url"):
                logging.info("Returning audio from Telegram channel")
                return video_data["audio_telegram_url"], video_data.get("audio_quality", "HD")
        
        # Step 2: Check in-memory cache
        cache_key = f"audio_{key}"
        cached_result = self.cache_manager.get(cache_key)
        if cached_result:
            logging.info("Returning cached audio download URL")
            return cached_result
            
        # Step 3: Fetch from external API
        audio_formats = ["320", "256", "192", "128", "mp3", "m4a"]
        
        def check_audio_format(format_type):
            try:
                cdn = self.get_cdn()
                r = self.session.post(f"https://{cdn}/download", json={
                    "downloadType": "audio",
                    "quality": format_type,
                    "key": key
                }, timeout=6)
                
                if r.status_code == 200:
                    res = r.json()
                    if res.get("status") and res["data"].get("downloadUrl"):
                        return res["data"]["downloadUrl"], format_type
                return None
            except Exception as e:
                logging.warning(f"Audio format {format_type} check failed: {str(e)}")
                return None

        # Try formats in priority order
        for fmt in audio_formats:
            quality_label = f"{fmt}kbps" if fmt.isdigit() else fmt.upper()
            logging.info(f"Trying audio quality: {quality_label}")
            result = check_audio_format(fmt)
            if result:
                download_url, format_type = result
                logging.info(f"Successfully found {quality_label} audio quality")
                
                # Cache for 30 minutes
                self.cache_manager.set(cache_key, (download_url, format_type), ttl=1800)
                
                # Background upload to Telegram (fire and forget)
                if video_id:
                    logging.info(f"Starting background upload for audio {video_id}")
                    self.background_upload_to_telegram(video_id, download_url, 'audio', format_type)
                
                return download_url, format_type
        
        raise Exception("No HD audio download URL found - all qualities failed")
    
    def background_upload_to_telegram(self, video_id, download_url, file_type, quality):
        """Upload file to Telegram in background thread"""
        def upload_task():
            try:
                logging.info(f"Background upload task started for {file_type} {video_id}")
                
                # Check if already uploaded
                video_data = db_manager.videos_collection.find_one({"video_id": video_id})
                if not video_data:
                    logging.error(f"Video data not found for {video_id}")
                    return
                
                # Check if already uploaded to avoid duplicates
                if file_type == 'video' and video_data.get("video_telegram_url"):
                    logging.info(f"Video {video_id} already uploaded to Telegram")
                    return
                elif file_type == 'audio' and video_data.get("audio_telegram_url"):
                    logging.info(f"Audio {video_id} already uploaded to Telegram")
                    return
                
                logging.info(f"Proceeding with upload for {file_type} {video_id}")
                
                # Generate filename
                filename = telegram_service.generate_filename(
                    video_data["title"], video_id, file_type, quality
                )
                logging.info(f"Generated filename: {filename}")
                
                # Create caption
                caption = f"🎬 {video_data['title']}\n📹 {quality}{'p' if file_type == 'video' else 'kbps'} {file_type.title()}"
                
                # Upload to Telegram
                logging.info(f"Starting Telegram upload for {filename}")
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(
                    telegram_service.upload_file_to_telegram(download_url, filename, caption)
                )
                loop.close()
                
                if result:
                    logging.info(f"Telegram upload successful for {file_type} {video_id}")
                    # Update MongoDB with Telegram URL
                    update_data = {}
                    if file_type == 'video':
                        update_data["video_telegram_url"] = result["telegram_url"]
                        update_data["video_quality"] = quality
                        update_data["video_message_id"] = result["message_id"]
                    else:
                        update_data["audio_telegram_url"] = result["telegram_url"]
                        update_data["audio_quality"] = quality
                        update_data["audio_message_id"] = result["message_id"]
                    
                    db_manager.videos_collection.update_one(
                        {"video_id": video_id},
                        {"$set": update_data}
                    )
                    
                    logging.info(f"Successfully uploaded {file_type} {video_id} to Telegram and updated database")
                else:
                    logging.error(f"Failed to upload {file_type} {video_id} to Telegram - no result returned")
                    
            except Exception as e:
                logging.error(f"Background upload error for {video_id}: {str(e)}")
                import traceback
                logging.error(f"Full traceback: {traceback.format_exc()}")
        
        # Run in background thread
        logging.info(f"Starting background thread for {file_type} {video_id}")
        threading.Thread(target=upload_task, daemon=True).start()
