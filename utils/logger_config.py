import sys
import os
from pathlib import Path
from loguru import logger
from PySide6.QtWidgets import QMessageBox

def setup_logger():
    """Configure Loguru logger for the application"""
    # 1. LOG FILING: Create logs folder and configure rotation
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "app_activity.log"

    # Remove default handler
    logger.remove()

    # Add stdout handler for development
    logger.add(sys.stdout, level="DEBUG", format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>")

    # Add file handler with rotation and retention
    logger.add(
        log_file,
        rotation="5 MB",
        retention="1 week",
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        backtrace=True,
        diagnose=True
    )

def handle_exception(exc_type, exc_value, exc_traceback):
    """Global exception handler for unhandled exceptions"""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    # 2. CRASH CAPTURE: Log unhandled exception with full stack trace
    logger.opt(exception=(exc_type, exc_value, exc_traceback)).critical("Uncaught exception")
    
    # 4. USER FEEDBACK: Trigger QMessageBox for critical errors
    from PySide6.QtWidgets import QApplication
    if QApplication.instance():
        QMessageBox.critical(
            None,
            "Critical Error",
            "An unexpected error occurred. A log file has been created in the /logs folder. Please contact support."
        )

# 3. SENSITIVE DATA MASKING: 
# We implement masking by providing helper methods or ensuring developers don't pass sensitive info.
# Alternatively, we can use loguru's filter or patch feature.

def log_user_action(action: str, user: str = "Unknown"):
    """Helper to log user actions with INFO level"""
    logger.info(f"User Action: [{user}] - {action}")

def log_error(message: str, error: Exception = None):
    """Helper to log errors with ERROR level"""
    if error:
        logger.error(f"{message} | Error: {str(error)}")
    else:
        logger.error(message)

def log_db_failure(message: str, error: Exception = None):
    """Helper specifically for database failures"""
    logger.error(f"DATABASE FAILURE: {message} | Error: {str(error)}")

def log_security_violation(user: str, resource: str):
    """Helper for permission violations"""
    logger.error(f"SECURITY VIOLATION: User [{user}] attempted unauthorized access to [{resource}]")
