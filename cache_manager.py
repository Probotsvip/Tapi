import time
import threading
from typing import Any, Optional

class CacheManager:
    def __init__(self):
        self._cache = {}
        self._lock = threading.RLock()
        self._stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'total_requests': 0
        }

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            self._stats['total_requests'] += 1
            
            if key not in self._cache:
                self._stats['misses'] += 1
                return None
            
            entry = self._cache[key]
            current_time = time.time()
            
            # Check if entry has expired
            if current_time > entry['expires_at']:
                del self._cache[key]
                self._stats['misses'] += 1
                return None
            
            self._stats['hits'] += 1
            return entry['value']

    def set(self, key: str, value: Any, ttl: int = 3600):
        """Set cache entry with TTL in seconds"""
        with self._lock:
            self._stats['sets'] += 1
            expires_at = time.time() + ttl
            
            self._cache[key] = {
                'value': value,
                'expires_at': expires_at,
                'created_at': time.time()
            }

    def delete(self, key: str):
        with self._lock:
            if key in self._cache:
                del self._cache[key]

    def clear(self):
        with self._lock:
            self._cache.clear()
            self._stats = {
                'hits': 0,
                'misses': 0,
                'sets': 0,
                'total_requests': 0
            }

    def get_stats(self):
        with self._lock:
            hit_rate = 0
            if self._stats['total_requests'] > 0:
                hit_rate = (self._stats['hits'] / self._stats['total_requests']) * 100
            
            return {
                'cache_size': len(self._cache),
                'hits': self._stats['hits'],
                'misses': self._stats['misses'],
                'sets': self._stats['sets'],
                'total_requests': self._stats['total_requests'],
                'hit_rate': round(hit_rate, 2)
            }

    def cleanup_expired(self):
        """Remove expired entries"""
        with self._lock:
            current_time = time.time()
            expired_keys = []
            
            for key, entry in self._cache.items():
                if current_time > entry['expires_at']:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self._cache[key]
            
            return len(expired_keys)
