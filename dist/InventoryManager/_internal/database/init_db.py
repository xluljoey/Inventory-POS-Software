import sqlite3
from config.app_config import AppConfig
from services.auth_service import AuthService

def init_database_with_default_admin():
    """Initialize the database with a default admin user"""
    # Ensure database is deployed to LocalAppData if running in production/installer mode
    AppConfig.ensure_db_setup()
    
    from config.database_config import DatabaseConfig
    DatabaseConfig.init_database()
    
    # Check if admin user already exists
    from database.database import DatabaseService
    admin_user = DatabaseService.get_user_by_username('admin')
    
    if not admin_user:
        # Create default admin user with username: admin, password: admin123, PIN: 1234
        from database.models import User
        password_hash, salt = AuthService.hash_password('admin123')
        # Store salt with the password hash in the format "salt$hash"
        salted_hash = f"{salt}${password_hash}"
        
        # Hash the admin PIN
        pin_hash, pin_salt = AuthService.hash_password('1234')
        pin_hashed = f"{pin_salt}${pin_hash}"
        
        admin_user = User(
            username='admin',
            password_hash=salted_hash,
            role='admin',
            full_name='Administrator',
            pin_hash=pin_hashed  # Admin PIN set to "1234"
        )
        
        DatabaseService.create_user(admin_user)
        print("Default admin user created: username: admin, password: admin123, PIN: 1234")
        
        # Create a default sales rep user as well
        sales_user = DatabaseService.get_user_by_username('sales_rep')
        if not sales_user:
            sales_password_hash, sales_salt = AuthService.hash_password('sales123')
            sales_salted_hash = f"{sales_salt}${sales_password_hash}"
            
            sales_user = User(
                username='sales_rep',
                password_hash=sales_salted_hash,
                role='sales_rep',
                full_name='Sales Representative',
                pin_hash=None
            )
            
            DatabaseService.create_user(sales_user)
            print("Default sales rep user created: username: sales_rep, password: sales123")

if __name__ == "__main__":
    init_database_with_default_admin()