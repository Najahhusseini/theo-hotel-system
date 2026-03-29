# scripts/add_indexes.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import engine
from sqlalchemy import text, inspect

def add_indexes():
    """Add database indexes for better query performance"""
    
    print("🔍 Adding database indexes...")
    print("="*50)
    
    with engine.connect() as conn:
        # Check if indexes already exist
        inspector = inspect(engine)
        existing_indexes = [idx['name'] for idx in inspector.get_indexes('reservations')]
        
        # Indexes for reservations table
        if 'idx_reservations_dates' not in existing_indexes:
            conn.execute(text("""
                CREATE INDEX idx_reservations_dates 
                ON reservations(check_in_date, check_out_date)
            """))
            print("✅ Created index: idx_reservations_dates")
        else:
            print("⚠️ Index already exists: idx_reservations_dates")
        
        if 'idx_reservations_status' not in existing_indexes:
            conn.execute(text("""
                CREATE INDEX idx_reservations_status 
                ON reservations(status)
            """))
            print("✅ Created index: idx_reservations_status")
        
        if 'idx_reservations_guest' not in existing_indexes:
            conn.execute(text("""
                CREATE INDEX idx_reservations_guest 
                ON reservations(guest_id)
            """))
            print("✅ Created index: idx_reservations_guest")
        
        # Indexes for rooms table
        inspector = inspect(engine)
        existing_indexes = [idx['name'] for idx in inspector.get_indexes('rooms')]
        
        if 'idx_rooms_status' not in existing_indexes:
            conn.execute(text("""
                CREATE INDEX idx_rooms_status 
                ON rooms(status)
            """))
            print("✅ Created index: idx_rooms_status")
        
        if 'idx_rooms_hotel' not in existing_indexes:
            conn.execute(text("""
                CREATE INDEX idx_rooms_hotel 
                ON rooms(hotel_id)
            """))
            print("✅ Created index: idx_rooms_hotel")
        
        # Indexes for guests table
        inspector = inspect(engine)
        existing_indexes = [idx['name'] for idx in inspector.get_indexes('guests')]
        
        if 'idx_guests_email' not in existing_indexes:
            conn.execute(text("""
                CREATE INDEX idx_guests_email 
                ON guests(email)
            """))
            print("✅ Created index: idx_guests_email")
        
        if 'idx_guests_loyalty' not in existing_indexes:
            conn.execute(text("""
                CREATE INDEX idx_guests_loyalty 
                ON guests(loyalty_level)
            """))
            print("✅ Created index: idx_guests_loyalty")
        
        # Indexes for transactions table
        inspector = inspect(engine)
        existing_indexes = [idx['name'] for idx in inspector.get_indexes('transactions')]
        
        if 'idx_transactions_folio' not in existing_indexes:
            conn.execute(text("""
                CREATE INDEX idx_transactions_folio 
                ON transactions(folio_id)
            """))
            print("✅ Created index: idx_transactions_folio")
        
        if 'idx_transactions_type' not in existing_indexes:
            conn.execute(text("""
                CREATE INDEX idx_transactions_type 
                ON transactions(transaction_type)
            """))
            print("✅ Created index: idx_transactions_type")
        
        # Indexes for housekeeping_tasks table
        inspector = inspect(engine)
        existing_indexes = [idx['name'] for idx in inspector.get_indexes('housekeeping_tasks')]
        
        if 'idx_tasks_status' not in existing_indexes:
            conn.execute(text("""
                CREATE INDEX idx_tasks_status 
                ON housekeeping_tasks(status)
            """))
            print("✅ Created index: idx_tasks_status")
        
        if 'idx_tasks_assigned' not in existing_indexes:
            conn.execute(text("""
                CREATE INDEX idx_tasks_assigned 
                ON housekeeping_tasks(assigned_to_id)
            """))
            print("✅ Created index: idx_tasks_assigned")
        
        # Indexes for maintenance_requests table
        inspector = inspect(engine)
        existing_indexes = [idx['name'] for idx in inspector.get_indexes('maintenance_requests')]
        
        if 'idx_maintenance_status' not in existing_indexes:
            conn.execute(text("""
                CREATE INDEX idx_maintenance_status 
                ON maintenance_requests(status)
            """))
            print("✅ Created index: idx_maintenance_status")
        
        if 'idx_maintenance_priority' not in existing_indexes:
            conn.execute(text("""
                CREATE INDEX idx_maintenance_priority 
                ON maintenance_requests(priority)
            """))
            print("✅ Created index: idx_maintenance_priority")
        
        conn.commit()
    
    print("="*50)
    print("✅ All indexes added successfully!")

if __name__ == "__main__":
    add_indexes()