from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
                               QLabel, QPushButton, QFrame, QTableWidget, 
                               QTableWidgetItem, QLineEdit, QComboBox, 
                               QHeaderView, QAbstractItemView, QMessageBox, QCompleter)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QFont, QColor

from database.models import User, Sale, SaleItem
from services.sales_service import SalesService
from services.inventory_service import InventoryService
from services.customer_service import CustomerService
from ui.custom_dialog import CustomWarningDialog, CustomErrorDialog, CustomInfoDialog
from datetime import datetime
from utils.printer import ReceiptPrinter


class SalesScreen(QWidget):
    """Simplified Sales/POS screen for processing transactions"""
    
    sale_completed = Signal()  # Signal emitted when a sale is completed
    
    def __init__(self):
        super().__init__()
        self.current_user = None
        self.cart_items = []
        self.all_products = []
        self.init_ui()
        self.load_product_data()
        
    def init_ui(self):
        """Initialize the simplified POS UI"""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Header Section - Title Only
        title_label = QLabel("Point of Sale")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #2C3E50;")
        main_layout.addWidget(title_label)

        # Main content area
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)
        
        # --- LEFT PANEL: Product Selection ---
        left_panel = QFrame()
        left_panel.setStyleSheet("background-color: white; border-radius: 12px; border: none;")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(15, 15, 15, 15)
        left_layout.setSpacing(15)
        
        left_layout.addWidget(QLabel("Product Selection", styleSheet="font-size: 16px; font-weight: bold; color: #2C3E50;"))
        
        # Search field (Capsule style)
        self.search_container = QFrame()
        self.search_container.setFixedHeight(40)
        self.search_container.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border-radius: 20px;
                border: 2px solid #1976D2;
            }
            QFrame:focus-within {
                background-color: #FFFFFF;
                border: 2px solid #1565C0;
            }
        """)
        search_layout = QHBoxLayout(self.search_container)
        search_layout.setContentsMargins(15, 0, 15, 0)
        search_layout.setSpacing(10)
        
        search_icon = QLabel("🔍")
        search_icon.setStyleSheet("color: #6C757D; font-size: 14px; background: transparent; border: none;")
        search_layout.addWidget(search_icon)
        
        self.product_search = QLineEdit()
        self.product_search.setPlaceholderText("Search items...")
        self.product_search.setStyleSheet("""
            QLineEdit {
                border: none;
                background: transparent;
                font-size: 14px;
                color: #212529;
                padding: 0px;
                min-height: 0px;
                selection-background-color: #E3F2FD;
            }
        """)
        self.product_search.textChanged.connect(self.on_product_search_changed)
        search_layout.addWidget(self.product_search)
        left_layout.addWidget(self.search_container)
        
        # Product Table
        self.product_table = QTableWidget()
        self.product_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.product_table.setShowGrid(False)
        self.product_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: none;
                gridline-color: transparent;
                outline: none;
            }
            QTableWidget::item {
                border-bottom: 1px solid #F1F3F5;
                padding: 10px;
            }
            QTableWidget::item:selected {
                background-color: #E3F2FD;
                color: #1976D2;
            }
        """)
        self.product_table.setColumnCount(4)
        self.product_table.setHorizontalHeaderLabels(["Name", "SKU", "Price", "Stock"])
        self.product_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.product_table.verticalHeader().setVisible(False)
        self.product_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.product_table.horizontalHeader().setStyleSheet("""
            QHeaderView::section {
                background-color: #F8F9FA;
                color: #495057;
                padding: 10px;
                font-weight: bold;
                border: none;
                border-bottom: 2px solid #E9ECEF;
            }
        """)
        self.product_table.doubleClicked.connect(self.on_product_double_clicked)
        left_layout.addWidget(self.product_table)
        
        content_layout.addWidget(left_panel, 3) # 60% width
        
        # --- RIGHT PANEL: Cart & Payment ---
        right_panel = QFrame()
        right_panel.setStyleSheet("background-color: white; border-radius: 12px; border: none;")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(15, 15, 15, 15)
        right_layout.setSpacing(15)
        
        right_layout.addWidget(QLabel("Current Cart", styleSheet="font-size: 16px; font-weight: bold; color: #2C3E50;"))
        
        # Cart Table
        self.cart_table = QTableWidget()
        self.cart_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.cart_table.setShowGrid(False)
        self.cart_table.setColumnCount(4)
        self.cart_table.setHorizontalHeaderLabels(["Item", "Qty", "Subtotal", ""])
        self.cart_table.verticalHeader().setVisible(False)
        self.cart_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: none;
                outline: none;
            }
            QTableWidget::item {
                border-bottom: 1px solid #F1F3F5;
                padding: 5px;
            }
        """)
        self.cart_table.horizontalHeader().setStyleSheet("""
            QHeaderView::section {
                background-color: #F8F9FA;
                color: #495057;
                padding: 8px;
                font-weight: bold;
                border: none;
                border-bottom: 2px solid #E9ECEF;
            }
        """)
        self.cart_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch) # Item
        self.cart_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents) # Qty
        self.cart_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents) # Subtotal
        self.cart_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed) # Action
        self.cart_table.setColumnWidth(3, 50)
        right_layout.addWidget(self.cart_table)
        
        # Totals Display
        totals_container = QFrame()
        totals_container.setStyleSheet("background-color: #F8F9FA; border-radius: 8px; padding: 10px;")
        totals_layout = QVBoxLayout(totals_container)
        
        self.cart_total_label = QLabel("TOTAL: GH₵ 0.00")
        self.cart_total_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #1976D2;")
        self.cart_total_label.setAlignment(Qt.AlignCenter)
        totals_layout.addWidget(self.cart_total_label)
        
        right_layout.addWidget(totals_container)
        
        # Checkout Section
        right_layout.addWidget(QLabel("Checkout", styleSheet="font-size: 14px; font-weight: bold; color: #2C3E50;"))
        
        self.customer_combo = QComboBox()
        self.customer_combo.setFixedHeight(45)
        self.customer_combo.setEditable(True)
        self.customer_combo.completer().setCompletionMode(QCompleter.PopupCompletion)
        self.customer_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #B0BEC5;
                border-radius: 8px;
                padding: 5px 15px;
                font-size: 14px;
                color: #2C3E50;
                background-color: #FFFFFF;
            }
            QComboBox:focus {
                border: 2px solid #1976D2;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
                border-left: 1px solid #CFD8DC;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 6px solid transparent;
                border-right: 6px solid transparent;
                border-top: 6px solid #546E7A;
                margin-right: 5px;
            }
            QComboBox QAbstractItemView {
                border: 1px solid #B0BEC5;
                selection-background-color: #E3F2FD;
                selection-color: #1976D2;
                background-color: #FFFFFF;
                outline: none;
                padding: 5px;
            }
        """)
        self.load_customers()
        right_layout.addWidget(self.customer_combo)
        
        self.tender_input = QLineEdit()
        self.tender_input.setPlaceholderText("Amount Tendered (GH₵)")
        self.tender_input.setFixedHeight(45)
        self.tender_input.textChanged.connect(self.on_tender_amount_changed)
        # Watermark style for placeholder
        self.tender_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #B0BEC5;
                border-radius: 8px;
                padding: 0 15px;
                font-size: 16px;
                background-color: #FFFFFF;
                color: #2C3E50;
            }
            QLineEdit:focus {
                border: 2px solid #1976D2;
            }
        """)
        # Note: Placeholder color is usually handled by palette or specific flags, 
        # but basic CSS placeholder styling isn't fully supported in all QT versions.
        # We rely on default behavior which is usually greyed out.
        
        right_layout.addWidget(self.tender_input)
        
        # Change Due
        self.change_label = QLabel("Change Due: GH₵ 0.00")
        self.change_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #27AE60;")
        right_layout.addWidget(self.change_label)
        
        # Checkout Buttons
        self.complete_sale_btn = QPushButton("COMPLETE SALE")
        self.complete_sale_btn.setFixedHeight(55)
        self.complete_sale_btn.setCursor(Qt.PointingHandCursor)
        self.complete_sale_btn.setStyleSheet("""
            QPushButton {
                background-color: #1976D2;
                color: white;
                border-radius: 8px;
                font-weight: bold;
                font-size: 16px;
                letter-spacing: 1px;
            }
            QPushButton:disabled { background-color: #B0BEC5; color: #F5F5F5; }
            QPushButton:hover { background-color: #1565C0; }
            QPushButton:pressed { background-color: #0D47A1; }
        """)
        self.complete_sale_btn.setEnabled(False)
        self.complete_sale_btn.clicked.connect(self.on_complete_sale_clicked)
        right_layout.addWidget(self.complete_sale_btn)
        
        self.clear_cart_btn = QPushButton("Clear Cart")
        self.clear_cart_btn.setCursor(Qt.PointingHandCursor)
        self.clear_cart_btn.setStyleSheet("""
            QPushButton {
                color: #E57373; 
                background: transparent;
                border: 1px solid #EF9A9A; 
                border-radius: 6px;
                font-weight: bold; 
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #FFEBEE;
                color: #D32F2F;
                border-color: #D32F2F;
            }
        """)
        self.clear_cart_btn.clicked.connect(self.on_clear_cart_clicked)
        right_layout.addWidget(self.clear_cart_btn, 0, Qt.AlignCenter)
        
        content_layout.addWidget(right_panel, 2) # 40% width
        
        main_layout.addLayout(content_layout)

    def set_current_user(self, user: User):
        self.current_user = user

    def load_product_data(self):
        try:
            # Fetch all products from service
            self.all_products = InventoryService.get_all_products()
            # Display all products initially without filtering
            self.display_products(self.all_products)
        except Exception as e:
            print(f"Error loading products: {e}")
            QMessageBox.critical(self, "Database Error", f"Failed to load products: {str(e)}")

    def display_products(self, products):
        self.product_table.setRowCount(len(products))
        for row, p in enumerate(products):
            self.product_table.setItem(row, 0, QTableWidgetItem(p["name"]))
            self.product_table.setItem(row, 1, QTableWidgetItem(p["sku"]))
            self.product_table.setItem(row, 2, QTableWidgetItem(f"GH₵ {p['selling_price']:.2f}"))
            stock_item = QTableWidgetItem(str(int(p["quantity"])))
            if p["is_low_stock"]: stock_item.setForeground(QColor("#E74C3C"))
            self.product_table.setItem(row, 3, stock_item)

    def load_customers(self):
        try:
            customers = CustomerService.get_all_customers()
            self.customer_combo.clear()
            self.customer_combo.addItem("Walk-in Customer", None)
            for c in customers:
                self.customer_combo.addItem(c["name"], c["id"])
        except Exception as e:
            logger.error(f"Failed to load customers in SalesScreen: {e}")

    def on_product_search_changed(self, text):
        filtered = [p for p in self.all_products if text.lower() in p["name"].lower() or text.lower() in p["sku"].lower()]
        self.display_products(filtered)

    def on_product_double_clicked(self, index):
        row = index.row()
        product_name = self.product_table.item(row, 0).text()
        # Find product in original list
        product = next((p for p in self.all_products if p["name"] == product_name), None)
        if product and product["quantity"] > 0:
            self.add_to_cart(product)
        elif product:
            dialog = CustomWarningDialog("Out of Stock", "This item is currently out of stock and cannot be added to the cart.", self)
            dialog.setFixedSize(450, 220) # Stretched for better visibility
            dialog.exec()

    def add_to_cart(self, product):
        for item in self.cart_items:
            if item["id"] == product["id"]:
                if item["qty"] < product["quantity"]:
                    item["qty"] += 1
                    self.update_cart_display()
                return
        
        self.cart_items.append({"id": product["id"], "name": product["name"], "price": product["selling_price"], "qty": 1, "max": product["quantity"]})
        self.update_cart_display()

    def update_cart_display(self):
        """UI Polish: Total rewrite of cart controls to fix stretching and visibility."""
        self.cart_table.setRowCount(len(self.cart_items))
        self.cart_table.verticalHeader().setDefaultSectionSize(52)
        total = 0
        
        # --- STYLE OVERRIDE (FORCE SQUARE) ---
        qty_btn_style = """
            QPushButton {
                border: 1px solid #cccccc;
                border-radius: 4px;
                background-color: #ffffff;
                color: #1e40af;
                font-weight: bold;
                padding: 0;
            }
            QPushButton:hover {
                background-color: #f0f0f0;
            }
        """
        remove_btn_style = """
            QPushButton {
                background-color: transparent;
                color: #dc2626;
                border: none;
                font-weight: bold;
                font-size: 16px;
            }
            QPushButton:hover {
                color: #b91c1c;
            }
        """

        for row, item in enumerate(self.cart_items):
            sub = item["price"] * item["qty"]
            
            # --- ROW SETUP ---
            name_item = QTableWidgetItem(item["name"])
            name_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self.cart_table.setItem(row, 0, name_item)

            # --- LAYOUT FIX: Flex container for Qty ---
            qty_container = QWidget()
            qty_layout = QHBoxLayout(qty_container)
            qty_layout.setContentsMargins(0, 0, 0, 0)
            qty_layout.setSpacing(10)
            qty_layout.setAlignment(Qt.AlignCenter)

            # --- DECREMENT BUTTON (TEXT FALLBACK) ---
            minus_btn = QPushButton("−") # Using bold minus symbol
            minus_btn.setFixedSize(32, 32)
            minus_btn.setStyleSheet(qty_btn_style)
            minus_btn.setCursor(Qt.PointingHandCursor)
            minus_btn.clicked.connect(lambda checked=False, idx=row: self.adjust_cart_qty(idx, -1))
            
            qty_label = QLabel(f"<b>{item['qty']}</b>")
            qty_label.setAlignment(Qt.AlignCenter)
            
            # --- INCREMENT BUTTON (TEXT FALLBACK) ---
            plus_btn = QPushButton("+")
            plus_btn.setFixedSize(32, 32)
            plus_btn.setStyleSheet(qty_btn_style)
            plus_btn.setCursor(Qt.PointingHandCursor)
            plus_btn.clicked.connect(lambda checked=False, idx=row: self.adjust_cart_qty(idx, 1))

            qty_layout.addWidget(minus_btn)
            qty_layout.addWidget(qty_label)
            qty_layout.addWidget(plus_btn)
            self.cart_table.setCellWidget(row, 1, qty_container)
            
            # --- SUBTOTAL ---
            sub_item = QTableWidgetItem(f"GH₵ {sub:.2f}")
            sub_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.cart_table.setItem(row, 2, sub_item)

            # --- TRASH CAN REFACTOR ---
            remove_container = QWidget()
            remove_layout = QHBoxLayout(remove_container)
            remove_layout.setContentsMargins(0, 0, 0, 0)
            remove_layout.setAlignment(Qt.AlignCenter)
            remove_btn = QPushButton("✕") # Using 'X' as a clear remove symbol
            remove_btn.setFixedSize(32, 32)
            remove_btn.setStyleSheet(remove_btn_style)
            remove_btn.setCursor(Qt.PointingHandCursor)
            remove_btn.setToolTip("Remove Item")
            remove_btn.clicked.connect(lambda checked=False, idx=row: self.remove_cart_item(idx))
            remove_layout.addWidget(remove_btn)
            self.cart_table.setCellWidget(row, 3, remove_container)
            
            total += sub
        
        self.cart_total_label.setText(f"TOTAL: GH₵ {total:,.2f}")
        self.complete_sale_btn.setEnabled(total > 0)
        self.update_change_display()

    def adjust_cart_qty(self, index, delta):
        if 0 <= index < len(self.cart_items):
            item = self.cart_items[index]
            new_qty = item["qty"] + delta
            if 1 <= new_qty <= item["max"]:
                item["qty"] = new_qty
                self.update_cart_display()
            elif new_qty > item["max"]:
                QMessageBox.warning(self, "Stock Limit", f"Only {int(item['max'])} units available in stock.")

    def remove_cart_item(self, index):
        if 0 <= index < len(self.cart_items):
            self.cart_items.pop(index)
            self.update_cart_display()

    def on_tender_amount_changed(self):
        self.update_change_display()

    def update_change_display(self):
        try:
            total_text = self.cart_total_label.text().split("GH₵")[1].strip().replace(",", "")
            total = float(total_text)
            tender = float(self.tender_input.text() or "0")
            change = tender - total
            self.change_label.setText(f"Change Due: GH₵ {max(0, change):.2f}")
            self.change_label.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {'#27AE60' if change >= 0 else '#E74C3C'};")
        except Exception as e:
            logger.error(f"Error updating change display: {e}")

    def on_clear_cart_clicked(self):
        if self.cart_items and QMessageBox.question(self, "Clear Cart", "Clear all items?") == QMessageBox.Yes:
            self.cart_items = []
            self.update_cart_display()

    def on_complete_sale_clicked(self):
        total_text = self.cart_total_label.text().split("GH₵")[1].strip().replace(",", "")
        total = float(total_text)
        
        # Validation: Restrict sales without payment unless a customer is selected
        customer_id = self.customer_combo.currentData()
        tender_text = self.tender_input.text().strip()
        tender_amount = 0.0
        try:
            tender_amount = float(tender_text) if tender_text else 0.0
        except ValueError:
            QMessageBox.warning(self, "Invalid Amount", "Please enter a valid tender amount.")
            return

        if customer_id is None and tender_amount < total:
            QMessageBox.warning(self, "Payment Required", 
                                "Walk-in customers must provide full payment to complete the sale.\n"
                                "Alternatively, select a customer to allow credit transactions.")
            return
        
        sale = {
            "date": datetime.now().isoformat(),
            "total_amount": total,
            "payment_method": "cash" if tender_amount >= total else "credit",
            "amount_paid": tender_amount,
            "customer_id": customer_id,
            "cashier_user": self.current_user.username if self.current_user else "admin",
            "items": [{"product_id": i["id"], "product_name": i["name"], "quantity": i["qty"], "unit_price": i["price"], "subtotal": i["price"]*i["qty"]} for i in self.cart_items]
        }
        
        try:
            sale_id = SalesService.create_sale(sale)
            if sale_id:
                # Add ID for printing
                sale['id'] = sale_id
                
                # POP UP RECEIPT FOR PRINTING
                try:
                    ReceiptPrinter.print_receipt(sale)
                except Exception as print_err:
                    logger.error(f"Receipt printing failed: {print_err}")
                
                CustomInfoDialog("Success", "Sale completed!", self).exec()
                self.cart_items = []
                self.tender_input.clear()
                self.update_cart_display()
                # CRITICAL FIX #2: Refresh product data to show updated stock
                self.load_product_data()
                self.sale_completed.emit()
        except Exception as e:
            CustomErrorDialog("Transaction Error", f"Failed to complete sale: {str(e)}", self).exec()
        
        