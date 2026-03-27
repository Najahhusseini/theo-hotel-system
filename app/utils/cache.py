# app/utils/cache.py
import redis
import json
import hashlib
from functools import wraps
from typing import Optional, Any, Callable
import os
import logging

logger = logging.getLogger(__name__)

# Redis client configuration
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    db=int(os.getenv("REDIS_DB", 0)),
    decode_responses=True,
    socket_connect_timeout=5,
    socket_timeout=5,
    retry_on_timeout=True
)

def cache_key(prefix: str, *args, **kwargs) -> str:
    """Generate a consistent cache key from arguments"""
    key_parts = [prefix]
    key_parts.extend(str(arg) for arg in args)
    key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
    key_string = ":".join(key_parts)
    return hashlib.md5(key_string.encode()).hexdigest()

def cached(ttl: int = 300, key_prefix: str = ""):
    """Cache decorator for functions"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            key = cache_key(key_prefix or func.__name__, *args, **kwargs)
            
            # Try to get from cache
            try:
                cached_data = redis_client.get(key)
                if cached_data:
                    logger.debug(f"Cache hit for key: {key}")
                    return json.loads(cached_data)
                logger.debug(f"Cache miss for key: {key}")
            except Exception as e:
                logger.warning(f"Redis error on get: {e}")
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Store in cache
            try:
                redis_client.setex(key, ttl, json.dumps(result))
                logger.debug(f"Cached result for key: {key} (TTL: {ttl}s)")
            except Exception as e:
                logger.warning(f"Redis error on set: {e}")
            
            return result
        return wrapper
    return decorator

def invalidate_cache(pattern: str):
    """Invalidate all cache keys matching a pattern"""
    try:
        keys = redis_client.keys(f"*{pattern}*")
        if keys:
            redis_client.delete(*keys)
            logger.info(f"Invalidated {len(keys)} cache keys matching pattern: {pattern}")
            return len(keys)
        return 0
    except Exception as e:
        logger.error(f"Error invalidating cache: {e}")
        return 0

def clear_all_cache():
    """Clear all cache keys (use with caution)"""
    try:
        redis_client.flushdb()
        logger.warning("All cache cleared!")
        return True
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        return False

def get_cache_stats() -> dict:
    """Get cache statistics"""
    try:
        info = redis_client.info("stats")
        return {
            "total_commands_processed": info.get("total_commands_processed", 0),
            "total_connections_received": info.get("total_connections_received", 0),
            "keyspace_hits": info.get("keyspace_hits", 0),
            "keyspace_misses": info.get("keyspace_misses", 0),
            "hit_rate": info.get("keyspace_hits", 0) / (info.get("keyspace_hits", 0) + info.get("keyspace_misses", 1)) * 100
        }
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        return {}