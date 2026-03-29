# app/utils/cache.py
import os
import redis
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Get Redis configuration from environment
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)
REDIS_DB = int(os.getenv("REDIS_DB", 0))

# Try to get full URL first, then fallback to individual variables
REDIS_URL = os.getenv("REDIS_URL")

if REDIS_URL:
    try:
        redis_client = redis.Redis.from_url(
            REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True
        )
        # Test connection
        redis_client.ping()
        logger.info("Redis connected via URL")
    except Exception as e:
        logger.warning(f"Redis URL connection failed: {e}, trying individual variables")
        redis_client = None
else:
    redis_client = None

# Fallback to individual variables if URL didn't work
if not redis_client:
    try:
        redis_client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            password=REDIS_PASSWORD if REDIS_PASSWORD else None,
            db=REDIS_DB,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True
        )
        redis_client.ping()
        logger.info(f"Redis connected via host: {REDIS_HOST}:{REDIS_PORT}")
    except Exception as e:
        logger.warning(f"Redis connection failed: {e}")
        redis_client = None

def get_cache_stats():
    """Get Redis cache statistics"""
    if not redis_client:
        return {"error": "Redis not available"}
    try:
        info = redis_client.info("stats")
        hits = info.get("keyspace_hits", 0)
        misses = info.get("keyspace_misses", 0)
        total = hits + misses
        return {
            "total_commands_processed": info.get("total_commands_processed", 0),
            "keyspace_hits": hits,
            "keyspace_misses": misses,
            "hit_rate": round(hits / total * 100, 2) if total > 0 else 0,
            "connected_clients": info.get("connected_clients", 0),
            "used_memory_human": info.get("used_memory_human", "0")
        }
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        return {"error": str(e)}