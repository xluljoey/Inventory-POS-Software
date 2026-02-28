# utils/logger.py
import sys
import os
import platform
import traceback # Added for exception_hook
from pathlib import Path
from loguru import logger
from PySide6.QtWidgets import QMessageBox, QApplication # Import QApplication for safety check

# Determine base directory for persistent data (user-specific and OS-aware)
if platform.system() == "Windows":
    _base_dir = Path(os.getenv('LOCALAPPDATA')) / "InventoryApp"
else:
    # Use ~/.config or ~/.local/share on Linux/macOS
    _base_dir = Path.home() / ".config" / "InventoryApp" 
    if not _base_dir.exists(): # Fallback for non-standard systems
        _base_dir = Path.home() / ".local" / "share" / "InventoryApp"

_base_dir.mkdir(parents=True, exist_ok=True)
log_dir = _base_dir / "logs"
log_dir.mkdir(parents=True, exist_ok=True)
log_file_path = log_dir / "app.log" # Renamed to app.log

# Configure Loguru logger globally
logger.remove() # Remove default handler to ensure clean configuration

# Add file handler with rotation and retention for critical errors and general logs
logger.add(
    str(log_file_path), # Convert Path object to string for logger.add
    rotation="5 MB",
    retention="1 week", # Keep 1 week of rotated logs
    level="INFO", # Log INFO and above to file
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    # backtrace=True, # Removed, exception hook handles full stack trace
    # diagnose=True,  # Removed, exception hook handles full stack trace
    catch=True # Catch errors in logging itself
)

# Add a handler for stdout for development/debugging visibility
logger.add(
    sys.stdout, 
    level="DEBUG", # Log DEBUG and above to stdout
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
)

# Global exception handler for unhandled exceptions (similar to task's exception_hook)
def exception_hook(exctype, value, tb):
    """
    Global exception hook to catch unhandled exceptions, log them critically,
    and then call the default system exception hook.
    """
    error_msg = "".join(traceback.format_exception(exctype, value, tb))
    logger.critical(f"FATAL CRASH:\n{error_msg}")
    # Avoid showing a blocking QMessageBox here because many Qt callbacks
    # and library exceptions may surface during startup; instead we log
    # the crash and write it to the log file. If an interactive popup is
    # desired during development, set the environment variable
    # `INVENTORYAPP_SHOW_CRASH_POPUP=1` and the popup will be shown.
    try:
        if os.getenv('INVENTORYAPP_SHOW_CRASH_POPUP') == '1' and QApplication.instance():
            log_path_str = str(log_file_path.parent)
            QMessageBox.critical(
                None,
                "Critical Error",
                f"An unexpected error occurred. A crash report has been saved to:\n{log_path_str}\n\nPlease contact support."
            )
    except Exception:
        # Never let the exception hook itself raise
        pass
    
    # Call the original excepthook to ensure Python's default behavior (e.g., printing to stderr)
    sys.__excepthook__(exctype, value, tb)
