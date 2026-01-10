
import requests
from PySide6.QtCore import QThread, Signal, QTimer
from loguru import logger
from core import config

class SyncManager(QThread):
    sync_status_changed = Signal(bool)  # True if online/synced, False otherwise
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.running = False
        self.timer = QTimer()
        self.timer.timeout.connect(self.sync_data)

    def run(self):
        """Start the sync loop"""
        if not config.CLOUD_SYNC_ENABLED:
            logger.info("Cloud sync disabled (Basic Mode).")
            return

        logger.info("Starting SyncManager thread...")
        self.running = True
        # Create timer in the thread's event loop
        self.timer.start(60000)  # 60 seconds
        self.exec()

    def sync_data(self):
        """Check connection and push unsynced sales"""
        if not self.check_connection():
            self.sync_status_changed.emit(False)
            return

        try:
            # Placeholder for database query
            # unsynced_sales = Database.get_unsynced_sales()
            unsynced_sales = [] # Mock empty list
            
            if unsynced_sales:
                logger.info(f"Found {len(unsynced_sales)} unsynced sales. Pushing to cloud...")
                # push_to_cloud(unsynced_sales)
                # Mark as synced in DB
            
            self.sync_status_changed.emit(True)
            
        except Exception as e:
            logger.error(f"Sync failed: {e}")
            self.sync_status_changed.emit(False)

    def check_connection(self):
        """Simple connectivity check"""
        try:
            # Ping a reliable host (Google DNS)
            requests.get("https://8.8.8.8", timeout=3)
            return True
        except requests.RequestException:
            return False

    def stop(self):
        self.running = False
        self.quit()
        self.wait()
