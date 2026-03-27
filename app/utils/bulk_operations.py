# app/utils/bulk_operations.py
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

def bulk_insert(db: Session, model, items: List[Dict[str, Any]], chunk_size: int = 100):
    """Bulk insert with chunking for performance"""
    total = len(items)
    inserted = 0
    
    for i in range(0, total, chunk_size):
        chunk = items[i:i + chunk_size]
        db.bulk_insert_mappings(model, chunk)
        db.commit()
        inserted += len(chunk)
        logger.info(f"Inserted {inserted}/{total} items")
    
    return inserted

def bulk_update(db: Session, model, items: List[Dict[str, Any]], key_field: str = "id"):
    """Bulk update records"""
    for item in items:
        db.query(model).filter(getattr(model, key_field) == item[key_field]).update(item)
    db.commit()