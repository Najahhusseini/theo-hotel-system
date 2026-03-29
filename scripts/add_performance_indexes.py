# scripts/add_performance_indexes.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import engine
from sqlalchemy import text

def add_performance_indexes():
    """Add indexes to speed up slow queries"""
    
    print("🔍 Adding performance indexes...")
    print("="*50)
    
    with engine.connect() as conn:
        # Reservations table indexes
        print("\n📅 Reservations indexes:")
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_reservations_check_in 
            ON reservations(check_in_date)
        """))
        print("  ✅ idx_reservations_check_in")
        
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_reservations_check_out 
            ON reservations(check_out_date)
        """))
        print("  ✅ idx_reservations_check_out")
        
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_reservations_status_date 
            ON reservations(status, check_in_date)
        """))
        print("  ✅ idx_reservations_status_date")
        
        # Rooms table indexes
        print("\n🛏️ Rooms indexes:")
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_rooms_hotel_status 
            ON rooms(hotel_id, status)
        """))
        print("  ✅ idx_rooms_hotel_status")
        
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_rooms_type_price 
            ON rooms(room_type, price_per_night)
        """))
        print("  ✅ idx_rooms_type_price")
        
        # Guests table indexes
        print("\n👤 Guests indexes:")
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_guests_name 
            ON guests(first_name, last_name)
        """))
        print("  ✅ idx_guests_name")
        
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_guests_loyalty_stays 
            ON guests(loyalty_level, total_stays)
        """))
        print("  ✅ idx_guests_loyalty_stays")
        
        # Transactions table indexes
        print("\n💰 Transactions indexes:")
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_transactions_folio_date 
            ON transactions(folio_id, created_at)
        """))
        print("  ✅ idx_transactions_folio_date")
        
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_transactions_type_amount 
            ON transactions(transaction_type, amount)
        """))
        print("  ✅ idx_transactions_type_amount")
        
        conn.commit()
    
    print("\n" + "="*50)
    print("✅ All performance indexes added!")

if __name__ == "__main__":
    add_performance_indexes()