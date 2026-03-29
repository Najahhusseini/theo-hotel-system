# scripts/migrate_to_supabase.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
import getpass

# Import models at module level
from app.core.database import Base
from app.models import *
from app.models.user import User, UserRole
from app.utils.security import get_password_hash
from sqlalchemy.orm import Session

def get_supabase_url():
    """Get Supabase connection URL from user"""
    print("\n🔐 Supabase Database Connection")
    print("="*50)
    print("You need to provide your Supabase connection details:")
    print("1. Go to your Supabase project → Settings → Database")
    print("2. Copy the Connection string (URI)")
    print("3. It should look like: postgresql://postgres:password@db.xxxxx.supabase.co:5432/postgres")
    print("="*50)
    
    url = input("\nEnter your Supabase connection string: ").strip()
    
    # Test connection
    try:
        engine = create_engine(url, pool_pre_ping=True)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()
            print(f"✅ Connected to PostgreSQL: {version[0][:50]}...")
        return url
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return None

def migrate_schema(db_url):
    """Create all tables in Supabase"""
    print("\n📦 Creating database schema...")
    print("="*50)
    
    engine = create_engine(db_url, pool_pre_ping=True)
    
    with engine.connect() as conn:
        # Enable UUID extension
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";"))
        conn.commit()
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("✅ All tables created successfully!")
    
    # Create admin user
    session = Session(engine)
    admin = session.query(User).filter(User.username == "admin").first()
    if not admin:
        admin = User(
            username="admin",
            email="admin@theo.com",
            password_hash=get_password_hash("Admin123!"),
            first_name="System",
            last_name="Administrator",
            role=UserRole.SUPER_ADMIN,
            is_active=True
        )
        session.add(admin)
        session.commit()
        print("✅ Admin user created!")
    else:
        print("⚠️ Admin user already exists")
    session.close()
    
    print("\n✅ Schema migration complete!")

def verify_tables(db_url):
    """Verify all tables were created"""
    print("\n🔍 Verifying tables...")
    print("="*50)
    
    engine = create_engine(db_url, pool_pre_ping=True)
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """))
        
        tables = [row[0] for row in result]
        print(f"Found {len(tables)} tables:")
        for table in tables:
            print(f"  ✅ {table}")
    
    print("\n✅ Verification complete!")

if __name__ == "__main__":
    print("\n" + "🚀"*20)
    print("   THEO SUPABASE MIGRATION TOOL")
    print("🚀"*20)
    
    db_url = get_supabase_url()
    if db_url:
        migrate_schema(db_url)
        verify_tables(db_url)
        print("\n" + "🎉"*20)
        print("   MIGRATION COMPLETE!")
        print("🎉"*20)
        print("\nSave this connection string for your .env file:")
        print(f"DATABASE_URL={db_url}")