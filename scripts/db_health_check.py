# scripts/db_health_check.py
import os
import time
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_database_connection(max_retries=5, retry_delay=5):
    """Check database connection with retries"""
    DATABASE_URL = os.getenv("DATABASE_URL")
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    
    for attempt in range(max_retries):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                logger.info(f"✅ Database connected (attempt {attempt + 1})")
                return True
        except OperationalError as e:
            logger.warning(f"⚠️ Database connection failed (attempt {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                logger.error("❌ Database connection failed after all retries")
                return False
    return False

if __name__ == "__main__":
    check_database_connection()