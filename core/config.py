import os
import sys

# This checks if you typed 'export APP_MODE=PREMIUM' in your terminal
APP_MODE = os.getenv("APP_MODE", "BASIC") 

IS_PREMIUM = APP_MODE == "PREMIUM"

FEATURES = {
    "google_drive_backup": True,
    "realtime_sync": True if IS_PREMIUM else False,
    "admin_remote_view": True if IS_PREMIUM else False
}

# Dynamic Path Discovery
# ----------------------
# Determine the absolute path to the project root directory
if getattr(sys, 'frozen', False):
    # If the application is run as a bundle, the PyInstaller bootloader
    # extends the sys module by a flag frozen=True and sets the app 
    # path into variable _MEIPASS.
    BASE_DIR = sys._MEIPASS
else:
    # Normal Python execution
    # This file is in core/config.py, so we go up one level to get to root
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Define the assets directory
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
ICON_DIR = os.path.join(ASSETS_DIR, "icons")