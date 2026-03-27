from app.core.database import SessionLocal
from app.models.user import User
import bcrypt

db = SessionLocal()
user = db.query(User).filter(User.username == 'admin').first()
if user:
    new_hash = bcrypt.hashpw('Admin123!'.encode(), bcrypt.gensalt()).decode()
    user.password_hash = new_hash
    user.is_locked = False
    user.failed_login_attempts = 0
    db.commit()
    print(f'✅ Password updated successfully!')
    print(f'New hash: {new_hash}')
else:
    print('❌ Admin not found')
db.close()