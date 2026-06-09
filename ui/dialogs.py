from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
                               QLabel, QPushButton, QFrame, QTableWidget, 
                               QTableWidgetItem, QLineEdit, QComboBox, 
                               QHeaderView, QAbstractItemView, QSpinBox, 
                               QDoubleSpinBox, QMessageBox, QDialog, 
                               QDialogButtonBox, QFormLayout, QGroupBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from services.inventory_service import InventoryService
from services.customer_service import CustomerService




class EditProductDialog(QDialog):
    """Dialog for editing existing products"""
    
    def __init__(self, parent=None, product_data=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Product")
        self.setModal(True)
        self.setMinimumWidth(600)  # Make dialog wider for better visibility
        self.product_data = product_data
        self.init_ui()
        if product_data:
            self.populate_fields()
    
    def init_ui(self):
        """Initialize the dialog UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Title
        title_label = QLabel("Edit Product")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #1976d2;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Form layout for product details
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        
        # Name field
        self.name_input = QLineEdit()
        self.name_input.setObjectName("inputField")
        form_layout.addRow("Product Name*", self.name_input)
        
        # SKU field
        self.sku_input = QLineEdit()
        self.sku_input.setObjectName("inputField")
        form_layout.addRow("SKU", self.sku_input)
        
        # Category field
        self.category_input = QLineEdit()
        self.category_input.setObjectName("inputField")
        form_layout.addRow("Category", self.category_input)
        
        # Unit type
        self.unit_type_input = QLineEdit()
        self.unit_type_input.setObjectName("inputField")
        self.unit_type_input.setText("pieces")  # Default
        form_layout.addRow("Unit Type", self.unit_type_input)
        
        # Quantity field
        self.quantity_input = QDoubleSpinBox()
        self.quantity_input.setMinimum(0)
        self.quantity_input.setMaximum(99999)
        self.quantity_input.setDecimals(2)
        self.quantity_input.setValue(0)
        form_layout.addRow("Quantity*", self.quantity_input)
        
        # Cost price field
        self.cost_price_input = QDoubleSpinBox()
        self.cost_price_input.setMinimum(0)
        self.cost_price_input.setMaximum(99999)
        self.cost_price_input.setDecimals(2)
        self.cost_price_input.setValue(0)
        form_layout.addRow("Cost Price*", self.cost_price_input)
        
        # Selling price field
        self.selling_price_input = QDoubleSpinBox()
        self.selling_price_input.setMinimum(0)
        self.selling_price_input.setMaximum(99999)
        self.selling_price_input.setDecimals(2)
        self.selling_price_input.setValue(0)
        form_layout.addRow("Selling Price*", self.selling_price_input)
        
        # Reorder level
        self.reorder_level_input = QSpinBox()
        self.reorder_level_input.setMinimum(0)
        self.reorder_level_input.setMaximum(999999)
        self.reorder_level_input.setValue(5)
        form_layout.addRow("Reorder Level", self.reorder_level_input)
        
        # Supplier
        self.supplier_input = QLineEdit()
        self.supplier_input.setObjectName("inputField")
        form_layout.addRow("Supplier", self.supplier_input)
        
        # Notes
        self.notes_input = QLineEdit()
        self.notes_input.setObjectName("inputField")
        form_layout.addRow("Notes", self.notes_input)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setCursor(Qt.PointingHandCursor)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF;
                color: #555555;
                border: 1px solid #CCCCCC;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #F5F5F5;
                color: #333333;
            }
        """)
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        self.save_btn = QPushButton("Save Changes")
        self.save_btn.setCursor(Qt.PointingHandCursor)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #1976D2;
                color: #FFFFFF;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #1565C0;
            }
        """)
        self.save_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.save_btn)
        
        layout.addLayout(button_layout)
    
    def populate_fields(self):
        """Populate fields with existing product data"""
        if self.product_data:
            self.name_input.setText(self.product_data.get('name', ''))
            self.sku_input.setText(self.product_data.get('sku', ''))
            self.category_input.setText(self.product_data.get('category', '') or '')
            self.unit_type_input.setText(self.product_data.get('unit_type', ''))
            self.quantity_input.setValue(float(self.product_data.get('quantity', 0)))
            self.cost_price_input.setValue(float(self.product_data.get('cost_price', 0)))
            self.selling_price_input.setValue(float(self.product_data.get('selling_price', 0)))
            self.reorder_level_input.setValue(int(self.product_data.get('reorder_level', 0)))
            self.supplier_input.setText(self.product_data.get('supplier', '') or '')
            self.notes_input.setText(self.product_data.get('notes', '') or '')
    
    def get_product_data(self):
        """Get product data from the form"""
        return {
            'name': self.name_input.text().strip(),
            'sku': self.sku_input.text().strip() or None,
            'category': self.category_input.text().strip() or None,
            'unit_type': self.unit_type_input.text().strip(),
            'quantity': float(self.quantity_input.value()),
            'cost_price': float(self.cost_price_input.value()),
            'selling_price': float(self.selling_price_input.value()),
            'reorder_level': int(self.reorder_level_input.value()),
            'supplier': self.supplier_input.text().strip() or None,
            'notes': self.notes_input.text().strip() or None,
            'expiry_date': None  # Not implemented in this version
        }


class AddCustomerDialog(QDialog):
    """Dialog for adding new customers"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add New Customer")
        self.setModal(True)
        self.setMinimumWidth(500)  # Make dialog wider
        self.init_ui()
    
    def init_ui(self):
        """Initialize the dialog UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Title
        title_label = QLabel("Add New Customer")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #1976d2;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Form layout for customer details
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        
        # Name field
        self.name_input = QLineEdit()
        self.name_input.setObjectName("inputField")
        form_layout.addRow("Full Name*", self.name_input)
        
        # Phone field
        self.phone_input = QLineEdit()
        self.phone_input.setObjectName("inputField")
        form_layout.addRow("Phone", self.phone_input)
        
        # Email field
        self.email_input = QLineEdit()
        self.email_input.setObjectName("inputField")
        form_layout.addRow("Email", self.email_input)
        
        # Address field
        self.address_input = QLineEdit()
        self.address_input.setObjectName("inputField")
        form_layout.addRow("Address", self.address_input)
        
        # Credit limit
        self.credit_limit_input = QDoubleSpinBox()
        self.credit_limit_input.setMinimum(0)
        self.credit_limit_input.setMaximum(999999)
        self.credit_limit_input.setDecimals(2)
        self.credit_limit_input.setValue(0)
        form_layout.addRow("Credit Limit", self.credit_limit_input)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setCursor(Qt.PointingHandCursor)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF;
                color: #555555;
                border: 1px solid #CCCCCC;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #F5F5F5;
                color: #333333;
            }
        """)
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        self.save_btn = QPushButton("Save Customer")
        self.save_btn.setCursor(Qt.PointingHandCursor)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #1976D2;
                color: #FFFFFF;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #1565C0;
            }
        """)
        self.save_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.save_btn)
        
        layout.addLayout(button_layout)
    
    def get_customer_data(self):
        """Get customer data from the form"""
        return {
            'name': self.name_input.text().strip(),
            'phone': self.phone_input.text().strip() or None,
            'email': self.email_input.text().strip() or None,
            'address': self.address_input.text().strip() or None,
            'credit_limit': float(self.credit_limit_input.value())
        }


class EditCustomerDialog(QDialog):
    """Dialog for editing existing customers"""
    
    def __init__(self, parent=None, customer_data=None):
        super().__init__(parent)
        self.setWindowTitle("Update Customer Details")
        self.setModal(True)
        self.customer_data = customer_data
        self.setMinimumWidth(500)  # Make dialog wider
        self.init_ui()
        if customer_data:
            self.populate_fields()
    
    def init_ui(self):
        """Initialize the dialog UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Title
        title_label = QLabel("Update Customer Details")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #1976d2;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Form layout for customer details
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        
        # Name field
        self.name_input = QLineEdit()
        self.name_input.setObjectName("inputField")
        form_layout.addRow("Full Name*", self.name_input)
        
        # Phone field
        self.phone_input = QLineEdit()
        self.phone_input.setObjectName("inputField")
        form_layout.addRow("Phone", self.phone_input)
        
        # Email field
        self.email_input = QLineEdit()
        self.email_input.setObjectName("inputField")
        form_layout.addRow("Email", self.email_input)
        
        # Address field
        self.address_input = QLineEdit()
        self.address_input.setObjectName("inputField")
        form_layout.addRow("Address", self.address_input)
        
        # Credit limit
        self.credit_limit_input = QDoubleSpinBox()
        self.credit_limit_input.setMinimum(0)
        self.credit_limit_input.setMaximum(999999)
        self.credit_limit_input.setDecimals(2)
        self.credit_limit_input.setValue(0)
        form_layout.addRow("Credit Limit", self.credit_limit_input)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setCursor(Qt.PointingHandCursor)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF;
                color: #555555;
                border: 1px solid #CCCCCC;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #F5F5F5;
                color: #333333;
            }
        """)
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        self.save_btn = QPushButton("Save Changes")
        self.save_btn.setCursor(Qt.PointingHandCursor)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #1976D2;
                color: #FFFFFF;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #1565C0;
            }
        """)
        self.save_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.save_btn)
        
        layout.addLayout(button_layout)
    
    def populate_fields(self):
        """Populate fields with existing customer data"""
        if self.customer_data:
            self.name_input.setText(self.customer_data.get('name', ''))
            self.phone_input.setText(self.customer_data.get('phone', '') or '')
            self.email_input.setText(self.customer_data.get('email', '') or '')
            self.address_input.setText(self.customer_data.get('address', '') or '')
            self.credit_limit_input.setValue(float(self.customer_data.get('credit_limit', 0)))
    
    def get_customer_data(self):
        """Get customer data from the form"""
        return {
            'name': self.name_input.text().strip(),
            'phone': self.phone_input.text().strip() or None,
            'email': self.email_input.text().strip() or None,
            'address': self.address_input.text().strip() or None,
            'credit_limit': float(self.credit_limit_input.value())
        }


class AddCategoryDialog(QDialog):
    """Dialog for adding new categories"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add New Category")
        self.setModal(True)
        self.init_ui()
    
    def init_ui(self):
        """Initialize the dialog UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Title
        title_label = QLabel("Add New Category")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #1976d2;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Form layout for category details
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        
        # Name field
        self.name_input = QLineEdit()
        self.name_input.setObjectName("inputField")
        self.name_input.setPlaceholderText("Enter category name")
        form_layout.addRow("Category Name*", self.name_input)
        
        # Description field
        self.description_input = QLineEdit()
        self.description_input.setObjectName("inputField")
        self.description_input.setPlaceholderText("Enter category description (optional)")
        form_layout.addRow("Description", self.description_input)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setObjectName("secondaryButton")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        self.save_btn = QPushButton("Add Category")
        self.save_btn.setObjectName("primaryButton")
        self.save_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.save_btn)
        
        layout.addLayout(button_layout)
    
    def get_category_data(self):
        """Get category data from the form"""
        return {
            'name': self.name_input.text().strip(),
            'description': self.description_input.text().strip() or None
        }


class AddProductDialog(QDialog):
    """Dialog for adding new products"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add New Product")
        self.setModal(True)
        self.setMinimumWidth(600)  # Make dialog wider for better visibility
        self.init_ui()
        self.load_categories()
    
    def init_ui(self):
        """Initialize the dialog UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Title
        title_label = QLabel("Add New Product")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #1976d2;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Form layout for product details
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        
        # Name field
        self.name_input = QLineEdit()
        self.name_input.setObjectName("inputField")
        form_layout.addRow("Product Name*", self.name_input)
        
        # SKU field
        self.sku_input = QLineEdit()
        self.sku_input.setObjectName("inputField")
        form_layout.addRow("SKU", self.sku_input)
        
        # Category field - Changed to QComboBox
        self.category_combo = QComboBox()
        self.category_combo.setObjectName("inputField")
        self.category_combo.setEditable(True)  # Allow custom input
        form_layout.addRow("Category", self.category_combo)
        
        # Add "Add New Category" button
        category_layout = QHBoxLayout()
        category_layout.addWidget(self.category_combo)
        
        self.add_category_btn = QPushButton("+")
        self.add_category_btn.setObjectName("secondaryButton")
        self.add_category_btn.setToolTip("Add New Category")
        self.add_category_btn.clicked.connect(self.add_new_category)
        category_layout.addWidget(self.add_category_btn)
        
        form_layout.addRow("Category", category_layout)
        
        # Unit type
        self.unit_type_input = QLineEdit()
        self.unit_type_input.setObjectName("inputField")
        self.unit_type_input.setText("pieces")  # Default
        form_layout.addRow("Unit Type", self.unit_type_input)
        
        # Quantity field
        self.quantity_input = QDoubleSpinBox()
        self.quantity_input.setMinimum(0)
        self.quantity_input.setMaximum(999999)
        self.quantity_input.setDecimals(2)
        self.quantity_input.setValue(0)
        form_layout.addRow("Quantity*", self.quantity_input)
        
        # Cost price field
        self.cost_price_input = QDoubleSpinBox()
        self.cost_price_input.setMinimum(0)
        self.cost_price_input.setMaximum(9999)
        self.cost_price_input.setDecimals(2)
        self.cost_price_input.setValue(0)
        form_layout.addRow("Cost Price*", self.cost_price_input)
        
        # Selling price field
        self.selling_price_input = QDoubleSpinBox()
        self.selling_price_input.setMinimum(0)
        self.selling_price_input.setMaximum(999)
        self.selling_price_input.setDecimals(2)
        self.selling_price_input.setValue(0)
        form_layout.addRow("Selling Price*", self.selling_price_input)
        
        # Reorder level
        self.reorder_level_input = QSpinBox()
        self.reorder_level_input.setMinimum(0)
        self.reorder_level_input.setMaximum(999999)
        self.reorder_level_input.setValue(5)
        form_layout.addRow("Reorder Level", self.reorder_level_input)
        
        # Supplier
        self.supplier_input = QLineEdit()
        self.supplier_input.setObjectName("inputField")
        form_layout.addRow("Supplier", self.supplier_input)
        
        # Notes
        self.notes_input = QLineEdit()
        self.notes_input.setObjectName("inputField")
        form_layout.addRow("Notes", self.notes_input)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setObjectName("secondaryButton")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        self.save_btn = QPushButton("Save Product")
        self.save_btn.setObjectName("primaryButton")
        self.save_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.save_btn)
        
        layout.addLayout(button_layout)
    
    def load_categories(self):
        """Load categories into the combobox"""
        try:
            categories = InventoryService.get_all_categories()
            self.category_combo.clear()
            for category in categories:
                self.category_combo.addItem(category['name'])
            # Add option for new category at the end
            self.category_combo.addItem("Add New Category...")
        except Exception as e:
            print(f"Error loading categories: {e}")
            # Fallback to default categories
            self.category_combo.addItems(["Electronics", "Clothing", "Food", "Other", "Add New Category..."])
    
    def add_new_category(self):
        """Open dialog to add a new category"""
        dialog = AddCategoryDialog(self)
        if dialog.exec() == QDialog.Accepted:
            category_data = dialog.get_category_data()
            if category_data['name']:  # Check if name is provided
                try:
                    category_id = InventoryService.add_category(category_data)
                    if category_id:
                        # Reload categories to include the new one
                        self.load_categories()
                        # Select the newly added category
                        index = self.category_combo.findText(category_data['name'])
                        if index >= 0:
                            self.category_combo.setCurrentIndex(index)
                        QMessageBox.information(self, "Success", "Category added successfully!")
                    else:
                        QMessageBox.critical(self, "Error", "Failed to add category")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to add category: {str(e)}")
    
    def get_product_data(self):
        """Get product data from the form"""
        # Get the selected text from the combo box
        selected_category = self.category_combo.currentText()
        
        # If user selected "Add New Category..." option, show the dialog
        if selected_category == "Add New Category...":
            self.add_new_category()
            # After adding, get the current text again
            selected_category = self.category_combo.currentText()
        
        # Ensure SKU is not None (database requirement)
        name = self.name_input.text().strip()
        sku = self.sku_input.text().strip()
        if not sku:
            # Simple fallback SKU
            import time
            sku = f"{name[:5].upper()}_{int(time.time())}"

        return {
            'name': name,
            'sku': sku,
            'category': selected_category if selected_category != "Add New Category..." else None,
            'unit_type': self.unit_type_input.text().strip(),
            'quantity': float(self.quantity_input.value()),
            'cost_price': float(self.cost_price_input.value()),
            'selling_price': float(self.selling_price_input.value()),
            'reorder_level': int(self.reorder_level_input.value()),
            'supplier': self.supplier_input.text().strip() or None,
            'notes': self.notes_input.text().strip() or None,
            'expiry_date': None  # Not implemented in this version
        }


from ui.confirm_dialog import ClearDebtConfirmationDialog

class PayDebtDialog(QDialog):
    """Dialog for paying off customer debt"""
    
    def __init__(self, current_debt, parent=None):
        super().__init__(parent)
        self.current_debt = current_debt
        self.payment_amount = None
        self.setWindowTitle("Pay Debt")
        self.setModal(True)
        self.setFixedSize(400, 250)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Header
        title = QLabel("Record Payment")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2C3E50;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Current Debt Display
        debt_frame = QFrame()
        debt_frame.setStyleSheet("background-color: #FFF3E0; border-radius: 6px; padding: 10px;")
        debt_layout = QHBoxLayout(debt_frame)
        debt_label = QLabel(f"Current Debt: GHS {self.current_debt:,.2f}")
        debt_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #E65100;")
        debt_label.setAlignment(Qt.AlignCenter)
        debt_layout.addWidget(debt_label)
        layout.addWidget(debt_frame)
        
        # Input Field
        self.amount_input = QDoubleSpinBox()
        self.amount_input.setPrefix("GHS ")
        self.amount_input.setMaximum(999999.99)
        self.amount_input.setDecimals(2)
        self.amount_input.setStyleSheet("""
            QDoubleSpinBox {
                padding: 10px;
                font-size: 16px;
                border: 1px solid #CCCCCC;
                border-radius: 6px;
            }
        """)
        layout.addWidget(self.amount_input)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setCursor(Qt.PointingHandCursor)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF;
                color: #555555;
                border: 1px solid #CCCCCC;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #F5F5F5; }
        """)
        self.cancel_btn.clicked.connect(self.reject)
        
        self.clear_debt_btn = QPushButton("Clear Debt")
        self.clear_debt_btn.setCursor(Qt.PointingHandCursor)
        self.clear_debt_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #F57C00; }
        """)
        self.clear_debt_btn.clicked.connect(self.clear_debt)
        
        self.pay_btn = QPushButton("Pay")
        self.pay_btn.setCursor(Qt.PointingHandCursor)
        self.pay_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 24px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #388E3C; }
        """)
        self.pay_btn.clicked.connect(self.pay_amount)
        
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.clear_debt_btn)
        btn_layout.addWidget(self.pay_btn)
        
        layout.addLayout(btn_layout)
        
    def clear_debt(self):
        dialog = ClearDebtConfirmationDialog(self)
        if dialog.exec() == QDialog.Accepted:
            self.payment_amount = self.current_debt
            self.accept()
        
    def pay_amount(self):
        val = self.amount_input.value()
        if val <= 0:
            return # Don't accept 0
        self.payment_amount = val
        self.accept()
    
    def get_payment_amount(self):
        return self.payment_amount


class ProductDetailsDialog(QDialog):
    """Dialog for viewing product details"""
    
    def __init__(self, parent=None, product_data=None, show_cost=False):
        super().__init__(parent)
        self.setWindowTitle("Product Details")
        self.setModal(True)
        self.setMinimumWidth(500)
        self.product_data = product_data or {}
        self.show_cost = show_cost
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Header
        header = QLabel(self.product_data.get('name', 'Product Name'))
        header.setStyleSheet("font-size: 22px; font-weight: bold; color: #1976D2; margin-bottom: 10px;")
        header.setAlignment(Qt.AlignLeft)
        layout.addWidget(header)
        
        # Details Container
        details_frame = QFrame()
        details_frame.setStyleSheet("""
            QFrame {
                background-color: #F8F9FA;
                border-radius: 8px;
                border: 1px solid #E0E0E0;
            }
            QLabel {
                font-size: 14px;
                color: #333333;
                padding: 4px;
            }
            QLabel#label {
                font-weight: bold;
                color: #555555;
            }
        """)
        
        form_layout = QFormLayout(details_frame)
        form_layout.setContentsMargins(20, 20, 20, 20)
        form_layout.setSpacing(15)
        form_layout.setLabelAlignment(Qt.AlignLeft)
        
        # Helper to add rows
        def add_row(label, value):
            lbl = QLabel(label)
            lbl.setObjectName("label")
            val = QLabel(str(value))
            val.setWordWrap(True)
            form_layout.addRow(lbl, val)
            
        add_row("SKU:", self.product_data.get('sku', 'N/A'))
        add_row("Category:", self.product_data.get('category', 'N/A'))
        add_row("Unit Type:", self.product_data.get('unit_type', 'pieces'))
        add_row("Quantity:", f"{self.product_data.get('quantity', 0)} {self.product_data.get('unit_type', 'pieces')}")
        add_row("Selling Price:", f"GHS {self.product_data.get('selling_price', 0):.2f}")
        
        if self.show_cost:
            add_row("Cost Price:", f"GHS {self.product_data.get('cost_price', 0):.2f}")
            # Calculate Margin
            cp = self.product_data.get('cost_price', 0)
            sp = self.product_data.get('selling_price', 0)
            if cp > 0:
                margin = ((sp - cp) / cp) * 100
                add_row("Profit Margin:", f"{margin:.1f}%")
        
        if self.product_data.get('supplier'):
            add_row("Supplier:", self.product_data.get('supplier'))
            
        if self.product_data.get('notes'):
            add_row("Notes:", self.product_data.get('notes'))
        
        layout.addWidget(details_frame)
        
        layout.addStretch()
        
        # Close Button
        close_btn = QPushButton("Close")
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #1976D2;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 24px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #1565C0; }
        """)
        close_btn.clicked.connect(self.accept)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)