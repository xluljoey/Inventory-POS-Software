# -*- coding: utf-8 -*-
import os
import platform
import json
from pathlib import Path
from loguru import logger

class AppConfig:
    """Application configuration settings, now including config.json management."""
    
    # Define base directory for persistent data (user-specific and OS-aware)
    if platform.system() == "Windows":
        _base_dir = Path(os.getenv('LOCALAPPDATA')) / "InventoryApp"
    else:
        # Use ~/.config or ~/.local/share for Linux/macOS
        _base_dir = Path.home() / ".config" / "InventoryApp" 
        if not _base_dir.exists(): # Fallback for non-standard systems
            _base_dir = Path.home() / ".local" / "share" / "InventoryApp"
    
    _base_dir.mkdir(parents=True, exist_ok=True)

    # Define paths using the base directory
    DB_PATH = _base_dir / 'inventory_v1.db'
    CONFIG_PATH = _base_dir / 'config.json'

    # Internal cache for configuration settings from config.json
    _config_data = {}

    @classmethod
    def load_config(cls):
        """Loads configuration from config.json."""
        if cls.CONFIG_PATH.exists():
            try:
                with open(cls.CONFIG_PATH, 'r', encoding='utf-8') as f:
                    cls._config_data = json.load(f)
                logger.info(f"Configuration loaded from {cls.CONFIG_PATH}")
            except json.JSONDecodeError as e:
                logger.error(f"Error decoding config.json: {e}. Using default/empty config.")
                cls._config_data = {}
            except Exception as e:
                logger.error(f"Error loading config.json: {e}. Using default/empty config.")
                cls._config_data = {}
        else:
            logger.info(f"config.json not found at {cls.CONFIG_PATH}. Creating default.")
            cls.save_config() # Create an empty config file
            
        # Ensure 'database' section exists with default db_host if not present
        if 'database' not in cls._config_data:
            cls._config_data['database'] = {}
        if 'db_host' not in cls._config_data['database']:
            cls._config_data['database']['db_host'] = 'localhost'
            cls.save_config() # Save with default db_host
            logger.info("Default db_host 'localhost' added to config.json.")


    @classmethod
    def save_config(cls):
        """Saves current configuration to config.json."""
        try:
            with open(cls.CONFIG_PATH, 'w', encoding='utf-8') as f:
                json.dump(cls._config_data, f, indent=4)
            logger.info(f"Configuration saved to {cls.CONFIG_PATH}")
        except Exception as e:
            logger.error(f"Error saving config.json: {e}")

    @classmethod
    def get_setting(cls, key, default=None):
        """Retrieves a setting from the loaded configuration, with fallback."""
        if not cls._config_data:
            cls.load_config() # Ensure config is loaded on first access

        # Example: to get db_host, use get_setting('database.db_host', 'localhost')
        keys = key.split('.')
        value = cls._config_data
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default # Key not found at this level
        return value

    @classmethod
    def set_setting(cls, key, value):
        """Sets a configuration setting and marks it for saving."""
        if not cls._config_data:
            cls.load_config() # Ensure config is loaded on first access
        
        keys = key.split('.')
        current_level = cls._config_data
        for i, k in enumerate(keys):
            if i == len(keys) - 1: # Last key in path
                current_level[k] = value
            else:
                if not isinstance(current_level, dict):
                    logger.error(f"Cannot set setting '{key}': Intermediate key '{k}' is not a dictionary.")
                    return
                if k not in current_level:
                    current_level[k] = {} # Create sub-dictionary if it doesn't exist
                current_level = current_level[k]
        cls.save_config() # Save after setting
        logger.info(f"Setting '{key}' updated to '{value}'.")


    # Static business settings (can be overridden by database settings or config.json)
    BUSINESS_NAME = "Inventory Management System"
    CURRENCY_SYMBOL = "GH₵"
    TAX_RATE = 0.0
    RECEIPT_HEADER = "Thank you for your purchase!"
    RECEIPT_FOOTER = "We appreciate your business"
    LOW_STOCK_THRESHOLD = 10
    BACKUP_FREQUENCY_DAYS = 1
    BACKUP_RETENTION_DAYS = 30
    DATE_FORMAT = "%Y-%m-%d"
    DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
    
    @classmethod
    def get_db_path(cls):
        """Get the database file path from AppConfig.DB_PATH."""
        return str(cls.DB_PATH)
    
    @classmethod
    def get_config_path(cls):
        """Get the config.json file path from AppConfig.CONFIG_PATH."""
        return str(cls.CONFIG_PATH)

    @classmethod
    def get_backup_dir(cls):
        """Get the backup directory path within the base directory."""
        backup_dir = cls._base_dir / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        return str(backup_dir)

# Initialize config on module load
AppConfig.load_config()
