#!/usr/bin/env python3
"""
Main application entry point for the Inventory Management System
Using PySide6 QtWidgets for the UI (stable alternative to QML)
"""

import os, sys
import traceback # Added for exception_hook
from PySide6.QtCore import Qt, QTimer # QTimer added
from PySide6.QtGui import QGuiApplication
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
QGuiApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)

from PySide6.QtWidgets import (QApplication, QMainWindow, QStackedWidget, 
                               QVBoxLayout, QWidget, QHBoxLayout, QSizePolicy, QMessageBox)
from PySide6.QtCore import Qt, QFile, QTextStream, QSize
from PySide6.QtGui import QIcon, QPixmap

# --- GLOBAL EXCEPTION HOOK ---
from utils.logger import logger, exception_hook
sys.excepthook = exception_hook
# --- END GLOBAL EXCEPTION HOOK ---

# Ensure logger is configured before any other modules might log
logger.info("Application starting up...")


# from core import config # No longer needed
from utils.cloud_sync import SyncManager

from config.database_config import DatabaseConfig
from services.auth_service import AuthService
from database.models import User
from config.app_config import AppConfig # Imported AppConfig for settings


# SPRINT FIX: Import all major services at top-level to prevent circular import issues
from services.sales_service import SalesService
from services.customer_service import CustomerService
from services.inventory_service import InventoryService


# Import screen modules
from screens.login_screen import LoginScreen
from screens.dashboard_screen import DashboardScreen
from screens.inventory_screen import InventoryScreen
from screens.sales_screen import SalesScreen
from screens.customers_screen import CustomersScreen
from screens.reports_screen import ReportsScreen
from screens.settings_screen import SettingsScreen

# Import Custom Navigation Bar
from ui.navigation_bar import MainNavigationBar
from ui.animated_stacked_widget import AnimatedStackedWidget


class MainWindow(QMainWindow):
    """Main application window with navigation and screen management"""
    
    def __init__(self):
        logger.info("MainWindow.__init__ started")
        super().__init__()
        self.current_user = None
        self.sync_manager = None # For auto-backup
        self.backup_timer = None # For auto-backup
        logger.info("Calling init_ui...")
        self.init_ui()
        logger.info("Calling load_styles...")
        self.load_styles()
        logger.info("MainWindow.__init__ finished")
        
    def init_ui(self):
        """Initialize the main UI components"""
        logger.debug("init_ui started")
        self.setWindowTitle("Inventory Management System")
        self.setGeometry(100, 100, 1400, 900)
        
        # Enable window maximization and proper sizing
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.setMinimumSize(1200, 800)  # Set minimum size
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        self.main_layout = QVBoxLayout(central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Header container for Nav Bar and Profile
        self.header_container = QWidget()
        self.header_container.setFixedHeight(85)
        self.header_layout = QHBoxLayout(self.header_container)
        self.header_layout.setContentsMargins(20, 0, 20, 0)
        self.header_layout.setSpacing(0)
        
        # Modern Capsule Navigation Bar
        logger.debug("Creating Navigation Bar...")
        self.nav_bar = MainNavigationBar(self)
        self.nav_bar.nav_changed.connect(self.on_nav_changed)
        # Logout now handled by profile widget, but keeping signal for fallback
        self.nav_bar.logout_requested.connect(self.logout)
        
        self.header_layout.addWidget(self.nav_bar, 1) # Nav bar takes stretch
        
        # User Profile Dropdown (Top Right)
        from ui.user_profile_widget import UserProfileWidget
        self.profile_widget = UserProfileWidget(User()) # Dummy user initially
        self.profile_widget.logout_requested.connect(self.logout)
        self.profile_widget.settings_requested.connect(self.show_settings)
        self.header_layout.addWidget(self.profile_widget)
        
        self.main_layout.addWidget(self.header_container)
        self.header_container.setVisible(False)
        
        # Create stacked widget for screen navigation
        self.stacked_widget = AnimatedStackedWidget()
        self.main_layout.addWidget(self.stacked_widget)
        
        # Initialize screens
        logger.debug("Initializing screens...")
        self.init_screens()
        
        # Start with login screen
        logger.debug("Showing login screen...")
        self.show_login_screen()
        logger.debug("init_ui finished")
        
    def load_styles(self):
        """Load QSS styling using the resource path helper."""
        from utils.resource_path import get_resource_path
        qss_file_path = get_resource_path("styles.qss")
        qss_file = QFile(qss_file_path)
        if qss_file.exists():
            qss_file.open(QFile.ReadOnly | QFile.Text)
            stylesheet = QTextStream(qss_file).readAll()
            self.setStyleSheet(stylesheet)
        else:
            logger.error(f"Could not find stylesheet at: {qss_file_path}")
    
    def init_screens(self):
        """Initialize all application screens"""
        # Login screen
        self.login_screen = LoginScreen()
        self.login_screen.login_successful.connect(self.on_login_success)
        self.stacked_widget.addWidget(self.login_screen)
        
        # Dashboard screen
        self.dashboard_screen = DashboardScreen()
        self.dashboard_screen.set_main_window(self)
        self.stacked_widget.addWidget(self.dashboard_screen)
        
        # Inventory screen
        self.inventory_screen = InventoryScreen()
        self.stacked_widget.addWidget(self.inventory_screen)
        
        # Sales screen
        self.sales_screen = SalesScreen()
        self.sales_screen.sale_completed.connect(self.on_sale_completed)
        self.stacked_widget.addWidget(self.sales_screen)
        
        # Customers screen
        self.customers_screen = CustomersScreen()
        self.stacked_widget.addWidget(self.customers_screen)
        
        # Reports screen
        self.reports_screen = ReportsScreen()
        self.stacked_widget.addWidget(self.reports_screen)
        
        # Settings screen
        self.settings_screen = SettingsScreen()
        self.stacked_widget.addWidget(self.settings_screen)
    
    def show_login_screen(self):
        """Show the login screen and hide navigation"""
        if hasattr(self, 'header_container'):
            self.header_container.setVisible(False)
        self.login_screen.clear_fields()
        self.stacked_widget.setCurrentWidget(self.login_screen)
    
    def on_login_success(self, user: User):
        """Handle successful login"""
        try:
            logger.debug(f"Login successful for {user.username} (Role: {user.role})")
            self.current_user = user

            # Update profile widget
            if hasattr(self, 'profile_widget'):
                try:
                    self.profile_widget.update_user_info(user)
                except Exception:
                    logger.exception("Failed to update profile widget")

            # RBAC: Configure navigation bar
            try:
                self.nav_bar.set_role(user.role)
            except Exception:
                logger.exception("Failed to set navigation role")

            if hasattr(self, 'header_container'):
                self.header_container.setVisible(True)

            # Update user info in screens with defensive error handling
            try:
                logger.debug("Updating user info across screens...")
                self.dashboard_screen.set_current_user(user)
                self.inventory_screen.set_current_user(user)
                self.sales_screen.current_user = user
                self.customers_screen.set_current_user(user)
                self.reports_screen.set_current_user(user)
                self.settings_screen.set_current_user(user)
            except Exception:
                logger.exception("Failed to update one or more screens after login")

            # Force UI update to ensure all role-based elements are properly visible
            try:
                self.inventory_screen.update()
            except Exception:
                logger.exception("Inventory screen update failed")

            # Show dashboard by default
            try:
                self.show_dashboard()
            except Exception:
                logger.exception("Failed to show dashboard after login")

            # 4. BACKUP REMINDER (Startup Logic) — run defensively
            if user.role == "admin":
                try:
                    self._check_backup_reminder()
                except Exception:
                    logger.exception("Backup reminder check failed")

        except Exception: # Catch internal exception of this method
            logger.exception("Unexpected error during on_login_success")

    def _check_backup_reminder(self):
        """Check if a backup reminder is needed (> 7 days since last sync)."""
        from database.database import DatabaseService
        from datetime import datetime, timedelta

        def _parse_last_sync(val):
            """Try several parsing strategies for stored last sync values."""
            if not val:
                return None
            # If it's already a datetime
            if isinstance(val, datetime):
                return val
            # If a timedelta was stored accidentally, interpret as offset from now
            from datetime import timedelta as _td
            if isinstance(val, _td):
                try:
                    return datetime.now() - val
                except Exception:
                    return None

            # Strings: try common formats
            if isinstance(val, str):
                s = val.strip()
                if s.lower() == "never":
                    return None
                # Try explicit format first
                for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
                    try:
                        return datetime.strptime(s, fmt)
                    except Exception:
                        continue
                # Try ISO parser fallback
                try:
                    return datetime.fromisoformat(s)
                except Exception:
                    pass
                # Try numeric epoch
                try:
                    ts = float(s)
                    return datetime.fromtimestamp(ts)
                except Exception:
                    pass

            # Could not parse
            return None

        sync_setting = DatabaseService.get_setting("last_cloud_sync")
        show_reminder = False

        if not sync_setting or sync_setting.value is None:
            show_reminder = True
        else:
            try:
                last_sync = _parse_last_sync(sync_setting.value)
                if not last_sync:
                    show_reminder = True
                else:
                    try:
                        if datetime.now() - last_sync > timedelta(days=7):
                            show_reminder = True
                    except Exception:
                        # Defensive fallback if subtraction fails for any reason
                        show_reminder = True
            except Exception:
                show_reminder = True

        if show_reminder:
            try:
                from ui.custom_dialog import CustomWarningDialog
                msg = "SAFETY REMINDER: It has been more than 7 days since your last cloud backup. Please sync to Google Drive to ensure your data is safe."
                dialog = CustomWarningDialog("Backup Reminder", msg, self)
                dialog.exec()
            except Exception:
                logger.exception("Failed to show backup reminder dialog")
    
    def on_nav_changed(self, btn_id):
        """Handle navigation bar button clicks"""
        if btn_id == 0: self.show_dashboard()
        elif btn_id == 1: self.show_inventory()
        elif btn_id == 2: self.show_sales()
        elif btn_id == 3: self.show_customers()
        elif btn_id == 4: self.show_reports()
        elif btn_id == 5: self.show_settings()
    
    def show_dashboard(self):
        self.dashboard_screen.update_dashboard()
        self.stacked_widget.setCurrentWidget(self.dashboard_screen)
        self.nav_bar.set_active_btn(0)
    
    def show_inventory(self):
        self.inventory_screen.load_inventory_data()
        self.stacked_widget.setCurrentWidget(self.inventory_screen)
        self.nav_bar.set_active_btn(1)
    
    def show_sales(self):
        self.sales_screen.load_product_data()
        self.sales_screen.load_customers()
        self.stacked_widget.setCurrentWidget(self.sales_screen)
        self.nav_bar.set_active_btn(2)
    
    def show_customers(self):
        self.customers_screen.load_customer_data()
        self.stacked_widget.setCurrentWidget(self.customers_screen)
        self.nav_bar.set_active_btn(3)
    
    def show_reports(self):
        self.reports_screen.load_report_data()
        self.stacked_widget.setCurrentWidget(self.reports_screen)
        self.nav_bar.set_active_btn(4)
    
    def show_settings(self):
        self.settings_screen.load_all_settings_data()
        self.stacked_widget.setCurrentWidget(self.settings_screen)
        self.nav_bar.set_active_btn(5)
    
    def logout(self):
        """Handle user logout"""
        self.current_user = None
        self.show_login_screen()
    
    def on_sale_completed(self):
        """Handle sale completion - refresh reports and dashboard"""
        self.reports_screen.update_report_data_after_sale()
        self.reports_screen.refresh_daily_sales_data()
        self.dashboard_screen.update_dashboard()
        # Synchronize Inventory and Customers screens
        self.inventory_screen.load_inventory_data()
        self.customers_screen.load_customer_data()


def main():
    """Main application entry point"""
    logger.info("Starting main application...")
    try:
        logger.info("Initializing database...")
        from database.init_db import init_database_with_default_admin
        init_database_with_default_admin()
        
        # Create test sales data if database is empty
        logger.info("Checking for test data...")
        from database.database import DatabaseService
        from datetime import datetime
        from config.app_config import AppConfig # Imported for auto-backup setting
        
        # --- FIRST-RUN SETUP CHECK ---
        business_setting = DatabaseService.get_setting("business_name")
        is_first_run = not business_setting or business_setting.value == "Inventory Management System" or not business_setting.value.strip()
        
        logger.info("Creating QApplication...")
        app = QApplication(sys.argv)
        app.setStyle("Fusion")
        app.setPalette(app.style().standardPalette())
        
        if is_first_run:
            from ui.setup_wizard import SetupWizard
            wizard = SetupWizard()
            if wizard.exec() != SetupWizard.Accepted:
                logger.info("Setup cancelled. Exiting.")
                sys.exit(0)
            else:
                # Refresh status
                business_setting = DatabaseService.get_setting("business_name")
                if not business_setting or not business_setting.value.strip():
                    logger.error("Setup wizard accepted but no business name found. Emergency exit.")
                    sys.exit(1)
        
        app.setApplicationName("Inventory Management System")
        app.setApplicationVersion("1.0")
        
        logger.info("Creating MainWindow...")
        main_window = MainWindow()
        
        # Auto Cloud Backup: Initialize and start QTimer if enabled
        auto_backup_enabled = AppConfig.get_setting("auto_cloud_backup_enabled", "0") == "1"
        if auto_backup_enabled:
            logger.info("Auto Cloud Backup is enabled. Initializing sync manager and timer.")
            main_window.sync_manager = SyncManager() # Instantiate SyncManager
            main_window.backup_timer = QTimer(main_window) # Create QTimer
            
            # Connect timer to sync manager's start_sync method
            main_window.backup_timer.timeout.connect(main_window.sync_manager.start_sync)
            
            # Start timer with a 15-minute interval (900,000 ms)
            main_window.backup_timer.start(15 * 60 * 1000)
            logger.info(f"Auto Cloud Backup timer started with 15 minute interval.")
        else:
            logger.info("Auto Cloud Backup is disabled.")

        logger.info("Showing MainWindow...")
        main_window.show()
        logger.info("Entering main loop...")
        
        # 2. CRASH CAPTURE: Wrap main loop
        # Removed redundant try-except as global exception_hook handles this
        sys.exit(app.exec())
            
    except Exception: # Catch any startup errors not caught by QApplication.exec()
        logger.exception("Failed to start application")
        sys.exit(1)


if __name__ == "__main__":
    main()