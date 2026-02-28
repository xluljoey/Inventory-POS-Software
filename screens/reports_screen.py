from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
                               QLabel, QPushButton, QFrame, QTableWidget, 
                               QTableWidgetItem, QComboBox, QHeaderView, 
                               QAbstractItemView, QGroupBox, QDateEdit,
                               QCalendarWidget, QTabWidget, QMessageBox, QFileDialog,
                               QStackedWidget, QSizePolicy, QSpacerItem) # Added QSizePolicy, QSpacerItem
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont, QColor, QTextDocument
from PySide6.QtPrintSupport import QPrinter, QPrintDialog
from loguru import logger
import pandas as pd
from fpdf import FPDF
import os

from database.models import User
from services.inventory_service import InventoryService
from services.customer_service import CustomerService
from services.sales_service import SalesService
from database.database import DatabaseService
from config.app_config import AppConfig
from datetime import datetime, timedelta
from ui.common_widgets import EmptyStateWidget


class ReportsScreen(QWidget):
    """Reports and analytics screen with various reports"""
    
    def __init__(self):
        super().__init__()
        self.current_user = None
        self.init_ui()

    def _create_table_stack(self, table_widget, icon, message):
        """Helper to create a QStackedWidget for a table and its empty state."""
        stack = QStackedWidget()
        empty_widget = EmptyStateWidget(icon, message)
        stack.addWidget(table_widget)
        stack.addWidget(empty_widget)
        # Store widgets for easy access
        return stack, table_widget, empty_widget
        
    def init_ui(self):
        """Initialize the reports screen UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(24)
        
        header_layout = QHBoxLayout()
        header_layout.setSpacing(16)
        title_label = QLabel("Reports & Analytics")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #2C3E50;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        main_layout.addLayout(header_layout)
        
        date_range_group = QFrame()
        date_layout = QHBoxLayout(date_range_group)
        date_layout.setContentsMargins(0, 0, 0, 0)
        
        date_selection_style = """
            QComboBox, QDateEdit {
                border: 1px solid #D1D5DB;
                border-radius: 6px;
                padding: 5px 10px;
                background-color: #FFFFFF;
                min-width: 120px;
                min-height: 35px; /* Ensuring consistency with button height */
                font-size: 13px;
            }
            QComboBox:hover, QDateEdit:hover {
                border: 1px solid #1976D2;
            }
            QComboBox::drop-down, QDateEdit::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 25px;
                border-left: 1px solid #E5E7EB;
            }
            /* The image for QDateEdit down-arrow was removed as the asset is not available. */
            QDateEdit::down-arrow:no-image {
                border: 2px solid #6B7280;
                width: 6px;
                height: 6px;
                background: #6B7280;
            }
            QCalendarWidget QAbstractItemView {
                selection-background-color: #3B82F6;
                selection-color: white;
            }
        """
        
        self.date_preset_combo = QComboBox()
        self.date_preset_combo.addItems(["Today", "Yesterday", "This Week", "Last Week", "This Month", "Last Month", "This Quarter", "Last Quarter", "This Year", "Last Year", "All Time", "Custom"])
        self.date_preset_combo.setStyleSheet(date_selection_style)
        self.date_preset_combo.currentTextChanged.connect(self.on_date_range_changed)
        date_layout.addWidget(self.date_preset_combo)
        
        self.start_date_label = QLabel("Start Date:")
        self.start_date_label.setObjectName("secondaryText")
        date_layout.addWidget(self.start_date_label)
        
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setDate(QDate.currentDate().addDays(-7))
        self.start_date_edit.setDisplayFormat("yyyy-MM-dd")
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setStyleSheet(date_selection_style)
        self.start_date_edit.dateChanged.connect(self.on_date_range_changed)
        date_layout.addWidget(self.start_date_edit)
        
        self.end_date_label = QLabel("End Date:")
        self.end_date_label.setObjectName("secondaryText")
        date_layout.addWidget(self.end_date_label)
        
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setDate(QDate.currentDate())
        self.end_date_edit.setDisplayFormat("yyyy-MM-dd")
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setStyleSheet(date_selection_style)
        self.end_date_edit.dateChanged.connect(self.on_date_range_changed)
        date_layout.addWidget(self.end_date_edit)
        
        self.update_report_btn = QPushButton("Update Report")
        self.update_report_btn.setFixedWidth(120)
        self.update_report_btn.setStyleSheet("""
            QPushButton {
                padding: 5px;
                font-weight: 500;
                background-color: #1976D2;
                color: white;
                border-radius: 6px;
                height: 35px; /* Matches the new min-height of QDateEdit/QComboBox */
            }
            QPushButton:hover { background-color: #1565C0; }
        """)
        self.update_report_btn.clicked.connect(self.on_update_report_clicked)
        date_layout.addWidget(self.update_report_btn)
        
        date_layout.addStretch() # This stretch now sits before the export actions.
        
        # --- Export Actions Bar ---
        export_label = QLabel("Export As:")
        export_label.setStyleSheet("color: #757575; font-size: 13px;")
        date_layout.addWidget(export_label)
        
        # PDF Button
        pdf_btn = QPushButton("PDF")
        pdf_btn.setStyleSheet("""
            QPushButton {
                background-color: #D32F2F; /* Red for PDF */
                color: white;
                border-radius: 6px;
                padding: 5px 10px;
                font-weight: 500;
                height: 35px;
            }
            QPushButton:hover { background-color: #C62828; }
        """)
        pdf_btn.clicked.connect(self.on_pdf_export_clicked)
        date_layout.addWidget(pdf_btn)
        
        # Excel Button
        excel_btn = QPushButton("Excel")
        excel_btn.setStyleSheet("""
            QPushButton {
                background-color: #388E3C; /* Green for Excel */
                color: white;
                border-radius: 6px;
                padding: 5px 10px;
                font-weight: 500;
                height: 35px;
            }
            QPushButton:hover { background-color: #2E7D32; }
        """)
        excel_btn.clicked.connect(self.on_excel_export_clicked)
        date_layout.addWidget(excel_btn)
        
        # Print Button
        print_btn = QPushButton("Print")
        print_btn.setStyleSheet("""
            QPushButton {
                background-color: #0288D1; /* Light Blue for Print */
                color: white;
                border-radius: 6px;
                padding: 5px 10px;
                font-weight: 500;
                height: 35px;
            }
            QPushButton:hover { background-color: #0277BD; }
        """)
        print_btn.clicked.connect(self.on_print_clicked)
        date_layout.addWidget(print_btn)
        # --- End Export Actions Bar ---
        
        main_layout.addWidget(date_range_group)
        
        self.report_tabs = QTabWidget()
        self.report_tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #e0e0e0; border-radius: 8px; background-color: white; }
            QTabBar::tab { background-color: #f5f5f5; border: 1px solid #e0e0e0; border-bottom-color: #e0e0e0; border-top-left-radius: 8px; border-top-right-radius: 8px; min-width: 100px; padding: 12px 20px; color: #333; font-weight: bold; }
            QTabBar::tab:selected { background-color: white; border-bottom-color: white; color: #1976d2; }
            QTabBar::tab:hover { background-color: #e0e0e0; }
        """)
        
        self.sales_report_tab = self.create_sales_report_tab()
        self.report_tabs.addTab(self.sales_report_tab, "Sales Report")
        self.inventory_report_tab = self.create_inventory_report_tab()
        self.report_tabs.addTab(self.inventory_report_tab, "Inventory Report")
        self.customer_report_tab = self.create_customer_report_tab()
        self.report_tabs.addTab(self.customer_report_tab, "Customer Report")
        self.financial_report_tab = self.create_financial_report_tab()
        self.report_tabs.addTab(self.financial_report_tab, "Financial Report")
        self.daily_sales_report_tab = self.create_daily_sales_report_tab()
        self.report_tabs.addTab(self.daily_sales_report_tab, "Daily Sales")
        self.stock_audit_tab = self.create_stock_audit_tab()
        self.report_tabs.addTab(self.stock_audit_tab, "Stock Audit Trail")
        
        main_layout.addWidget(self.report_tabs)
        self.load_report_data()
    
    def set_current_user(self, user: User):
        self.current_user = user
        # SECURITY & ROLE REINFORCEMENT
        if user.role == "sales_rep":
            self.report_tabs.setTabVisible(1, False) # Inventory
            self.report_tabs.setTabVisible(3, False) # Financial Report LOCKED
            self.report_tabs.setTabVisible(5, False) # Stock Audit Trail LOCKED
        else:
            self.report_tabs.setTabVisible(1, True)
            self.report_tabs.setTabVisible(3, True)
            self.report_tabs.setTabVisible(5, True)
        
        self.report_tabs.setTabVisible(2, True)  # Customer
        self.report_tabs.setTabVisible(4, True)  # Daily Sales
        self.load_report_data()
    
    def create_export_row(self): # This method is no longer used for the top bar.
        # This method is now obsolete as export buttons are directly integrated into init_ui.
        # It's kept for now in case other parts of the code still reference it for internal use or are adapted.
        logger.warning("create_export_row method is deprecated and should no longer be used for top bar export buttons.")
        export_group = QFrame()
        export_layout = QHBoxLayout(export_group)
        export_layout.setContentsMargins(0, 0, 0, 0)
        export_layout.addWidget(QLabel("Export Report As:", styleSheet="color: #757575; font-size: 12px;"))
        
        pdf_btn = QPushButton("PDF")
        pdf_btn.setObjectName("dangerButton")
        pdf_btn.setFixedSize(80, 32)
        pdf_btn.clicked.connect(self.on_pdf_export_clicked)
        export_layout.addWidget(pdf_btn)
        
        excel_btn = QPushButton("Excel")
        excel_btn.setObjectName("secondaryButton")
        excel_btn.setFixedSize(80, 32)
        excel_btn.clicked.connect(self.on_excel_export_clicked)
        export_layout.addWidget(excel_btn)
        
        print_btn = QPushButton("Print")
        print_btn.setObjectName("secondaryButton")
        print_btn.setFixedSize(80, 32)
        print_btn.clicked.connect(self.on_print_clicked)
        export_layout.addWidget(print_btn)
        
        export_layout.addStretch()
        return export_group

    def create_summary_card(self, title, value, color):
        """Standardized Summary Card Design for all reports"""
        card = QFrame()
        card.setObjectName("summaryCard")
        # Apply style directly to QWidget for padding and border-radius
        card.setStyleSheet(f"""
            QFrame#summaryCard {{ 
                background-color: {color}; 
                border-radius: 10px; 
                border: none;
            }}
        """)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 2, 10, 2) # Minimal top/bottom padding
        layout.setSpacing(0) # No spacing between title and value
        card.setFixedSize(200, 85) # Fixed width and height for perfect symmetry
        
        title_label = QLabel(title)
        title_label.setStyleSheet("color: rgba(255, 255, 255, 0.8); font-size: 10pt; font-weight: bold;") # Set font size to 10pt, bold
        title_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter) # Left align
        layout.addWidget(title_label)
        
        value_label = QLabel(value)
        value_label.setStyleSheet("color: white; font-size: 15pt; font-weight: bolder;") # Set font size to 15pt, extra bold
        value_label.setObjectName("value_label")
        value_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter) # Left align
        layout.addWidget(value_label)
        
        layout.addStretch() # Push content to top
        card.value_label = value_label
        return card

    def _setup_table_widget(self, table_widget, column_count, header_labels):
        """Helper to set up common table widget properties"""
        table_widget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table_widget.setSelectionBehavior(QAbstractItemView.SelectRows)
        table_widget.setShowGrid(False)
        table_widget.setMinimumHeight(200) # Ensure table has some minimum size
        table_widget.setColumnCount(column_count)
        table_widget.setHorizontalHeaderLabels(header_labels)
        table_widget.setAlternatingRowColors(True)
        table_widget.setSelectionMode(QAbstractItemView.SingleSelection)
        table_widget.setSortingEnabled(True)
        table_widget.verticalHeader().setVisible(False) # Hide row numbers
        table_widget.verticalHeader().setSectionResizeMode(QHeaderView.Fixed) # Fixed vertical header size
        header = table_widget.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch) # Stretch to fill available width
        header.setSectionsMovable(False) # Disable column reordering
        header.setSectionsClickable(False) # Disable sorting by clicking headers (if not handled programmatically elsewhere)
    
    def create_sales_report_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20) # Global layout priority margins
        layout.setSpacing(10) # Global layout priority spacing
        
        card_grid_container = QFrame() # New container for the grid layout
        card_grid_layout = QGridLayout(card_grid_container) # Use QGridLayout
        card_grid_layout.setContentsMargins(0,0,0,0)
        card_grid_layout.setSpacing(15) # Spacing between cards
        card_grid_container.setFixedHeight(90) # Fixed height for card container
        
        self.total_sales_card = self.create_summary_card("Total Sales", f"{self.get_currency_symbol()}0.00", "#4caf50")
        card_grid_layout.addWidget(self.total_sales_card, 0, 0)
        
        self.total_transactions_card = self.create_summary_card("Transactions", "0", "#1976d2")
        card_grid_layout.addWidget(self.total_transactions_card, 0, 1)
        
        self.avg_transaction_card = self.create_summary_card("Avg. Transaction", f"{self.get_currency_symbol()}0.00", "#ff9800")
        card_grid_layout.addWidget(self.avg_transaction_card, 0, 2)
        
        self.top_product_card = self.create_summary_card("Top Product", "N/A", "#9c27b0")
        card_grid_layout.addWidget(self.top_product_card, 0, 3)
        
        # Add horizontalSpacer at the end of the grid row
        card_grid_layout.addItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Fixed), 0, 4)
        
        layout.addWidget(card_grid_container, 0) # Cards container gets 0 stretch
        
        self.sales_table_stack = QStackedWidget()
        self.sales_empty_state = EmptyStateWidget(icon="📊", message="No sales data found for the selected period.")

        self.sales_table = QTableWidget()
        self._setup_table_widget(self.sales_table, 7, ["Date", "Product", "Quantity", "Unit Price", "Total (Paid)", "Customer", "Cashier"])
        
        self.sales_table_stack.addWidget(self.sales_table)
        self.sales_table_stack.addWidget(self.sales_empty_state)
        layout.addWidget(self.sales_table_stack, 1) # Table container gets 1 stretch
        
        return tab
    
    def create_inventory_report_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20) # Global layout priority margins
        layout.setSpacing(10) # Global layout priority spacing
        
        card_grid_container = QFrame() # New container for the grid layout
        card_grid_layout = QGridLayout(card_grid_container) # Use QGridLayout
        card_grid_layout.setContentsMargins(0,0,0,0)
        card_grid_layout.setSpacing(15) # Spacing between cards
        card_grid_container.setFixedHeight(90) # Fixed height for card container
        
        self.total_products_card = self.create_summary_card("Total", "0", "#1976d2")
        card_grid_layout.addWidget(self.total_products_card, 0, 0)
        
        self.low_stock_card = self.create_summary_card("Low Stock", "0", "#ff9800")
        card_grid_layout.addWidget(self.low_stock_card, 0, 1)
        
        self.out_of_stock_card = self.create_summary_card("Out of Stock", "0", "#f44336")
        card_grid_layout.addWidget(self.out_of_stock_card, 0, 2)
        
        self.total_value_card = self.create_summary_card("Total Value", f"{self.get_currency_symbol()}0.00", "#4caf50")
        card_grid_layout.addWidget(self.total_value_card, 0, 3)
        
        card_grid_layout.addItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Fixed), 0, 4)
        
        layout.addWidget(card_grid_container, 0) # Cards container gets 0 stretch
        
        self.inventory_table_stack = QStackedWidget()
        self.inventory_empty_state = EmptyStateWidget(icon="📦", message="No inventory data found for the selected period.")

        self.inventory_table = QTableWidget()
        self._setup_table_widget(self.inventory_table, 8, ["Product", "SKU", "Category", "Quantity", "Cost", "Price", "Value", "Status"])
        
        self.inventory_table_stack.addWidget(self.inventory_table)
        self.inventory_table_stack.addWidget(self.inventory_empty_state)
        layout.addWidget(self.inventory_table_stack, 1) # Table container gets 1 stretch
        return tab
    
    def create_customer_report_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20) # Global layout priority margins
        layout.setSpacing(10) # Global layout priority spacing
        
        card_grid_container = QFrame() # New container for the grid layout
        card_grid_layout = QGridLayout(card_grid_container) # Use QGridLayout
        card_grid_layout.setContentsMargins(0,0,0,0)
        card_grid_layout.setSpacing(15) # Spacing between cards
        card_grid_container.setFixedHeight(90) # Fixed height for card container
        
        self.total_customers_card = self.create_summary_card("Total Customers", "0", "#1976d2")
        card_grid_layout.addWidget(self.total_customers_card, 0, 0)
        
        self.active_customers_card = self.create_summary_card("Active", "0", "#4caf50")
        card_grid_layout.addWidget(self.active_customers_card, 0, 1)
        
        self.credit_customers_card = self.create_summary_card("Credit Customers", "0", "#ff9800")
        card_grid_layout.addWidget(self.credit_customers_card, 0, 2)
        
        self.overdue_accounts_card = self.create_summary_card("Overdue Accounts", "0", "#f44336")
        card_grid_layout.addWidget(self.overdue_accounts_card, 0, 3)
        
        card_grid_layout.addItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Fixed), 0, 4)
        
        layout.addWidget(card_grid_container, 0) # Cards container gets 0 stretch
        
        self.customer_table_stack = QStackedWidget()
        self.customer_empty_state = EmptyStateWidget(icon="👥", message="No customer data found.")

        self.customer_table = QTableWidget()
        self._setup_table_widget(self.customer_table, 6, ["Name", "Email", "Phone", "Amount Paid", "Balance", "Status"])
        
        self.customer_table_stack.addWidget(self.customer_table)
        self.customer_table_stack.addWidget(self.customer_empty_state)
        layout.addWidget(self.customer_table_stack, 1) # Table container gets 1 stretch
        return tab
    
    def create_financial_report_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20) # Global layout priority margins
        layout.setSpacing(10) # Global layout priority spacing
        
        card_grid_container = QFrame() # New container for the grid layout
        card_grid_layout = QGridLayout(card_grid_container) # Use QGridLayout
        card_grid_layout.setContentsMargins(0,0,0,0)
        card_grid_layout.setSpacing(15) # Spacing between cards
        card_grid_container.setFixedHeight(90) # Fixed height for card container
        
        self.total_revenue_card = self.create_summary_card("Total Revenue", f"{self.get_currency_symbol()}0.00", "#4caf50")
        card_grid_layout.addWidget(self.total_revenue_card, 0, 0)
        
        self.total_costs_card = self.create_summary_card("Total Costs", f"{self.get_currency_symbol()}0.00", "#f44336")
        card_grid_layout.addWidget(self.total_costs_card, 0, 1)
        
        self.total_profit_card = self.create_summary_card("Total Profit", f"{self.get_currency_symbol()}0.00", "#9c27b0")
        card_grid_layout.addWidget(self.total_profit_card, 0, 2)
        
        self.profit_margin_card = self.create_summary_card("Profit Margin", "0%", "#ff9800")
        card_grid_layout.addWidget(self.profit_margin_card, 0, 3)
        
        card_grid_layout.addItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Fixed), 0, 4)
        
        layout.addWidget(card_grid_container, 0) # Cards container gets 0 stretch
        
        self.financial_table_stack = QStackedWidget()
        self.financial_empty_state = EmptyStateWidget(icon="💸", message="No financial data found for the selected period.")

        self.financial_table = QTableWidget()
        self._setup_table_widget(self.financial_table, 5, ["Date", "Revenue", "Costs", "Profit", "Profit Margin"])
        
        self.financial_table_stack.addWidget(self.financial_table)
        self.financial_table_stack.addWidget(self.financial_empty_state)
        layout.addWidget(self.financial_table_stack, 1) # Table container gets 1 stretch
        return tab

    def create_daily_sales_report_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20) # Global layout priority margins
        layout.setSpacing(10) # Global layout priority spacing
        
        card_grid_container = QFrame() # New container for the grid layout
        card_grid_layout = QGridLayout(card_grid_container) # Use QGridLayout
        card_grid_layout.setContentsMargins(0,0,0,0)
        card_grid_layout.setSpacing(15) # Spacing between cards
        card_grid_container.setFixedHeight(90) # Fixed height for card container
        
        self.daily_total_sales_card = self.create_summary_card("Today's Revenue", f"{self.get_currency_symbol()}0.00", "#4caf50")
        card_grid_layout.addWidget(self.daily_total_sales_card, 0, 0)
        
        self.daily_transactions_card = self.create_summary_card("Transactions", "0", "#1976d2")
        card_grid_layout.addWidget(self.daily_transactions_card, 0, 1)
        
        self.daily_avg_transaction_card = self.create_summary_card("Avg. Transaction", f"{self.get_currency_symbol()}0.00", "#ff9800")
        card_grid_layout.addWidget(self.daily_avg_transaction_card, 0, 2)
        
        self.daily_customers_card = self.create_summary_card("Customers", "0", "#9c27b0")
        card_grid_layout.addWidget(self.daily_customers_card, 0, 3)
        
        card_grid_layout.addItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Fixed), 0, 4)
        
        layout.addWidget(card_grid_container, 0) # Cards container gets 0 stretch
        
        self.daily_sales_table_stack = QStackedWidget()
        self.daily_sales_empty_state = EmptyStateWidget(icon="📅", message="No daily sales data found for today.")

        self.daily_sales_table = QTableWidget()
        self._setup_table_widget(self.daily_sales_table, 6, ["Product ID", "Product", "Customer", "Quantity", "Total", "Paid"])
        
        self.daily_sales_table_stack.addWidget(self.daily_sales_table)
        self.daily_sales_table_stack.addWidget(self.daily_sales_empty_state)
        layout.addWidget(self.daily_sales_table_stack, 1) # Table container gets 1 stretch
        return tab

    def create_stock_audit_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20) # Global layout priority margins
        layout.setSpacing(10) # Global layout priority spacing
        
        card_grid_container = QFrame() # New container for the grid layout
        card_grid_layout = QGridLayout(card_grid_container) # Use QGridLayout
        card_grid_layout.setContentsMargins(0,0,0,0)
        card_grid_layout.setSpacing(15) # Spacing between cards
        card_grid_container.setFixedHeight(90) # Fixed height for card container
        
        self.total_arrivals_card = self.create_summary_card("Total Arrivals", "0", "#4caf50")
        card_grid_layout.addWidget(self.total_arrivals_card, 0, 0)
        
        self.total_restocked_qty_card = self.create_summary_card("Total Qty Added", "0", "#1976d2")
        card_grid_layout.addWidget(self.total_restocked_qty_card, 0, 1)
        
        self.unique_products_restocked_card = self.create_summary_card("Products Restocked", "0", "#ff9800")
        card_grid_layout.addWidget(self.unique_products_restocked_card, 0, 2)
        
        card_grid_layout.addItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Fixed), 0, 3) # Added spacer, adjust col index
        
        layout.addWidget(card_grid_container, 0) # Cards container gets 0 stretch
        
        self.stock_audit_table_stack = QStackedWidget()
        self.stock_audit_empty_state = EmptyStateWidget(icon="📋", message="No stock audit entries found for the selected period.")

        self.stock_audit_table = QTableWidget()
        self._setup_table_widget(self.stock_audit_table, 7, ["Product ID", "Product", "Qty Before", "Qty Added", "Qty After", "Date", "Type"])
        
        self.stock_audit_table_stack.addWidget(self.stock_audit_table)
        self.stock_audit_table_stack.addWidget(self.stock_audit_empty_state)
        layout.addWidget(self.stock_audit_table_stack, 1) # Table container gets 1 stretch
        return tab
    
    def refresh_data(self):
        """Refresh all report data when global data changes"""
        self.load_report_data()
        self.load_daily_sales_data()

    def get_date_range(self):
        preset = self.date_preset_combo.currentText()
        today = datetime.now().date()
        if preset == "Today": start = today; end = today
        elif preset == "Yesterday": start = today - timedelta(days=1); end = start
        elif preset == "This Week": start = today - timedelta(days=today.weekday()); end = start + timedelta(days=6)
        elif preset == "Last Week": start = today - timedelta(days=today.weekday() + 7); end = start + timedelta(days=6)
        elif preset == "This Month": start = today.replace(day=1); end = today
        elif preset == "Last Month": end = today.replace(day=1) - timedelta(days=1); start = end.replace(day=1)
        elif preset == "This Year": start = today.replace(month=1, day=1); end = today
        elif preset == "All Time": start = QDate(2000, 1, 1).toPython(); end = today
        else: start = self.start_date_edit.date().toPython(); end = self.end_date_edit.date().toPython()
        return datetime.combine(start, datetime.min.time()), datetime.combine(end, datetime.max.time())
    
    def load_report_data(self):
        try:
            start_date, end_date = self.get_date_range()
            self.load_sales_data(start_date, end_date)
            self.load_inventory_data()
            self.load_customer_data()
            self.load_financial_data(start_date, end_date)
            self.load_daily_sales_data()
            self.load_stock_audit_data()
        except Exception as e:
            print(f"Failed to load report data: {str(e)}")
    
    def update_report_data_after_sale(self):
        self.load_report_data()
    
    def get_currency_symbol(self):
        return AppConfig.get_setting("currency_symbol", AppConfig.CURRENCY_SYMBOL)
    
    def load_sales_data(self, start_date, end_date):
        try:
            sales_data = DatabaseService.get_sales_by_date_range(start_date, end_date)
            
            if not sales_data:
                self.sales_table_stack.setCurrentWidget(self.sales_empty_state)
                self.total_sales_card.value_label.setText(f"{self.get_currency_symbol()}0.00")
                self.total_transactions_card.value_label.setText("0")
                self.avg_transaction_card.value_label.setText(f"{self.get_currency_symbol()}0.00")
                self.top_product_card.value_label.setText("N/A")
                self.sales_table.setRowCount(0) # Clear table
                return

            self.sales_table_stack.setCurrentWidget(self.sales_table)
            
            total_sales = sum(sale['total_amount'] for sale in sales_data)
            total_transactions = len(sales_data)
            avg_transaction = total_sales / total_transactions if total_transactions > 0 else 0
            
            product_sales = {}
            for sale in sales_data:
                for item in sale.get('items', []):
                    p_name = item.get('product_name', 'Unknown')
                    product_sales[p_name] = product_sales.get(p_name, 0) + item.get('quantity', 0)
            top_product = max(product_sales, key=product_sales.get) if product_sales else "N/A"
            
            self.total_sales_card.value_label.setText(f"{self.get_currency_symbol()}{total_sales:.2f}")
            self.total_transactions_card.value_label.setText(str(total_transactions))
            self.avg_transaction_card.value_label.setText(f"{self.get_currency_symbol()}{avg_transaction:.2f}")
            self.top_product_card.value_label.setText(top_product)
            
            # --- POPULATE TABLE (Itemized rows) ---
            all_rows = []
            for sale in sales_data:
                for item in sale['items']:
                    all_rows.append((sale, item))
            
            self.sales_table.setRowCount(len(all_rows))
            for row_idx, (sale, item) in enumerate(all_rows):
                date_str = sale['date'][:10] if sale['date'] else "N/A"
                self.sales_table.setItem(row_idx, 0, QTableWidgetItem(date_str))
                self.sales_table.setItem(row_idx, 1, QTableWidgetItem(item['product_name']))
                
                qty_item = QTableWidgetItem(str(item['quantity']))
                qty_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.sales_table.setItem(row_idx, 2, qty_item)
                
                up_item = QTableWidgetItem(f"{self.get_currency_symbol()}{item['unit_price']:.2f}")
                up_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.sales_table.setItem(row_idx, 3, up_item)
                
                # Total (Paid) column
                total_item = QTableWidgetItem(f"{self.get_currency_symbol()}{item['subtotal']:.2f}")
                total_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                
                if sale.get('amount_paid', 0.0) < sale['total_amount']:
                    total_item.setForeground(Qt.red)
                
                self.sales_table.setItem(row_idx, 4, total_item)
                
                customer_name = "Walk-in"
                if sale['customer_id']:
                    customer = CustomerService.get_customer_by_id(sale['customer_id'])
                    if customer: customer_name = customer['name']
                self.sales_table.setItem(row_idx, 5, QTableWidgetItem(customer_name))
                self.sales_table.setItem(row_idx, 6, QTableWidgetItem(sale['cashier_user']))
                
        except Exception as e:
            print(f"Sales load error: {e}")
    
    def load_inventory_data(self):
        try:
            products = InventoryService.get_all_products()
            
            if not products:
                self.inventory_table_stack.setCurrentWidget(self.inventory_empty_state)
                self.total_products_card.value_label.setText(f"{self.get_currency_symbol()}0.00")
                self.low_stock_card.value_label.setText("0")
                self.out_of_stock_card.value_label.setText("0")
                self.total_value_card.value_label.setText(f"{self.get_currency_symbol()}0.00")
                self.inventory_table.setRowCount(0) # Clear table
                return
                
            self.inventory_table_stack.setCurrentWidget(self.inventory_table)
            
            total_products = len(products)
            low_stock_products = [p for p in products if p['is_low_stock']]
            out_of_stock_products = [p for p in products if p['quantity'] <= 0]
            total_value = sum(p['total_value'] for p in products)
            
            self.total_products_card.value_label.setText(str(total_products))
            self.low_stock_card.value_label.setText(str(len(low_stock_products)))
            self.out_of_stock_card.value_label.setText(str(len(out_of_stock_products)))
            self.total_value_card.value_label.setText(f"{self.get_currency_symbol()}{total_value:.2f}")
            
            self.inventory_table.setRowCount(len(products))
            for i, p in enumerate(products):
                self.inventory_table.setItem(i, 0, QTableWidgetItem(p['name']))
                self.inventory_table.setItem(i, 1, QTableWidgetItem(p['sku']))
                self.inventory_table.setItem(i, 2, QTableWidgetItem(p['category'] or "N/A"))
                self.inventory_table.setItem(i, 3, QTableWidgetItem(str(p['quantity'])))
                self.inventory_table.setItem(i, 4, QTableWidgetItem(f"{self.get_currency_symbol()}{p['cost_price']:.2f}"))
                self.inventory_table.setItem(i, 5, QTableWidgetItem(f"{self.get_currency_symbol()}{p['selling_price']:.2f}"))
                self.inventory_table.setItem(i, 6, QTableWidgetItem(f"{self.get_currency_symbol()}{p['total_value']:.2f}"))
                status = "In Stock"
                status_color = Qt.green
                if p['quantity'] <= 0: 
                    status = "Out of Stock"
                    status_color = Qt.red
                elif p['is_low_stock']: 
                    status = "Low Stock"
                    status_color = Qt.darkYellow
                
                status_item = QTableWidgetItem(status)
                status_item.setForeground(status_color)
                self.inventory_table.setItem(i, 7, status_item)
        except Exception as e:
            print(f"Inventory load error: {e}")

    def load_customer_data(self):
        try:
            customers = CustomerService.get_all_customers()
            
            if not customers:
                self.customer_table_stack.setCurrentWidget(self.customer_empty_state)
                self.total_customers_card.value_label.setText("0")
                self.active_customers_card.value_label.setText("0")
                self.credit_customers_card.value_label.setText("0")
                self.overdue_accounts_card.value_label.setText("0")
                self.customer_table.setRowCount(0) # Clear table
                return

            self.customer_table_stack.setCurrentWidget(self.customer_table)
            
            total_customers = len(customers)
            active_customers = [c for c in customers if c['outstanding_balance'] == 0]
            credit_customers = [c for c in customers if c['credit_limit'] > 0]
            overdue_customers = [c for c in customers if c['outstanding_balance'] > c['credit_limit']]
            
            self.total_customers_card.value_label.setText(str(total_customers))
            self.active_customers_card.value_label.setText(str(len(active_customers)))
            self.credit_customers_card.value_label.setText(str(len(credit_customers)))
            self.overdue_accounts_card.value_label.setText(str(len(overdue_customers)))
            
            self.customer_table.setRowCount(len(customers))
            for row, customer in enumerate(customers):
                self.customer_table.setItem(row, 0, QTableWidgetItem(customer['name']))
                self.customer_table.setItem(row, 1, QTableWidgetItem(customer['email'] or "N/A"))
                self.customer_table.setItem(row, 2, QTableWidgetItem(customer['phone'] or "N/A"))
                
                # Amount Paid
                amount_paid = CustomerService.get_total_paid(customer['id'])
                paid_item = QTableWidgetItem(f"{self.get_currency_symbol()}{amount_paid:.2f}")
                paid_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.customer_table.setItem(row, 3, paid_item)
                
                balance_item = QTableWidgetItem(f"{self.get_currency_symbol()}{customer['outstanding_balance']:.2f}")
                balance_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                if customer['outstanding_balance'] > customer['credit_limit']: 
                    balance_item.setForeground(Qt.red)
                self.customer_table.setItem(row, 4, balance_item)
                
                status = "Active"
                status_color = Qt.green
                if customer['outstanding_balance'] > customer['credit_limit'] and customer['credit_limit'] > 0: 
                    status = "Overdue"
                    status_color = Qt.red
                elif customer['outstanding_balance'] > 0: 
                    status = "Debt"
                    status_color = Qt.darkYellow
                
                status_item = QTableWidgetItem(status)
                status_item.setForeground(status_color)
                self.customer_table.setItem(row, 5, status_item)
        except Exception as e:
            print(f"Customer load error: {e}")

    def load_financial_data(self, start, end):
        try:
            sales = DatabaseService.get_sales_by_date_range(start, end)
            
            if not sales:
                self.financial_table_stack.setCurrentWidget(self.financial_empty_state)
                self.total_revenue_card.value_label.setText(f"{self.get_currency_symbol()}0.00")
                self.total_costs_card.value_label.setText(f"{self.get_currency_symbol()}0.00")
                self.total_profit_card.value_label.setText(f"{self.get_currency_symbol()}0.00")
                self.profit_margin_card.value_label.setText("0%")
                self.financial_table.setRowCount(0) # Clear table
                return
            
            self.financial_table_stack.setCurrentWidget(self.financial_table)
            
            rev = sum(s['total_amount'] for s in sales)
            cost = 0
            for s in sales:
                for item in s['items']:
                    p = InventoryService.get_product_by_id(item['product_id'])
                    if p: cost += p['cost_price'] * item['quantity']
            
            profit = rev - cost
            margin = (profit / rev * 100) if rev > 0 else 0
            
            self.total_revenue_card.value_label.setText(f"{self.get_currency_symbol()}{rev:.2f}")
            self.total_costs_card.value_label.setText(f"{self.get_currency_symbol()}{cost:.2f}")
            self.total_profit_card.value_label.setText(f"{self.get_currency_symbol()}{profit:.2f}")
            self.profit_margin_card.value_label.setText(f"{margin:.2f}%")
            
            self.financial_table.setRowCount(1)
            self.financial_table.setItem(0, 0, QTableWidgetItem(f"{start.date()} to {end.date()}"))
            self.financial_table.setItem(0, 1, QTableWidgetItem(f"{self.get_currency_symbol()}{rev:.2f}"))
            self.financial_table.setItem(0, 2, QTableWidgetItem(f"{self.get_currency_symbol()}{cost:.2f}"))
            self.financial_table.setItem(0, 3, QTableWidgetItem(f"{self.get_currency_symbol()}{profit:.2f}"))
            self.financial_table.setItem(0, 4, QTableWidgetItem(f"{margin:.2f}%"))
        except Exception as e:
            print(f"Financial load error: {e}")

    def load_daily_sales_data(self):
        try:
            today = datetime.now().date()
            start = datetime.combine(today, datetime.min.time())
            end = datetime.combine(today, datetime.max.time())
            sales = DatabaseService.get_sales_by_date_range(start, end)
            
            if not sales:
                self.daily_sales_table_stack.setCurrentWidget(self.daily_sales_empty_state)
                self.daily_total_sales_card.value_label.setText(f"{self.get_currency_symbol()}0.00")
                self.daily_transactions_card.value_label.setText("0")
                self.daily_avg_transaction_card.value_label.setText(f"{self.get_currency_symbol()}0.00")
                self.daily_customers_card.value_label.setText("0")
                self.daily_sales_table.setRowCount(0) # Clear table
                return

            self.daily_sales_table_stack.setCurrentWidget(self.daily_sales_table)

            total_sales = sum(sale['total_amount'] for sale in sales)
            total_transactions = len(sales)
            avg_transaction = total_sales / total_transactions if total_transactions > 0 else 0
            unique_customers = set(sale['customer_id'] for sale in sales if sale['customer_id'])
            
            self.daily_total_sales_card.value_label.setText(f"{self.get_currency_symbol()}{total_sales:.2f}")
            self.daily_transactions_card.value_label.setText(str(total_transactions))
            self.daily_avg_transaction_card.value_label.setText(f"{self.get_currency_symbol()}{avg_transaction:.2f}")
            self.daily_customers_card.value_label.setText(str(len(unique_customers)))
            
            rows = []
            for s in sales:
                for item in s['items']:
                    cname = "Walk-in"
                    if s['customer_id']:
                        c = CustomerService.get_customer_by_id(s['customer_id'])
                        if c: cname = c['name']
                    rows.append((item['product_id'], item['product_name'], cname, item['quantity'], item['subtotal'], s['payment_method']))
            
            self.daily_sales_table.setRowCount(len(rows))
            for i, r in enumerate(rows):
                for j, val in enumerate(r):
                    self.daily_sales_table.setItem(i, j, QTableWidgetItem(str(val)))
        except Exception as e:
            print(f"Daily sales load error: {e}")

    def load_stock_audit_data(self):
        try:
            history = InventoryService.get_restock_history(100)
            
            if not history:
                self.stock_audit_table_stack.setCurrentWidget(self.stock_audit_empty_state)
                self.total_arrivals_card.value_label.setText("0")
                self.total_restocked_qty_card.value_label.setText("0.00")
                self.unique_products_restocked_card.value_label.setText("0")
                self.stock_audit_table.setRowCount(0) # Clear table
                return

            self.stock_audit_table_stack.setCurrentWidget(self.stock_audit_table)

            self.total_arrivals_card.value_label.setText(str(len(history)))
            self.total_restocked_qty_card.value_label.setText(f"{sum(item['added_qty'] for item in history):.2f}")
            self.unique_products_restocked_card.value_label.setText(str(len(set(item['product_id'] for item in history))))
            
            self.stock_audit_table.setRowCount(len(history))
            for i, e in enumerate(history):
                self.stock_audit_table.setItem(i, 0, QTableWidgetItem(str(e['product_id'])))
                self.stock_audit_table.setItem(i, 1, QTableWidgetItem(e['product_name']))
                self.stock_audit_table.setItem(i, 2, QTableWidgetItem(f"{e['old_qty']:.2f}"))
                
                added = QTableWidgetItem(f"{e['added_qty']:.2f}")
                if e['added_qty'] > 0:
                    added.setForeground(Qt.darkGreen)
                else:
                    added.setForeground(Qt.darkYellow)
                self.stock_audit_table.setItem(i, 3, added)
                
                self.stock_audit_table.setItem(i, 4, QTableWidgetItem(f"{e['new_qty']:.2f}"))
                self.stock_audit_table.setItem(i, 5, QTableWidgetItem(str(e['date'])[:19]))
                
                t_item = QTableWidgetItem(e.get('record_type', 'Arrival'))
                if e.get('record_type') == 'Correction':
                    t_item.setForeground(Qt.blue)
                self.stock_audit_table.setItem(i, 6, t_item)
        except Exception as e:
            print(f"Error loading stock audit data: {e}")

    def on_date_range_changed(self, text=None):
        is_custom = self.date_preset_combo.currentText() == "Custom"
        self.start_date_label.setVisible(is_custom)
        self.start_date_edit.setVisible(is_custom)
        self.end_date_label.setVisible(is_custom)
        self.end_date_edit.setVisible(is_custom)
    
    def on_update_report_clicked(self):
        self.load_report_data()
    
    def _scrape_table_data(self):
        """Extract headers and data from the currently active report table."""
        idx = self.report_tabs.currentIndex()
        table_map = {
            0: (self.sales_table, "Sales_Report"),
            1: (self.inventory_table, "Inventory_Report"),
            2: (self.customer_table, "Customer_Report"),
            3: (self.financial_table, "Financial_Report"),
            4: (self.daily_sales_table, "Daily_Sales_Report"),
            5: (self.stock_audit_table, "Stock_Audit_Report")
        }
        table, report_name = table_map.get(idx, (None, "Report"))
        
        if not table: return None, None, None
        
        headers = []
        for i in range(table.columnCount()):
            header_item = table.horizontalHeaderItem(i)
            headers.append(header_item.text() if header_item else f"Column {i}")
            
        data = []
        for row in range(table.rowCount()):
            row_data = []
            for col in range(table.columnCount()):
                item = table.item(row, col)
                if not item:
                    widget = table.cellWidget(row, col)
                    label = widget.findChild(QLabel) if widget else None
                    row_data.append(label.text() if label else "")
                else:
                    row_data.append(item.text())
            data.append(row_data)
            
        return headers, data, report_name

    def generate_report_html(self, headers, data, title):
        """Generate a clean HTML table for printing"""
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1 {{ color: #2C3E50; text-align: center; }}
                h3 {{ color: #7F8C8D; text-align: center; margin-bottom: 30px; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #BDC3C7; padding: 10px; text-align: left; font-size: 12px; }}
                th {{ background-color: #1976D2; color: white; }}
                tr:nth-child(even) {{ background-color: #F8F9FA; }}
                .footer {{ text-align: right; margin-top: 20px; font-size: 10px; color: #95A5A6; }}
            </style>
        </head>
        <body>
            <h1>{title.replace('_', ' ').upper()}</h1>
            <h3>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</h3>
            <table>
                <thead>
                    <tr>
                        {"".join(f"<th>{h}</th>" for h in headers)}
                    </tr>
                </thead>
                <tbody>
        """
        for row in data:
            html += "<tr>"
            for item in row:
                html += f"<td>{str(item)}</td>"
            html += "</tr>"
            
        html += f"""
                </tbody>
            </table>
            <div class="footer">Inventory Management System - {datetime.now().year}</div>
        </body>
        </html>
        """
        return html

    def on_pdf_export_clicked(self):
        """Generate actual professional PDF from table data."""
        if self.report_tabs.currentIndex() == 3 and self.current_user.role != "admin":
            QMessageBox.warning(self, "Access Denied", "Only administrators can export Financial Reports.")
            return

        headers, data, name = self._scrape_table_data()
        if not headers: return

        # Fetch Store Name for branding
        from database.database import DatabaseService
        store_setting = DatabaseService.get_setting("business_name")
        store_name = store_setting.value if store_setting else "Inventory System"

        downloads_dir = os.path.join(os.path.expanduser("~"), "Downloads", "Inventory_Reports")
        os.makedirs(downloads_dir, exist_ok=True)
        
        default_name = f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        file_path, _ = QFileDialog.getSaveFileName(self, "Save PDF Report", os.path.join(downloads_dir, default_name), "PDF Files (*.pdf)")
        
        if not file_path: return

        try:
            pdf = FPDF(orientation='L', unit='mm', format='A4')
            pdf.add_page()
            
            pdf.set_font("Arial", 'B', 20)
            pdf.cell(0, 15, store_name.upper(), ln=True, align='C')
            
            pdf.set_font("Arial", 'B', 14)
            pdf.cell(0, 10, f"Report: {name.replace('_', ' ')}", ln=True, align='C')
            
            pdf.set_font("Arial", '', 10)
            pdf.cell(0, 8, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True, align='C')
            pdf.ln(10)
            
            pdf.set_fill_color(25, 118, 210) # Navy Blue
            pdf.set_text_color(255, 255, 255)
            pdf.set_font("Arial", 'B', 9)
            col_width = (pdf.w - pdf.l_margin - pdf.r_margin) / len(headers) # Corrected line
            for h in headers:
                pdf.cell(col_width, 10, h, border=1, fill=True, align='C')
            pdf.ln()
            
            pdf.set_text_color(0, 0, 0)
            pdf.set_font("Arial", '', 8)
            for row in data:
                for item in row:
                    # Fix character encoding error for Cedi symbol
                    clean_item = str(item).replace("₵", "GHS")
                    pdf.cell(col_width, 8, clean_item[:25], border=1)
                pdf.ln()
                
            pdf.output(file_path)
            QMessageBox.information(self, "Success", f"Report saved to:\n{file_path}")
        except Exception as e:
            logger.error(f"PDF Export failed: {e}")
            QMessageBox.critical(self, "Error", f"Failed to generate PDF: {str(e)}")

    def on_excel_export_clicked(self):
        """Generate actual Excel from table data."""
        headers, data, name = self._scrape_table_data()
        if not headers: return

        downloads_dir = os.path.join(os.path.expanduser("~"), "Downloads", "Inventory_Reports")
        os.makedirs(downloads_dir, exist_ok=True)
        
        default_name = f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Excel Report", os.path.join(downloads_dir, default_name), "Excel Files (*.xlsx)")
        
        if not file_path: return

        try:
            df = pd.DataFrame(data, columns=headers)
            df.to_excel(file_path, index=False)
            QMessageBox.information(self, "Success", f"Report saved to:\n{file_path}")
        except Exception as e:
            logger.error(f"Excel Export failed: {e}")
            QMessageBox.critical(self, "Error", f"Failed to generate Excel: {str(e)}")

    def on_print_clicked(self):
        """Direct printing using QPrinter and QTextDocument"""
        headers, data, name = self._scrape_table_data()
        if not headers:
            return

        try:
            printer = QPrinter(QPrinter.HighResolution)
            dialog = QPrintDialog(printer, self)
            
            if dialog.exec() == QPrintDialog.Accepted:
                document = QTextDocument()
                html = self.generate_report_html(headers, data, name) 
                document.setHtml(html)
                document.print_(printer)
                QMessageBox.information(self, "Success", "Report sent to printer.")
        except Exception as e:
            logger.error(f"Printing failed: {e}")
            QMessageBox.critical(self, "Print Error", f"Could not trigger print: {str(e)}")

    def refresh_daily_sales_data(self):
        self.load_daily_sales_data()