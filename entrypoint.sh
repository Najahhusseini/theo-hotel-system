#!/bin/bash
# entrypoint.sh

echo "Waiting for PostgreSQL to be ready..."
while ! nc -z postgres 5432; do
  sleep 1
done
echo "PostgreSQL is ready!"

# Run database migrations (create tables)
echo "Creating database tables..."
python -c "
from app.core.database import engine, Base
from app.models import *
Base.metadata.create_all(bind=engine)
print('Database tables created successfully!')
"

# Create admin user if not exists
echo "Checking for admin user..."
python -c "
from app.core.database import SessionLocal
from app.models.user import User, UserRole
from app.utils.security import get_password_hash

db = SessionLocal()
admin = db.query(User).filter(User.username == 'admin').first()
if not admin:
    admin = User(
        username='admin',
        email='admin@theo.com',
        password_hash=get_password_hash('Admin123!'),
        first_name='System',
        last_name='Administrator',
        role=UserRole.SUPER_ADMIN,
        is_active=True
    )
    db.add(admin)
    db.commit()
    print('Admin user created!')
else:
    print('Admin user already exists')
db.close()
"

# Start the application
exec uvicorn main:app --host 0.0.0.0 --port 8000