import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Premium Features Configuration ---
# Hardcode to True on the premium-sync branch
IS_PREMIUM = True
CLOUD_SYNC_ENABLED = IS_PREMIUM

# --- Cloud Services (Supabase) ---
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

FEATURES = {
    "google_drive_backup": True,
    "realtime_sync": True,
    "admin_remote_view": True
}

# Dynamic Path Discovery
if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ASSETS_DIR = os.path.join(BASE_DIR, "assets")
ICON_DIR = os.path.join(ASSETS_DIR, "icons")
