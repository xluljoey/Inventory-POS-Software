#!/usr/bin/env python3
"""
Main application entry point for the Inventory Management System
Using PySide6 QtWidgets for the UI (stable alternative to QML)
"""

import sys
import os
from PySide6.QtWidgets import (QApplication, QMainWindow, QStackedWidget, 
                               QVBoxLayout, QWidget, QHBoxLayout, QSizePolicy, QMessageBox)
from PySide6.QtCore import Qt, QFile, QTextStream, QSize
from PySide6.QtGui import QIcon, QPixmap
from loguru import logger
from core import config
from utils.cloud_sync import SyncManager

from config.database_config import DatabaseConfig
from services.auth_service import AuthService
from database.models import User
from utils.logger_config import setup_logger, handle_exception, log_user_action

# Initialize logger
setup_logger()
# Set global exception hook
sys.excepthook = handle_exception

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
        print("MainWindow.__init__ started")
        super().__init__()
        self.current_user = None
        print("Calling init_ui...")
        self.init_ui()
        print("Calling load_styles...")
        self.load_styles()
        print("MainWindow.__init__ finished")
        
    def init_ui(self):
        """Initialize the main UI components"""
        print("init_ui started")
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
        print("Creating Navigation Bar...")
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
        print("Initializing screens...")
        self.init_screens()
        
        # Start with login screen
        print("Showing login screen...")
        self.show_login_screen()
        print("init_ui finished")
        
    def load_styles(self):
        """Load QSS styling"""
        qss_file = QFile("styles.qss")
        if qss_file.exists():
            qss_file.open(QFile.ReadOnly | QFile.Text)
            stylesheet = QTextStream(qss_file).readAll()
            self.setStyleSheet(stylesheet)
    
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
        print(f"DEBUG: Login successful for {user.username} (Role: {user.role})")
        self.current_user = user
        
        # Update profile widget
        if hasattr(self, 'profile_widget'):
            self.profile_widget.update_user_info(user)
        
        # RBAC: Configure navigation bar
        self.nav_bar.set_role(user.role)
        if hasattr(self, 'header_container'):
            self.header_container.setVisible(True)
        
        # Update user info in screens
        print("DEBUG: Updating user info across screens...")
        self.dashboard_screen.set_current_user(user)
        self.inventory_screen.set_current_user(user)
        self.sales_screen.current_user = user
        self.customers_screen.set_current_user(user)
        self.reports_screen.set_current_user(user)
        self.settings_screen.set_current_user(user)
        
        # Force UI update to ensure all role-based elements are properly visible
        self.inventory_screen.update()
        
        # Show dashboard by default
        self.show_dashboard()

        # 4. BACKUP REMINDER (Startup Logic)
        if user.role == "admin":
            self._check_backup_reminder()

    def _check_backup_reminder(self):
        """Check if a backup reminder is needed (> 7 days since last sync)."""
        from database.database import DatabaseService
        from datetime import datetime, timedelta
        
        sync_setting = DatabaseService.get_setting("last_cloud_sync")
        show_reminder = False
        
        if not sync_setting or sync_setting.value == "Never":
            show_reminder = True
        else:
            try:
                last_sync = datetime.strptime(sync_setting.value, "%Y-%m-%d %H:%M:%S")
                if datetime.now() - last_sync > timedelta(days=7):
                    show_reminder = True
            except ValueError:
                show_reminder = True
                
        if show_reminder:
            from ui.custom_dialog import CustomWarningDialog
            msg = "SAFETY REMINDER: It has been more than 7 days since your last cloud backup. Please sync to Google Drive to ensure your data is safe."
            dialog = CustomWarningDialog("Backup Reminder", msg, self)
            dialog.exec()
    
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
    print("Starting main application...")
    try:
        print("Initializing database...")
        from database.init_db import init_database_with_default_admin
        init_database_with_default_admin()
        
        # Create test sales data if database is empty
        print("Checking for test data...")
        from database.database import DatabaseService
        from datetime import datetime
        
        # --- FIRST-RUN SETUP CHECK ---
        business_setting = DatabaseService.get_setting("business_name")
        is_first_run = not business_setting or business_setting.value == "Inventory Management System" or not business_setting.value.strip()
        
        print("Creating QApplication...")
        app = QApplication(sys.argv)
        
        if is_first_run:
            from ui.setup_wizard import SetupWizard
            wizard = SetupWizard()
            if wizard.exec() != SetupWizard.Accepted:
                print("Setup cancelled. Exiting.")
                sys.exit(0)
            else:
                # Refresh status
                business_setting = DatabaseService.get_setting("business_name")
                if not business_setting or not business_setting.value.strip():
                    logger.error("Setup wizard accepted but no business name found. Emergency exit.")
                    sys.exit(1)
        
        app.setApplicationName("Inventory Management System")
        app.setApplicationVersion("1.0")
        
        print("Creating MainWindow...")
        main_window = MainWindow()
        
        # Start Premium Sync Thread if enabled
        if config.IS_PREMIUM:
            main_window.sync_worker = SyncManager()
            main_window.sync_worker.start()
            logger.info("Premium Sync Engine initialized.")

        print("Showing MainWindow...")
        main_window.show()
        print("Entering main loop...")
        
        # 2. CRASH CAPTURE: Wrap main loop
        try:
            sys.exit(app.exec())
        except Exception as e:
            logger.exception("Application crashed unexpectedly")
            QMessageBox.critical(
                None,
                "Critical Error",
                "An unexpected error occurred. A log file has been created in the /logs folder. Please contact support."
            )
            sys.exit(1)
            
    except Exception as e:
        logger.exception("Failed to start application")
        sys.exit(1)


if __name__ == "__main__":
    main()