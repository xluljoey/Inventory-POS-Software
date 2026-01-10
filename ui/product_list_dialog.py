from PySide6.QtWidgets import (QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, 
                               QHeaderView, QLabel, QFrame, QHBoxLayout, QPushButton, QAbstractItemView)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

class ProductListDialog(QDialog):
    """Dialog to display a list of products (e.g. Low Stock, Out of Stock)"""
    def __init__(self, title, products, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.resize(800, 500)
        self.products = products
        self.init_ui(title)

    def init_ui(self, title_text):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Title
        title = QLabel(title_text)
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #2C3E50;")
        layout.addWidget(title)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        
        # Dynamic date column label based on context
        date_col_label = "Expiry Date" if "Expiry" in title_text or "Expired" in title_text else "Date"
        
        self.table.setHorizontalHeaderLabels(["Name", "SKU", "Category", "Stock", "Status", date_col_label])
        self.table.setShowGrid(True)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        
        # Style
        self.table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                background-color: white;
                gridline-color: #F0F0F0;
                selection-background-color: #E3F2FD;
                selection-color: #1976D2;
                font-size: 14px;
            }
            QHeaderView::section {
                background-color: #F8F9FA;
                padding: 12px;
                border: none;
                border-right: 1px solid #E0E0E0;
                border-bottom: 1px solid #E0E0E0;
                font-weight: bold;
                font-size: 13px;
                color: #555;
            }
            QTableWidget::item {
                padding: 10px 5px;
                border-right: 1px solid #F0F0F0;
            }
        """)
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch) # Name
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents) # SKU
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents) # Category
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents) # Stock
        header.setSectionResizeMode(4, QHeaderView.Fixed) # Status
        header.setSectionResizeMode(5, QHeaderView.Stretch) # Date
        self.table.setColumnWidth(4, 120)

        self.populate_table()
        layout.addWidget(self.table)

        # Close Button
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        close_btn = QPushButton("Close")
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #757575;
                color: white;
                border-radius: 6px;
                padding: 8px 20px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #616161; }
        """)
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

    def populate_table(self):
        self.table.setRowCount(len(self.products))
        for row, p in enumerate(self.products):
            self.table.setItem(row, 0, QTableWidgetItem(p.get('name', '')))
            self.table.setItem(row, 1, QTableWidgetItem(p.get('sku', '')))
            self.table.setItem(row, 2, QTableWidgetItem(p.get('category', '')))
            
            qty = p.get('quantity', 0)
            qty_item = QTableWidgetItem(str(qty))
            qty_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row, 3, qty_item)
            
            status = "In Stock"
            color = "#2ECC71" # Green
            if qty <= 0:
                status = "Out of Stock"
                color = "#E74C3C" # Red
            elif p.get('is_low_stock', False):
                status = "Low Stock"
                color = "#F39C12" # Orange
            
            status_item = QTableWidgetItem(status)
            status_item.setForeground(QColor(color))
            status_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 4, status_item)

            # Date (Expiry or Updated At)
            date_val = p.get('expiry_date')
            if not date_val:
                date_val = p.get('updated_at', '')
            
            if date_val:
                try:
                    # Clean up iso format for display
                    date_str = str(date_val)[:10] if 'expiry_date' in p and p['expiry_date'] else str(date_val)[:16].replace('T', ' ')
                except:
                    date_str = str(date_val)
            else:
                date_str = "N/A"
            
            date_item = QTableWidgetItem(date_str)
            date_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 5, date_item)
