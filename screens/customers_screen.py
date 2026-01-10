from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
                               QLabel, QPushButton, QFrame, QTableWidget, 
                               QTableWidgetItem, QLineEdit, QComboBox, 
                               QHeaderView, QAbstractItemView, QGroupBox,
                               QDialog, QDialogButtonBox, QFormLayout,
                               QMessageBox, QTabWidget, QScrollArea)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QColor

from database.models import User, Customer
from services.customer_service import CustomerService
from services.sales_service import SalesService
from ui.dialogs import AddCustomerDialog, EditCustomerDialog, PayDebtDialog
from ui.custom_dialog import CustomWarningDialog, CustomErrorDialog, CustomInfoDialog
from datetime import datetime


class CustomersScreen(QWidget):
    """Customer management screen with dashboard layout"""
    
    def __init__(self):
        super().__init__()
        self.current_user = None
        self.all_customers = []
        self.init_ui()
        self.load_customer_data()
        
    def init_ui(self):
        """Initialize the customer screen UI without sidebar"""
        # Set main background color
        self.setStyleSheet("background-color: #F7F7FD;")
        
        # Main layout (without sidebar)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Create main content area only
        self.create_main_content(main_layout)
    
    def set_current_user(self, user: User):
        """Set current user and update UI permissions"""
        self.current_user = user
        self.load_customer_data() # Refresh table to show correct action buttons
    
    def create_main_content(self, main_layout):
        """Create the main content area with summary cards and table"""
        # Redundant wrapper removed
        
        # Header section
        header_layout = QHBoxLayout()
        header_layout.setSpacing(20)
        
        # Title
        title_label = QLabel("Customers")
        title_label.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #2C3E50;
        """)
        header_layout.addWidget(title_label)
        
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
        
        # Search icon
        search_icon = QLabel("🔍")
        search_icon.setStyleSheet("color: #6C757D; font-size: 14px; background: transparent; border: none;")
        search_layout.addWidget(search_icon)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search customers...")
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
        
        # Add Customers button
        self.add_customer_btn = QPushButton("+ Add Customers")
        self.add_customer_btn.setStyleSheet("""
            QPushButton {
                background-color: #4A76D9;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #3A5FA9;
            }
        """)
        self.add_customer_btn.clicked.connect(self.on_add_customer_clicked)
        header_layout.addWidget(self.add_customer_btn)
        
        main_layout.addLayout(header_layout)
        
        # Summary cards section
        self.create_summary_cards(main_layout)
        
        # Customers data table
        self.create_customers_table(main_layout)
    
    def create_summary_cards(self, parent_layout):
        """Create the four summary cards (KPIs)"""
        cards_layout = QGridLayout()
        cards_layout.setSpacing(16)
        
        self.total_customers_card = self.create_kpi_card("Total Customers", "0", "#192A56")
        cards_layout.addWidget(self.total_customers_card, 0, 0)
        
        self.avg_orders_card = self.create_kpi_card("Average orders", "0", "#192A56")
        cards_layout.addWidget(self.avg_orders_card, 0, 1)
        
        self.new_customers_card = self.create_kpi_card("New Customers", "0", "#00BCD4")
        cards_layout.addWidget(self.new_customers_card, 0, 2)
        
        self.top_customer_card = self.create_kpi_card("Top Customer", "N/A", "#4A76D9")
        cards_layout.addWidget(self.top_customer_card, 0, 3)
        
        parent_layout.addLayout(cards_layout)
    
    def create_kpi_card(self, title, value, bg_color):
        """Create a KPI card with specified solid background color"""
        card = QFrame()
        card.setFixedHeight(120)
        
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border-radius: 10px;
                border: none;
            }}
        """)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(8)
        
        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 14px; font-weight: 500; color: white; opacity: 0.9;")
        layout.addWidget(title_label)
        
        # Value
        value_label = QLabel(value)
        value_label.setStyleSheet("font-size: 28px; font-weight: bold; color: white;")
        layout.addWidget(value_label)
        
        layout.addStretch()
        card.value_label = value_label
        return card
    
    def create_customers_table(self, parent_layout):
        """Create the customers data table with new columns"""
        table_container = QFrame()
        table_container.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 10px;
                border: none;
            }
        """)
        
        table_layout = QVBoxLayout(table_container)
        table_layout.setContentsMargins(20, 20, 20, 20)
        table_layout.setSpacing(0)
        
        # Table title
        table_title = QLabel("Customers Data")
        table_title.setStyleSheet("font-size: 16px; font-weight: 600; color: #2C3E50; margin-bottom: 12px;")
        table_layout.addWidget(table_title)
        
        # Customers table
        self.customers_table = QTableWidget()
        self.customers_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.customers_table.setShowGrid(False)
        self.customers_table.setColumnCount(5)
        # UPDATED COLUMNS: ID, Customer Name, Phone, Debt(GHS), Actions
        self.customers_table.setHorizontalHeaderLabels([
            "ID", "Customer Name", "Phone", "Debt (GHS)", "Actions"
        ])
        
        # Configure table appearance
        self.customers_table.setAlternatingRowColors(True)
        self.customers_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.customers_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.customers_table.setSortingEnabled(True)
        
        # Style table header
        self.customers_table.horizontalHeader().setStyleSheet("""
            QHeaderView::section {
                background-color: #F8F9FA;
                color: #2C3E50;
                padding: 12px;
                font-weight: 600;
                border: none;
                border-bottom: 1px solid #E0E0E0;
                font-size: 12px;
                text-align: left;
            }
        """)
        
        self.customers_table.setStyleSheet("""
            /* Table Widget Base Styles */
            QTableWidget {
                background-color: white;
                border: none;
                gridline-color: transparent;
                outline: none;
            }
            
            /* Fixed Row Height and Cell Styles */
            QTableWidget::item {
                padding: 12px 8px;
                border: none;
                min-height: 50px;
                max-height: 50px;
            }
            
            /* Alternating Row Colors */
            QTableWidget::item:alternate {
                background-color: #FAFAFA;
            }
            
            QTableWidget::item:!alternate {
                background-color: #FFFFFF;
            }
            
            /* Selected Row Style */
            QTableWidget::item:selected {
                background-color: #E3F2FD;
                color: #1976D2;
            }
            
            /* Hover State */
            QTableWidget::item:hover {
                background-color: #F5F5F5;
            }
        """)
        
        # Enforce fixed row heights
        self.customers_table.verticalHeader().setDefaultSectionSize(50)
        self.customers_table.verticalHeader().setVisible(False)

        # Set column widths
        header = self.customers_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)   # ID
        header.setSectionResizeMode(1, QHeaderView.Stretch) # Name
        header.setSectionResizeMode(2, QHeaderView.Fixed)   # Phone
        header.setSectionResizeMode(3, QHeaderView.Fixed)   # Debt
        header.setSectionResizeMode(4, QHeaderView.Fixed)   # Actions
        
        self.customers_table.setColumnWidth(0, 50)  # ID
        self.customers_table.setColumnWidth(2, 150) # Phone
        self.customers_table.setColumnWidth(3, 120) # Debt
        self.customers_table.setColumnWidth(4, 250) # Actions
        
        table_layout.addWidget(self.customers_table)
        
        parent_layout.addWidget(table_container)
    
    def load_customer_data(self):
        """Load customer data from service"""
        try:
            customers_data = CustomerService.get_all_customers()
            self.all_customers = customers_data
            self.display_customers(self.all_customers)
            self.update_summary_cards()
        except Exception as e:
            dialog = CustomErrorDialog("Error", f"Failed to load customer data: {str(e)}", self)
            dialog.exec()
    
    def update_summary_cards(self):
        """Update summary cards with current data, ensuring robustness against empty data."""
        try:
            customers = self.all_customers
            total_customer_count = len(customers)
            self.total_customers_card.value_label.setText(str(total_customer_count))
            
            # New Customers (last 30 days)
            new_customers_data = CustomerService.get_new_customer_count(days=30)
            self.new_customers_card.value_label.setText(str(new_customers_data.get('count', 0)))
            
            # Average Orders (requires total sales transactions)
            total_sales_count = CustomerService.get_total_sales_count().get('count', 0)
            # Prevent ZeroDivisionError if there are no customers
            avg_orders = total_sales_count / total_customer_count if total_customer_count > 0 else 0
            self.avg_orders_card.value_label.setText(f"{avg_orders:.1f}")
            
            # Fetch real top customer
            top_customer = CustomerService.get_top_customer()
            if top_customer:
                name = top_customer['name']
                revenue = top_customer['total_sales']
                count = top_customer['transaction_count']
                
                # Use triple-quoted f-string for cleaner multi-line HTML formatting
                display_text = f"""<div style='text-align: left; line-height: 1.2;'>
                                     <span style='font-size: 20px; font-weight: bold; color: white;'>{name}</span><br>
                                     <span style='font-size: 15px; font-weight: normal; color: rgba(255,255,255,0.9);'>
                                         GH₵ {revenue:,.2f} • {count} sales
                                     </span>
                                 </div>"""
                
                self.top_customer_card.value_label.setText(display_text)
                self.top_customer_card.value_label.setStyleSheet("font-size: 14px; color: inherit;") # Let HTML handle styling
                self.top_customer_card.setToolTip(f"Customer: {name}\nTotal Revenue: GH₵ {revenue:,.2f}\nTotal Transactions: {count}")
            else:
                self.top_customer_card.value_label.setText("N/A")
                self.top_customer_card.value_label.setStyleSheet("font-size: 28px; font-weight: bold; color: white;") # Reset to default if N/A
                
        except Exception as e:
            QMessageBox.warning(self, "Warning", f"Failed to update summary cards: {str(e)}")
            print(f"Error updating summary cards: {e}")

    def display_customers(self, customers):
        """Display customers in table with new column structure"""
        self.customers_table.setRowCount(len(customers))
        
        for row, customer in enumerate(customers):
            # ID
            id_item = QTableWidgetItem(str(customer.get("id")))
            id_item.setTextAlignment(Qt.AlignCenter)
            id_item.setData(Qt.UserRole, customer.get("id"))
            self.customers_table.setItem(row, 0, id_item)
            
            # Customer Name
            name_item = QTableWidgetItem(customer.get("name", "N/A"))
            self.customers_table.setItem(row, 1, name_item)
            
            # Phone
            phone_item = QTableWidgetItem(customer.get("phone", "N/A"))
            self.customers_table.setItem(row, 2, phone_item)
            
            # Debt (GHS) - from outstanding_balance
            debt = customer.get("outstanding_balance", 0.0)
            debt_item = QTableWidgetItem(f"{debt:,.2f}")
            debt_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            if debt > 0:
                debt_item.setForeground(QColor("#E74C3C")) # Red if they have debt
            self.customers_table.setItem(row, 3, debt_item)

            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(2, 0, 2, 0)
            actions_layout.setSpacing(6)
            actions_layout.setAlignment(Qt.AlignCenter)
            
            # View Button
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
            view_btn.clicked.connect(lambda checked=False, r=row: self.view_customer(r))
            actions_layout.addWidget(view_btn)

            # Admin only actions
            if self.current_user and self.current_user.role == "admin":
                edit_btn = QPushButton("✏️ Edit")
                edit_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #ffc107;
                        color: #333333;
                        border: none;
                        border-radius: 4px;
                        padding: 4px 8px;
                        font-size: 11px;
                        font-weight: 600;
                        min-height: 24px;
                    }
                    QPushButton:hover {
                        background-color: #ffb300;
                    }
                """)
                edit_btn.clicked.connect(lambda checked=False, r=row: self.edit_customer(r))
                actions_layout.addWidget(edit_btn)
                
                delete_btn = QPushButton("🗑️ Delete")
                delete_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #f44336;
                        color: white;
                        border: none;
                        border-radius: 4px;
                        padding: 4px 8px;
                        font-size: 11px;
                        font-weight: 600;
                        min-height: 24px;
                    }
                    QPushButton:hover {
                        background-color: #e53935;
                    }
                """)
                delete_btn.clicked.connect(lambda checked=False, r=row: self.delete_customer(r))
                actions_layout.addWidget(delete_btn)
            
            self.customers_table.setCellWidget(row, 4, actions_widget)
    
    def on_search_changed(self, text):
        if not text:
            self.display_customers(self.all_customers)
        else:
            filtered = [
                c for c in self.all_customers
                if text.lower() in c.get("name", "").lower() or text.lower() in c.get("phone", "").lower()
            ]
            self.display_customers(filtered)
    
    def on_add_customer_clicked(self):
        try:
            dialog = AddCustomerDialog(self)
            if dialog.exec() == QDialog.Accepted:
                customer_data = dialog.get_customer_data()
                if CustomerService.add_customer(customer_data):
                    self.load_customer_data()
                    CustomInfoDialog("Success", "Customer added successfully!", self).exec()
                else:
                    CustomErrorDialog("Error", "Failed to add customer", self).exec()
        except Exception as e:
            CustomErrorDialog("Error", f"Failed to add customer: {str(e)}", self).exec()
    
    def view_customer(self, row):
        """Open the detailed Customer History Dialog"""
        customer_id = self.customers_table.item(row, 0).data(Qt.UserRole)
        customer_data = next((c for c in self.all_customers if c["id"] == customer_id), None)
        
        if customer_data:
            dialog = CustomerHistoryDialog(self, customer_data)
            dialog.exec()
    
    def edit_customer(self, row):
        if self.current_user and self.current_user.role != "admin":
            CustomWarningDialog("Access Denied", "You do not have permission to edit customers.", self).exec()
            return

        customer_id = self.customers_table.item(row, 0).data(Qt.UserRole)
        customer_data = next((c for c in self.all_customers if c["id"] == customer_id), None)

        if customer_data:
            dialog = EditCustomerDialog(self, customer_data)
            if dialog.exec() == QDialog.Accepted:
                updated_data = dialog.get_customer_data()
                updated_data['id'] = customer_data['id']
                if CustomerService.update_customer(updated_data):
                    self.load_customer_data()
                    CustomInfoDialog("Success", "Customer updated successfully!", self).exec()
                else:
                    CustomErrorDialog("Error", "Failed to update customer", self).exec()
    
    def delete_customer(self, row):
        if self.current_user and self.current_user.role != "admin":
            CustomWarningDialog("Access Denied", "You do not have permission to delete customers.", self).exec()
            return

        customer_id = self.customers_table.item(row, 0).data(Qt.UserRole)
        if customer_id:
            name = self.customers_table.item(row, 1).text()
            if CustomWarningDialog("Confirm Delete", f"Delete customer '{name}'?", self).exec() == QDialog.Accepted:
                if CustomerService.delete_customer(customer_id):
                    self.load_customer_data()
                    CustomInfoDialog("Success", "Customer deleted successfully!", self).exec()
                else:
                    CustomErrorDialog("Error", "Failed to delete customer", self).exec()


class CustomerHistoryDialog(QDialog):
    """Redesigned Customer View with 3 Tabs: Sales, Credit, Payment History"""
    
    def __init__(self, parent=None, customer_data=None):
        super().__init__(parent)
        self.customer = customer_data
        self.setWindowTitle(f"Customer Details - {self.customer['name']}")
        self.setModal(True)
        self.setMinimumSize(900, 700)
        self.setStyleSheet("background-color: #F7F7FD;")
        self.init_ui()
        self.load_data()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Header Info
        header_frame = QFrame()
        header_frame.setStyleSheet("background-color: white; border-radius: 10px; border: 1px solid #E0E0E0;")
        header_layout = QHBoxLayout(header_frame)
        
        name_lbl = QLabel(f"{self.customer['name']}")
        name_lbl.setStyleSheet("font-size: 20px; font-weight: bold; color: #2C3E50;")
        phone_lbl = QLabel(f"📞 {self.customer.get('phone', 'N/A')}")
        phone_lbl.setStyleSheet("font-size: 14px; color: #555;")
        
        # Balance Label
        balance = self.customer.get('outstanding_balance', 0.0)
        balance_color = "#E74C3C" if balance > 0 else "#27AE60"
        balance_lbl = QLabel(f"Balance: GH₵ {balance:,.2f}")
        balance_lbl.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {balance_color}; margin-left: 15px;")
        
        header_layout.addWidget(name_lbl)
        header_layout.addWidget(phone_lbl)
        header_layout.addWidget(balance_lbl)
        header_layout.addStretch()
        
        # Pay Debt Button
        self.pay_debt_btn = QPushButton("Pay Debt")
        self.pay_debt_btn.setCursor(Qt.PointingHandCursor)
        self.pay_debt_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #388E3C; }
        """)
        self.pay_debt_btn.clicked.connect(self.on_pay_debt_clicked)
        header_layout.addWidget(self.pay_debt_btn)
        
        layout.addWidget(header_frame)
        
        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #E0E0E0; background: white; border-radius: 8px; }
            QTabBar::tab { background: #F5F5F5; padding: 10px 20px; border-top-left-radius: 8px; border-top-right-radius: 8px; margin-right: 2px; }
            QTabBar::tab:selected { background: white; color: #1976D2; font-weight: bold; border-bottom: 2px solid #1976D2; }
        """)
        
        self.sales_tab = self.create_sales_history_tab()
        self.credit_tab = self.create_credit_history_tab()
        self.payment_tab = self.create_payment_history_tab()
        
        self.tabs.addTab(self.sales_tab, "Sales History")
        self.tabs.addTab(self.credit_tab, "Credit History")
        self.tabs.addTab(self.payment_tab, "Payment History")
        
        layout.addWidget(self.tabs)
        
        # Close Button
        close_btn_layout = QHBoxLayout()
        close_btn_layout.addStretch()
        
        self.close_btn = QPushButton("Close")
        self.close_btn.setCursor(Qt.PointingHandCursor)
        self.close_btn.setFixedSize(100, 40)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: #757575;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #616161; }
        """)
        self.close_btn.clicked.connect(self.reject)
        
        close_btn_layout.addWidget(self.close_btn)
        layout.addLayout(close_btn_layout)

    def on_pay_debt_clicked(self):
        # Refresh current customer data to get latest debt
        updated_customer = CustomerService.get_customer_by_id(self.customer['id'])
        if updated_customer:
            self.customer = updated_customer # Update local reference
            
        current_debt = self.customer.get('outstanding_balance', 0.0)
        
        if current_debt <= 0:
            CustomInfoDialog("No Debt", "This customer has no outstanding debt.", self).exec()
            return

        dialog = PayDebtDialog(current_debt, self)
        if dialog.exec() == QDialog.Accepted:
            amount = dialog.get_payment_amount()
            if amount:
                payment_data = {
                    'customer_id': self.customer['id'],
                    'amount': amount,
                    'date': datetime.now().isoformat(),
                    'payment_method': 'Cash', # Default to cash for debt repayment
                    'notes': 'Debt Payment'
                }
                
                if CustomerService.add_customer_payment(payment_data):
                    CustomInfoDialog("Success", f"Payment of GH₵ {amount:,.2f} recorded!", self).exec()
                    # Refresh data
                    self.load_data()
                    # Also notify parent to refresh main table
                    if self.parent():
                        self.parent().load_customer_data()
                else:
                    CustomErrorDialog("Error", "Failed to record payment.", self).exec()

    def create_card(self, title, value, color):
        card = QFrame()
        card.setFixedHeight(100)
        card.setStyleSheet(f"background-color: {color}; border-radius: 10px;")
        l = QVBoxLayout(card)
        l.addWidget(QLabel(title, styleSheet="color: white; font-size: 14px; opacity: 0.9;"))
        self.lbl_map = getattr(self, 'lbl_map', {})
        val_lbl = QLabel(value, styleSheet="color: white; font-size: 24px; font-weight: bold;")
        l.addWidget(val_lbl)
        self.lbl_map[title] = val_lbl 
        return card

    def create_sales_history_tab(self):
        tab = QWidget()
        l = QVBoxLayout(tab)
        
        # Card
        self.total_sales_card = self.create_card("Total Sales Transactions", "0", "#4caf50") # Green
        l.addWidget(self.total_sales_card)
        
        # Table
        self.sales_table = QTableWidget()
        self.sales_table.setColumnCount(6)
        self.sales_table.setHorizontalHeaderLabels(["Date", "Product", "Quantity", "Total Price", "Amount Paid", "Debt Added"])
        self.sales_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        l.addWidget(self.sales_table)
        return tab

    def create_credit_history_tab(self):
        tab = QWidget()
        l = QVBoxLayout(tab)
        
        # Card
        self.total_credit_card = self.create_card("Total Credit Entries", "0", "#ff9800") # Orange
        l.addWidget(self.total_credit_card)
        
        # Table
        self.credit_table = QTableWidget()
        self.credit_table.setColumnCount(6)
        self.credit_table.setHorizontalHeaderLabels(["Date", "Product", "Quantity", "Total Price", "Amount Paid", "Debt Amount"])
        self.credit_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        l.addWidget(self.credit_table)
        return tab

    def create_payment_history_tab(self):
        tab = QWidget()
        l = QVBoxLayout(tab)
        
        # Card
        self.total_payments_card = self.create_card("Total Payments", "GH₵ 0.00", "#1976d2") # Blue
        l.addWidget(self.total_payments_card)
        
        # Table
        self.payment_table = QTableWidget()
        self.payment_table.setColumnCount(5)
        self.payment_table.setHorizontalHeaderLabels(["Date", "Payment Amount", "Previous Balance", "New Balance", "Reduction"])
        self.payment_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        l.addWidget(self.payment_table)
        return tab

    def load_data(self):
        try:
            cid = self.customer['id']
            
            # --- FETCH DATA ---
            sales = SalesService.get_sales_by_customer(cid)
            payments = CustomerService.get_customer_payments(cid)
            
            # --- LEDGER RECONSTRUCTION ---
            # Combine all events to calculate running balance
            events = []
            
            for s in sales:
                # Calculate debt increase (Credit Sale)
                total = s.get('total_amount', 0.0)
                paid = s.get('amount_paid', 0.0)
                debt_increase = total - paid
                
                if debt_increase > 0 or s['payment_method'].lower() == 'credit':
                    events.append({
                        'type': 'sale',
                        'date': s['date'], # ISO string
                        'amount': debt_increase,
                        'id': s['id']
                    })
            
            for p in payments:
                events.append({
                    'type': 'payment',
                    'date': p['date'], # ISO string
                    'amount': p['amount'],
                    'id': p['id']
                })
                
            # Sort by date (oldest first)
            events.sort(key=lambda x: x['date'])
            
            running_balance = 0.0
            payment_snapshots = {} # Map payment_id -> (prev_balance, new_balance)
            
            for e in events:
                if e['type'] == 'sale':
                    running_balance += e['amount']
                elif e['type'] == 'payment':
                    prev = running_balance
                    running_balance -= e['amount']
                    # Snapshot for display
                    payment_snapshots[e['id']] = (prev, running_balance)

            # --- SALES TAB ---
            self.lbl_map["Total Sales Transactions"].setText(str(len(sales)))
            self.sales_table.setRowCount(len(sales))
            for r, s in enumerate(sales):
                date = s['date'][:10] if s['date'] else "N/A"
                products = ", ".join([i['product_name'] for i in s['items']])
                qty = sum([i['quantity'] for i in s['items']])
                total = s['total_amount']
                paid = s.get('amount_paid', 0.0)
                debt_added = max(0, total - paid)
                
                self.sales_table.setItem(r, 0, QTableWidgetItem(date))
                self.sales_table.setItem(r, 1, QTableWidgetItem(products))
                self.sales_table.setItem(r, 2, QTableWidgetItem(str(qty)))
                self.sales_table.setItem(r, 3, QTableWidgetItem(f"{total:.2f}"))
                self.sales_table.setItem(r, 4, QTableWidgetItem(f"{paid:.2f}"))
                self.sales_table.setItem(r, 5, QTableWidgetItem(f"{debt_added:.2f}"))

            # --- CREDIT TAB ---
            credit_sales = [s for s in sales if (s['total_amount'] - s.get('amount_paid', 0)) > 0]
            self.lbl_map["Total Credit Entries"].setText(str(len(credit_sales)))
            self.credit_table.setRowCount(len(credit_sales))
            for r, s in enumerate(credit_sales):
                date = s['date'][:10] if s['date'] else "N/A"
                products = ", ".join([i['product_name'] for i in s['items']])
                qty = sum([i['quantity'] for i in s['items']])
                total = s['total_amount']
                paid = s.get('amount_paid', 0.0)
                debt = total - paid
                
                self.credit_table.setItem(r, 0, QTableWidgetItem(date))
                self.credit_table.setItem(r, 1, QTableWidgetItem(products))
                self.credit_table.setItem(r, 2, QTableWidgetItem(str(qty)))
                self.credit_table.setItem(r, 3, QTableWidgetItem(f"{total:.2f}"))
                self.credit_table.setItem(r, 4, QTableWidgetItem(f"{paid:.2f}"))
                self.credit_table.setItem(r, 5, QTableWidgetItem(f"{debt:.2f}"))

            # --- PAYMENT TAB ---
            total_paid = sum([p['amount'] for p in payments])
            self.lbl_map["Total Payments"].setText(f"GH₵ {total_paid:,.2f}")
            self.payment_table.setRowCount(len(payments))
            
            for r, p in enumerate(payments):
                date = p['date'][:10] if p['date'] else "N/A"
                amt = p['amount']
                
                # Retrieve snapshot
                prev_bal, new_bal = payment_snapshots.get(p['id'], (0.0, 0.0))
                
                self.payment_table.setItem(r, 0, QTableWidgetItem(date))
                self.payment_table.setItem(r, 1, QTableWidgetItem(f"{amt:.2f}"))
                self.payment_table.setItem(r, 2, QTableWidgetItem(f"{prev_bal:.2f}"))
                self.payment_table.setItem(r, 3, QTableWidgetItem(f"{new_bal:.2f}"))
                self.payment_table.setItem(r, 4, QTableWidgetItem(f"{amt:.2f}"))

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load customer history: {str(e)}")
            print(f"Error loading customer history: {e}")
