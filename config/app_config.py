# -*- coding: utf-8 -*-
import os
import platform
from pathlib import Path

class AppConfig:
    """Application configuration settings"""
    
    # Business settings
    BUSINESS_NAME = "Inventory Management System"
    CURRENCY_SYMBOL = "GH₵"  # Updated to Ghana Cedi as requested
    TAX_RATE = 0.0  # Default to 0%, can be updated in settings
    RECEIPT_HEADER = "Thank you for your purchase!"
    RECEIPT_FOOTER = "We appreciate your business"
    
    # Low stock threshold (default)
    LOW_STOCK_THRESHOLD = 10
    
    # Backup settings
    BACKUP_FREQUENCY_DAYS = 1  # Daily backups
    BACKUP_RETENTION_DAYS = 30  # Keep 30 days of backups
    
    # Date format preference
    DATE_FORMAT = "%Y-%m-%d"
    DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
    
    @staticmethod
    def get_data_dir():
        """Get the appropriate data directory for the platform"""
        if platform.system() == "Windows":
            # Use AppData on Windows
            appdata = os.getenv('APPDATA')
            if appdata:
                return Path(appdata) / "InventoryManagement"
        else:
            # Use ~/.local/share on Linux
            home = Path.home()
            return home / ".local" / "share" / "InventoryManagement"
        
        # Fallback to current directory if platform-specific directories fail
        return Path.cwd() / "data"
    
    @staticmethod
    def get_db_path():
        """Get the database file path"""
        # TEMPORARY: Use local database file for debugging
        return Path.cwd() / "inventory_management.db"
        
        # Original code (commented out for debugging):
        # data_dir = AppConfig.get_data_dir()
        # data_dir.mkdir(parents=True, exist_ok=True)
        # return data_dir / "inventory.db"
    
    @staticmethod
    def get_backup_dir():
        """Get the backup directory path"""
        data_dir = AppConfig.get_data_dir()
        backup_dir = data_dir / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        return backup_dir