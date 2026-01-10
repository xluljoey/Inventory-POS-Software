# utils/cloud_sync.py
import time
from PySide6.QtCore import QThread, Signal
from loguru import logger
from core.config import IS_PREMIUM, FEATURES
from database.database import DatabaseService

class SupabaseClient:
    """Stub for real-time cloud mirroring using Supabase/PostgreSQL."""
    def __init__(self):
        self.enabled = IS_PREMIUM and FEATURES.get('realtime_cloud_sync')
        
    def push_record(self, table_name, data):
        """Mock method to push local SQLite row to Supabase."""
        if not self.enabled: return False
        logger.info(f"Premium Sync: Mirroring {table_name} record to Cloud...")
        # Implementation would use 'supabase-py' library here
        return True

class SyncManager(QThread):
    """
    Background worker that monitors the SQLite 'Sync_Log' table 
    and pushes unsynced changes to the cloud.
    """
    sync_status = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.running = True
        self.client = SupabaseClient()

    def run(self):
        if not IS_PREMIUM:
            logger.info("SyncManager: Basic version detected. Thread idle.")
            return

        logger.info("SyncManager: Premium Background Sync started.")
        while self.running:
            try:
                self.process_unsynced_records()
            except Exception as e:
                logger.error(f"SyncManager Error: {e}")
            
            # Poll every 10 seconds for new changes
            time.sleep(10)

    def process_unsynced_records(self):
        """Queries Sync_Log for records where sync_status = 0."""
        with DatabaseService.get_connection() as conn:
            cursor = conn.cursor()
            # Note: Sync_Log table created in database/init_db.py
            cursor.execute("SELECT id, table_name, record_id FROM Sync_Log WHERE sync_status = 0 LIMIT 50")
            records = cursor.fetchall()

            for log_id, table, rec_id in records:
                # 1. Fetch the actual data from the source table
                cursor.execute(f"SELECT * FROM {table} WHERE id = ?", (rec_id,))
                row = cursor.fetchone()
                
                if row:
                    data = dict(row)
                    # 2. Push to Supabase
                    if self.client.push_record(table, data):
                        # 3. Mark as synced
                        conn.execute("UPDATE Sync_Log SET sync_status = 1 WHERE id = ?", (log_id,))
                        conn.commit()
                        self.sync_status.emit(f"Synced {table} #{rec_id}")

    def stop(self):
        self.running = False
        self.wait()
