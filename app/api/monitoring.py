from fastapi import APIRouter, Depends
from app.core.database import get_pool_status
from app.utils.cache import get_cache_stats
from app.utils.dependencies import require_super_admin

router = APIRouter(prefix="/monitoring", tags=["monitoring"])

@router.get("/db-pool")
def get_db_pool_status(current_user=Depends(require_super_admin)):
    """Get database connection pool status"""
    return get_pool_status()

@router.get("/cache-stats")
def get_cache_status(current_user=Depends(require_super_admin)):
    """Get Redis cache statistics"""
    try:
        import redis
        from app.utils.cache import redis_client
        info = redis_client.info("stats")
        return {
            "total_commands_processed": info.get("total_commands_processed", 0),
            "keyspace_hits": info.get("keyspace_hits", 0),
            "keyspace_misses": info.get("keyspace_misses", 0),
            "hit_rate": info.get("keyspace_hits", 0) / (info.get("keyspace_hits", 0) + info.get("keyspace_misses", 1)) * 100,
            "connected_clients": info.get("connected_clients", 0),
            "used_memory_human": info.get("used_memory_human", "0")
        }
    except Exception as e:
        return {"error": str(e)}
