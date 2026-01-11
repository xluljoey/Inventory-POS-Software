import requests
from PySide6.QtCore import QThread, Signal, QTimer
from loguru import logger
from core import config

class SyncWorker(QThread):
    """
    Background worker to sync local SQLite data to Supabase.
    Pushes records where 'synced = 0' to the 'sales_sync' table.
    """
    cloud_status_changed = Signal(bool) # True = Online/Synced, False = Offline

    def __init__(self, parent=None):
        super().__init__(parent)
        self.timer = None

    def run(self):
        if not config.CLOUD_SYNC_ENABLED:
            logger.warning("Sync disabled in config.")
            return

        self.timer = QTimer()
        self.timer.timeout.connect(self.perform_sync)
        self.timer.start(30000) # Sync every 30 seconds
        logger.info("Premium SyncWorker started.")
        self.exec()

    def perform_sync(self):
        if not self.is_online():
            self.cloud_status_changed.emit(False)
            return

        # Signal 'Connected' state
        self.cloud_status_changed.emit(True)
        
        try:
            self.sync_sales()
        except Exception as e:
            logger.error(f"Sync failed: {e}")
            self.cloud_status_changed.emit(False)

    def sync_sales(self):
        from database.database import DatabaseService
        
        # 1. Get unsynced sales
        unsynced_sales = DatabaseService.get_unsynced_records('sales')
        if not unsynced_sales:
            return

        headers = {
            "apikey": config.SUPABASE_KEY,
            "Authorization": f"Bearer {config.SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal"
        }
        url = f"{config.SUPABASE_URL}/rest/v1/sales_sync"

        for sale in unsynced_sales:
            sale_id = sale['id']
            sale_obj = DatabaseService.get_sale_by_id(sale_id)
            
            if not sale_obj or not sale_obj.items:
                DatabaseService.mark_records_as_synced('sales', [sale_id])
                continue

            # 2. Map local sale items to Supabase 'sales_sync' table
            payload = []
            for item in sale_obj.items:
                payload.append({
                    "item_name": item.product_name,
                    "amount": float(item.subtotal),
                    "quantity": int(item.quantity)
                })

            # 3. Post to Cloud
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            if response.status_code in [200, 201]:
                DatabaseService.mark_records_as_synced('sales', [sale_id])
                logger.info(f"Cloud Sync: Sale {sale_id} pushed to Supabase.")

    def is_online(self):
        try:
            requests.get("https://8.8.8.8", timeout=3)
            return True
        except requests.RequestException:
            return False