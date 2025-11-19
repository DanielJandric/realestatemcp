"""
Simple in-memory cache for MCP server to reduce Supabase API calls
"""
import time
from typing import Any, Optional, Callable
from functools import wraps
import json
import hashlib

class SimpleCache:
    """Simple TTL-based cache"""
    
    def __init__(self, ttl_seconds: int = 300):
        self.cache = {}
        self.ttl = ttl_seconds
    
    def _make_key(self, func_name: str, args: tuple, kwargs: dict) -> str:
        """Generate cache key from function name and arguments"""
        key_data = {
            'func': func_name,
            'args': args,
            'kwargs': kwargs
        }
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired"""
        if key in self.cache:
            value, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                return value
            else:
                # Expired, remove it
                del self.cache[key]
        return None
    
    def set(self, key: str, value: Any):
        """Set value in cache with current timestamp"""
        self.cache[key] = (value, time.time())
    
    def invalidate(self, pattern: str = None):
        """Invalidate cache entries matching pattern or all if no pattern"""
        if pattern is None:
            self.cache.clear()
        else:
            keys_to_delete = [k for k in self.cache.keys() if pattern in k]
            for key in keys_to_delete:
                del self.cache[key]
    
    def stats(self) -> dict:
        """Get cache statistics"""
        total = len(self.cache)
        expired = sum(1 for _, (_, ts) in self.cache.items() 
                     if time.time() - ts >= self.ttl)
        return {
            'total_entries': total,
            'active_entries': total - expired,
            'expired_entries': expired,
            'ttl_seconds': self.ttl
        }

# Global cache instance
_cache = SimpleCache(ttl_seconds=300)  # 5 minutes default

def cached(ttl: int = 300):
    """
    Decorator to cache function results
    
    Args:
        ttl: Time to live in seconds (default 300 = 5 minutes)
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = _cache._make_key(func.__name__, args, kwargs)
            
            # Try to get from cache
            cached_result = _cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            _cache.set(cache_key, result)
            return result
        
        return wrapper
    return decorator

def invalidate_cache(pattern: str = None):
    """Invalidate cache entries"""
    _cache.invalidate(pattern)

def get_cache_stats() -> dict:
    """Get cache statistics"""
    return _cache.stats()
