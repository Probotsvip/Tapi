#!/usr/bin/env python3
import asyncio
import logging
import sys
from telegram_service import telegram_service

logging.basicConfig(level=logging.DEBUG)

async def test_upload():
    # Test with a real small file URL for testing
    test_url = "https://www.learningcontainer.com/wp-content/uploads/2020/05/sample-mp4-file.mp4"
    filename = "test_video.mp4"
    caption = "🎬 Test Video\n📹 480p Video"
    
    print("Testing Telegram upload...")
    print(f"URL: {test_url}")
    print(f"Filename: {filename}")
    
    result = await telegram_service.upload_file_to_telegram(test_url, filename, caption)
    
    if result:
        print(f"✅ Upload successful!")
        print(f"Telegram URL: {result['telegram_url']}")
        print(f"Message ID: {result['message_id']}")
        return True
    else:
        print("❌ Upload failed")
        return False

if __name__ == "__main__":
    try:
        success = asyncio.run(test_upload())
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)