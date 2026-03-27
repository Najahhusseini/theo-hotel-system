# app/api/health.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import redis
import os
from datetime import datetime
import shutil
import platform
import psutil

from app.core.database import get_db
from app.utils.cache import redis_client, get_cache_stats

router = APIRouter(prefix="/health", tags=["health"])

@router.get("/")
async def health_check(db: Session = Depends(get_db)):
    """Comprehensive health check for all services"""
    
    status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": os.getenv("APP_VERSION", "1.0.0"),
        "environment": os.getenv("ENVIRONMENT", "development"),
        "services": {},
        "system": {}
    }
    
    # Check database
    try:
        db.execute("SELECT 1")
        status["services"]["database"] = {
            "status": "healthy",
            "type": "postgresql"
        }
    except Exception as e:
        status["services"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        status["status"] = "degraded"
    
    # Check Redis
    try:
        redis_client.ping()
        cache_stats = get_cache_stats()
        status["services"]["redis"] = {
            "status": "healthy",
            "hit_rate": f"{cache_stats.get('hit_rate', 0):.2f}%",
            "keyspace_hits": cache_stats.get("keyspace_hits", 0)
        }
    except Exception as e:
        status["services"]["redis"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        status["status"] = "degraded"
    
    # Check disk space
    try:
        disk = shutil.disk_usage("/")
        free_percent = (disk.free / disk.total) * 100
        status["system"]["disk"] = {
            "status": "healthy" if free_percent > 10 else "warning",
            "free_gb": round(disk.free / (1024**3), 2),
            "total_gb": round(disk.total / (1024**3), 2),
            "used_gb": round((disk.total - disk.free) / (1024**3), 2),
            "free_percent": round(free_percent, 2)
        }
    except Exception as e:
        status["system"]["disk"] = {"status": "unknown", "error": str(e)}
    
    # Check memory
    try:
        memory = psutil.virtual_memory()
        status["system"]["memory"] = {
            "status": "healthy" if memory.percent < 90 else "warning",
            "total_gb": round(memory.total / (1024**3), 2),
            "available_gb": round(memory.available / (1024**3), 2),
            "percent_used": memory.percent
        }
    except Exception as e:
        status["system"]["memory"] = {"status": "unknown", "error": str(e)}
    
    # Check CPU
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        status["system"]["cpu"] = {
            "status": "healthy" if cpu_percent < 80 else "warning",
            "percent_used": cpu_percent,
            "cores": psutil.cpu_count()
        }
    except Exception as e:
        status["system"]["cpu"] = {"status": "unknown", "error": str(e)}
    
    # System info
    status["system"]["info"] = {
        "platform": platform.system(),
        "platform_release": platform.release(),
        "python_version": platform.python_version(),
        "hostname": platform.node()
    }
    
    return status

@router.get("/ready")
async def readiness_check(db: Session = Depends(get_db)):
    """Kubernetes readiness probe"""
    try:
        db.execute("SELECT 1")
        redis_client.ping()
        return {"status": "ready", "timestamp": datetime.now().isoformat()}
    except Exception as e:
        return {"status": "not ready", "error": str(e)}, 503

@router.get("/live")
async def liveness_check():
    """Kubernetes liveness probe"""
    return {"status": "alive", "timestamp": datetime.now().isoformat()}