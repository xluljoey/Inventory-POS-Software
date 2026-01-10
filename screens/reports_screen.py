from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
                               QLabel, QPushButton, QFrame, QTableWidget, 
                               QTableWidgetItem, QComboBox, QHeaderView, 
                               QAbstractItemView, QGroupBox, QDateEdit,
                               QCalendarWidget, QTabWidget, QMessageBox, QFileDialog)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont, QColor
from loguru import logger
import pandas as pd
from fpdf import FPDF
import os

from database.models import User
from services.sales_service import SalesService
from services.inventory_service import InventoryService
from services.customer_service import CustomerService
from config.app_config import AppConfig
from datetime import datetime, timedelta


class ReportsScreen(QWidget):
    """Reports and analytics screen with various reports"""
    
    def __init__(self):
        super().__init__()
        self.current_user = None
        self.init_ui()
        
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
                border: 1px solid #E0E0E0;
                border-radius: 6px;
                padding: 8px 12px;
                background-color: #FFFFFF;
                min-height: 36px;
                font-size: 13px;
            }
            QComboBox:hover, QDateEdit:hover {
                border: 1px solid #1976D2;
            }
            QComboBox::drop-down, QDateEdit::drop-down { border: none; }
            QComboBox::down-arrow, QDateEdit::down-arrow {
                image: none; border-left: 5px solid transparent; border-right: 5px solid transparent;
                border-top: 5px solid #757575; margin-right: 10px;
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
                height: 36px;
            }
            QPushButton:hover { background-color: #1565C0; }
        """)
        self.update_report_btn.clicked.connect(self.on_update_report_clicked)
        date_layout.addWidget(self.update_report_btn)
        
        date_layout.addStretch()
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
    
    def create_export_row(self):
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
        """Original Summary Card Design restored"""
        card = QFrame()
        card.setObjectName("summaryCard")
        card.setStyleSheet(f"QFrame#summaryCard {{ background-color: {color}; border-radius: 10px; border: none; }}")
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(4)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("color: rgba(255, 255, 255, 0.8); font-size: 11px; font-weight: 500;")
        layout.addWidget(title_label)
        
        value_label = QLabel(value)
        value_label.setStyleSheet("color: white; font-size: 18px; font-weight: bold;")
        value_label.setObjectName("value_label")
        layout.addWidget(value_label)
        
        layout.addStretch()
        card.value_label = value_label
        return card

    def create_sales_report_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        top_row = QHBoxLayout()
        top_row.setSpacing(10)
        
        self.total_sales_card = self.create_summary_card("Total Sales", "GH₵0.00", "#4caf50")
        self.total_sales_card.setFixedWidth(160)
        top_row.addWidget(self.total_sales_card)
        
        self.total_transactions_card = self.create_summary_card("Transactions", "0", "#1976d2")
        self.total_transactions_card.setFixedWidth(140)
        top_row.addWidget(self.total_transactions_card)
        
        self.avg_transaction_card = self.create_summary_card("Avg. Transaction", "GH₵0.00", "#ff9800")
        self.avg_transaction_card.setFixedWidth(160)
        top_row.addWidget(self.avg_transaction_card)
        
        self.top_product_card = self.create_summary_card("Top Product", "N/A", "#9c27b0")
        self.top_product_card.setFixedWidth(160)
        top_row.addWidget(self.top_product_card)
        
        top_row.addStretch()
        top_row.addWidget(self.create_export_row(), 0, Qt.AlignTop | Qt.AlignRight)
        layout.addLayout(top_row)
        
        self.sales_table = QTableWidget()
        self.sales_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.sales_table.setShowGrid(False)
        self.sales_table.setMinimumHeight(700)
        self.sales_table.setColumnCount(7)
        self.sales_table.setHorizontalHeaderLabels(["Date", "Product", "Quantity", "Unit Price", "Total (Paid)", "Customer", "Cashier"])
        self.sales_table.setAlternatingRowColors(True)
        self.sales_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.sales_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.sales_table.setSortingEnabled(True)
        header = self.sales_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.sales_table)
        return tab
    
    def create_inventory_report_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        top_row = QHBoxLayout()
        top_row.setSpacing(10)
        
        self.total_products_card = self.create_summary_card("Total", "0", "#1976d2")
        self.total_products_card.setFixedSize(120, 70)
        top_row.addWidget(self.total_products_card)
        
        self.low_stock_card = self.create_summary_card("Low Stock", "0", "#ff9800")
        self.low_stock_card.setFixedSize(120, 70)
        top_row.addWidget(self.low_stock_card)
        
        self.out_of_stock_card = self.create_summary_card("Out of Stock", "0", "#f44336")
        self.out_of_stock_card.setFixedSize(120, 70)
        top_row.addWidget(self.out_of_stock_card)
        
        self.total_value_card = self.create_summary_card("Total Value", "GH₵0.00", "#4caf50")
        self.total_value_card.setFixedSize(150, 70)
        top_row.addWidget(self.total_value_card)
        
        top_row.addStretch()
        top_row.addWidget(self.create_export_row(), 0, Qt.AlignTop | Qt.AlignRight)
        layout.addLayout(top_row)
        
        self.inventory_table = QTableWidget()
        self.inventory_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.inventory_table.setShowGrid(False)
        self.inventory_table.setMinimumHeight(700)
        self.inventory_table.setColumnCount(8)
        self.inventory_table.setHorizontalHeaderLabels(["Product", "SKU", "Category", "Quantity", "Cost", "Price", "Value", "Status"])
        self.inventory_table.setAlternatingRowColors(True)
        self.inventory_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.inventory_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.inventory_table.setSortingEnabled(True)
        header = self.inventory_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.inventory_table)
        return tab
    
    def create_customer_report_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        top_row = QHBoxLayout()
        top_row.setSpacing(10)
        
        self.total_customers_card = self.create_summary_card("Total Customers", "0", "#1976d2")
        self.total_customers_card.setFixedWidth(160)
        top_row.addWidget(self.total_customers_card)
        
        self.active_customers_card = self.create_summary_card("Active", "0", "#4caf50")
        self.active_customers_card.setFixedWidth(140)
        top_row.addWidget(self.active_customers_card)
        
        self.credit_customers_card = self.create_summary_card("Credit Customers", "0", "#ff9800")
        self.credit_customers_card.setFixedWidth(160)
        top_row.addWidget(self.credit_customers_card)
        
        self.overdue_accounts_card = self.create_summary_card("Overdue Accounts", "0", "#f44336")
        self.overdue_accounts_card.setFixedWidth(160)
        top_row.addWidget(self.overdue_accounts_card)
        
        top_row.addStretch()
        top_row.addWidget(self.create_export_row(), 0, Qt.AlignTop | Qt.AlignRight)
        layout.addLayout(top_row)
        
        self.customer_table = QTableWidget()
        self.customer_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.customer_table.setShowGrid(False)
        self.customer_table.setMinimumHeight(700)
        self.customer_table.setColumnCount(6)
        self.customer_table.setHorizontalHeaderLabels(["Name", "Email", "Phone", "Amount Paid", "Balance", "Status"])
        self.customer_table.setAlternatingRowColors(True)
        self.customer_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.customer_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.customer_table.setSortingEnabled(True)
        header = self.customer_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.customer_table)
        return tab
    
    def create_financial_report_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        top_row = QHBoxLayout()
        top_row.setSpacing(10)
        
        self.total_revenue_card = self.create_summary_card("Total Revenue", "GH₵0.00", "#4caf50")
        self.total_revenue_card.setFixedWidth(160)
        top_row.addWidget(self.total_revenue_card)
        
        self.total_costs_card = self.create_summary_card("Total Costs", "GH₵0.00", "#f44336")
        self.total_costs_card.setFixedWidth(160)
        top_row.addWidget(self.total_costs_card)
        
        self.total_profit_card = self.create_summary_card("Total Profit", "GH₵0.00", "#9c27b0")
        self.total_profit_card.setFixedWidth(160)
        top_row.addWidget(self.total_profit_card)
        
        self.profit_margin_card = self.create_summary_card("Profit Margin", "0%", "#ff9800")
        self.profit_margin_card.setFixedWidth(140)
        top_row.addWidget(self.profit_margin_card)
        
        top_row.addStretch()
        top_row.addWidget(self.create_export_row(), 0, Qt.AlignTop | Qt.AlignRight)
        layout.addLayout(top_row)
        
        self.financial_table = QTableWidget()
        self.financial_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.financial_table.setShowGrid(False)
        self.financial_table.setMinimumHeight(700)
        self.financial_table.setColumnCount(5)
        self.financial_table.setHorizontalHeaderLabels(["Date", "Revenue", "Costs", "Profit", "Profit Margin"])
        self.financial_table.setAlternatingRowColors(True)
        self.financial_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.financial_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.financial_table.setSortingEnabled(True)
        header = self.financial_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.financial_table)
        return tab

    def create_daily_sales_report_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        top_row = QHBoxLayout()
        top_row.setSpacing(10)
        
        self.daily_total_sales_card = self.create_summary_card("Today's Revenue", "GH₵0.00", "#4caf50")
        self.daily_total_sales_card.setFixedWidth(180)
        top_row.addWidget(self.daily_total_sales_card)
        
        self.daily_transactions_card = self.create_summary_card("Transactions", "0", "#1976d2")
        self.daily_transactions_card.setFixedWidth(120)
        top_row.addWidget(self.daily_transactions_card)
        
        self.daily_avg_transaction_card = self.create_summary_card("Avg. Transaction", "GH₵0.00", "#ff9800")
        self.daily_avg_transaction_card.setFixedWidth(180)
        top_row.addWidget(self.daily_avg_transaction_card)
        
        self.daily_customers_card = self.create_summary_card("Customers", "0", "#9c27b0")
        self.daily_customers_card.setFixedWidth(120)
        top_row.addWidget(self.daily_customers_card)
        
        top_row.addStretch()
        top_row.addWidget(self.create_export_row(), 0, Qt.AlignTop | Qt.AlignRight)
        layout.addLayout(top_row)
        
        self.daily_sales_table = QTableWidget()
        self.daily_sales_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.daily_sales_table.setShowGrid(False)
        self.daily_sales_table.setMinimumHeight(700)
        self.daily_sales_table.setColumnCount(6)
        self.daily_sales_table.setHorizontalHeaderLabels(["Product ID", "Product", "Customer", "Quantity", "Total", "Paid"])
        self.daily_sales_table.setAlternatingRowColors(True)
        self.daily_sales_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.daily_sales_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.daily_sales_table.setSortingEnabled(True)
        header = self.daily_sales_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.daily_sales_table)
        return tab

    def create_stock_audit_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        top_row = QHBoxLayout()
        top_row.setSpacing(10)
        
        self.total_arrivals_card = self.create_summary_card("Total Arrivals", "0", "#4caf50")
        self.total_arrivals_card.setFixedWidth(160)
        top_row.addWidget(self.total_arrivals_card)
        
        self.total_restocked_qty_card = self.create_summary_card("Total Qty Added", "0", "#1976d2")
        self.total_restocked_qty_card.setFixedWidth(160)
        top_row.addWidget(self.total_restocked_qty_card)
        
        self.unique_products_restocked_card = self.create_summary_card("Products Restocked", "0", "#ff9800")
        self.unique_products_restocked_card.setFixedWidth(180)
        top_row.addWidget(self.unique_products_restocked_card)
        
        top_row.addStretch()
        top_row.addWidget(self.create_export_row(), 0, Qt.AlignTop | Qt.AlignRight)
        layout.addLayout(top_row)
        
        self.stock_audit_table = QTableWidget()
        self.stock_audit_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.stock_audit_table.setShowGrid(False)
        self.stock_audit_table.setMinimumHeight(700)
        self.stock_audit_table.setColumnCount(7)
        self.stock_audit_table.setHorizontalHeaderLabels(["Product ID", "Product", "Qty Before", "Qty Added", "Qty After", "Date", "Type"])
        self.stock_audit_table.setAlternatingRowColors(True)
        self.stock_audit_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.stock_audit_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.stock_audit_table.setSortingEnabled(True)
        header = self.stock_audit_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.stock_audit_table)
        return tab
    
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
        return AppConfig.CURRENCY_SYMBOL
    
    def load_sales_data(self, start_date, end_date):
        try:
            sales_data = SalesService.get_sales_by_date_range(start_date, end_date)
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
                self.inventory_table.setItem(i, 4, QTableWidgetItem(f"GH₵{p['cost_price']:.2f}"))
                self.inventory_table.setItem(i, 5, QTableWidgetItem(f"GH₵{p['selling_price']:.2f}"))
                self.inventory_table.setItem(i, 6, QTableWidgetItem(f"GH₵{p['total_value']:.2f}"))
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
            sales = SalesService.get_sales_by_date_range(start, end)
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
            self.financial_table.setItem(0, 1, QTableWidgetItem(f"GH₵{rev:.2f}"))
            self.financial_table.setItem(0, 2, QTableWidgetItem(f"GH₵{cost:.2f}"))
            self.financial_table.setItem(0, 3, QTableWidgetItem(f"GH₵{profit:.2f}"))
            self.financial_table.setItem(0, 4, QTableWidgetItem(f"{margin:.2f}%"))
        except Exception as e:
            print(f"Financial load error: {e}")

    def load_daily_sales_data(self):
        try:
            today = datetime.now().date()
            start = datetime.combine(today, datetime.min.time())
            end = datetime.combine(today, datetime.max.time())
            sales = SalesService.get_sales_by_date_range(start, end)
            
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
            col_width = pdf.epw / len(headers)
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
        """Trigger print dialog by generating a temp PDF and opening it."""
        headers, data, name = self._scrape_table_data()
        if not headers: return

        temp_pdf = os.path.join("logs", f"temp_print_{datetime.now().strftime('%H%M%S')}.pdf")
        
        try:
            pdf = FPDF(orientation='L', unit='mm', format='A4')
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(0, 10, f"PRINT PREVIEW - {name.replace('_', ' ')}", ln=True, align='C')
            pdf.ln(5)
            
            pdf.set_font("Arial", 'B', 9)
            col_width = pdf.epw / len(headers)
            for h in headers:
                pdf.cell(col_width, 8, h, border=1)
            pdf.ln()
            
            pdf.set_font("Arial", '', 8)
            for row in data:
                for item in row:
                    pdf.cell(col_width, 7, str(item).replace("₵", "GHS")[:25], border=1)
                pdf.ln()
                
            pdf.output(temp_pdf)
            
            import subprocess
            import platform
            if platform.system() == "Windows":
                os.startfile(temp_pdf, "print")
            elif platform.system() == "Darwin": # macOS
                subprocess.run(["open", temp_pdf])
            else: # Linux
                subprocess.run(["xdg-open", temp_pdf])
                
            QMessageBox.information(self, "Printing", "The report has been sent to your system viewer for printing.")
        except Exception as e:
            QMessageBox.critical(self, "Print Error", f"Could not trigger print: {str(e)}")

    def refresh_daily_sales_data(self):
        self.load_daily_sales_data()