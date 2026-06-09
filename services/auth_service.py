import hashlib
import secrets
from typing import Optional
from loguru import logger
from database.database import DatabaseService
from database.models import User

class AuthService:
    """Authentication service for user login and session management"""
    
    @staticmethod
    def hash_password(password: str, salt: Optional[str] = None) -> tuple[str, str]:
        """
        Hash a password with a salt using PBKDF2
        Returns: (hashed_password, salt)
        """
        if salt is None:
            salt = secrets.token_hex(16)
        
        # Use PBKDF2 with SHA-256
        pwdhash = hashlib.pbkdf2_hmac('sha256', 
                                      password.encode('utf-8'), 
                                      salt.encode('ascii'), 
                                      100000)
        pwdhash = pwdhash.hex()
        return pwdhash, salt
    
    @staticmethod
    def verify_password(password_hash: str, provided_password: str, salt: str) -> bool:
        """Verify a provided password against the stored hash and salt"""
        # Extract salt from stored password hash if it's in the format "salt$hash"
        if '$' in password_hash:
            stored_salt, stored_hash = password_hash.split('$')
        else:
            # If no salt in stored password, use provided salt
            stored_salt = salt
            stored_hash = password_hash
        
        pwdhash, _ = AuthService.hash_password(provided_password, stored_salt)
        return pwdhash == stored_hash
    
    @staticmethod
    def authenticate_user(username: str, password: str) -> Optional[User]:
        """Authenticate a user with username and password"""
        user = DatabaseService.get_user_by_username(username)
        if not user:
            logger.warning(f"Failed login attempt: Username '{username}' not found.")
            return None
        
        # Verify password - extract salt from stored password hash
        if '$' in user.password_hash:
            # Salt is stored with the password in format "salt$hash"
            salt, stored_hash = user.password_hash.split('$', 1)
            pwdhash, _ = AuthService.hash_password(password, salt)
            if pwdhash == stored_hash:
                logger.info(f"User logged in: {username} (Role: {user.role})")
                return user
        else:
            # For backwards compatibility
            pwdhash, _ = AuthService.hash_password(password)
            if pwdhash == user.password_hash:
                logger.info(f"User logged in: {username} (Role: {user.role})")
                return user
        
        logger.warning(f"Failed login attempt for user: {username}")
        return None
    
    @staticmethod
    def authenticate_admin_pin(user: User, pin: str) -> bool:
        """Authenticate an admin with PIN"""
        if user.role != 'admin' or not user.pin_hash:
            return False
        
        # Extract salt from stored PIN hash if it's in the format "salt$hash"
        if '$' in user.pin_hash:
            stored_salt, stored_hash = user.pin_hash.split('$', 1)
            pwdhash, _ = AuthService.hash_password(pin, stored_salt)
            return pwdhash == stored_hash
        else:
            # For backwards compatibility, if no salt stored with hash
            pwdhash, _ = AuthService.hash_password(pin)
            return pwdhash == user.pin_hash
    
    @staticmethod
    def get_all_users() -> list[User]:
        """Retrieve all registered users."""
        return DatabaseService.get_all_users()

    @staticmethod
    def admin_reset_user_password(admin_user: User, admin_password: str, target_user_id: int, new_password: str) -> bool:
        """Reset a user's password after verifying admin credentials."""
        # 1. Verify Admin identity
        authenticated_admin = AuthService.authenticate_user(admin_user.username, admin_password)
        if not authenticated_admin or authenticated_admin.role != "admin":
            logger.warning(f"Admin password verification failed during password reset for User ID {target_user_id}")
            return False
            
        # 2. Perform Reset
        hashed_password, salt = AuthService.hash_password(new_password)
        # Store in "salt$hash" format
        salted_hash = f"{salt}${hashed_password}"
        success = DatabaseService.update_user_password(target_user_id, salted_hash)
        if success:
            logger.info(f"Administrative password reset completed for User ID: {target_user_id} by {admin_user.username}")
        return success

    @staticmethod
    def change_password(user_id: int, old_password: str, new_password: str) -> bool:
        """Change user's password after verifying old password"""
        user = DatabaseService.get_user_by_id(user_id)
        if not user:
            return False
        
        # Verify old password
        if not AuthService.verify_password(user.password_hash, old_password, ""):
            return False
        
        # Hash and update new password
        hashed_password, salt = AuthService.hash_password(new_password)
        # Store in "salt$hash" format
        salted_hash = f"{salt}${hashed_password}"
        success = DatabaseService.update_user_password(user_id, salted_hash)
        if success:
            logger.info(f"Password changed for User ID: {user_id}")
        return success
    
    @staticmethod
    def reset_password(username: str, new_password: str) -> bool:
        """Reset password for a user (admin only function)"""
        user = DatabaseService.get_user_by_username(username)
        if not user:
            return False
        
        hashed_password, salt = AuthService.hash_password(new_password)
        # Store in "salt$hash" format
        salted_hash = f"{salt}${hashed_password}"
        return DatabaseService.update_user_password(user.id, salted_hash)