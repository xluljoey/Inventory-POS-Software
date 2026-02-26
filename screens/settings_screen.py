from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QStackedWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QFormLayout,
    QLineEdit, QComboBox, QDoubleSpinBox, QCheckBox, QDialog, QDialogButtonBox,
    QScrollArea, QMessageBox
)
from PySide6.QtCore import Qt, QSize, QTimer # Added QTimer
from PySide6.QtGui import QFont, QColor
from loguru import logger
from datetime import datetime
from pathlib import Path

from database.models import User
from services.inventory_service import InventoryService
from services.customer_service import CustomerService
from services.auth_service import AuthService
from database.database import DatabaseService
from config.app_config import AppConfig
from screens.about_screen import AboutScreen
from utils.cloud_service import CloudService

# from core.config import IS_PREMIUM # IS_PREMIUM is commented out in main.py, so I'll comment it here too.

# --- New/Improved Dialogs for CRUD Operations ---

class CategoryDialog(QDialog):
    """A dialog for adding or editing a category."""
    def __init__(self, parent=None, category_data=None):
        super().__init__(parent)
        self.category_data = category_data
        title = "Edit Category" if category_data else "Add New Category"
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.name_input = QLineEdit()
        self.name_input.setObjectName("inputField")
        form_layout.addRow("Category Name:", self.name_input)

        self.description_input = QLineEdit()
        self.description_input.setObjectName("inputField")
        form_layout.addRow("Description:", self.description_input)

        if category_data:
            self.name_input.setText(category_data.get('name', ''))
            self.description_input.setText(category_data.get('description', ''))

        layout.addLayout(form_layout)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_data(self):
        return {
            'name': self.name_input.text().strip(),
            'description': self.description_input.text().strip(),
        }

# --- Main Settings Screen Rebuild ---

class SettingsScreen(QWidget):
    """
    A modern, high-fidelity Admin Control Center with a sidebar layout,
    rebuilt from scratch to replace the old tabbed interface.
    """
    def __init__(self):
        super().__init__()
        self.current_user = None
        self.init_ui()

    def init_ui(self):
        self.setObjectName("SettingsScreen")
        self.setStyleSheet("#SettingsScreen { background-color: #F3F4F6; }")

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Create pages first, so they exist when the sidebar is created
        self.access_denied_page = self._create_access_denied_page()
        self.inventory_page = self._create_inventory_pricing_page()
        self.category_page = self._create_category_management_page()
        self.pos_page = self._create_pos_permissions_page()
        self.backup_page = self._create_backup_restore_page()
        self.security_page = self._create_security_page()
        self.about_page = AboutScreen()

        # 1. ARCHITECTURE: Left Sidebar Navigation
        sidebar = self._create_sidebar()
        main_layout.addWidget(sidebar)

        # 2. ARCHITECTURE: Right Content Panel
        self.content_stack = QStackedWidget()
        main_layout.addWidget(self.content_stack, 1)

        # Add the created pages to the stack
        self.content_stack.addWidget(self.access_denied_page)
        self.content_stack.addWidget(self.inventory_page)
        self.content_stack.addWidget(self.category_page)
        self.content_stack.addWidget(self.pos_page)
        self.content_stack.addWidget(self.backup_page)
        self.content_stack.addWidget(self.security_page)
        self.content_stack.addWidget(self.about_page)

        # Add a single Save button at the bottom
        self.save_btn = QPushButton("Save All Changes")
        self.save_btn.setFixedHeight(40)
        self.save_btn.clicked.connect(self._save_all_settings)
        
        # Create a container for the main content and the save button
        main_content_container = QWidget()
        main_content_layout = QVBoxLayout(main_content_container)
        main_content_layout.setContentsMargins(0,0,0,0)
        main_content_layout.setSpacing(0)
        main_content_layout.addWidget(self.content_stack)
        
        # Add save button outside the stack, but within the right-side panel
        save_layout = QHBoxLayout()
        save_layout.setContentsMargins(32, 10, 32, 10)
        save_layout.addStretch()
        save_layout.addWidget(self.save_btn)
        main_content_layout.addLayout(save_layout)
        
        main_layout.addWidget(main_content_container, 1)

    def set_current_user(self, user: User):
        self.current_user = user
        self._apply_role_based_access()
        if user.role == "admin":
            self.load_all_settings_data()

    def _apply_role_based_access(self):
        """6. SECURITY: Restricts access based on user role."""
        is_admin = self.current_user and self.current_user.role == "admin"
        
        # Always show sidebar, but hide specific buttons for non-admins
        self.sidebar_widget.setVisible(True)
        self.save_btn.setVisible(is_admin)

        for btn in self.nav_buttons:
            if btn.property("admin_only"):
                btn.setVisible(is_admin)

        # ADMIN PROTECTION: Hide sensitive cloud/restore/auto-backup buttons for Sales Reps
        if hasattr(self, 'link_drive_btn'):
            is_linked = self.cloud_service.is_linked()
            self.link_drive_btn.setVisible(is_admin and not is_linked)
            self.unlink_drive_btn.setVisible(is_admin and is_linked)
            self.sync_cloud_btn.setVisible(is_admin)
            self.cloud_restore_btn.setVisible(is_admin)
            self.sys_backup_btn.setVisible(is_admin)
            self.local_restore_btn.setVisible(is_admin)
            # Auto backup toggle
            if hasattr(self, 'auto_cloud_backup_checkbox'):
                self.auto_cloud_backup_checkbox.setVisible(is_admin)

        if not is_admin:
            self.content_stack.setCurrentWidget(self.about_page)
            # Find and check the about button
            for btn in self.nav_buttons:
                if btn.text() == "About & Licensing":
                    btn.setChecked(True)
                    break
        else:
            # Default to the first actual settings page
            self.content_stack.setCurrentWidget(self.inventory_page)
            # Set the first button as active
            if self.nav_buttons:
                self.nav_buttons[0].setChecked(True)

    def load_all_settings_data(self):
        """Load data for all admin panels."""
        self._load_category_data()
        self._load_pos_settings()
        self._load_inventory_settings()
        self._load_user_data()
        self._refresh_bulk_categories()
        # Load auto-backup setting
        self._load_backup_settings() # Corrected: this method is now defined below

    def _refresh_bulk_categories(self):
        """Refresh categories in the bulk update dropdown."""
        try:
            categories = InventoryService.get_all_categories()
            self.bulk_cat_combo.clear()
            self.bulk_cat_combo.addItem("Select Category")
            for cat in categories:
                self.bulk_cat_combo.addItem(cat['name'])
        except Exception as e:
            logger.error(f"Failed to load bulk categories: {e}")

    def _save_all_settings(self):
        """Saves all settings from the UI to the database."""
        try:
            # POS & General Settings
            AppConfig.set_setting("business_name", self.store_name_input.text()) # Changed to AppConfig.set_setting
            AppConfig.set_setting("business_address", self.address_input.text()) # Changed to AppConfig.set_setting
            currency_text = self.currency_combo.currentText()
            if "(" in currency_text and ")" in currency_text:
                symbol = currency_text.split('(')[1].split(')')[0]
                AppConfig.set_setting("currency_symbol", symbol) # Changed to AppConfig.set_setting

            # Permissions (IMPLEMENTED)
            AppConfig.set_setting("allow_sales_rep_discounts", "1" if self.perm_discounts.isChecked() else "0") # Changed to AppConfig.set_setting
            AppConfig.set_setting("show_reports_to_sales_rep", "1" if self.perm_reports.isChecked() else "0") # Changed to AppConfig.set_setting
            AppConfig.set_setting("show_cost_to_sales_rep", "1" if self.perm_costs.isChecked() else "0") # Changed to AppConfig.set_setting

            # Inventory & Pricing Settings
            AppConfig.set_setting("global_markup", str(self.markup_input.value())) # Changed to AppConfig.set_setting
            AppConfig.set_setting("low_stock_threshold", str(self.low_stock_input.value())) # Changed to AppConfig.set_setting

            # Auto Backup Setting
            # This setting is saved directly by _on_auto_backup_toggled, no need to save here.
            
            QMessageBox.information(self, "Success", "All settings have been saved successfully.")
            logger.info(f"System settings updated by Admin: {self.current_user.username}")
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save settings: {str(e)}")

    # --- Sidebar Creation ---
    def _create_sidebar(self):
        self.sidebar_widget = QFrame()
        self.sidebar_widget.setObjectName("Sidebar")
        self.sidebar_widget.setStyleSheet("""
            #Sidebar {
                background-color: #FFFFFF;
                border-right: 1px solid #E5E7EB;
            }
        """)
        self.sidebar_widget.setFixedWidth(240)
        sidebar_layout = QVBoxLayout(self.sidebar_widget)
        sidebar_layout.setContentsMargins(8, 8, 8, 8)
        sidebar_layout.setSpacing(4)
        sidebar_layout.setAlignment(Qt.AlignTop)
        
        self.nav_buttons = []
        nav_options = [
            ("Inventory & Pricing", self.inventory_page, True),
            ("Category Management", self.category_page, True),
            ("POS & Transactions", self.pos_page, True),
            ("Backup & Restore", self.backup_page, True),
            ("Security", self.security_page, True),
            ("About & Licensing", self.about_page, False),
        ]

        for text, page, admin_only in nav_options:
            btn = self._create_nav_button(text)
            btn.setProperty("admin_only", admin_only)
            btn.clicked.connect(lambda checked=False, p=page: self.content_stack.setCurrentWidget(p))
            sidebar_layout.addWidget(btn)
            self.nav_buttons.append(btn)
        
        # 4. PREMIUM UPSELL: Show Upgrade button if Basic
        # if not IS_PREMIUM:
        #     sidebar_layout.addStretch()
        #     upgrade_btn = QPushButton("⭐ Upgrade to Premium")
        #     upgrade_btn.setFixedHeight(45)
        #     upgrade_btn.setCursor(Qt.PointingHandCursor)
        #     upgrade_btn.setStyleSheet("""
        #         QPushButton {
        #             background-color: #FFF7ED;
        #             color: #C2410C;
        #             border: 1px solid #FED7AA;
        #             border-radius: 8px;
        #             font-weight: bold;
        #             margin: 8px;
        #         }
        #         QPushButton:hover { background-color: #FFEDD5; }
        #     """)
        #     upgrade_btn.clicked.connect(lambda: QMessageBox.information(self, "Premium", "Contact support at joey@example.com to unlock Real-time Sync!"))
        #     sidebar_layout.addWidget(upgrade_btn)
        
        sidebar_layout.addStretch() # Ensure stretch is always there
        return self.sidebar_widget

    def _create_nav_button(self, text):
        btn = QPushButton(text)
        btn.setCheckable(True)
        btn.setAutoExclusive(True)
        btn.setFixedHeight(40)
        btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #374151;
                border: none;
                border-radius: 6px;
                text-align: left;
                padding-left: 12px;
                font-weight: 600;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #F3F4F6;
                color: #111827;
            }
            QPushButton:checked {
                background-color: #EFF6FF;
                color: #1D4ED8;
            }
        """)
        return btn

    # --- Page/Panel Creation ---

    def _create_page_widget(self, title):
        """Helper to create a standard page container."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(20)
        layout.setAlignment(Qt.AlignTop)

        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #111827;")
        layout.addWidget(title_label)
        
        # Add a scroll area for content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        layout.addWidget(scroll_area)
        
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(20)
        content_layout.setAlignment(Qt.AlignTop)
        
        scroll_area.setWidget(content_widget)

        return container, content_layout

    def _create_card_frame(self):
        """Helper to create a standard card frame."""
        card = QFrame()
        card.setObjectName("SettingsCard")
        card.setStyleSheet("""
            #SettingsCard {
                background-color: white;
                border-radius: 12px;
                border: 1px solid #E5E7EB;
            }
        """)
        return card
        
    def _create_access_denied_page(self):
        page, layout = self._create_page_widget("Access Denied")
        
        card = self._create_card_frame()
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(40, 40, 40, 40)
        card_layout.setSpacing(15)
        card_layout.setAlignment(Qt.AlignCenter)
        
        icon_label = QLabel("🚫")
        icon_label.setStyleSheet("font-size: 48px;")
        icon_label.setAlignment(Qt.AlignCenter)
        
        message_label = QLabel("You do not have permission to access this area.")
        message_label.setStyleSheet("font-size: 16px; font-weight: 500; color: #374151;")
        message_label.setAlignment(Qt.AlignCenter)
        
        back_btn = QPushButton("Back to Dashboard")
        back_btn.setFixedWidth(200)
        back_btn.clicked.connect(self._go_to_dashboard)
        
        card_layout.addWidget(icon_label)
        card_layout.addWidget(message_label)
        card_layout.addWidget(back_btn, 0, Qt.AlignCenter)
        
        layout.addWidget(card, 0, Qt.AlignCenter)
        return page

    def _create_inventory_pricing_page(self):
        """4. INVENTORY & PRICING: Dad's Primary Controls."""
        page, layout = self._create_page_widget("Inventory & Pricing")
        
        # Section: Global Thresholds
        card = self._create_card_frame()
        card_layout = QFormLayout(card)
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setSpacing(15)

        self.markup_input = QDoubleSpinBox()
        self.markup_input.setSuffix(" %")
        card_layout.addRow("Global Markup:", self.markup_input)

        self.low_stock_input = QDoubleSpinBox()
        card_layout.addRow("Low Stock Threshold:", self.low_stock_input)
        layout.addWidget(card)
        
        # Section: Bulk Price Update (IMPLEMENTED)
        bulk_card = self._create_card_frame()
        bulk_layout = QVBoxLayout(bulk_card)
        bulk_layout.setContentsMargins(20, 20, 20, 20)
        
        bulk_title = QLabel("Bulk Price Update")
        bulk_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #2C3E50;")
        bulk_layout.addWidget(bulk_title)
        
        bulk_form = QFormLayout()
        self.bulk_cat_combo = QComboBox()
        self.bulk_cat_combo.setFixedHeight(35)
        bulk_form.addRow("Select Category:", self.bulk_cat_combo)
        
        self.bulk_percent_input = QDoubleSpinBox()
        self.bulk_percent_input.setRange(-100.0, 500.0)
        self.bulk_percent_input.setSuffix(" %")
        self.bulk_percent_input.setFixedHeight(35)
        bulk_form.addRow("Adjustment Percentage:", self.bulk_percent_input)
        
        bulk_layout.addLayout(bulk_form)
        
        self.apply_bulk_btn = QPushButton("Apply Bulk Price Change")
        self.apply_bulk_btn.setObjectName("primaryButton")
        self.apply_bulk_btn.setStyleSheet("background-color: #1976D2; color: white; font-weight: bold; padding: 10px;")
        self.apply_bulk_btn.clicked.connect(self._apply_bulk_price_update)
        bulk_layout.addWidget(self.apply_bulk_btn)
        
        desc = QLabel("Note: This will increase or decrease ALL product prices in the selected category.")
        desc.setStyleSheet("color: #6B7280; font-style: italic; font-size: 12px;")
        bulk_layout.addWidget(desc)
        
        layout.addWidget(bulk_card)
        return page

    def _apply_bulk_price_update(self):
        """Execute the bulk price update logic."""
        category = self.bulk_cat_combo.currentText()
        percentage = self.bulk_percent_input.value()
        
        if not category or category == "All Categories":
            QMessageBox.warning(self, "Selection Required", "Please select a specific category.")
            return
            
        confirm = QMessageBox.question(
            self, "Confirm Bulk Update",
            f"Are you sure you want to adjust all prices in '{category}' by {percentage}%?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            try:
                count = InventoryService.bulk_price_update(category, percentage, self.current_user.role)
                QMessageBox.information(self, "Success", f"Successfully updated prices for {count} products.")
                self.bulk_percent_input.setValue(0.0)
            except Exception as e:
                logger.error(f"Bulk update failed: {e}")
                QMessageBox.critical(self, "Error", f"Failed to apply bulk update: {str(e)}")

    def _create_category_management_page(self):
        """2. NEW: CATEGORY MANAGEMENT (Admin Only)."""
        page, layout = self._create_page_widget("Category Management")
        
        # Action Bar
        action_layout = QHBoxLayout()
        action_layout.addStretch()
        add_btn = QPushButton("+ Add New Category")
        add_btn.setFixedWidth(200)
        add_btn.clicked.connect(self._add_category)
        action_layout.addWidget(add_btn)
        layout.addLayout(action_layout)
        
        # Table
        self.category_table = QTableWidget()
        self.category_table.setColumnCount(3)
        self.category_table.setHorizontalHeaderLabels(["Category Name", "Description", "Actions"])
        self.category_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.category_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.category_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.category_table.setSelectionMode(QAbstractItemView.NoSelection)
        self.category_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        layout.addWidget(self.category_table)
        
        return page

    def _create_pos_permissions_page(self):
        """5. POS & USER PERMISSIONS."""
        page, layout = self._create_page_widget("POS & General Settings")
        
        # Store Info Card
        card = self._create_card_frame()
        form_layout = QFormLayout(card)
        form_layout.setContentsMargins(20, 20, 20, 20)

        self.store_name_input = QLineEdit()
        form_layout.addRow("Store Name:", self.store_name_input)
        self.address_input = QLineEdit()
        form_layout.addRow("Address:", self.address_input)
        self.currency_combo = QComboBox()
        self.currency_combo.addItems(["GHS (GH₵)", "USD ($)"])
        form_layout.addRow("Currency:", self.currency_combo)
        layout.addWidget(card)
        
        # Permissions Matrix (IMPLEMENTED)
        perm_card = self._create_card_frame()
        perm_layout = QVBoxLayout(perm_card)
        perm_layout.setContentsMargins(20, 20, 20, 20)
        
        perm_title = QLabel("Sales Representative Permissions")
        perm_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #2C3E50; margin-bottom: 10px;")
        perm_layout.addWidget(perm_title)
        
        self.perm_discounts = QCheckBox("Allow Sales Rep to apply discounts")
        self.perm_reports = QCheckBox("Show 'Reports' tab to Sales Rep")
        self.perm_costs = QCheckBox("Allow Sales Rep to view product cost price")
        
        perm_layout.addWidget(self.perm_discounts)
        perm_layout.addWidget(self.perm_reports)
        perm_layout.addWidget(self.perm_costs)
        
        layout.addWidget(perm_card)
        return page

    def _create_backup_restore_page(self):
        """3. REFACTOR: BACKUP & RESTORE with Cloud Integration."""
        page, layout = self._create_page_widget("Backup & Restore")
        self.cloud_service = CloudService()
        
        # 1. UI SYNC: Cloud Status Label
        self.cloud_status_label = QLabel("Cloud Status: Checking...")
        self.cloud_status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #DC2626; margin-bottom: 10px;")
        layout.addWidget(self.cloud_status_label)

        # Auto Cloud Backup Toggle (New)
        self.auto_cloud_backup_checkbox = QCheckBox("Enable Auto Cloud Backup")
        self.auto_cloud_backup_checkbox.setStyleSheet("font-size: 14px; font-weight: 500; margin-top: 10px;")
        self.auto_cloud_backup_checkbox.toggled.connect(self._on_auto_backup_toggled)
        layout.addWidget(self.auto_cloud_backup_checkbox)

        # Section: Local Database Operations
        local_title = QLabel("Local Database Operations")
        local_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #2C3E50; margin-top: 20px;")
        layout.addWidget(local_title)

        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(20)
        
        # Backup Card (Refactored to "Generate System Backup")
        backup_card = self._create_card_frame()
        backup_card_layout = QVBoxLayout(backup_card)
        backup_card_layout.setAlignment(Qt.AlignCenter)
        backup_card_layout.setSpacing(15)
        backup_icon = QLabel("📦")
        backup_icon.setStyleSheet("font-size: 32px;")
        backup_desc = QLabel("Local SQLite backup + immediate Cloud Sync if linked.")
        backup_desc.setWordWrap(True)
        self.sys_backup_btn = QPushButton("Generate System Backup")
        self.sys_backup_btn.clicked.connect(self._handle_system_backup)
        backup_card_layout.addWidget(backup_icon, 0, Qt.AlignCenter)
        backup_card_layout.addWidget(backup_desc)
        backup_card_layout.addWidget(self.sys_backup_btn, 0, Qt.AlignCenter)
        
        # Restore Card (Refactored to "Local Restore")
        restore_card = self._create_card_frame()
        restore_card_layout = QVBoxLayout(restore_card)
        restore_card_layout.setAlignment(Qt.AlignCenter)
        restore_card_layout.setSpacing(15)
        restore_icon = QLabel("🔄")
        restore_icon.setStyleSheet("font-size: 32px;")
        restore_desc = QLabel("Restore from a local backup file.")
        restore_desc.setWordWrap(True)
        self.local_restore_btn = QPushButton("Local Restore")
        self.local_restore_btn.setStyleSheet("background-color: #FBC02D; color: #212121; font-weight: bold;")
        restore_card_layout.addWidget(restore_icon, 0, Qt.AlignCenter)
        restore_card_layout.addWidget(restore_desc)
        restore_card_layout.addWidget(self.local_restore_btn, 0, Qt.AlignCenter)
        
        cards_layout.addWidget(backup_card)
        cards_layout.addWidget(restore_card)
        layout.addLayout(cards_layout)

        # Section: Cloud Sync
        cloud_title = QLabel("Cloud Sync (Google Drive)")
        cloud_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #2C3E50; margin-top: 20px;")
        layout.addWidget(cloud_title)

        cloud_card = self._create_card_frame()
        cloud_layout = QVBoxLayout(cloud_card)
        cloud_layout.setContentsMargins(20, 20, 20, 20)
        
        cloud_h_layout = QHBoxLayout()
        
        self.link_drive_btn = QPushButton("Link Google Drive")
        self.link_drive_btn.setFixedWidth(200)
        
        self.unlink_drive_btn = QPushButton("Unlink Account")
        self.unlink_drive_btn.setFixedWidth(150)
        self.unlink_drive_btn.setStyleSheet("color: #D32F2F; border: 1px solid #D32F2F;")
        self.unlink_drive_btn.clicked.connect(self._unlink_google_drive)
        
        self.sync_cloud_btn = QPushButton("Sync to Cloud now")
        self.sync_cloud_btn.setFixedWidth(200)
        self.sync_cloud_btn.setStyleSheet("background-color: #1976D2; color: white; font-weight: bold;")
        self.sync_cloud_btn.clicked.connect(self._sync_to_cloud)
        
        self.cloud_restore_btn = QPushButton("Restore from Cloud")
        self.cloud_restore_btn.setFixedWidth(200)
        self.cloud_restore_btn.setStyleSheet("background-color: #FBC02D; color: #212121; font-weight: bold;")
        self.cloud_restore_btn.clicked.connect(self._restore_from_cloud)
        
        cloud_h_layout.addWidget(self.link_drive_btn)
        cloud_h_layout.addWidget(self.unlink_drive_btn)
        cloud_h_layout.addSpacing(10)
        cloud_h_layout.addWidget(self.sync_cloud_btn)
        cloud_h_layout.addSpacing(10)
        cloud_h_layout.addWidget(self.cloud_restore_btn)
        cloud_h_layout.addStretch()
        
        cloud_layout.addLayout(cloud_h_layout)
        
        cloud_note = QLabel("Note: Cloud operations require an active Google Drive link.")
        cloud_note.setStyleSheet("color: #6B7280; font-size: 12px; margin-top: 10px;")
        cloud_layout.addWidget(cloud_note)
        
        layout.addWidget(cloud_card)
        
        # Initialize Status
        self._update_drive_status()
        self.link_drive_btn.clicked.connect(self._link_google_drive)
        
        return page

    def _on_auto_backup_toggled(self, checked):
        """Save the state of the auto cloud backup checkbox to AppConfig."""
        AppConfig.set_setting("auto_cloud_backup_enabled", "1" if checked else "0")
        logger.info(f"Auto Cloud Backup Toggled: {'Enabled' if checked else 'Disabled'}")

    def _update_drive_status(self):
        """1. UI SYNC: Update status label and button states."""
        is_linked = self.cloud_service.is_linked()
        sync_setting = DatabaseService.get_setting("last_cloud_sync")
        last_sync = sync_setting.value if sync_setting else "Never"

        if is_linked:
            email = self.cloud_service.get_user_email() or "Unknown Account"
            self.cloud_status_label.setText(f"Cloud Status: ✓ Linked: {email} | Last Sync: {last_sync}")
            self.cloud_status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #16A34A; margin-bottom: 10px;")
            self.link_drive_btn.setVisible(False)
            self.unlink_drive_btn.setVisible(self.current_user.role == "admin")
            self.sync_cloud_btn.setEnabled(True)
            self.cloud_restore_btn.setEnabled(True)
            # Load auto backup state
            auto_backup_enabled = AppConfig.get_setting("auto_cloud_backup_enabled", "0") == "1"
            self.auto_cloud_backup_checkbox.setChecked(auto_backup_enabled)
            self.auto_cloud_backup_checkbox.setEnabled(True) # Enable if linked
        else:
            self.cloud_status_label.setText("Cloud Status: Not Linked")
            self.cloud_status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #DC2626; margin-bottom: 10px;")
            self.link_drive_btn.setVisible(True)
            self.link_drive_btn.setText("Link Google Drive")
            self.link_drive_btn.setStyleSheet("background-color: #1976D2; color: white; font-weight: bold;")
            self.unlink_drive_btn.setVisible(False)
            self.sync_cloud_btn.setEnabled(False)
            self.cloud_restore_btn.setEnabled(False)
            self.auto_cloud_backup_checkbox.setChecked(False) # Disable if not linked
            self.auto_cloud_backup_checkbox.setEnabled(False)

    def _unlink_google_drive(self):
        """Disconnect Google Drive account."""
        if self.current_user.role != "admin":
            QMessageBox.warning(self, "Access Denied", "Only administrators can unlink accounts.")
            return
            
        confirm = QMessageBox.question(self, "Unlink Account", 
                                     "Are you sure you want to unlink your Google Drive account?\n"
                                     "This will not delete your cloud backups, but you will need to re-authenticate to sync again.",
                                     QMessageBox.Yes | QMessageBox.No)
        
        if confirm == QMessageBox.Yes:
            if self.cloud_service.unlink():
                # Also disable auto backup if unlinked
                AppConfig.set_setting("auto_cloud_backup_enabled", "0")
                self._update_drive_status()
                QMessageBox.information(self, "Success", "Google Drive account has been unlinked.")

    def _handle_system_backup(self):
        """2. CLOUD BACKUP ACTION: Local backup followed by cloud upload."""
        try:
            # Step A: Local Backup
            import shutil
            db_path = AppConfig.get_db_path()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            local_backup_path = Path("logs") / f"local_backup_{timestamp}.db"
            shutil.copy2(db_path, local_backup_path)
            
            # Step B: Cloud Sync if linked
            cloud_msg = ""
            if self.cloud_service.is_linked():
                filename = self.cloud_service.upload_backup(db_path)
                
                # Update Sync Timestamp
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                DatabaseService.update_setting("last_cloud_sync", now_str)
                self._update_drive_status() # Refresh UI

                cloud_msg = f"\n\nCloud backup successfully uploaded as: {filename}"
                logger.info(f"System Backup: Local and Cloud sync completed at {now_str}.")
            else:
                logger.info("System Backup: Local completed (Cloud not linked).")
            
            QMessageBox.information(self, "Backup Complete", 
                                  f"Local database snapshot created in /logs folder.{cloud_msg}")
        except Exception as e:
            logger.error(f"System backup failed: {e}")
            QMessageBox.critical(self, "Backup Error", f"Failed to complete backup: {str(e)}")

    def _link_google_drive(self):
        """Perform OAuth flow to link Google Drive."""
        if self.current_user.role != "admin":
            QMessageBox.warning(self, "Access Denied", "Only administrators can link cloud accounts.")
            return
            
        try:
            if self.cloud_service.authenticate():
                self._update_drive_status()
                QMessageBox.information(self, "Success", "Google Drive has been successfully linked!")
        except Exception as e:
            logger.error(f"Failed to link Google Drive: {e}")
            QMessageBox.critical(self, "Connection Error", f"Could not authenticate with Google: {str(e)}")

    def _sync_to_cloud(self):
        """Zip and upload the database to the cloud and update timestamp."""
        if not self.cloud_service.is_linked():
            QMessageBox.warning(self, "Not Linked", "Please link your Google Drive account first.")
            return
            
        try:
            db_path = AppConfig.get_db_path()
            filename = self.cloud_service.upload_backup(db_path)
            
            # 3. STATUS WIDGET: Update Last Sync Timestamp
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            DatabaseService.update_setting("last_cloud_sync", now_str)
            self._update_drive_status() 

            QMessageBox.information(self, "Cloud Sync", f"Backup '{filename}' successfully uploaded to Google Drive.")
        except Exception as e:
            logger.error(f"Cloud sync failed: {e}")
            QMessageBox.critical(self, "Sync Error", f"Failed to upload backup: {str(e)}")

    def _restore_from_cloud(self):
        """3. RESTORE FROM CLOUD: Finalized with Password Check and Restart."""
        if self.current_user.role != "admin":
            QMessageBox.warning(self, "Access Denied", "Only administrators can restore data.")
            return
            
        if not self.cloud_service.is_linked():
            QMessageBox.warning(self, "Not Linked", "Please link your Google Drive account first.")
            return

        try:
            # a) Fetches the last 5 backup filenames
            all_backups = self.cloud_service.list_backups()
            backups = all_backups[:5] 
            
            if not backups:
                QMessageBox.information(self, "No Backups", "No backups found in your Google Drive folder.")
                return
                
            # b) Shows selection list
            from PySide6.QtWidgets import QInputDialog
            items = [f"{b['name']} ({b['createdTime'][:10]})" for b in backups]
            item, ok = QInputDialog.getItem(self, "Select Cloud Version", "Choose one of the last 5 backups:", items, 0, False)
            
            if ok and item:
                # 4. SECURITY CHECK: Require Admin Password
                admin_pass, ok_pass = QInputDialog.getText(self, "Security Verification", 
                                                    "Enter Admin password to AUTHORIZE system restore:",
                                                    QLineEdit.Password)
                if not ok_pass or not admin_pass: return

                # Authenticate
                if not AuthService.authenticate_user(self.current_user.username, admin_pass):
                    QMessageBox.critical(self, "Unauthorized", "Invalid Admin password. Restore aborted.")
                    return

                idx = items.index(item)
                selected_file = backups[idx]
                
                # 1. RESTORE WORKFLOW: Final Confirmation
                confirm = QMessageBox.critical(self, "⚠ CRITICAL WARNING ⚠", 
                                             f"You are about to OVERWRITE all local data with backup '{selected_file['name']}'.\n\n"
                                             "This action is irreversible. The application will restart immediately after.\n\n"
                                             "Do you want to proceed?",
                                             QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                
                if confirm == QMessageBox.Yes:
                    db_path = AppConfig.get_db_path()
                    if self.cloud_service.download_and_restore(selected_file['id'], db_path):
                        # 2. AUTO-RESTART: Successful replacement triggers restart
                        QMessageBox.information(self, "Restore Successful", "The system has been restored. Restarting now...")
                        self._restart_application()
        except Exception as e:
            logger.error(f"Cloud restore failed: {e}")
            QMessageBox.critical(self, "Restore Error", f"Failed to restore from cloud: {str(e)}")

    def _restart_application(self):
        """Restart the PySide6 application."""
        import os
        import sys
        QApplication.quit()
        os.execl(sys.executable, sys.executable, *sys.argv)

    def _create_security_page(self):
        """Implementation of User Management and Security Settings."""
        page, layout = self._create_page_widget("Security & User Management")
        
        card = self._create_card_frame()
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 20, 20, 20)
        
        title = QLabel("Registered Users")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #2C3E50;")
        card_layout.addWidget(title)
        
        self.user_table = QTableWidget()
        self.user_table.setColumnCount(4)
        self.user_table.setHorizontalHeaderLabels(["Username", "Full Name", "Role", "Actions"])
        self.user_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.user_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.user_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.user_table.setFixedHeight(300)
        card_layout.addWidget(self.user_table)
        
        layout.addWidget(card)
        return page

    def _load_user_data(self):
        """Load registered users into the security table."""
        try:
            users = AuthService.get_all_users()
            self.user_table.setRowCount(len(users))
            for row, user in enumerate(users):
                self.user_table.setItem(row, 0, QTableWidgetItem(user.username))
                self.user_table.setItem(row, 1, QTableWidgetItem(user.full_name))
                self.user_table.setItem(row, 2, QTableWidgetItem(user.role))
                
                reset_btn = QPushButton("Reset Password")
                reset_btn.setStyleSheet("padding: 5px; color: #1D4ED8;")
                reset_btn.setCursor(Qt.PointingHandCursor)
                reset_btn.clicked.connect(lambda checked=False, u=user: self._reset_password_dialog(u))
                self.user_table.setCellWidget(row, 3, reset_btn)
        except Exception as e:
            logger.error(f"Failed to load users: {e}")

    def _reset_password_dialog(self, target_user):
        """Trigger password reset with admin verification."""
        from PySide6.QtWidgets import QInputDialog
        
        # 1. Ask for New Password
        new_pass, ok1 = QInputDialog.getText(self, "Reset Password", 
                                          f"Enter new password for '{target_user.username}':",
                                          QLineEdit.Password)
        if not ok1 or not new_pass: return
        
        # 2. Ask for Admin Password for Security
        admin_pass, ok2 = QInputDialog.getText(self, "Security Verification", 
                                            "Enter YOUR Admin password to confirm this action:",
                                            QLineEdit.Password)
        if not ok2 or not admin_pass: return
        
        try:
            from services.auth_service import AuthService
            success = AuthService.admin_reset_user_password(self.current_user, admin_pass, target_user.id, new_pass)
            if success:
                QMessageBox.information(self, "Success", f"Password for {target_user.username} has been reset.")
            else:
                QMessageBox.critical(self, "Error", "Admin password verification failed.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to reset password: {str(e)}")

    # --- Data and Logic ---

    def _go_to_dashboard(self):
        # Find the main window and ask it to show the dashboard
        main_window = self.window()
        if hasattr(main_window, 'show_dashboard'):
            main_window.show_dashboard()

    def _load_inventory_settings(self):
        markup_setting = AppConfig.get_setting("global_markup", "0.0") # Changed to AppConfig.get_setting
        if markup_setting: # No need to check .value if it returns a string
            self.markup_input.setValue(float(markup_setting))
            
        threshold_setting = AppConfig.get_setting("low_stock_threshold", "10") # Changed to AppConfig.get_setting
        if threshold_setting: # No need to check .value if it returns a string
            self.low_stock_input.setValue(float(threshold_setting))

    def _load_pos_settings(self):
        business_name_setting = AppConfig.get_setting("business_name", "") # Changed to AppConfig.get_setting
        self.store_name_input.setText(business_name_setting)
        
        address_setting = AppConfig.get_setting("business_address", "") # Changed to AppConfig.get_setting
        self.address_input.setText(address_setting)
        
        currency_setting = AppConfig.get_setting("currency_symbol", AppConfig.CURRENCY_SYMBOL) # Changed to AppConfig.get_setting
        if currency_setting:
            # Find the item in the combobox that contains the symbol
            for i in range(self.currency_combo.count()):
                if currency_setting in self.currency_combo.itemText(i):
                    self.currency_combo.setCurrentIndex(i)
                    break
        
        # Load Permissions
        p_discounts = AppConfig.get_setting("allow_sales_rep_discounts", "0") # Changed to AppConfig.get_setting
        self.perm_discounts.setChecked(p_discounts == "1")
        
        p_reports = AppConfig.get_setting("show_reports_to_sales_rep", "0") # Changed to AppConfig.get_setting
        self.perm_reports.setChecked(p_reports == "1")
        
        p_costs = AppConfig.get_setting("show_cost_to_sales_rep", "0") # Changed to AppConfig.get_setting
        self.perm_costs.setChecked(p_costs == "1")

    def _load_backup_settings(self): # Added missing method
        """Load settings related to backup and restore."""
        auto_backup_enabled = AppConfig.get_setting("auto_cloud_backup_enabled", "0") == "1"
        self.auto_cloud_backup_checkbox.setChecked(auto_backup_enabled)
        # The checkbox's enabled state is handled by _update_drive_status based on link status.
        
    def _load_category_data(self):
        self.category_table.setRowCount(0)
        try:
            categories = InventoryService.get_all_categories()
            self.category_table.setRowCount(len(categories))
            for row, category in enumerate(categories):
                self.category_table.setItem(row, 0, QTableWidgetItem(category['name']))
                self.category_table.setItem(row, 1, QTableWidgetItem(category.get('description') or ''))
                
                # Actions
                actions_widget = QWidget()
                actions_layout = QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(0,0,0,0)
                
                edit_btn = QPushButton("✏️")
                edit_btn.setCursor(Qt.PointingHandCursor)
                edit_btn.setToolTip("Edit Category")
                edit_btn.clicked.connect(lambda c=False, r=row, cat=category: self._edit_category(cat))
                
                delete_btn = QPushButton("🗑️")
                delete_btn.setCursor(Qt.PointingHandCursor)
                delete_btn.setToolTip("Delete Category")
                delete_btn.clicked.connect(lambda c=False, r=row, cat_id=category['id']: self._delete_category(cat_id))

                actions_layout.addWidget(edit_btn)
                actions_layout.addWidget(delete_btn)
                self.category_table.setCellWidget(row, 2, actions_widget)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load categories: {str(e)}")

    def _add_category(self):
        dialog = CategoryDialog(self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            if data['name']:
                InventoryService.add_category(data)
                self._load_category_data() # Refresh
            else:
                QMessageBox.warning(self, "Validation Error", "Category name cannot be empty.")
    
    def _edit_category(self, category_data):
        dialog = CategoryDialog(self, category_data)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            if data['name']:
                data['id'] = category_data['id']
                InventoryService.update_category(data)
                self._load_category_data() # Refresh
            else:
                QMessageBox.warning(self, "Validation Error", "Category name cannot be empty.")

    def _delete_category(self, category_id):

        # 1. Fetch category name
        category = InventoryService.get_category_by_id(category_id)
        if not category: return

        # 2. Check for linked products
        with DatabaseService.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM products WHERE category = ?", (category['name'],))
            count = cursor.fetchone()[0]
            
        if count > 0:
            QMessageBox.warning(self, "Cannot Delete", 
                                f"This category is linked to {count} products. "
                                "Please reassign or delete the products first.")
            return

        reply = QMessageBox.question(self, 'Confirm Delete', 
                                     f"Are you sure you want to delete '{category['name']}'?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            InventoryService.delete_category(category_id)
            self._load_category_data() # Refresh
            self._refresh_bulk_categories()
