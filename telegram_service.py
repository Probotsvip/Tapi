import asyncio
import aiohttp
import logging
import os
from datetime import datetime
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID

class TelegramService:
    def __init__(self):
        self.bot_token = TELEGRAM_BOT_TOKEN
        self.channel_id = TELEGRAM_CHANNEL_ID
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
    
    async def upload_file_to_telegram(self, file_url, filename, caption=""):
        """Upload file to Telegram channel and get download URL"""
        try:
            logging.info(f"Starting Telegram upload for {filename}")
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=300)) as session:
                # Download file first
                logging.info(f"Downloading file from: {file_url}")
                async with session.get(file_url) as response:
                    if response.status != 200:
                        logging.error(f"Failed to download file: {response.status}")
                        return None
                    
                    file_data = await response.read()
                    file_size = len(file_data)
                    logging.info(f"Downloaded file size: {file_size} bytes")
                    
                    # Check file size limit (50MB for Telegram)
                    if file_size > 50 * 1024 * 1024:
                        logging.error(f"File too large: {file_size} bytes (max 50MB)")
                        return None
                    
                    # Prepare form data for Telegram upload
                    data = aiohttp.FormData()
                    data.add_field('chat_id', self.channel_id)
                    data.add_field('caption', caption)
                    
                    # Determine file type and upload accordingly
                    if filename.endswith(('.mp4', '.mkv', '.avi')):
                        data.add_field('video', file_data, filename=filename, content_type='video/mp4')
                        upload_url = f"{self.base_url}/sendVideo"
                        logging.info("Uploading as video")
                    elif filename.endswith(('.mp3', '.m4a', '.aac')):
                        data.add_field('audio', file_data, filename=filename, content_type='audio/mpeg')
                        upload_url = f"{self.base_url}/sendAudio"
                        logging.info("Uploading as audio")
                    else:
                        data.add_field('document', file_data, filename=filename)
                        upload_url = f"{self.base_url}/sendDocument"
                        logging.info("Uploading as document")
                    
                    # Upload to Telegram
                    logging.info(f"Uploading to Telegram: {upload_url}")
                    async with session.post(upload_url, data=data) as upload_response:
                        response_text = await upload_response.text()
                        logging.info(f"Telegram response status: {upload_response.status}")
                        
                        if upload_response.status == 200:
                            result = await upload_response.json()
                            logging.info(f"Telegram response: {result}")
                            
                            if result.get('ok'):
                                # Get file info to create download URL
                                message = result['result']
                                file_id = None
                                
                                if 'video' in message:
                                    file_id = message['video']['file_id']
                                elif 'audio' in message:
                                    file_id = message['audio']['file_id']
                                elif 'document' in message:
                                    file_id = message['document']['file_id']
                                
                                if file_id:
                                    # Get file download URL
                                    download_url = await self.get_file_download_url(file_id)
                                    logging.info(f"Successfully uploaded {filename} to Telegram")
                                    return {
                                        'telegram_url': download_url,
                                        'message_id': message['message_id'],
                                        'file_id': file_id
                                    }
                                else:
                                    logging.error("No file_id found in Telegram response")
                                    return None
                            else:
                                logging.error(f"Telegram API error: {result}")
                                return None
                        else:
                            logging.error(f"Failed to upload to Telegram: {upload_response.status}")
                            logging.error(f"Telegram error response: {response_text}")
                            return None
                            
        except Exception as e:
            logging.error(f"Error uploading to Telegram: {str(e)}")
            import traceback
            logging.error(f"Full traceback: {traceback.format_exc()}")
            return None
    
    async def get_file_download_url(self, file_id):
        """Get direct download URL for Telegram file"""
        try:
            async with aiohttp.ClientSession() as session:
                get_file_url = f"{self.base_url}/getFile"
                params = {'file_id': file_id}
                
                async with session.get(get_file_url, params=params) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get('ok'):
                            file_path = result['result']['file_path']
                            download_url = f"https://api.telegram.org/file/bot{self.bot_token}/{file_path}"
                            return download_url
                    return None
        except Exception as e:
            logging.error(f"Error getting file download URL: {str(e)}")
            return None
    
    async def check_file_in_channel(self, video_id, file_type='video'):
        """Check if file exists in Telegram channel (placeholder - would need channel history search)"""
        # Note: This would require implementing a search through channel history
        # For now, we'll rely on database to track uploaded files
        return None
    
    def generate_filename(self, video_title, video_id, file_type, quality):
        """Generate filename for Telegram upload"""
        safe_title = "".join(c for c in video_title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_title = safe_title[:50]  # Limit length
        
        if file_type == 'video':
            extension = '.mp4'
            filename = f"{safe_title}_{video_id}_{quality}p{extension}"
        else:  # audio
            extension = '.mp3' if quality in ['mp3', 'audio'] else '.m4a'
            filename = f"{safe_title}_{video_id}_{quality}kbps{extension}"
        
        return filename

# Global Telegram service instance
telegram_service = TelegramService()