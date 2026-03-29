# app/core/database.py
from dotenv import load_dotenv
load_dotenv()

import os
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import logging
import time
from functools import wraps

logger = logging.getLogger(__name__)

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable not set")

print(f"Connecting to: {DATABASE_URL[:50]}...")

# ==================== CONNECTION POOL SETUP ====================
# Optimized pool settings for production
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,           # Verify connection before using
    pool_size=20,                  # Max connections in pool
    max_overflow=40,               # Extra connections when pool is full
    pool_timeout=30,               # Seconds to wait for connection
    pool_recycle=3600,             # Recycle connections after 1 hour
    echo=False,                    # Don't log SQL in production
    connect_args={
        "connect_timeout": 10,     # Connection timeout in seconds
        "keepalives": 1,           # Enable TCP keepalives
        "keepalives_idle": 30,     # Seconds before sending keepalive
        "keepalives_interval": 10, # Seconds between keepalives
        "keepalives_count": 5      # Failed keepalives before closing
    }
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ==================== READ/WRITE SPLITTING (Optional) ====================
# For production with read replicas
READ_DATABASE_URL = os.getenv("READ_DATABASE_URL", DATABASE_URL)
WRITE_DATABASE_URL = os.getenv("WRITE_DATABASE_URL", DATABASE_URL)

# Create separate engines for read and write if configured
if READ_DATABASE_URL != WRITE_DATABASE_URL:
    read_engine = create_engine(
        READ_DATABASE_URL,
        pool_pre_ping=True,
        pool_size=30,              # More connections for reads
        max_overflow=60,
        pool_recycle=3600,
        echo=False
    )
    write_engine = engine  # Use main engine for writes
    READ_REPLICA_ENABLED = True
else:
    read_engine = engine
    write_engine = engine
    READ_REPLICA_ENABLED = False

# ==================== SESSION FACTORIES ====================
def get_db():
    """Get database session for writes (default)"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_read_db():
    """Get database session for reads (can use read replica)"""
    if READ_REPLICA_ENABLED:
        db = SessionLocal(bind=read_engine)
    else:
        db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_write_db():
    """Get database session for writes (always primary)"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ==================== RETRY LOGIC ====================
def retry_on_db_failure(max_retries=3, delay=1, backoff=2):
    """
    Decorator to retry database operations on failure
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            current_delay = delay
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    retries += 1
                    if retries >= max_retries:
                        raise
                    
                    logger.warning(
                        f"Database operation failed (attempt {retries}/{max_retries}): {e}. "
                        f"Retrying in {current_delay}s..."
                    )
                    time.sleep(current_delay)
                    current_delay *= backoff
            return None
        return wrapper
    return decorator

# ==================== HEALTH CHECK ====================

def check_db_connection():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))  # Already has text() - good
            return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False

def check_read_replica_connection():
    """Check read replica connection health"""
    if not READ_REPLICA_ENABLED:
        return {"enabled": False}
    
    try:
        with read_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            return {"enabled": True, "status": "healthy"}
    except Exception as e:
        logger.error(f"Read replica connection failed: {e}")
        return {"enabled": True, "status": "unhealthy", "error": str(e)}

# ==================== POOL STATUS ====================
def get_pool_status():
    """Get current connection pool status"""
    try:
        pool = engine.pool
        return {
            "size": pool.size(),
            "checked_in": pool.checkedin(),
            "overflow": pool.overflow(),
            "checked_out": pool.checkedout(),
            "read_replica_enabled": READ_REPLICA_ENABLED,
            "read_replica_status": check_read_replica_connection()
        }
    except Exception as e:
        logger.error(f"Error getting pool status: {e}")
        return {"error": str(e)}

# ==================== CONNECTION MONITORING ====================
def get_connection_stats():
    """Get detailed connection statistics"""
    try:
        pool = engine.pool
        
        # Different pool implementations have different methods
        total = 0
        max_connections = pool.size() + pool._max_overflow
        
        try:
            total = pool.total()
        except AttributeError:
            # Some pool implementations don't have total() method
            total = pool.size() + pool.overflow()
        
        checked_out = pool.checkedout()
        usage_percent = round((checked_out / max_connections) * 100, 2) if max_connections > 0 else 0
        
        return {
            "pool_size": pool.size(),
            "checked_in": pool.checkedin(),
            "overflow": pool.overflow(),
            "total_connections": total,
            "checked_out": checked_out,
            "max_connections": max_connections,
            "usage_percent": usage_percent,
            "read_replica_enabled": READ_REPLICA_ENABLED
        }
    except Exception as e:
        logger.error(f"Error getting connection stats: {e}")
        return {}