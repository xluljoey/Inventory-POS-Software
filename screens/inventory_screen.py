from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
                               QLabel, QPushButton, QFrame, QTableWidget, 
                               QTableWidgetItem, QLineEdit, QComboBox, 
                               QHeaderView, QAbstractItemView, QSpinBox, 
                               QDoubleSpinBox, QMessageBox, QDialog, 
                               QDialogButtonBox, QFormLayout, QScrollArea, QCompleter)
from PySide6.QtCore import Qt, QSize, QTimer, QStringListModel
from PySide6.QtGui import QFont, QPixmap, QPainter, QColor

from database.models import User, Product
from services.inventory_service import InventoryService
from ui.dialogs import AddProductDialog, EditProductDialog, ProductDetailsDialog
from ui.custom_dialog import CustomWarningDialog, CustomErrorDialog, CustomInfoDialog
from config.app_config import AppConfig # Added

class InventoryScreen(QWidget):
    """Inventory management screen with main content area"""
    
    def __init__(self):
        super().__init__()
        # Ensure UI is built immediately
        self.init_ui()
        # Basic state
        self.current_user = None
        self.all_products = []  # Store all products for filtering
        # Defer loading and permission checks until UI is fully ready
        QTimer.singleShot(200, self.initial_load)

    def initial_load(self):
        # Only now, after 200ms, do we touch the UI
        try:
            self.load_inventory_data()
        except Exception:
            pass
        try:
            self.apply_permissions()
        except Exception:
            pass
        
    def get_currency_symbol(self): # Added method
        return AppConfig.get_setting("currency_symbol", AppConfig.CURRENCY_SYMBOL)

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
        search_layout = QHBoxLayout(search_container) # Fixed: removed self.
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
        
        # Initialize Completer
        self.completer = QCompleter()
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.setFilterMode(Qt.MatchContains)
        self.search_input.setCompleter(self.completer)
        
        search_layout.addWidget(self.search_input)
        
        main_layout.addWidget(search_container)
        
        main_layout.addLayout(header_layout)
        
        # Create content area with table only (no log) - full width
        self.create_table_section(main_layout)
    
    def create_table_section(self, parent_layout):
        """Create the data table section with a stacked layout for empty state handling."""
        from ui.common_widgets import EmptyStateWidget
        from PySide6.QtWidgets import QStackedWidget

        # SPRINT 4: Use QStackedWidget to manage table and empty state
        self.table_stack = QStackedWidget()
        
        # --- Table Widget ---
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
        table_layout.setContentsMargins(0, 0, 0, 0)
        table_layout.setSpacing(0)
        
        self.product_table = QTableWidget()
        self.product_table.setAlternatingRowColors(True)
        self.product_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.product_table.setSelectionBehavior(QAbstractItemView.SelectRows) # Add this
        self.product_table.setShowGrid(False)
        self.product_table.setColumnCount(7)
        self.product_table.setHorizontalHeaderLabels([
            "Name", "SKU", "Category", "Quantity", "Cost Price", "Selling Price", "Actions"
        ])
        self.product_table.verticalHeader().setVisible(False)
        self.product_table.verticalHeader().setSectionResizeMode(QHeaderView.Fixed) # Add this
        header = self.product_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch) # Apply stretch to all
        header.setSectionsMovable(False) # Add this
        header.setSectionsClickable(False) # Add this
        # Remove individual column resize mode settings as Stretch applies to all


        table_layout.addWidget(self.product_table)
        
        # --- Empty State Widget ---
        self.empty_state_widget = EmptyStateWidget(
            icon="📦",
            message="No items in inventory yet.\nClick 'Add Item' to get started!"
        )

        # Add both to the stack
        self.table_stack.addWidget(table_container)
        self.table_stack.addWidget(self.empty_state_widget)
        
        parent_layout.addWidget(self.table_stack)

    def set_current_user(self, user: User):
        """Set the current user and update UI permissions"""
        self.current_user = user
        self.apply_permissions()
        if user:
            self.load_inventory_data() # Refresh data which will in turn refresh action buttons

    def apply_permissions(self):
        """Strict permission check using the 'NoneType Shield' pattern"""
        # Safely determine the user's role - default to False
        is_admin = False
        role = "rep"
        if self.current_user:
            role = self.current_user.role
            is_admin = (role == "admin")
        
        # Shield pattern for all potential management buttons
        for btn_name in ['manage_stock_btn', 'btn_add', 'btn_edit', 'btn_delete', 'btn_export']:
            btn = getattr(self, btn_name, None)
            if btn is not None: # This is the ONLY way to be 100% safe
                try:
                    btn.setEnabled(is_admin)
                    # manage_stock_btn is a special case: should also be hidden for non-admins
                    if btn_name == 'manage_stock_btn':
                        btn.setVisible(is_admin)
                except Exception:
                    pass

        # Table logic - safely handled via hasattr
        if hasattr(self, 'product_table') and self.product_table is not None:
            try:
                self.product_table.setColumnHidden(4, not is_admin)
                if role == "sales_rep":
                    self.product_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
            except Exception:
                pass

    def check_permissions(self):
        """Legacy check - delegating to new strict method"""
        self.apply_permissions()
            
    def open_manage_stock_dialog(self):
        """Open the Manage Stock dialog (Admin only)"""
        if not self.current_user or self.current_user.role != "admin":
            CustomWarningDialog("Access Denied", "You do not have permission to manage stock.", self).exec()
            return
            
        try:
            from ui.manage_stock_dialog import ManageStockDialog
            dialog = ManageStockDialog(self, self.current_user)
            if dialog.exec() == QDialog.Accepted:
                self.load_inventory_data()
        except Exception as e:
            CustomErrorDialog("Error", f"Could not open Manage Stock dialog: {str(e)}", self).exec()

    def refresh_data(self):
        """Refresh inventory data when global data changes"""
        self.load_inventory_data()

    def load_inventory_data(self):
        """Load inventory data from the service and handle empty state."""
        try:
            products_data = InventoryService.get_all_products()
            self.all_products = products_data
            self.display_products(self.all_products)
            self.update_completer()

            # SPRINT 4: Toggle empty state view
            if not products_data:
                self.table_stack.setCurrentWidget(self.empty_state_widget)
            else:
                self.table_stack.setCurrentWidget(self.table_stack.widget(0)) # Show table container

        except Exception as e:
            CustomErrorDialog("Error", f"Failed to load inventory data: {str(e)}", self).exec()
            self.table_stack.setCurrentWidget(self.empty_state_widget) # Show empty state on error too

    def update_completer(self):
        """Update the search completer with current product names and SKUs"""
        search_list = []
        for p in self.all_products:
            if p.get("name"):
                search_list.append(p["name"])
            if p.get("sku"):
                search_list.append(p["sku"])
        
        model = QStringListModel(search_list)
        self.completer.setModel(model)

    
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
            
            # Format prices with dynamic currency
            cost_item = QTableWidgetItem(f"{self.get_currency_symbol()} {product['cost_price']:.2f}") # Replaced GH₵
            selling_item = QTableWidgetItem(f"{self.get_currency_symbol()} {product['selling_price']:.2f}") # Replaced GH₵
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

            if self.current_user and self.current_user.role == "admin":
                edit_btn = QPushButton("✏️ Edit")
                edit_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #FFA000;
                        color: white;
                        border: none;
                        border-radius: 4px;
                        padding: 4px 8px;
                        font-size: 11px;
                        font-weight: 600;
                        min-height: 24px;
                    }
                    QPushButton:hover {
                        background-color: #FF8F00;
                    }
                """)
                edit_btn.clicked.connect(lambda checked=False, r=row: self.edit_product(r))
                actions_layout.addWidget(edit_btn)

                delete_btn = QPushButton("🗑️ Delete")
                delete_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #D32F2F;
                        color: white;
                        border: none;
                        border-radius: 4px;
                        padding: 4px 8px;
                        font-size: 11px;
                        font-weight: 600;
                        min-height: 24px;
                    }
                    QPushButton:hover {
                        background-color: #C62828;
                    }
                """)
                delete_btn.clicked.connect(lambda checked=False, r=row: self.delete_product(r))
                actions_layout.addWidget(delete_btn)
            
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
            error_dialog = CustomErrorDialog("Error", f"Failed to add product: {str(e)}", self).exec()

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
                error_dialog = CustomErrorDialog("Error", f"Failed to update product: {str(e)}", self).exec()

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
                error_dialog = CustomErrorDialog("Error", f"Failed to delete product: {str(e)}", self).exec()