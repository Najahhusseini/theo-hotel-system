# app/utils/token_blacklist.py
import hashlib
import os
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Try to import redis, but work without it
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not available, token blacklist will use in-memory storage")

# In-memory fallback
_blacklist = {}
_user_logout = {}

class TokenBlacklist:
    """Manage token blacklisting for logout and revocation."""
    
    @staticmethod
    def _get_redis_client():
        if REDIS_AVAILABLE:
            return redis.Redis(
                host=os.getenv("REDIS_HOST", "localhost"),
                port=int(os.getenv("REDIS_PORT", 6379)),
                db=int(os.getenv("REDIS_DB", 1)),
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
            )
        return None
    
    @staticmethod
    def blacklist_token(token: str, expires_in: int = 86400):
        """Add token to blacklist."""
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        try:
            client = TokenBlacklist._get_redis_client()
            if client:
                client.setex(f"blacklist:{token_hash}", expires_in, "1")
            else:
                # In-memory fallback
                _blacklist[token_hash] = datetime.now() + timedelta(seconds=expires_in)
            logger.info(f"Token blacklisted (expires in {expires_in}s)")
            return True
        except Exception as e:
            logger.error(f"Error blacklisting token: {e}")
            return False
    
    @staticmethod
    def is_blacklisted(token: str) -> bool:
        """Check if a token is blacklisted."""
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        try:
            client = TokenBlacklist._get_redis_client()
            if client:
                return client.exists(f"blacklist:{token_hash}") == 1
            else:
                # Check in-memory
                if token_hash in _blacklist:
                    if _blacklist[token_hash] > datetime.now():
                        return True
                    else:
                        del _blacklist[token_hash]
                return False
        except Exception as e:
            logger.error(f"Error checking blacklist: {e}")
            return False
    
    @staticmethod
    def logout_user(user_id: int):
        """Logout a user by invalidating all their tokens."""
        try:
            client = TokenBlacklist._get_redis_client()
            if client:
                client.setex(f"user_logout:{user_id}", 86400, "1")
            else:
                _user_logout[user_id] = datetime.now() + timedelta(seconds=86400)
            logger.info(f"User {user_id} logged out globally")
            return True
        except Exception as e:
            logger.error(f"Error logging out user: {e}")
            return False
    
    @staticmethod
    def is_user_logged_out(user_id: int) -> bool:
        """Check if a user has been globally logged out."""
        try:
            client = TokenBlacklist._get_redis_client()
            if client:
                return client.exists(f"user_logout:{user_id}") == 1
            else:
                if user_id in _user_logout:
                    if _user_logout[user_id] > datetime.now():
                        return True
                    else:
                        del _user_logout[user_id]
                return False
        except Exception as e:
            logger.error(f"Error checking user logout: {e}")
            return False