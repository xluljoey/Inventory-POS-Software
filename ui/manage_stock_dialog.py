from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, 
                               QWidget, QLabel, QComboBox, QLineEdit, 
                               QPushButton, QFormLayout, QTableWidget, 
                               QTableWidgetItem, QHeaderView, QMessageBox,
                               QFrame, QAbstractItemView, QDoubleSpinBox, QSpinBox, QListView, QDateEdit, QCheckBox)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont
from datetime import datetime, timedelta

from services.inventory_service import InventoryService
from ui.custom_dialog import CustomWarningDialog, CustomInfoDialog, CustomErrorDialog
from config.app_config import AppConfig # Added import

class ManageStockDialog(QDialog):
    def __init__(self, parent=None, user=None):
        super().__init__(parent)
        self.user = user
        self.setWindowTitle("Manage Stock")
        self.setModal(True)
        self.setMinimumSize(800, 700)
        
        self.all_products = []
        
        self.init_ui()
        self.refresh_products_list()
        
    def get_currency_symbol(self): # Added method
        return AppConfig.get_setting("currency_symbol", AppConfig.CURRENCY_SYMBOL)

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Header
        header_label = QLabel("Inventory Manager")
        header_label.setObjectName("pageTitle")
        layout.addWidget(header_label)
        
        # Tab Widget
        self.tabs = QTabWidget()
        self.tabs.addTab(self.create_manage_tab(), "Manage Stock")
        self.tabs.addTab(self.create_add_tab(), "Add Product")
        self.tabs.addTab(self.create_arrivals_tab(), "New Arrivals")
        layout.addWidget(self.tabs)
        
        # Close Button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        close_btn = QPushButton("Close")
        close_btn.setObjectName("secondaryButton")
        close_btn.setFixedHeight(35)
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)

    def create_manage_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Selection Card
        card = QFrame()
        card.setObjectName("card")
        card_layout = QVBoxLayout(card)
        
        form_layout = QFormLayout()
        form_layout.setSpacing(15)
        
        self.manage_product_combo = QComboBox()
        self.manage_product_combo.setObjectName("inputField")
        self.manage_product_combo.setView(QListView()) # Fix flickering
        self.manage_product_combo.currentIndexChanged.connect(self.on_manage_product_selected)
        form_layout.addRow("Select Product:", self.manage_product_combo)
        
        # Update Price Section
        self.manage_price_input = QDoubleSpinBox()
        self.manage_price_input.setMaximum(999999.99)
        self.manage_price_input.setPrefix(f"{self.get_currency_symbol()} ") # Replaced GH₵
        self.manage_price_input.setFixedHeight(35)
        
        update_price_btn = QPushButton("Update Price")
        update_price_btn.setObjectName("primaryButton")
        update_price_btn.setStyleSheet("""
            QPushButton {
                background-color: #1976D2;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #1565C0;
            }
        """)
        update_price_btn.clicked.connect(self.update_price)
        
        price_widget = QWidget()
        price_layout = QHBoxLayout(price_widget)
        price_layout.setContentsMargins(0, 0, 0, 0)
        price_layout.addWidget(self.manage_price_input, 1)
        price_layout.addWidget(update_price_btn)
        form_layout.addRow("New Price:", price_widget)

        # Update Cost Section (Added)
        self.manage_cost_input = QDoubleSpinBox()
        self.manage_cost_input.setMaximum(999999.99)
        self.manage_cost_input.setPrefix(f"{self.get_currency_symbol()} ") # Replaced GH₵
        self.manage_cost_input.setFixedHeight(35)
        
        update_cost_btn = QPushButton("Update Cost")
        update_cost_btn.setObjectName("primaryButton")
        update_cost_btn.setStyleSheet("""
            QPushButton {
                background-color: #1976D2;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #1565C0;
            }
        """)
        update_cost_btn.clicked.connect(self.update_cost)
        
        cost_widget = QWidget()
        cost_layout = QHBoxLayout(cost_widget)
        cost_layout.setContentsMargins(0, 0, 0, 0)
        cost_layout.addWidget(self.manage_cost_input, 1)
        cost_layout.addWidget(update_cost_btn)
        form_layout.addRow("Update Cost:", cost_widget)
        
        # Correct Stock Section
        self.manage_stock_input = QDoubleSpinBox()
        self.manage_stock_input.setMaximum(999999.99)
        self.manage_stock_input.setFixedHeight(35)
        
        update_stock_btn = QPushButton("Update Stock")
        update_stock_btn.setObjectName("primaryButton")
        update_stock_btn.setStyleSheet("""
            QPushButton {
                background-color: #1976D2;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #1565C0;
            }
        """)
        update_stock_btn.clicked.connect(self.correct_stock)
        
        stock_widget = QWidget()
        stock_layout = QHBoxLayout(stock_widget)
        stock_layout.setContentsMargins(0, 0, 0, 0)
        stock_layout.addWidget(self.manage_stock_input, 1)
        stock_layout.addWidget(update_stock_btn)
        form_layout.addRow("Correct Stock:", stock_widget)
        
        card_layout.addLayout(form_layout)
        layout.addWidget(card)
        
        layout.addStretch()
        
        # Delete Section
        delete_btn = QPushButton("🗑️ DELETE THIS PRODUCT")
        delete_btn.setObjectName("dangerButton")
        delete_btn.setStyleSheet("background-color: #F44336; color: white;") # Force red if style doesn't
        delete_btn.clicked.connect(self.delete_product)
        layout.addWidget(delete_btn)
        
        return tab

    def create_add_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        
        card = QFrame()
        card.setObjectName("card")
        form_layout = QFormLayout(card)
        form_layout.setSpacing(15)
        
        self.add_name_input = QLineEdit()
        self.add_name_input.setObjectName("inputField")
        form_layout.addRow("Product Name*:", self.add_name_input)
        
        # Cost Price (Added)
        self.add_cost_input = QDoubleSpinBox()
        self.add_cost_input.setMaximum(999999.99)
        self.add_cost_input.setPrefix(f"{self.get_currency_symbol()} ") # Replaced GH₵
        form_layout.addRow(f"Cost Price ({self.get_currency_symbol()})*:", self.add_cost_input) # Replaced GH₵

        self.add_price_input = QDoubleSpinBox()
        self.add_price_input.setMaximum(999999.99)
        self.add_price_input.setPrefix(f"{self.get_currency_symbol()} ") # Replaced GH₵
        form_layout.addRow(f"Selling Price ({self.get_currency_symbol()})*:", self.add_price_input) # Replaced GH₵
        
        self.add_unit_combo = QComboBox()
        self.add_unit_combo.setObjectName("inputField")
        self.add_unit_combo.setView(QListView())
        self.add_unit_combo.addItems(["Pieces", "Bags", "Liters", "Boxes", "Kg"])
        form_layout.addRow("Unit Type:", self.add_unit_combo)
        
        self.add_weight_input = QDoubleSpinBox()
        self.add_weight_input.setValue(1.0)
        form_layout.addRow("Weight/Size per Unit:", self.add_weight_input)
        
        self.add_stock_input = QDoubleSpinBox()
        self.add_stock_input.setMaximum(999999.99)
        form_layout.addRow("Initial Stock*:", self.add_stock_input)
        
        self.add_category_combo = QComboBox()
        self.add_category_combo.setObjectName("inputField")
        self.add_category_combo.setView(QListView())
        self.add_category_combo.addItems(["General", "Food", "Electronics", "Clothing", "Other"])
        form_layout.addRow("Category:", self.add_category_combo)
        
        layout.addWidget(card)
        
        create_btn = QPushButton("CREATE PRODUCT")
        create_btn.setObjectName("successButton")
        create_btn.setStyleSheet("background-color: #4CAF50; color: white;")
        create_btn.clicked.connect(self.create_new_product)
        layout.addWidget(create_btn)
        
        layout.addStretch()
        return tab

    def create_arrivals_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Arrival Form Card
        card = QFrame()
        card.setObjectName("card")
        card_layout = QVBoxLayout(card)
        form_layout = QFormLayout()
        
        self.arrival_product_combo = QComboBox()
        self.arrival_product_combo.setObjectName("inputField")
        self.arrival_product_combo.setView(QListView())
        self.arrival_product_combo.currentIndexChanged.connect(self.on_arrival_product_selected)
        form_layout.addRow("Select Product:", self.arrival_product_combo)
        
        self.arrival_current_stock_label = QLabel("Current Stock: 0")
        self.arrival_current_stock_label.setStyleSheet("color: #4CAF50; font-weight: bold; font-size: 14px;")
        form_layout.addRow("", self.arrival_current_stock_label)
        
        self.arrival_qty_input = QDoubleSpinBox()
        self.arrival_qty_input.setMaximum(999999.99)
        form_layout.addRow("Quantity to Add:", self.arrival_qty_input)
        
        # Batch Number
        self.arrival_batch_input = QLineEdit()
        self.arrival_batch_input.setPlaceholderText("Optional")
        self.arrival_batch_input.setObjectName("inputField")
        form_layout.addRow("Batch Number:", self.arrival_batch_input)
        
        # Expiry Date
        self.arrival_expiry_input = QDateEdit()
        self.arrival_expiry_input.setCalendarPopup(True)
        self.arrival_expiry_input.setDisplayFormat("yyyy-MM-dd")
        self.arrival_expiry_input.setDate(datetime.now().date() + timedelta(days=365))
        self.arrival_expiry_input.setEnabled(False)
        self.arrival_expiry_input.setStyleSheet("""
            QDateEdit {
                padding: 10px 12px; 
                border: 1px solid #E0E0E0; 
                border-radius: 6px; 
                font-size: 13px; 
                background-color: #FFFFFF;
                min-height: 40px;
            }
            QDateEdit:disabled {
                background-color: #F5F5F5;
                color: #BDBDBD;
            }
        """)
        
        self.expiry_checkbox = QCheckBox("Has Expiry Date")
        self.expiry_checkbox.setChecked(False)
        self.expiry_checkbox.toggled.connect(self.arrival_expiry_input.setEnabled)
        
        expiry_layout = QHBoxLayout()
        expiry_layout.addWidget(self.expiry_checkbox)
        expiry_layout.addWidget(self.arrival_expiry_input)
        form_layout.addRow("Expiry Date:", expiry_layout)
        
        card_layout.addLayout(form_layout)
        
        record_btn = QPushButton("RECORD ARRIVAL")
        record_btn.setObjectName("successButton")
        record_btn.setFixedHeight(35) # Reduced size
        record_btn.setStyleSheet("background-color: #4CAF50; color: white;")
        record_btn.clicked.connect(self.record_arrival)
        card_layout.addWidget(record_btn)
        
        layout.addWidget(card)
        
        # History Table
        history_label = QLabel("Recent Arrivals")
        history_label.setObjectName("sectionHeading")
        layout.addWidget(history_label)
        
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(5)
        self.history_table.setHorizontalHeaderLabels(["Date/Time", "Product", "Before", "Added", "After"])
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.history_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        layout.addWidget(self.history_table)
        
        self.load_arrival_history()
        
        return tab

    def refresh_products_list(self):
        self.all_products = InventoryService.get_all_products()
        
        # Update Tab 1 Combo
        self.manage_product_combo.clear()
        for p in self.all_products:
            self.manage_product_combo.addItem(p['name'], p['id'])
            
        # Update Tab 3 Combo
        self.arrival_product_combo.clear()
        for p in self.all_products:
            self.arrival_product_combo.addItem(p['name'], p['id'])

    def on_manage_product_selected(self, index):
        if index < 0: return
        product_id = self.manage_product_combo.currentData()
        product = next((p for p in self.all_products if p['id'] == product_id), None)
        if product:
            self.manage_price_input.setValue(product['selling_price'])
            self.manage_stock_input.setValue(product['quantity'])
            self.manage_cost_input.setValue(product['cost_price'])

    def on_arrival_product_selected(self, index):
        if index < 0: return
        product_id = self.arrival_product_combo.currentData()
        product = next((p for p in self.all_products if p['id'] == product_id), None)
        if product:
            self.arrival_current_stock_label.setText(f"Current Stock: {product['quantity']} {product['unit_type']}")

    def update_price(self):
        product_id = self.manage_product_combo.currentData()
        if not product_id: return
        
        new_price = self.manage_price_input.value()
        username = self.user.username if self.user else "admin"
        if InventoryService.update_product_price(product_id, new_price, username):
            CustomInfoDialog("Success", "Price updated successfully!", self).exec()
            self.refresh_products_list()
        else:
            CustomErrorDialog("Error", "Failed to update price", self).exec()

    def update_cost(self):
        product_id = self.manage_product_combo.currentData()
        if not product_id: return
        
        new_cost = self.manage_cost_input.value()
        username = self.user.username if self.user else "admin"
        if InventoryService.update_product_cost(product_id, new_cost, username):
            CustomInfoDialog("Success", "Cost price updated successfully!", self).exec()
            self.refresh_products_list()
        else:
            CustomErrorDialog("Error", "Failed to update cost price", self).exec()

    def correct_stock(self):
        product_id = self.manage_product_combo.currentData()
        if not product_id: return
        
        new_qty = self.manage_stock_input.value()
        username = self.user.username if self.user else "admin"
        if InventoryService.overwrite_product_stock(product_id, new_qty, username):
            CustomInfoDialog("Success", "Stock level corrected successfully!", self).exec()
            self.refresh_products_list()
        else:
            CustomErrorDialog("Error", "Failed to update stock", self).exec()

    def delete_product(self):
        product_id = self.manage_product_combo.currentData()
        product_name = self.manage_product_combo.currentText()
        if not product_id: return
        
        confirm = CustomWarningDialog(
            "Confirm Delete", 
            f"Are you sure you want to delete '{product_name}'?\nThis cannot be undone.", 
            self
        )
        if confirm.exec() == QDialog.Accepted:
            if InventoryService.delete_product(product_id):
                CustomInfoDialog("Success", "Product deleted successfully!", self).exec()
                self.refresh_products_list()
            else:
                CustomErrorDialog("Error", "Failed to delete product", self).exec()

    def create_new_product(self):
        try:
            name = self.add_name_input.text().strip()
            cost_price = self.add_cost_input.value()
            selling_price = self.add_price_input.value()
            unit = self.add_unit_combo.currentText()
            weight = self.add_weight_input.value()
            stock = self.add_stock_input.value()
            category = self.add_category_combo.currentText()
            
            if not name:
                CustomErrorDialog("Validation Error", "Product name is required!", self).exec()
                return
            
            if selling_price <= 0:
                CustomErrorDialog("Validation Error", "Selling Price must be greater than 0!", self).exec()
                return
                
            product_id = InventoryService.create_product(name, selling_price, category, unit, weight, stock, cost_price)
            if product_id:
                CustomInfoDialog("Success", f"Product '{name}' created successfully!", self).exec()
                self.add_name_input.clear()
                self.add_price_input.setValue(0)
                self.add_cost_input.setValue(0)
                self.add_stock_input.setValue(0)
                self.refresh_products_list()
            else:
                CustomErrorDialog("Error", "Failed to create product. (Check if name/SKU already exists)", self).exec()
        except Exception as e:
            CustomErrorDialog("Error", f"An unexpected error occurred: {str(e)}", self).exec()

    def record_arrival(self):
        product_id = self.arrival_product_combo.currentData()
        if not product_id: return
        
        qty_to_add = self.arrival_qty_input.value()
        if qty_to_add <= 0:
            CustomErrorDialog("Validation Error", "Quantity must be greater than 0!", self).exec()
            return
            
        batch = self.arrival_batch_input.text().strip() or None
        expiry = None
        if self.expiry_checkbox.isChecked():
            d = self.arrival_expiry_input.date().toPython()
            expiry = datetime.combine(d, datetime.min.time())
            
        if InventoryService.add_product_stock(product_id, qty_to_add, batch_number=batch, expiry_date=expiry):
            CustomInfoDialog("Success", "Stock arrival recorded successfully!", self).exec()
            self.arrival_qty_input.setValue(0)
            self.arrival_batch_input.clear()
            self.expiry_checkbox.setChecked(False)
            self.refresh_products_list()
            self.load_arrival_history()
            # Refresh current stock label
            self.on_arrival_product_selected(self.arrival_product_combo.currentIndex())
        else:
            CustomErrorDialog("Error", "Failed to record arrival", self).exec()

    def load_arrival_history(self):
        history = InventoryService.get_restock_history(20)
        self.history_table.setRowCount(len(history))
        
        for row, entry in enumerate(history):
            self.history_table.setItem(row, 0, QTableWidgetItem(str(entry['date'])))
            self.history_table.setItem(row, 1, QTableWidgetItem(entry['product_name']))
            self.history_table.setItem(row, 2, QTableWidgetItem(f"{entry['old_qty']:.2f}"))
            self.history_table.setItem(row, 3, QTableWidgetItem(f"+{entry['added_qty']:.2f}"))
            self.history_table.setItem(row, 4, QTableWidgetItem(f"{entry['new_qty']:.2f}"))
