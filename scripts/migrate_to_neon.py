# scripts/migrate_to_neon.py
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.core.database import Base
from app.models import *
from app.models.user import User, UserRole
from app.utils.security import get_password_hash
from sqlalchemy.orm import Session
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("❌ DATABASE_URL not found in .env file")
    exit(1)

print("\n📦 Creating database schema in Neon...")
print("="*50)
print(f"Connecting to: {DATABASE_URL[:50]}...")

try:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    
    # Test connection
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version()"))
        version = result.fetchone()
        print(f"✅ Connected to: {version[0][:50]}...")
        
        # Enable UUID extension
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";"))
        conn.commit()
    
    # Create all tables
    print("\n📋 Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ All tables created successfully!")
    
    # Create admin user
    print("\n👤 Creating admin user...")
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
        print("   Username: admin")
        print("   Password: Admin123!")
    else:
        print("⚠️ Admin user already exists")
    session.close()
    
    # List all tables
    print("\n📊 Tables created:")
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """))
        tables = [row[0] for row in result]
        for table in tables:
            print(f"  ✅ {table}")
    
    print("\n" + "="*50)
    print("✅ Migration to Neon complete!")
    print("="*50)
    
except Exception as e:
    print(f"❌ Error: {e}")