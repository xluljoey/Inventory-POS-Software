#!/usr/bin/env python3
"""Test script to check user creation in the database"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from config.database_config import DatabaseConfig
from database.database import DatabaseService
from database.models import User
from services.auth_service import AuthService

def test_user_creation():
    """Test creating users in the database"""
    # Initialize database
    DatabaseConfig.init_database()
    
    # Check if sales_rep user exists
    sales_user = DatabaseService.get_user_by_username('sales_rep')
    print(f"Sales rep user (sales_rep): {sales_user}")
    
    # Check if sales user exists
    sales_user_alt = DatabaseService.get_user_by_username('sales')
    print(f"Sales rep user (sales): {sales_user_alt}")
    
    # Check all users
    all_users = DatabaseService.get_all_users()
    print("All users in database:")
    for user in all_users:
        print(f"  ID: {user.id}, Username: {user.username}, Role: {user.role}")

if __name__ == "__main__":
    test_user_creation()