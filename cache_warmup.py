import asyncio
import logging
import json
from app.core.database import SessionLocal
from app.models.room import Room, RoomStatus
from app.models.hotel import Hotel
from app.utils.cache import redis_client

logger = logging.getLogger(__name__)

async def warmup_cache():
    """Warm up cache with frequently accessed data"""
    logger.info("🔥 Warming up cache...")
    
    db = SessionLocal()
    
    try:
        # Cache all hotels
        hotels = db.query(Hotel).filter(Hotel.is_active == True).all()
        for hotel in hotels:
            cache_key = f"hotel:{hotel.id}"
            hotel_data = {
                "id": hotel.id,
                "name": hotel.name,
                "address": hotel.address,
                "phone": hotel.phone,
                "email": hotel.email
            }
            redis_client.setex(cache_key, 300, json.dumps(hotel_data))
        logger.info(f"  ✅ Cached {len(hotels)} hotels")
        
        # Cache room counts by hotel
        from sqlalchemy import func
        room_counts = db.query(
            Room.hotel_id, 
            func.count(Room.id).label('count')
        ).filter(Room.status == RoomStatus.CLEAN).group_by(Room.hotel_id).all()
        
        for hotel_id, count in room_counts:
            redis_client.setex(f"hotel:{hotel_id}:clean_rooms", 60, str(count))
        logger.info(f"  ✅ Cached room counts for {len(room_counts)} hotels")
        
    except Exception as e:
        logger.error(f"Cache warmup failed: {e}")
    finally:
        db.close()
    
    logger.info("✅ Cache warmup complete!")
