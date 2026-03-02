#!/usr/bin/env python3
"""
Main application entry point for the Inventory Management System
Using PySide6 QtWidgets for the UI (stable alternative to QML)
"""

import os, sys
import traceback
from PySide6.QtCore import Qt, QTimer, Signal, QSize, QFile, QTextStream
from PySide6.QtGui import QGuiApplication, QIcon, QPixmap
from PySide6.QtWidgets import (QApplication, QMainWindow, QStackedWidget, 
                               QVBoxLayout, QWidget, QHBoxLayout, QSizePolicy, QMessageBox, QLabel)

os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"

# Global logger placeholder to be initialized after QApplication
logger = None

class MainWindow(QMainWindow):
    """Main application window with navigation and screen management"""
    data_changed = Signal()
    
    def __init__(self):
        super().__init__()
        if logger: logger.info("MainWindow initializing...")
        self.current_user = None
        self.sync_manager = None 
        self.backup_timer = None 
        self.screens = {} # PERSONA REQUEST: Use screens dictionary
        
        self.init_ui()
        self.load_styles()
        self.update_branding_title()
        
        # Start on Login Screen (Hidden Header)
        self.show_login_screen()
        
        if logger: logger.info("MainWindow initialized")
        
    def update_branding_title(self):
        """Set window title based on config store name"""
        from config.app_config import AppConfig
        store_name = AppConfig.get_setting("business_name", "Inventory Management System")
        self.setWindowTitle(f"{store_name} - Developed by Joachim Korang Amponsah (Xluljoey)")

    def init_ui(self):
        """Initialize the main UI components"""
        if logger: logger.debug("init_ui started")
        from utils.resource_path import get_resource_path
        
        # FIX WINDOW ICON CRASH: Wrap setWindowIcon in a try/except block
        try:
            icon_path = get_resource_path(os.path.join("assets", "app_icon.ico"))
            if icon_path:
                self.setWindowIcon(QIcon(icon_path))
        except Exception as e:
            if logger: logger.warning(f"Failed to set window icon: {e}")

        self.setGeometry(100, 100, 1400, 900)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.setMinimumSize(1200, 800)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QVBoxLayout(central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Header Container
        self.header_container = QWidget()
        self.header_container.setFixedHeight(85)
        self.header_layout = QHBoxLayout(self.header_container)
        self.header_layout.setContentsMargins(20, 0, 20, 0)
        self.header_layout.setSpacing(0)
        
        from ui.navigation_bar import MainNavigationBar
        self.nav_bar = MainNavigationBar(self)
        self.nav_bar.nav_changed.connect(self.on_nav_changed)
        self.header_layout.addWidget(self.nav_bar, 1)
        
        from ui.user_profile_widget import UserProfileWidget
        from database.models import User
        self.profile_widget = UserProfileWidget(User())
        self.profile_widget.logout_requested.connect(self.logout)
        self.profile_widget.settings_requested.connect(self.show_settings)
        self.header_layout.addWidget(self.profile_widget)
        
        self.main_layout.addWidget(self.header_container)
        self.header_container.setVisible(False) # Hidden initially for login
        
        from ui.animated_stacked_widget import AnimatedStackedWidget
        self.stacked_widget = AnimatedStackedWidget()
        self.main_layout.addWidget(self.stacked_widget)
        
        self.init_screens()
        if logger: logger.debug("init_ui finished")
        
    def load_styles(self):
        """Load QSS styling using the resource path helper."""
        from utils.resource_path import get_resource_path
        qss_file_path = get_resource_path("styles.qss")
        if qss_file_path:
            qss_file = QFile(qss_file_path)
            if qss_file.exists():
                qss_file.open(QFile.ReadOnly | QFile.Text)
                stylesheet = QTextStream(qss_file).readAll()
                self.setStyleSheet(stylesheet)
    
    def init_screens(self):
        """Initialize all application screens"""
        from screens.login_screen import LoginScreen
        from screens.dashboard_screen import DashboardScreen
        from screens.inventory_screen import InventoryScreen
        from screens.sales_screen import SalesScreen
        from screens.customers_screen import CustomersScreen
        from screens.reports_screen import ReportsScreen
        from screens.settings_screen import SettingsScreen

        def _safe_add(widget_name, constructor, connect_fn=None, post_init=None):
            try:
                widget = constructor()
                if connect_fn: connect_fn(widget)
                if post_init: post_init(widget)
                self.stacked_widget.addWidget(widget)
                self.screens[widget_name] = widget # REGISTER IN DICTIONARY
                setattr(self, widget_name, widget) # BACKWARD COMPATIBILITY
                return widget
            except Exception:
                if logger: logger.exception(f"CRITICAL: Failed to initialize {widget_name}")
                # Use a proper QWidget fallback
                placeholder = QWidget()
                layout = QVBoxLayout(placeholder)
                layout.addWidget(QLabel(f"{widget_name} failed to initialize. Check logs."))
                self.stacked_widget.addWidget(placeholder)
                self.screens[widget_name] = placeholder
                setattr(self, widget_name, placeholder)
                return placeholder

        # 1. Login Screen (Page 0)
        _safe_add('login_screen', LoginScreen, 
                  connect_fn=lambda w: w.login_successful.connect(self.on_login_success))
        
        # 2. Functional Screens
        _safe_add('dashboard_screen', DashboardScreen, post_init=lambda w: w.set_main_window(self))
        _safe_add('inventory_screen', InventoryScreen)
        _safe_add('sales_screen', SalesScreen, connect_fn=lambda w: w.sale_completed.connect(self.on_sale_completed))
        _safe_add('customers_screen', CustomersScreen)
        _safe_add('reports_screen', ReportsScreen)
        _safe_add('settings_screen', SettingsScreen)
        
        self.data_changed.connect(self.global_refresh)

    def global_refresh(self):
        try:
            if 'dashboard_screen' in self.screens: self.dashboard_screen.refresh_data()
            if 'inventory_screen' in self.screens: self.inventory_screen.refresh_data()
            if 'customers_screen' in self.screens: self.customers_screen.refresh_data()
            if 'reports_screen' in self.screens: self.reports_screen.refresh_data()
        except Exception:
            if logger: logger.exception("Failed during global UI refresh")
    
    def show_login_screen(self):
        """Reset UI to Login State"""
        self.header_container.setVisible(False)
        if 'login_screen' in self.screens and hasattr(self.login_screen, 'clear_fields'):
            self.login_screen.clear_fields()
        self.stacked_widget.setCurrentWidget(self.login_screen)
        self.current_user = None

    def on_login_success(self, user):
        """Switch to Dashboard upon successful login"""
        try:
            if logger: logger.info(f"Login success for {user.username}")
            self.current_user = user
            self.update_branding_title()
            
            # Show Header
            self.header_container.setVisible(True)
            if hasattr(self, 'profile_widget'): self.profile_widget.update_user_info(user)
            self.nav_bar.set_role(user.role)
            
            # PERSONA REQUEST: Fix the 'Set User' Crash
            for screen_name, screen in self.screens.items():
                try:
                    if hasattr(screen, 'set_current_user'):
                        screen.set_current_user(user)
                    elif screen_name == "sales_screen":
                        screen.current_user = user
                except Exception:
                    if logger: logger.error(f"Failed to set user for screen: {screen_name}")

            # Move to Dashboard
            self.show_dashboard()
            
            # Post-login background tasks
            QTimer.singleShot(100, self.start_background_services)
            
            if user.role == "admin": self._check_backup_reminder()
        except Exception:
            if logger: logger.exception("Error during on_login_success")

    def start_background_services(self):
        """Move heavy services to background threads if needed"""
        from config.app_config import AppConfig
        if AppConfig.get_setting("auto_cloud_backup_enabled", "0") == "1":
            if logger: logger.info("Starting background cloud sync services...")
            from utils.cloud_sync import SyncManager
            if self.sync_manager is None:
                self.sync_manager = SyncManager() 
            
            if self.backup_timer is None:
                self.backup_timer = QTimer(self)
                if hasattr(self.sync_manager, "start_sync"):
                    self.backup_timer.timeout.connect(self.sync_manager.start_sync)
                    self.backup_timer.start(15 * 60 * 1000) # 15 mins

    def _check_backup_reminder(self):
        try:
            from database.database import DatabaseService
            from ui.custom_dialog import CustomWarningDialog
            sync_setting = DatabaseService.get_setting("last_cloud_sync")
            if not sync_setting or not sync_setting.value:
                dialog = CustomWarningDialog("Backup Reminder", "SAFETY REMINDER: Please sync to Google Drive.", self)
                dialog.exec()
        except Exception: pass
    
    def on_nav_changed(self, btn_id):
        if btn_id == 0: self.show_dashboard()
        elif btn_id == 1: self.show_inventory()
        elif btn_id == 2: self.show_sales()
        elif btn_id == 3: self.show_customers()
        elif btn_id == 4: self.show_reports()
        elif btn_id == 5: self.show_settings()
    
    def show_dashboard(self):
        if hasattr(self.dashboard_screen, 'update_dashboard'):
            self.dashboard_screen.update_dashboard()
        self.stacked_widget.setCurrentWidget(self.dashboard_screen)
        self.nav_bar.set_active_btn(0)
    
    def show_inventory(self):
        if hasattr(self.inventory_screen, 'load_inventory_data'):
            self.inventory_screen.load_inventory_data()
        self.stacked_widget.setCurrentWidget(self.inventory_screen)
        self.nav_bar.set_active_btn(1)
    
    def show_sales(self):
        if hasattr(self.sales_screen, 'load_product_data'):
            self.sales_screen.load_product_data()
            self.sales_screen.load_customers()
        self.stacked_widget.setCurrentWidget(self.sales_screen)
        self.nav_bar.set_active_btn(2)
    
    def show_customers(self):
        if hasattr(self.customers_screen, 'load_customer_data'):
            self.customers_screen.load_customer_data()
        self.stacked_widget.setCurrentWidget(self.customers_screen)
        self.nav_bar.set_active_btn(3)
    
    def show_reports(self):
        if hasattr(self.reports_screen, 'load_report_data'):
            self.reports_screen.load_report_data()
        self.stacked_widget.setCurrentWidget(self.reports_screen)
        self.nav_bar.set_active_btn(4)
    
    def show_settings(self):
        # DEFENSIVE: Check if screen is valid instance
        if hasattr(self.settings_screen, 'load_all_settings_data'):
            try:
                self.settings_screen.load_all_settings_data()
            except Exception:
                if logger: logger.error("Failed to load settings data")
        
        self.stacked_widget.setCurrentWidget(self.settings_screen)
        self.nav_bar.set_active_btn(5)
    
    def logout(self):
        """Zero-Lag Logout: Just switch back to Login Screen"""
        if logger: logger.info("User requested logout")
        self.show_login_screen()
    
    def on_sale_completed(self):
        self.data_changed.emit()

    def closeEvent(self, event):
        """Show confirmation dialog before exiting"""
        from utils.resource_path import get_resource_path
        
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle('Exit Confirmation')
        msg_box.setText("Are you sure you want to exit the application?")
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg_box.setDefaultButton(QMessageBox.No)
        msg_box.setIcon(QMessageBox.Question)
        
        # Apply icon to message box
        icon_path = get_resource_path(os.path.join("assets", "app_icon.ico"))
        if icon_path:
            msg_box.setWindowIcon(QIcon(icon_path))
            
        reply = msg_box.exec()
        
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName("Inventory Management System")
    app.setApplicationVersion("1.0")
    app.setStyle("Fusion")

    try:
        global logger
        from utils.logger import logger, exception_hook
        sys.excepthook = exception_hook
        
        # CRITICAL: Initialize database schema and default users BEFORE any other logic
        from database.init_db import init_database_with_default_admin
        init_database_with_default_admin()
        
        from config.app_config import AppConfig
        
        # 1. SETUP WIZARD (AppData Check for Persistence)
        config_exists = AppConfig.load_config()
        if not config_exists:
            if logger: logger.info("First run detected: Showing Setup Wizard")
            from ui.setup_wizard import SetupWizard
            wizard = SetupWizard()
            if wizard.exec() != SetupWizard.Accepted:
                return 0
        
        # 2. MAIN WINDOW (One Window to Rule Them All)
        main_window = MainWindow()
        main_window.show()
        main_window.raise_()
        main_window.activateWindow()
        
        return app.exec()
            
    except Exception as e:
        error_details = traceback.format_exc()
        if logger: logger.error(f"Startup error: {error_details}")
        QMessageBox.critical(None, "Startup Error", f"The application failed to start:\n\n{str(e)}\n\nCheck logs for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
