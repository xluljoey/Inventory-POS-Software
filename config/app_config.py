import os
import platform
import json
import sys
import shutil
from pathlib import Path
from loguru import logger

class AppConfig:
    """Application configuration settings for production and LAN readiness."""
    
    @staticmethod
    def get_resource_path(relative_path):
        """Get absolute path to resource, works for dev and for PyInstaller."""
        if hasattr(sys, "_MEIPASS"):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.abspath(".")
        path = os.path.join(base_path, relative_path)
        return path if os.path.exists(path) else None

    # Define base directory for persistent data (user-specific and OS-aware)
    if platform.system() == "Windows":
        _base_dir = Path(os.environ.get("LOCALAPPDATA", os.path.expanduser("~\\AppData\\Local"))) / "InventoryApp"
    else:
        _base_dir = Path.home() / ".config" / "InventoryApp"
    
    _base_dir.mkdir(parents=True, exist_ok=True)

    # Internal cache for configuration settings from config.json
    _config_data = {}
    CONFIG_PATH = _base_dir / 'config.json'

    @classmethod
    def load_config(cls):
        """Loads configuration from config.json with production defaults."""
        if cls.CONFIG_PATH.exists():
            try:
                with open(cls.CONFIG_PATH, 'r', encoding='utf-8') as f:
                    cls._config_data = json.load(f)
                logger.info(f"Configuration loaded from {cls.CONFIG_PATH}")
                return True # Config exists and loaded
            except Exception as e:
                logger.error(f"Error loading config.json: {e}")
                cls._config_data = {}
                return False
        else:
            # File doesn't exist, this is likely a first run
            cls._config_data = {}
            logger.info("Config file missing - preparing for first run")
            return False

    @classmethod
    def get_db_path(cls):
        """Dynamic DB Pathing: Returns local AppData path or Network UNC path."""
        db_mode = cls.get_setting('database.db_mode', 'local')
        if db_mode == 'network':
            network_path = cls.get_setting('database.network_path')
            if network_path:
                return network_path
            logger.warning("Network mode enabled but network_path is empty. Falling back to local.")
        
        return str(cls._base_dir / 'inventory.db')

    @classmethod
    def ensure_db_setup(cls):
        """Ensures database exists in the target path, copying from bundle if needed."""
        target_path = Path(cls.get_db_path())
        
        # If DB exists, do nothing
        if target_path.exists():
            return
            
        # If local mode, try to copy template from bundle (sys._MEIPASS)
        if cls.get_setting('database.db_mode', 'local') == 'local':
            template_path = Path(cls.get_resource_path(os.path.join('database', 'inventory.db')))
            if template_path.exists():
                try:
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(template_path, target_path)
                    logger.info(f"Initialized new database from template: {target_path}")
                except Exception as e:
                    logger.error(f"Failed to copy template database: {e}")
            else:
                logger.warning(f"Database template not found at {template_path}. Database will be created from scratch.")

    @classmethod
    def save_config(cls):
        """Saves current configuration to config.json."""
        try:
            with open(cls.CONFIG_PATH, 'w', encoding='utf-8') as f:
                json.dump(cls._config_data, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving config.json: {e}")

    @classmethod
    def get_setting(cls, key, default=None):
        """Retrieves a setting from the loaded configuration, with fallback."""
        if not cls._config_data:
            cls.load_config()
        keys = key.split('.')
        value = cls._config_data
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    @classmethod
    def set_setting(cls, key, value):
        """Sets a configuration setting and marks it for saving."""
        if not cls._config_data:
            cls.load_config()
        keys = key.split('.')
        current_level = cls._config_data
        for i, k in enumerate(keys):
            if i == len(keys) - 1:
                current_level[k] = value
            else:
                if k not in current_level or not isinstance(current_level[k], dict):
                    current_level[k] = {}
                current_level = current_level[k]
        cls.save_config()

    # Static business settings
    BUSINESS_NAME = "Inventory Management System - Joachim Korang Amponsah"
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
    def get_config_path(cls):
        return str(cls.CONFIG_PATH)

    @classmethod
    def get_base_dir(cls):
        """Returns the persistent AppData directory."""
        return str(cls._base_dir)

    @classmethod
    def get_backup_dir(cls):
        backup_dir = cls._base_dir / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        return str(backup_dir)

# Initialize config on module load
AppConfig.load_config()
