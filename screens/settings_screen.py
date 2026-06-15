from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QStackedWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QFormLayout,
    QLineEdit, QComboBox, QDoubleSpinBox, QCheckBox, QDialog, QDialogButtonBox,
    QScrollArea, QMessageBox, QFileDialog, QListView
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QColor
from loguru import logger
from datetime import datetime
from pathlib import Path
import sys

from database.models import User
from services.inventory_service import InventoryService
from services.customer_service import CustomerService
from services.auth_service import AuthService
from database.database import DatabaseService
from config.app_config import AppConfig
from screens.about_screen import AboutScreen
from utils.cloud_service import CloudService

from core.config import IS_PREMIUM

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
    A modern, high-fidelity Admin Control Center with a sidebar layout.
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

        # Create pages
        self.access_denied_page = self._create_access_denied_page()
        self.inventory_page = self._create_inventory_pricing_page()
        self.category_page = self._create_category_management_page()
        self.pos_page = self._create_pos_permissions_page()
        self.backup_page = self._create_backup_restore_page()
        self.security_page = self._create_security_page()
        self.about_page = AboutScreen()

        # Sidebar
        sidebar = self._create_sidebar()
        main_layout.addWidget(sidebar)

        # Content Panel
        self.content_stack = QStackedWidget()
        
        # Container for stack and save button
        main_content_container = QWidget()
        main_content_layout = QVBoxLayout(main_content_container)
        main_content_layout.setContentsMargins(0,0,0,0)
        main_content_layout.setSpacing(0)
        main_content_layout.addWidget(self.content_stack)
        
        self.save_btn = QPushButton("Save All Changes")
        self.save_btn.setFixedHeight(45)
        self.save_btn.setFixedWidth(200)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #059669;
                color: white;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #047857; }
        """)
        self.save_btn.clicked.connect(self._save_all_settings)
        
        save_layout = QHBoxLayout()
        save_layout.setContentsMargins(32, 10, 32, 20)
        save_layout.addStretch()
        save_layout.addWidget(self.save_btn)
        main_content_layout.addLayout(save_layout)

        # Add pages to stack
        self.content_stack.addWidget(self.access_denied_page)
        self.content_stack.addWidget(self.inventory_page)
        self.content_stack.addWidget(self.category_page)
        self.content_stack.addWidget(self.pos_page)
        self.content_stack.addWidget(self.backup_page)
        self.content_stack.addWidget(self.security_page)
        self.content_stack.addWidget(self.about_page)

        main_layout.addWidget(main_content_container, 1)

    def set_current_user(self, user: User):
        self.current_user = user
        self._apply_role_based_access()
        if user.role == "admin":
            self.load_all_settings_data()

    def _apply_role_based_access(self):
        is_admin = self.current_user and self.current_user.role == "admin"
        self.sidebar_widget.setVisible(True)
        self.save_btn.setVisible(is_admin)

        for btn in self.nav_buttons:
            if btn.property("admin_only"):
                btn.setVisible(is_admin)

        if not is_admin:
            self.content_stack.setCurrentWidget(self.about_page)
            for btn in self.nav_buttons:
                if btn.text() == "About & Licensing":
                    btn.setChecked(True)
                    break
        else:
            self.content_stack.setCurrentWidget(self.inventory_page)
            if self.nav_buttons:
                self.nav_buttons[0].setChecked(True)

    def load_all_settings_data(self):
        self._load_category_data()
        self._load_pos_settings()
        self._load_inventory_settings()
        self._load_user_data()
        self._refresh_bulk_categories()

    def _refresh_bulk_categories(self):
        try:
            categories = InventoryService.get_all_categories()
            self.bulk_cat_combo.clear()
            self.bulk_cat_combo.addItem("Select Category")
            for cat in categories:
                self.bulk_cat_combo.addItem(cat['name'])
        except Exception as e:
            logger.error(f"Failed to load bulk categories: {e}")

    def _save_all_settings(self):
        try:
            DatabaseService.update_setting("business_name", self.store_name_input.text())
            DatabaseService.update_setting("business_address", self.address_input.text())
            currency_text = self.currency_combo.currentText()
            if "(" in currency_text and ")" in currency_text:
                symbol = currency_text.split('(')[1].split(')')[0]
                DatabaseService.update_setting("currency_symbol", symbol)

            DatabaseService.update_setting("allow_sales_rep_discounts", "1" if self.perm_discounts.isChecked() else "0")
            DatabaseService.update_setting("show_reports_to_sales_rep", "1" if self.perm_reports.isChecked() else "0")
            DatabaseService.update_setting("show_cost_to_sales_rep", "1" if self.perm_costs.isChecked() else "0")
            DatabaseService.update_setting("global_markup", str(self.markup_input.value()))
            DatabaseService.update_setting("low_stock_threshold", str(self.low_stock_input.value()))
            
            QMessageBox.information(self, "Success", "All settings have been saved successfully.")
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save settings: {str(e)}")

    def _create_sidebar(self):
        self.sidebar_widget = QFrame()
        self.sidebar_widget.setObjectName("Sidebar")
        self.sidebar_widget.setStyleSheet("#Sidebar { background-color: #FFFFFF; border-right: 1px solid #E5E7EB; }")
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
        
        return self.sidebar_widget

    def _create_nav_button(self, text):
        btn = QPushButton(text)
        btn.setCheckable(True)
        btn.setAutoExclusive(True)
        btn.setFixedHeight(45)
        btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #4B5563;
                border: none;
                border-radius: 8px;
                text-align: left;
                padding-left: 15px;
                font-weight: 600;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #F9FAFB; }
            QPushButton:checked { background-color: #EFF6FF; color: #2563EB; }
        """)
        return btn

    def _create_page_widget(self, title):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(20)
        layout.setAlignment(Qt.AlignTop)

        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #111827;")
        layout.addWidget(title_label)
        
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(20)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setAlignment(Qt.AlignTop)
        layout.addWidget(content_widget)

        return container, content_layout

    def _create_card_frame(self):
        card = QFrame()
        card.setStyleSheet("background-color: white; border-radius: 12px; border: 1px solid #E5E7EB;")
        return card

    def _create_access_denied_page(self):
        page, layout = self._create_page_widget("Access Denied")
        return page

    def _create_inventory_pricing_page(self):
        page, layout = self._create_page_widget("Inventory & Pricing")
        card = self._create_card_frame()
        card_layout = QFormLayout(card)
        card_layout.setContentsMargins(20, 20, 20, 20)
        self.markup_input = QDoubleSpinBox()
        self.markup_input.setSuffix(" %")
        card_layout.addRow("Global Markup:", self.markup_input)
        self.low_stock_input = QDoubleSpinBox()
        card_layout.addRow("Low Stock Threshold:", self.low_stock_input)
        layout.addWidget(card)
        
        bulk_card = self._create_card_frame()
        bulk_layout = QVBoxLayout(bulk_card)
        bulk_layout.setContentsMargins(20, 20, 20, 20)
        bulk_form = QFormLayout()
        self.bulk_cat_combo = QComboBox()
        bulk_form.addRow("Category:", self.bulk_cat_combo)
        self.bulk_percent_input = QDoubleSpinBox()
        self.bulk_percent_input.setSuffix(" %")
        bulk_form.addRow("Percentage:", self.bulk_percent_input)
        bulk_layout.addLayout(bulk_form)
        self.apply_bulk_btn = QPushButton("Apply Bulk Update")
        self.apply_bulk_btn.clicked.connect(self._apply_bulk_price_update)
        bulk_layout.addWidget(self.apply_bulk_btn)
        layout.addWidget(bulk_card)
        return page

    def _apply_bulk_price_update(self):
        category = self.bulk_cat_combo.currentText()
        percentage = self.bulk_percent_input.value()
        if not category or category == "Select Category": return
        if QMessageBox.question(self, "Confirm", f"Update prices for {category}?", QMessageBox.Yes|QMessageBox.No) == QMessageBox.Yes:
            InventoryService.bulk_price_update(category, percentage, self.current_user.role)
            QMessageBox.information(self, "Success", "Prices updated.")

    def _create_category_management_page(self):
        page, layout = self._create_page_widget("Category Management")
        add_btn = QPushButton("+ Add New Category")
        add_btn.setFixedWidth(180)
        add_btn.clicked.connect(self._add_category)
        layout.addWidget(add_btn, 0, Qt.AlignRight)
        
        self.category_table = QTableWidget()
        self.category_table.setColumnCount(3)
        self.category_table.setHorizontalHeaderLabels(["Category Name", "Description", "Actions"])
        
        # ULTRA-STIFF CONFIG
        h = self.category_table.horizontalHeader()
        h.setSectionResizeMode(QHeaderView.Fixed)
        self.category_table.setColumnWidth(0, 250)
        self.category_table.setColumnWidth(1, 400)
        self.category_table.setColumnWidth(2, 180)
        h.setSectionsMovable(False)
        h.setSectionsClickable(False)
        
        self.category_table.verticalHeader().setVisible(False)
        self.category_table.verticalHeader().setDefaultSectionSize(75)
        self.category_table.setMinimumHeight(450)
        self.category_table.setStyleSheet("background-color: white; border-radius: 8px;")
        layout.addWidget(self.category_table)
        return page

    def _create_pos_permissions_page(self):
        page, layout = self._create_page_widget("POS & General Settings")
        card = self._create_card_frame()
        form = QFormLayout(card)
        form.setContentsMargins(20,20,20,20)
        self.store_name_input = QLineEdit()
        form.addRow("Store Name:", self.store_name_input)
        self.address_input = QLineEdit()
        form.addRow("Address:", self.address_input)
        self.currency_combo = QComboBox()
        self.currency_combo.addItems(["GHS (GHS)", "USD ($)"])
        form.addRow("Currency:", self.currency_combo)
        layout.addWidget(card)
        
        perm_card = self._create_card_frame()
        p_layout = QVBoxLayout(perm_card)
        p_layout.setContentsMargins(20,20,20,20)
        self.perm_discounts = QCheckBox("Allow Discounts")
        self.perm_reports = QCheckBox("Show Reports")
        self.perm_costs = QCheckBox("Show Cost Prices")
        p_layout.addWidget(self.perm_discounts)
        p_layout.addWidget(self.perm_reports)
        p_layout.addWidget(self.perm_costs)
        layout.addWidget(perm_card)
        return page

    def _create_backup_restore_page(self):
        """REFACTORED: High-Fidelity Backup & Restore Center."""
        page, layout = self._create_page_widget("Backup & Restore")
        self.cloud_service = CloudService()
        
        self.cloud_status_label = QLabel("Cloud Status: Checking...")
        self.cloud_status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #DC2626; margin-bottom: 10px;")
        layout.addWidget(self.cloud_status_label)

        local_title = QLabel("Local Database Operations")
        local_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #2C3E50;")
        layout.addWidget(local_title)

        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(20)
        
        # Backup Card
        backup_card = self._create_card_frame()
        backup_card.setFixedWidth(300)
        backup_card_layout = QVBoxLayout(backup_card)
        backup_card_layout.setAlignment(Qt.AlignCenter)
        backup_card_layout.setContentsMargins(20, 20, 20, 20)
        backup_card_layout.setSpacing(15)
        
        backup_icon = QLabel("📦")
        backup_icon.setStyleSheet("font-size: 32px;")
        backup_desc = QLabel("Create a local snapshot of your entire database (.db).")
        backup_desc.setWordWrap(True)
        backup_desc.setAlignment(Qt.AlignCenter)
        backup_desc.setStyleSheet("color: #6B7280; font-size: 12px;")
        
        self.sys_backup_btn = QPushButton("BACKUP NOW")
        self.sys_backup_btn.setFixedSize(160, 40)
        self.sys_backup_btn.setStyleSheet("background-color: #059669; color: white; border-radius: 6px; font-weight: bold;")
        self.sys_backup_btn.clicked.connect(self._handle_system_backup)
        
        backup_card_layout.addWidget(backup_icon)
        backup_card_layout.addWidget(backup_desc)
        backup_card_layout.addWidget(self.sys_backup_btn, 0, Qt.AlignCenter)
        
        # Restore Card
        restore_card = self._create_card_frame()
        restore_card.setFixedWidth(300)
        restore_card_layout = QVBoxLayout(restore_card)
        restore_card_layout.setAlignment(Qt.AlignCenter)
        restore_card_layout.setContentsMargins(20, 20, 20, 20)
        restore_card_layout.setSpacing(15)
        
        restore_icon = QLabel("🔄")
        restore_icon.setStyleSheet("font-size: 32px;")
        restore_desc = QLabel("Restore your data from a previously saved .db file.")
        restore_desc.setWordWrap(True)
        restore_desc.setAlignment(Qt.AlignCenter)
        restore_desc.setStyleSheet("color: #6B7280; font-size: 12px;")
        
        self.local_restore_btn = QPushButton("IMPORT .DB")
        self.local_restore_btn.setFixedSize(160, 40)
        self.local_restore_btn.setStyleSheet("background-color: #F59E0B; color: white; border-radius: 6px; font-weight: bold;")
        self.local_restore_btn.clicked.connect(self._local_restore)
        
        restore_card_layout.addWidget(restore_icon)
        restore_card_layout.addWidget(restore_desc)
        restore_card_layout.addWidget(self.local_restore_btn, 0, Qt.AlignCenter)
        
        cards_layout.addWidget(backup_card)
        cards_layout.addWidget(restore_card)
        cards_layout.addStretch()
        layout.addLayout(cards_layout)

        cloud_title = QLabel("Cloud Sync (Google Drive)")
        cloud_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #2C3E50; margin-top: 20px;")
        layout.addWidget(cloud_title)

        cloud_card = self._create_card_frame()
        cloud_layout = QVBoxLayout(cloud_card)
        cloud_layout.setContentsMargins(25, 25, 25, 25)
        
        cloud_h_layout = QHBoxLayout()
        cloud_h_layout.setSpacing(15)
        
        self.link_drive_btn = QPushButton("Link Google Drive")
        self.link_drive_btn.setFixedSize(180, 40)
        self.link_drive_btn.setStyleSheet("background-color: #2563EB; color: white; border-radius: 6px; font-weight: bold;")
        
        self.unlink_drive_btn = QPushButton("Unlink Account")
        self.unlink_drive_btn.setFixedSize(140, 40)
        self.unlink_drive_btn.setStyleSheet("color: #DC2626; border: 1px solid #FECACA; border-radius: 6px; font-weight: 500;")
        self.unlink_drive_btn.clicked.connect(self._unlink_google_drive)
        
        self.sync_cloud_btn = QPushButton("Sync to Cloud")
        self.sync_cloud_btn.setFixedSize(160, 40)
        self.sync_cloud_btn.setStyleSheet("background-color: #059669; color: white; border-radius: 6px; font-weight: bold;")
        self.sync_cloud_btn.clicked.connect(self._sync_to_cloud)
        
        self.cloud_restore_btn = QPushButton("Cloud Restore")
        self.cloud_restore_btn.setFixedSize(160, 40)
        self.cloud_restore_btn.setStyleSheet("background-color: #F59E0B; color: white; border-radius: 6px; font-weight: bold;")
        self.cloud_restore_btn.clicked.connect(self._restore_from_cloud)
        
        cloud_h_layout.addWidget(self.link_drive_btn)
        cloud_h_layout.addWidget(self.unlink_drive_btn)
        cloud_h_layout.addWidget(self.sync_cloud_btn)
        cloud_h_layout.addWidget(self.cloud_restore_btn)
        cloud_h_layout.addStretch()
        
        cloud_layout.addLayout(cloud_h_layout)
        layout.addWidget(cloud_card)
        
        self._update_drive_status()
        self.link_drive_btn.clicked.connect(self._link_google_drive)
        return page

    def _create_security_page(self):
        page, layout = self._create_page_widget("Security & User Management")
        self.user_table = QTableWidget()
        self.user_table.setColumnCount(4)
        self.user_table.setHorizontalHeaderLabels(["Username", "Full Name", "Role", "Actions"])
        
        h = self.user_table.horizontalHeader()
        h.setSectionResizeMode(QHeaderView.Fixed)
        self.user_table.setColumnWidth(0, 180)
        self.user_table.setColumnWidth(1, 300)
        self.user_table.setColumnWidth(2, 140)
        self.user_table.setColumnWidth(3, 200)
        h.setSectionsMovable(False)
        h.setSectionsClickable(False)
        
        self.user_table.verticalHeader().setVisible(False)
        self.user_table.verticalHeader().setDefaultSectionSize(75)
        self.user_table.setMinimumHeight(400)
        self.user_table.setStyleSheet("background-color: white; border-radius: 8px;")
        layout.addWidget(self.user_table)
        return page

    def _load_user_data(self):
        try:
            users = AuthService.get_all_users()
            self.user_table.setRowCount(len(users))
            for row, user in enumerate(users):
                self.user_table.setItem(row, 0, QTableWidgetItem(user.username))
                self.user_table.setItem(row, 1, QTableWidgetItem(user.full_name))
                self.user_table.setItem(row, 2, QTableWidgetItem(user.role))
                
                actions_widget = QWidget()
                actions_widget.setFixedWidth(200)
                actions_layout = QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(10, 0, 10, 0)
                actions_layout.setAlignment(Qt.AlignCenter)

                reset_btn = QPushButton("RESET PASSWORD")
                reset_btn.setFixedSize(170, 35)
                reset_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #EFF6FF;
                        color: #1D4ED8;
                        border: 1px solid #BFDBFE;
                        border-radius: 6px;
                        font-weight: bold;
                        font-size: 11px;
                    }
                    QPushButton:hover { background-color: #DBEAFE; }
                """)
                reset_btn.setCursor(Qt.PointingHandCursor)
                reset_btn.clicked.connect(lambda checked=False, u=user: self._reset_password_dialog(u))
                actions_layout.addWidget(reset_btn)
                self.user_table.setCellWidget(row, 3, actions_widget)
        except Exception as e:
            logger.error(f"Failed to load users: {e}")

    def _load_category_data(self):
        self.category_table.setRowCount(0)
        try:
            categories = InventoryService.get_all_categories()
            self.category_table.setRowCount(len(categories))
            for row, category in enumerate(categories):
                self.category_table.setItem(row, 0, QTableWidgetItem(category['name']))
                self.category_table.setItem(row, 1, QTableWidgetItem(category.get('description') or ''))
                
                actions_widget = QWidget()
                actions_widget.setFixedWidth(170)
                actions_layout = QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(5, 0, 5, 0)
                actions_layout.setSpacing(10)
                actions_layout.setAlignment(Qt.AlignCenter)

                edit_btn = QPushButton("EDIT")
                edit_btn.setFixedSize(70, 35)
                edit_btn.setStyleSheet("background-color: #EFF6FF; color: #1D4ED8; border: 1px solid #BFDBFE; border-radius: 6px; font-weight: bold; font-size: 10px;")
                edit_btn.clicked.connect(lambda c=False, cat=category: self._edit_category(cat))

                delete_btn = QPushButton("DELETE")
                delete_btn.setFixedSize(75, 35)
                delete_btn.setStyleSheet("background-color: #FEF2F2; color: #DC2626; border: 1px solid #FECACA; border-radius: 6px; font-weight: bold; font-size: 10px;")
                delete_btn.clicked.connect(lambda c=False, cat_id=category['id']: self._delete_category(cat_id))

                actions_layout.addWidget(edit_btn)
                actions_layout.addWidget(delete_btn)
                self.category_table.setCellWidget(row, 2, actions_widget)
        except Exception as e:
            logger.error(f"Failed to load categories: {e}")

    def _add_category(self):
        dialog = CategoryDialog(self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            if data['name']:
                InventoryService.add_category(data)
                self._load_category_data()

    def _edit_category(self, category_data):
        dialog = CategoryDialog(self, category_data)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            if data['name']:
                data['id'] = category_data['id']
                InventoryService.update_category(data)
                self._load_category_data()

    def _delete_category(self, category_id):
        category = InventoryService.get_category_by_id(category_id)
        if not category: return
        with DatabaseService.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM products WHERE category = ?", (category['name'],))
            count = cursor.fetchone()[0]
        if count > 0:
            QMessageBox.critical(self, "Deletion Blocked", f"STRICT REQUIREMENT: Category '{category['name']}' has {count} products. Reassign them first.")
            return
        if QMessageBox.question(self, "Delete", f"Delete empty category '{category['name']}'?", QMessageBox.Yes|QMessageBox.No) == QMessageBox.Yes:
            InventoryService.delete_category(category_id)
            self._load_category_data()
            self._refresh_bulk_categories()

    def _reset_password_dialog(self, target_user):
        from PySide6.QtWidgets import QInputDialog
        new_pass, ok1 = QInputDialog.getText(self, "Reset Password", f"New password for {target_user.username}:", QLineEdit.Password)
        if not ok1 or not new_pass: return
        admin_pass, ok2 = QInputDialog.getText(self, "Verify", "Enter Admin Password:", QLineEdit.Password)
        if not ok2 or not admin_pass: return
        if AuthService.admin_reset_user_password(self.current_user, admin_pass, target_user.id, new_pass):
            QMessageBox.information(self, "Success", "Password reset.")
        else:
            QMessageBox.critical(self, "Error", "Verification failed.")

    def _handle_system_backup(self):
        import shutil
        db_path = AppConfig.get_db_path()
        backup_dir = AppConfig.get_data_dir() / "logs"
        backup_dir.mkdir(parents=True, exist_ok=True)
        dest_path = backup_dir / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        shutil.copy2(db_path, dest_path)
        QMessageBox.information(self, "Success", f"Backup created in {backup_dir}")

    def _local_restore(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Backup", "", "Database Files (*.db)")
        if not file_path: return
        if QMessageBox.critical(self, "Warning", "OVERWRITE current data?", QMessageBox.Yes|QMessageBox.No) == QMessageBox.Yes:
            import shutil
            db_path = AppConfig.get_db_path()
            shutil.copy2(db_path, f"{db_path}.bak")
            shutil.copy2(file_path, db_path)
            QMessageBox.information(self, "Success", "Restored. Restarting...")
            self._restart_application()

    def _link_google_drive(self):
        try:
            if self.cloud_service.authenticate():
                self._update_drive_status()
                QMessageBox.information(self, "Success", "Linked!")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _unlink_google_drive(self):
        if QMessageBox.question(self, "Unlink", "Disconnect Drive?", QMessageBox.Yes|QMessageBox.No) == QMessageBox.Yes:
            if self.cloud_service.unlink():
                self._update_drive_status()
                QMessageBox.information(self, "Success", "Unlinked.")

    def _sync_to_cloud(self):
        try:
            db_path = AppConfig.get_db_path()
            filename = self.cloud_service.upload_backup(db_path)
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            DatabaseService.update_setting("last_cloud_sync", now_str)
            self._update_drive_status() 
            QMessageBox.information(self, "Success", f"Uploaded: {filename}")
        except Exception as e:
            logger.error(f"Sync failed: {e}")
            QMessageBox.critical(self, "Error", str(e))

    def _restore_from_cloud(self):
        try:
            backups = self.cloud_service.list_backups()[:5]
            if not backups:
                QMessageBox.information(self, "No Backups", "No backups on Drive.")
                return
            from PySide6.QtWidgets import QInputDialog
            items = [f"{b['name']} ({b['createdTime'][:10]})" for b in backups]
            item, ok = QInputDialog.getItem(self, "Select Version", "Choose backup:", items, 0, False)
            if ok and item:
                admin_pass, ok_pass = QInputDialog.getText(self, "Security", "Enter Admin Password:", QLineEdit.Password)
                if not ok_pass: return
                if not AuthService.authenticate_user(self.current_user.username, admin_pass):
                    QMessageBox.critical(self, "Error", "Invalid password.")
                    return
                selected = backups[items.index(item)]
                if QMessageBox.critical(self, "Warning", "OVERWRITE current data?", QMessageBox.Yes|QMessageBox.No) == QMessageBox.Yes:
                    db_path = AppConfig.get_db_path()
                    if self.cloud_service.download_and_restore(selected['id'], db_path):
                        QMessageBox.information(self, "Success", "Restored. Restarting...")
                        self._restart_application()
        except Exception as e:
            logger.error(f"Cloud restore failed: {e}")
            QMessageBox.critical(self, "Error", str(e))

    def _restart_application(self):
        import os
        import sys
        from PySide6.QtWidgets import QApplication
        QApplication.quit()
        os.execl(sys.executable, sys.executable, *sys.argv)

    def _update_drive_status(self):
        is_linked = self.cloud_service.is_linked()
        sync_setting = DatabaseService.get_setting("last_cloud_sync")
        last_sync = sync_setting.value if sync_setting else "Never"
        if is_linked:
            email = self.cloud_service.get_user_email() or "Linked"
            self.cloud_status_label.setText(f"Cloud Status: ✓ {email} | Last Sync: {last_sync}")
            self.cloud_status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #16A34A; margin-bottom: 10px;")
            self.link_drive_btn.setVisible(False)
            self.unlink_drive_btn.setVisible(True)
            self.sync_cloud_btn.setEnabled(True)
            self.cloud_restore_btn.setEnabled(True)
        else:
            self.cloud_status_label.setText("Cloud Status: Not Linked")
            self.cloud_status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #DC2626; margin-bottom: 10px;")
            self.link_drive_btn.setVisible(True)
            self.unlink_drive_btn.setVisible(False)
            self.sync_cloud_btn.setEnabled(False)
            self.cloud_restore_btn.setEnabled(False)

    def _go_to_dashboard(self):
        main_window = self.window()
        if hasattr(main_window, 'show_dashboard'): main_window.show_dashboard()

    def _load_pos_settings(self):
        b = DatabaseService.get_setting("business_name")
        self.store_name_input.setText(b.value if b else "")
        a = DatabaseService.get_setting("business_address")
        self.address_input.setText(a.value if a else "")
        c = DatabaseService.get_setting("currency_symbol")
        if c:
            for i in range(self.currency_combo.count()):
                if c.value in self.currency_combo.itemText(i):
                    self.currency_combo.setCurrentIndex(i)
                    break
        d = DatabaseService.get_setting("allow_sales_rep_discounts")
        self.perm_discounts.setChecked(d.value == "1" if d else False)
        r = DatabaseService.get_setting("show_reports_to_sales_rep")
        self.perm_reports.setChecked(r.value == "1" if r else False)
        co = DatabaseService.get_setting("show_cost_to_sales_rep")
        self.perm_costs.setChecked(co.value == "1" if co else False)

    def _load_inventory_settings(self):
        m = DatabaseService.get_setting("global_markup")
        if m: self.markup_input.setValue(float(m.value))
        l = DatabaseService.get_setting("low_stock_threshold")
        if l: self.low_stock_input.setValue(float(l.value))
