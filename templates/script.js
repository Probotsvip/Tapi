class YouTubeDownloader {
    constructor() {
        this.currentVideoKey = null;
        this.currentVideoId = null;
        this.initializeEventListeners();
        this.loadCacheStats();
        
        // Auto-refresh cache stats every 10 seconds
        setInterval(() => this.loadCacheStats(), 10000);
    }

    initializeEventListeners() {
        document.getElementById('downloadForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.analyzeVideo();
        });

        document.getElementById('downloadVideoBtn').addEventListener('click', () => {
            this.downloadContent('video');
        });

        document.getElementById('downloadAudioBtn').addEventListener('click', () => {
            this.downloadContent('audio');
        });
    }

    showAlert(message, type = 'info') {
        const alertContainer = document.getElementById('alertContainer');
        const alertId = 'alert_' + Date.now();
        
        const alertHTML = `
            <div class="alert alert-${type} alert-dismissible fade show fade-in" id="${alertId}" role="alert">
                <i class="fas fa-${type === 'success' ? 'check' : type === 'danger' ? 'exclamation-triangle' : 'info'}-circle"></i>
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        alertContainer.insertAdjacentHTML('beforeend', alertHTML);
        
        // Auto-remove alert after 5 seconds
        setTimeout(() => {
            const alert = document.getElementById(alertId);
            if (alert) {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }
        }, 5000);
    }

    setButtonLoading(buttonId, isLoading) {
        const button = document.getElementById(buttonId);
        const originalText = button.innerHTML;
        
        if (isLoading) {
            button.disabled = true;
            button.innerHTML = `<span class="loading-spinner"></span> Loading...`;
            button.dataset.originalText = originalText;
        } else {
            button.disabled = false;
            button.innerHTML = button.dataset.originalText || originalText;
        }
    }

    async analyzeVideo() {
        const url = document.getElementById('videoUrl').value.trim();
        
        if (!url) {
            this.showAlert('Please enter a YouTube URL', 'warning');
            return;
        }

        // Validate YouTube URL
        const youtubeRegex = /^(https?:\/\/)?(www\.)?(youtube\.com\/watch\?v=|youtu\.be\/)/;
        if (!youtubeRegex.test(url)) {
            this.showAlert('Please enter a valid YouTube URL', 'warning');
            return;
        }

        this.setButtonLoading('analyzeBtn', true);
        document.getElementById('videoInfo').style.display = 'none';

        try {
            const startTime = Date.now();
            const response = await fetch('/api/video-info', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ url })
            });

            const result = await response.json();
            const responseTime = Date.now() - startTime;

            if (result.status) {
                this.currentVideoKey = result.key;
                this.currentVideoId = result.video_id;
                this.displayVideoInfo(result);
                this.showAlert(`Video analyzed in ${responseTime}ms`, 'success');
            } else {
                this.showAlert(result.message || 'Failed to analyze video', 'danger');
            }
        } catch (error) {
            console.error('Analysis error:', error);
            this.showAlert('Network error. Please try again.', 'danger');
        } finally {
            this.setButtonLoading('analyzeBtn', false);
        }
    }

    displayVideoInfo(info) {
        document.getElementById('thumbnail').src = info.thumbnail;
        document.getElementById('videoTitle').textContent = info.title;
        document.getElementById('videoDuration').textContent = info.duration;
        
        const videoInfoCard = document.getElementById('videoInfo');
        videoInfoCard.style.display = 'block';
        videoInfoCard.classList.add('fade-in');
    }

    async downloadContent(type) {
        if (!this.currentVideoKey) {
            this.showAlert('Please analyze a video first', 'warning');
            return;
        }

        const buttonId = type === 'video' ? 'downloadVideoBtn' : 'downloadAudioBtn';
        this.setButtonLoading(buttonId, true);
        this.showDownloadProgress(true);

        try {
            const startTime = Date.now();
            const response = await fetch('/api/download', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    key: this.currentVideoKey,
                    video_id: this.currentVideoId,
                    type: type
                })
            });

            const result = await response.json();
            const responseTime = Date.now() - startTime;

            if (result.status) {
                // Create download link
                const downloadLink = document.createElement('a');
                downloadLink.href = result.download_url;
                downloadLink.download = '';
                downloadLink.target = '_blank';
                downloadLink.click();

                const formatInfo = type === 'video' ? 
                    `${result.quality}p HD video` : 
                    `${result.format}${result.format && result.format.match(/^\d+$/) ? 'kbps' : ''} HD audio`;
                
                const sourceIcon = result.source === 'telegram' ? '⚡' : '🌐';
                const sourceText = result.source === 'telegram' ? 'Telegram Cache' : 'Live';
                
                this.showAlert(`${sourceIcon} ${formatInfo} from ${sourceText} (${responseTime}ms)`, 'success');
            } else {
                this.showAlert(result.message || `Failed to get ${type} download link`, 'danger');
            }
        } catch (error) {
            console.error('Download error:', error);
            this.showAlert('Network error. Please try again.', 'danger');
        } finally {
            this.setButtonLoading(buttonId, false);
            this.showDownloadProgress(false);
        }
    }

    showDownloadProgress(show) {
        const progressCard = document.getElementById('downloadProgress');
        if (show) {
            progressCard.style.display = 'block';
            progressCard.classList.add('fade-in');
        } else {
            setTimeout(() => {
                progressCard.style.display = 'none';
            }, 1000);
        }
    }

    async loadCacheStats() {
        try {
            const response = await fetch('/api/cache-stats');
            const stats = await response.json();
            
            document.getElementById('hitRate').textContent = `${stats.cache?.hit_rate || 0}%`;
            document.getElementById('totalRequests').textContent = stats.cache?.total_requests || 0;
            document.getElementById('cacheSize').textContent = stats.total_cached_videos || 0;
        } catch (error) {
            console.error('Failed to load cache stats:', error);
        }
    }
}

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    new YouTubeDownloader();
});

// Add some utility functions for better UX
document.addEventListener('keydown', (e) => {
    // Allow Ctrl+Enter or Cmd+Enter to submit form
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        const form = document.getElementById('downloadForm');
        if (form) {
            form.dispatchEvent(new Event('submit'));
        }
    }
});

// Auto-focus URL input on page load
window.addEventListener('load', () => {
    const urlInput = document.getElementById('videoUrl');
    if (urlInput) {
        urlInput.focus();
    }
});
