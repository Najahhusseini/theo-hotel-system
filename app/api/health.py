# app/api/health.py
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from sqlalchemy import text
import os
import shutil
import platform
import time
from datetime import datetime, timedelta
import psutil

from app.core.database import get_db, get_pool_status, get_connection_stats, check_read_replica_connection
from app.utils.cache import redis_client, get_cache_stats

router = APIRouter(prefix="/health", tags=["health"], include_in_schema=True)

@router.get("")
async def health_check(db: Session = Depends(get_db), request: Request = None):
    """Comprehensive health check"""
    
    start_time = time.time()
    
    status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": os.getenv("APP_VERSION", "1.0.0"),
        "environment": os.getenv("ENVIRONMENT", "development"),
        "uptime_seconds": get_uptime(),
        "services": {},
        "system": {}
    }
    
    # ==================== DATABASE ====================
    try:
        # Test connection
        db.execute(text("SELECT 1"))
        db.execute(text("SELECT version()"))
        
        # Get pool stats
        pool_stats = get_connection_stats()
        
        status["services"]["database"] = {
            "status": "healthy",
            "pool": pool_stats,
            "latency_ms": round((time.time() - start_time) * 1000, 2)
        }
        
        # Warning if pool is getting full
        if pool_stats.get("usage_percent", 0) > 80:
            status["status"] = "degraded"
            status["services"]["database"]["warning"] = f"Pool usage at {pool_stats['usage_percent']}%"
            
    except Exception as e:
        status["status"] = "degraded"
        status["services"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # ==================== READ REPLICA ====================
    replica_status = check_read_replica_connection()
    if replica_status.get("enabled"):
        status["services"]["read_replica"] = replica_status
        if replica_status.get("status") == "unhealthy":
            status["status"] = "degraded"
    
    # ==================== REDIS ====================
    try:
        redis_client.ping()
        cache_stats = get_cache_stats()
        status["services"]["redis"] = {
            "status": "healthy",
            "connected_clients": cache_stats.get("connected_clients", 0),
            "hit_rate": cache_stats.get("hit_rate", 0),
            "memory_used": cache_stats.get("used_memory_human", "0")
        }
        
        # Warning if cache hit rate is low
        if cache_stats.get("hit_rate", 100) < 50:
            status["status"] = "degraded"
            status["services"]["redis"]["warning"] = f"Low cache hit rate: {cache_stats['hit_rate']}%"
            
    except Exception as e:
        status["status"] = "degraded"
        status["services"]["redis"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # ==================== DISK SPACE ====================
    try:
        disk = shutil.disk_usage("/")
        free_percent = (disk.free / disk.total) * 100
        
        status["system"]["disk"] = {
            "total_gb": round(disk.total / (1024**3), 2),
            "used_gb": round((disk.total - disk.free) / (1024**3), 2),
            "free_gb": round(disk.free / (1024**3), 2),
            "free_percent": round(free_percent, 2)
        }
        
        if free_percent < 10:
            status["status"] = "critical"
            status["system"]["disk"]["warning"] = "Critical disk space!"
        elif free_percent < 20:
            status["status"] = "degraded"
            status["system"]["disk"]["warning"] = "Low disk space"
            
    except Exception as e:
        status["system"]["disk"] = {"error": str(e)}
    
    # ==================== MEMORY ====================
    try:
        memory = psutil.virtual_memory()
        status["system"]["memory"] = {
            "total_gb": round(memory.total / (1024**3), 2),
            "available_gb": round(memory.available / (1024**3), 2),
            "percent_used": memory.percent
        }
        
        if memory.percent > 90:
            status["status"] = "critical"
        elif memory.percent > 80:
            status["status"] = "degraded"
            
    except Exception as e:
        status["system"]["memory"] = {"error": str(e)}
    
    # ==================== CPU ====================
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        status["system"]["cpu"] = {
            "percent_used": cpu_percent,
            "cores": psutil.cpu_count()
        }
        
        if cpu_percent > 90:
            status["status"] = "critical"
        elif cpu_percent > 80:
            status["status"] = "degraded"
            
    except Exception as e:
        status["system"]["cpu"] = {"error": str(e)}
    
    # ==================== RESPONSE TIME ====================
    response_time = round((time.time() - start_time) * 1000, 2)
    status["response_time_ms"] = response_time
    
    if response_time > 1000:
        status["status"] = "degraded"
        status["warning"] = f"Slow response time: {response_time}ms"
    
    return status

def get_uptime():
    """Get server uptime"""
    try:
        with open('/proc/uptime', 'r') as f:
            uptime_seconds = float(f.readline().split()[0])
            return int(uptime_seconds)
    except:
        return None

@router.get("/ready")
async def readiness_check(db: Session = Depends(get_db)):
    """Kubernetes readiness probe"""
    try:
        db.execute(text("SELECT 1"))
        redis_client.ping()
        return {"status": "ready", "timestamp": datetime.now().isoformat()}
    except:
        return {"status": "not ready"}, 503

@router.get("/live")
async def liveness_check():
    """Kubernetes liveness probe"""
    return {"status": "alive", "timestamp": datetime.now().isoformat()}