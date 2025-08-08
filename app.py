import os
import logging
from flask import Flask, render_template, request, jsonify
from ytmp4_service import OptimizedYtmp4Service
from cache_manager import CacheManager
from database import db_manager
from config import SECRET_KEY

# Configure logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.secret_key = SECRET_KEY

# Initialize services
cache_manager = CacheManager()
ytmp4_service = OptimizedYtmp4Service(cache_manager)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/video-info', methods=['POST'])
def get_video_info():
    """Get video information without download URLs - faster response"""
    try:
        data = request.get_json()
        url = data.get('url')
        
        if not url:
            return jsonify({"status": False, "message": "Missing YouTube URL"}), 400
        
        info = ytmp4_service.get_info(url)
        
        return jsonify({
            "status": True,
            "title": info["title"],
            "duration": info["duration"],
            "thumbnail": info["thumbnail"],
            "key": info["key"],
            "video_id": info["video_id"]
        })
    
    except Exception as e:
        logging.error(f"Error in get_video_info: {str(e)}")
        return jsonify({"status": False, "message": str(e)}), 500

@app.route('/api/download', methods=['POST'])
def get_download_links():
    """Get download links for video or audio with Telegram caching"""
    try:
        data = request.get_json()
        key = data.get('key')
        video_id = data.get('video_id')
        download_type = data.get('type', 'video')  # 'video' or 'audio'
        
        if not key:
            return jsonify({"status": False, "message": "Missing video key"}), 400
        
        if download_type == 'video':
            download_url, quality = ytmp4_service.get_best_quality_download(key, video_id)
            return jsonify({
                "status": True,
                "download_url": download_url,
                "quality": quality,
                "type": "video",
                "source": "telegram" if "telegram" in download_url else "external"
            })
        elif download_type == 'audio':
            download_url, format_type = ytmp4_service.get_best_audio_download(key, video_id)
            return jsonify({
                "status": True,
                "download_url": download_url,
                "format": format_type,
                "type": "audio",
                "source": "telegram" if "telegram" in download_url else "external"
            })
        else:
            return jsonify({"status": False, "message": "Invalid download type"}), 400
    
    except Exception as e:
        logging.error(f"Error in get_download_links: {str(e)}")
        return jsonify({"status": False, "message": str(e)}), 500

@app.route('/api/ytmp4')
def api_ytmp4():
    """Legacy endpoint for backward compatibility"""
    url = request.args.get("url")
    if not url:
        return jsonify({"status": False, "message": "Missing YouTube URL"}), 400
    
    try:
        info = ytmp4_service.get_info(url)
        download_url, selected_quality = ytmp4_service.get_best_quality_download(info['key'])
        
        return jsonify({
            "status": True,
            "title": info["title"],
            "duration": info["duration"],
            "thumbnail": info["thumbnail"],
            "quality": selected_quality,
            "download_url": download_url
        })
    except Exception as e:
        logging.error(f"Error in legacy api_ytmp4: {str(e)}")
        return jsonify({"status": False, "message": str(e)}), 500

@app.route('/api/cache-stats')
def cache_stats():
    """Get cache statistics for monitoring"""
    cache_stats = cache_manager.get_stats()
    db_stats = db_manager.get_stats()
    
    return jsonify({
        "cache": cache_stats,
        "database": db_stats,
        "total_cached_videos": db_stats["videos_with_telegram_video"] + db_stats["videos_with_telegram_audio"]
    })

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
