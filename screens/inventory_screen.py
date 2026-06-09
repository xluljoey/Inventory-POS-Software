from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
                               QLabel, QPushButton, QFrame, QTableWidget, 
                               QTableWidgetItem, QLineEdit, QComboBox, 
                               QHeaderView, QAbstractItemView, QSpinBox, 
                               QDoubleSpinBox, QMessageBox, QDialog, 
                               QDialogButtonBox, QFormLayout, QScrollArea)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QPixmap, QPainter, QColor

from database.models import User, Product
from services.inventory_service import InventoryService
from ui.dialogs import AddProductDialog, EditProductDialog, ProductDetailsDialog
from ui.custom_dialog import CustomWarningDialog, CustomErrorDialog, CustomInfoDialog


class InventoryScreen(QWidget):
    """Inventory management screen with main content area"""
    
    def __init__(self):
        super().__init__()
        self.current_user = None
        self.all_products = []  # Store all products for filtering
        self.init_ui()
        self.load_inventory_data()
        
    def init_ui(self):
        """Initialize the inventory screen UI without sidebar"""
        # Set main background color
        self.setStyleSheet("background-color: #F7F7FD;")
        
        # Main layout (without sidebar)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Create main content area only
        self.create_main_content(main_layout)
    
    
    def create_main_content(self, main_layout):
        """Create the main content area"""
        # Redundant wrapper removed
        
        # Header section
        header_layout = QHBoxLayout()
        header_layout.setSpacing(20)
        
        # Title
        title_label = QLabel("Inventory")
        title_label.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #2C3E50;
        """)
        header_layout.addWidget(title_label)
        
        # Add "Manage Stock" button (admin only) - Moved next to title for visibility
        self.manage_stock_btn = QPushButton("📦 Manage Stock")
        self.manage_stock_btn.setMinimumWidth(180)
        self.manage_stock_btn.setStyleSheet("""
            QPushButton {
                background-color: #436F80;
                color: white;
                border: 2px solid #FFFFFF;
                border-radius: 8px;
                padding: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #365966;
            }
        """)
        self.manage_stock_btn.clicked.connect(self.open_manage_stock_dialog)
        self.manage_stock_btn.setVisible(False) # Controlled by set_current_user
        header_layout.addWidget(self.manage_stock_btn)
        
        header_layout.addStretch()
        
        # Search bar with icon
        search_container = QFrame()
        search_container.setFixedHeight(40)
        search_container.setFixedWidth(300)
        search_container.setStyleSheet("""
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
        search_layout = QHBoxLayout(search_container)
        search_layout.setContentsMargins(15, 0, 15, 0)
        search_layout.setSpacing(10)
        
        # Search icon (text-based for now)
        search_icon = QLabel("🔍")
        search_icon.setStyleSheet("color: #6C757D; font-size: 14px; background: transparent; border: none;")
        search_layout.addWidget(search_icon)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search inventory...")
        self.search_input.setStyleSheet("""
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
        self.search_input.textChanged.connect(self.on_search_changed)
        search_layout.addWidget(self.search_input)
        
        header_layout.addWidget(search_container)
        
        main_layout.addLayout(header_layout)
        
        # Create content area with table only (no log) - full width
        self.create_table_section(main_layout)
    
    def create_table_section(self, parent_layout):
        """Create the data table section with robust CSS grid layout from scratch"""
        table_container = QFrame()
        table_container.setObjectName("tableContainer")
        table_container.setStyleSheet("""
            QFrame#tableContainer {
                background-color: white;
                border-radius: 8px;
                border: 1px solid #E0E0E0;
            }
        """)
        table_layout = QVBoxLayout(table_container)
        table_layout.setContentsMargins(20, 20, 20, 20)
        table_layout.setSpacing(0)
        
        # Product table with enhanced robust styling
        self.product_table = QTableWidget()
        self.product_table.setEditTriggers(QAbstractItemView.NoEditTriggers) # Disable editing
        self.product_table.setShowGrid(False) # Remove ghost lines
        self.product_table.setColumnCount(7)
        self.product_table.setHorizontalHeaderLabels([
            "Name", "SKU", "Category", "Quantity", "Cost Price", "Selling Price", "Actions"
        ])
        self.product_table.setObjectName("dataTable")
        
        # Configure table appearance
        self.product_table.setAlternatingRowColors(True)
        self.product_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.product_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.product_table.setSortingEnabled(True)
        
        # Apply comprehensive table styling with CSS grid layout approach
        self.product_table.setStyleSheet("""
            /* Table Widget Base Styles */
            QTableWidget#dataTable {
                background-color: white;
                border: none;
                gridline-color: transparent;
                outline: none;
            }
            
            /* Header Styles */
            QTableWidget#dataTable QHeaderView::section {
                background-color: #F8F9FA;
                color: #2C3E50;
                padding: 12px;
                font-weight: 600;
                border: none;
                border-bottom: 1px solid #E0E0E0;
                text-align: left;
            }
            
            /* Fixed Row Height and Cell Styles */
            QTableWidget#dataTable QAbstractItemView::item {
                padding: 12px 8px;  /* Increased vertical padding */
                border: none;
                min-height: 50px;  /* Increased min height */
                max-height: 50px;  /* Increased max height */
            }
            
            /* Alternating Row Colors */
            QTableWidget#dataTable QAbstractItemView::item:alternate {
                background-color: #FAFAFA;
            }
            
            QTableWidget#dataTable QAbstractItemView::item:!alternate {
                background-color: #FFFFFF;
            }
            
            /* Selected Row Style */
            QTableWidget#dataTable QAbstractItemView::item:selected {
                background-color: #E3F2FD;
                color: #1976D2;
            }
            
            /* Hover State */
            QTableWidget#dataTable QAbstractItemView::item:hover {
                background-color: #F5F5F5;
            }
            
            /* Vertical Header (Row Numbers) - Hidden */
            QTableWidget#dataTable QHeaderView::vertical {
                background-color: transparent;
                border: none;
                width: 0px;
            }
        """)
        
        # Enforce fixed row heights and prevent manual resizing
        self.product_table.verticalHeader().setDefaultSectionSize(50)  # Fixed 50px row height to match increased padding
        self.product_table.verticalHeader().setMinimumSectionSize(50)   # Minimum 50px to match padding
        self.product_table.verticalHeader().setMaximumSectionSize(50)   # Maximum 50px to match padding
        self.product_table.verticalHeader().setVisible(False)  # Hide row numbers
        
        # Configure column widths for optimal content display with robust distribution
        header = self.product_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)  # Name - Stretch to fill
        header.setSectionResizeMode(1, QHeaderView.Fixed)  # SKU - Fixed width
        header.setSectionResizeMode(2, QHeaderView.Fixed)  # Category - Fixed width
        header.setSectionResizeMode(3, QHeaderView.Fixed)  # Quantity - Fixed width
        header.setSectionResizeMode(4, QHeaderView.Fixed)  # Cost Price - Fixed width
        header.setSectionResizeMode(5, QHeaderView.Fixed)  # Selling Price - Fixed width
        header.setSectionResizeMode(6, QHeaderView.Fixed)  # Actions - Fixed width
        
        # Set alignment for numeric columns to right-align
        header.setSectionsClickable(True)
        header.setSortIndicatorShown(True)
        
        # Set specific column widths for optimal content display with better distribution
        self.product_table.setColumnWidth(0, 150)  # Name - Wider for better text display
        self.product_table.setColumnWidth(1, 100)  # SKU
        self.product_table.setColumnWidth(2, 120)  # Category
        self.product_table.setColumnWidth(3, 100)  # Quantity - Wider for status indicators
        self.product_table.setColumnWidth(4, 100)  # Cost Price - Right aligned
        self.product_table.setColumnWidth(5, 100)  # Selling Price - Right aligned
        self.product_table.setColumnWidth(6, 100)  # Actions - Just View button now
        
        table_layout.addWidget(self.product_table)
        
        parent_layout.addWidget(table_container)  # Takes full width
    
    def set_current_user(self, user: User):
        """Set the current user and update UI permissions"""
        print(f"DEBUG: InventoryScreen.set_current_user called for {user.username} with role {user.role}")
        self.current_user = user
        if hasattr(self, 'manage_stock_btn'):
            is_admin = (user.role == "admin")
            self.manage_stock_btn.setVisible(is_admin)
            
            # Show/Hide Cost Price Column (Index 4) based on role
            if is_admin:
                self.product_table.showColumn(4)
            else:
                self.product_table.hideColumn(4)
                
            print(f"DEBUG: Manage Stock button visibility set to {is_admin}")
        else:
            print("DEBUG: manage_stock_btn NOT FOUND in InventoryScreen")
        self.load_inventory_data() # Refresh to update action buttons
    
    def open_manage_stock_dialog(self):
        """Open the Manage Stock dialog (Admin only)"""
        # Double-check user permissions before opening dialog
        if not self.current_user or self.current_user.role != "admin":
            from ui.custom_dialog import CustomWarningDialog
            CustomWarningDialog("Access Denied", "You do not have permission to manage stock.", self).exec()
            return
            
        try:
            from ui.manage_stock_dialog import ManageStockDialog
            dialog = ManageStockDialog(self, self.current_user)
            if dialog.exec() == QDialog.Accepted:
                self.load_inventory_data()  # Refresh table after dialog closes
        except Exception as e:
            from ui.custom_dialog import CustomErrorDialog
            CustomErrorDialog("Error", f"Could not open Manage Stock dialog: {str(e)}", self).exec()
    
    def load_categories_for_filter(self):
        """Load categories into the filter dropdown"""
        try:
            categories = InventoryService.get_all_categories()
            self.category_combo.clear()
            self.category_combo.addItem("All Categories")
            for category in categories:
                self.category_combo.addItem(category['name'])
        except Exception as e:
            # If there's an error loading categories, use default ones
            self.category_combo.clear()
            self.category_combo.addItem("All Categories")
            self.category_combo.addItems(["Electronics", "Clothing", "Food", "Other"])
            print(f"Error loading categories: {e}")
            QMessageBox.warning(self, "Warning", f"Could not load categories: {e}. Using defaults.")

    def load_inventory_data(self):
        """Load inventory data from the service"""
        try:
            products_data = InventoryService.get_all_products()
            self.all_products = products_data  # Store for filtering
            self.display_products(self.all_products)
        except Exception as e:
            dialog = CustomErrorDialog("Error", f"Failed to load inventory data: {str(e)}", self)
            dialog.exec()
    
    def display_products(self, products):
        """Display products in the table with status indicators and action buttons"""
        self.product_table.setRowCount(len(products))
        
        for row, product in enumerate(products):
            # Name column - store product ID as user data
            name_item = QTableWidgetItem(product["name"])
            name_item.setData(Qt.UserRole, product["id"])  # Store product ID for easy lookup
            self.product_table.setItem(row, 0, name_item)
            
            self.product_table.setItem(row, 1, QTableWidgetItem(product["sku"]))
            self.product_table.setItem(row, 2, QTableWidgetItem(product["category"] or "N/A"))
            
            # Format quantity - Simplified absolute value display without layers
            quantity = product["quantity"]
            quantity_widget = QWidget()
            quantity_layout = QHBoxLayout(quantity_widget)
            quantity_layout.setContentsMargins(0, 0, 0, 0)
            quantity_layout.setAlignment(Qt.AlignCenter)
            
            quantity_label = QLabel(f"{quantity:.0f}")
            quantity_label.setAlignment(Qt.AlignCenter)
            
            if quantity <= 0:
                # Out of Stock - Red Text
                quantity_label.setStyleSheet("color: #E74C3C; font-weight: bold; font-size: 14px;")
            elif product.get("is_low_stock", False):
                # Low Stock - Purple Text
                quantity_label.setStyleSheet("color: #AF7AC5; font-weight: bold; font-size: 14px;")
            else:
                # In Stock - Standard Text
                quantity_label.setStyleSheet("color: #2C3E50; font-weight: 500; font-size: 14px;")
                
            quantity_layout.addWidget(quantity_label)
            self.product_table.setCellWidget(row, 3, quantity_widget)
            
            # Format prices with GHS currency
            cost_item = QTableWidgetItem(f"GHS {product['cost_price']:.2f}")
            selling_item = QTableWidgetItem(f"GHS {product['selling_price']:.2f}")
            cost_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            selling_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.product_table.setItem(row, 4, cost_item)
            self.product_table.setItem(row, 5, selling_item)
            
            # Actions column - adjust margins to prevent cutoff
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(2, 0, 2, 0) # Reduced margins
            actions_layout.setSpacing(6)
            actions_layout.setAlignment(Qt.AlignCenter)
            
            # Always show View Details button
            view_btn = QPushButton("👁️ View")
            view_btn.setStyleSheet("""
                QPushButton {
                    background-color: #607D8B;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 4px 8px;
                    font-size: 11px;
                    font-weight: 600;
                    min-height: 24px;
                }
                QPushButton:hover {
                    background-color: #455A64;
                }
            """)
            view_btn.clicked.connect(lambda checked=False, r=row: self.view_product(r))
            actions_layout.addWidget(view_btn)
            
            self.product_table.setCellWidget(row, 6, actions_widget)
    
    def on_search_changed(self, text):
        """Filter products based on search text"""
        if not text:
            self.display_products(self.all_products)
        else:
            filtered_products = [
                p for p in self.all_products
                if text.lower() in p["name"].lower() or text.lower() in p["sku"].lower()
            ]
            self.display_products(filtered_products)

    def on_filter_changed(self):
        """Filter products based on selected filters"""
        # Since we removed filter dropdowns in new design, this method is simplified
        self.display_products(self.all_products)

    def on_add_product_clicked(self):
        """Handle add product button click - check role"""
        if self.current_user and self.current_user.role != "admin":
            CustomWarningDialog("Access Denied", "You do not have permission to add products.", self).exec()
            return

        try:
            dialog = AddProductDialog(self)
            if dialog.exec() == QDialog.Accepted:
                product_data = dialog.get_product_data()
                product_id = InventoryService.add_product(product_data)
                if product_id:
                    # Reload data to show new product
                    self.load_inventory_data()
                    success_dialog = CustomInfoDialog("Success", "Product added successfully!", self)
                    success_dialog.exec()
                else:
                    error_dialog = CustomErrorDialog("Error", "Failed to add product", self)
                    error_dialog.exec()
        except Exception as e:
            error_dialog = CustomErrorDialog("Error", f"Failed to add product: {str(e)}", self)
            error_dialog.exec()

    def view_product(self, row):
        """View product details (Read-only)"""
        product_id_item = self.product_table.item(row, 0)
        if product_id_item is None:
            return
            
        product_id = product_id_item.data(Qt.UserRole)
        product_data = None
        for p in self.all_products:
            if p["id"] == product_id:
                product_data = p
                break
        
        if product_data:
            # Use the new modern dialog
            is_admin = self.current_user and self.current_user.role == "admin"
            dialog = ProductDetailsDialog(self, product_data, show_cost=is_admin)
            dialog.exec()

    def edit_product(self, row):
        """Edit product at specified row - check role"""
        if self.current_user and self.current_user.role != "admin":
            CustomWarningDialog("Access Denied", "You do not have permission to edit products.", self).exec()
            return

        product_id_item = self.product_table.item(row, 0)
        if product_id_item is None:
            return
            
        product_id = product_id_item.data(Qt.UserRole)  # Use stored ID if available

        # Find product data by ID
        product_data = None
        if product_id:
            for p in self.all_products:
                if p["id"] == product_id:
                    product_data = p
                    break

        if not product_data:
            return

        dialog = EditProductDialog(self, product_data)
        if dialog.exec() == QDialog.Accepted:
            updated_data = dialog.get_product_data()
            updated_data['id'] = product_data['id']  # Add ID for update
            try:
                if InventoryService.update_product(updated_data):
                    self.load_inventory_data()
                    success_dialog = CustomInfoDialog("Success", "Product updated successfully!", self)
                    success_dialog.exec()
                else:
                    error_dialog = CustomErrorDialog("Error", "Failed to update product", self)
                    error_dialog.exec()
            except Exception as e:
                error_dialog = CustomErrorDialog("Error", f"Failed to update product: {str(e)}", self)
                error_dialog.exec()

    def delete_product(self, row):
        """Delete product at specified row - check role"""
        if self.current_user and self.current_user.role != "admin":
            CustomWarningDialog("Access Denied", "You do not have permission to delete products.", self).exec()
            return

        product_id_item = self.product_table.item(row, 0)
        if product_id_item is None:
            return
            
        product_id = product_id_item.data(Qt.UserRole)

        if not product_id:
            return

        # Confirm deletion
        warning_dialog = CustomWarningDialog(
            "Confirm Delete", 
            "Are you sure you want to delete this product?", 
            self
        )
        
        if warning_dialog.exec() == QDialog.Accepted:
            try:
                if InventoryService.delete_product(product_id):
                    # Reload data to remove deleted product
                    self.load_inventory_data()
                    success_dialog = CustomInfoDialog("Success", "Product deleted successfully!", self)
                    success_dialog.exec()
                else:
                    error_dialog = CustomErrorDialog("Error", "Failed to delete product", self)
                    error_dialog.exec()
            except Exception as e:
                error_dialog = CustomErrorDialog("Error", f"Failed to delete product: {str(e)}", self)
                error_dialog.exec()
