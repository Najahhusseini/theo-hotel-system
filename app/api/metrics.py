# app/api/metrics.py
from fastapi import APIRouter, Request, Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST, Counter, Histogram, Gauge
import time
import psutil
import os

router = APIRouter(prefix="/metrics", tags=["metrics"])

# Define metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint'],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10)
)

ACTIVE_CONNECTIONS = Gauge(
    'active_connections',
    'Number of active WebSocket connections'
)

DB_POOL_SIZE = Gauge(
    'db_pool_size',
    'Database connection pool size'
)

CACHE_HITS = Counter(
    'cache_hits_total',
    'Total cache hits'
)

CACHE_MISSES = Counter(
    'cache_misses_total',
    'Total cache misses'
)

# System metrics
CPU_USAGE = Gauge('cpu_usage_percent', 'CPU usage percentage')
MEMORY_USAGE = Gauge('memory_usage_percent', 'Memory usage percentage')
DISK_USAGE = Gauge('disk_usage_percent', 'Disk usage percentage')

@router.get("")
async def get_metrics():
    """Prometheus metrics endpoint"""
    # Update system metrics
    CPU_USAGE.set(psutil.cpu_percent())
    MEMORY_USAGE.set(psutil.virtual_memory().percent)
    
    try:
        disk = psutil.disk_usage('/')
        DISK_USAGE.set((disk.used / disk.total) * 100)
    except:
        pass
    
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )

@router.get("/system")
async def get_system_metrics():
    """Detailed system metrics in JSON format"""
    return {
        "cpu": {
            "percent": psutil.cpu_percent(interval=1),
            "cores": psutil.cpu_count(),
            "frequency": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None
        },
        "memory": psutil.virtual_memory()._asdict(),
        "disk": psutil.disk_usage('/')._asdict(),
        "network": psutil.net_io_counters()._asdict()
    }