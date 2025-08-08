# Overview

This is an optimized YouTube video downloader web application built with Flask. The application allows users to input YouTube URLs, analyze video information, and download content in video or audio formats. It features a modern dark-themed web interface with real-time progress tracking, caching for improved performance, and integration with external YouTube processing services.

# User Preferences

Preferred communication style: Simple, everyday language.
Quality Priority: Always prioritize highest quality downloads - 1080p→720p→480p for video, 320kbps→MP3→M4A for audio.

# System Architecture

## Frontend Architecture
- **Technology**: HTML5, CSS3, JavaScript (ES6+), Bootstrap 5 with dark theme
- **Design Pattern**: Single Page Application (SPA) with dynamic content updates
- **UI Framework**: Bootstrap 5 for responsive design and components
- **JavaScript Architecture**: Class-based modular design with YouTubeDownloader class handling all client-side interactions
- **Real-time Features**: Auto-refreshing cache statistics and progress tracking
- **User Experience**: Loading states, alert notifications, and responsive design for mobile compatibility

## Backend Architecture
- **Framework**: Flask (Python) with modular service architecture
- **Design Pattern**: Service-oriented architecture with separation of concerns
- **Core Services**:
  - `OptimizedYtmp4Service`: Handles YouTube video processing and download link generation
  - `CacheManager`: Thread-safe in-memory caching with TTL support
- **API Design**: RESTful endpoints with JSON responses
- **Concurrency**: Thread-safe operations with locks and connection pooling
- **Error Handling**: Comprehensive exception handling with user-friendly error messages

## Data Storage Solutions
- **Primary Storage**: MongoDB Atlas cloud database for permanent data persistence
- **Smart Caching Strategy**: 3-tier caching system for ultra-fast responses
  - **Tier 1**: MongoDB lookup (fastest - local database query)
  - **Tier 2**: In-memory cache (fast - application memory)
  - **Tier 3**: External API call (slowest - only when needed)
- **Telegram Integration**: Automated file uploads to Telegram channel for permanent storage
- **Cache Features**: 
  - Time-to-live (TTL) expiration
  - Hit/miss statistics tracking
  - Thread-safe concurrent access with RLock
- **Session Management**: Flask sessions with configurable secret keys
- **Database Schema**: Videos collection with metadata, quality info, and Telegram URLs

## Authentication and Authorization
- **Security Model**: Minimal authentication (session-based)
- **Session Management**: Flask built-in sessions with environment-configurable secret keys
- **Access Control**: Open access model with no user authentication required
- **Security Considerations**: Basic input validation and error handling

## Performance Optimizations
- **Connection Pooling**: HTTP adapter with configurable pool sizes for external API calls
- **Caching Strategy**: Multi-level caching for CDN endpoints and video information
- **Concurrent Processing**: ThreadPoolExecutor for parallel operations with optimized timeouts
- **Retry Logic**: Configurable retry mechanisms for external service calls
- **Response Optimization**: Separated video info and download link endpoints for faster initial responses
- **JSON Parsing Enhancement**: Robust JSON parsing with extra data handling for encrypted responses
- **Sequential Audio Processing**: MP3/M4A formats tried sequentially first, then concurrent fallback for optimal speed
- **Error Recovery**: Improved error handling with detailed logging and graceful degradation

# External Dependencies

## Third-party Services
- **YouTube Processing API**: External ytmp4/savetube service for video information extraction and download link generation
- **CDN Service**: Dynamic CDN selection via `media.savetube.me/api/random-cdn` for load balancing
- **Encryption Service**: AES CBC mode decryption for processing encrypted API responses

## Python Libraries
- **Flask**: Web framework for HTTP handling and routing
- **Requests**: HTTP client library with session management and connection pooling
- **PyCryptodome**: AES encryption/decryption for API response processing
- **Threading**: Built-in Python threading for concurrent operations
- **Concurrent.futures**: Thread pool execution for parallel processing

## Frontend Libraries
- **Bootstrap 5**: CSS framework with dark theme support
- **Font Awesome 6**: Icon library for UI elements
- **Bootstrap JavaScript**: Modal dialogs, alerts, and interactive components

## Infrastructure Requirements
- **Python 3.x**: Runtime environment
- **Network Access**: Required for external API calls to YouTube processing services
- **Memory**: In-memory caching requires sufficient RAM for video metadata storage
- **Port Configuration**: Default Flask development server on port 5000

## API Integration Details
- **Encryption Protocol**: AES-256-CBC with hardcoded key for API response decryption
- **Timeout Configuration**: 5-10 second timeouts for external service calls
- **Rate Limiting**: Handled through caching and connection pooling
- **Error Recovery**: Automatic CDN failover and retry mechanisms