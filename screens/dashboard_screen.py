from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
                               QLabel, QPushButton, QFrame, QScrollArea,
                               QMessageBox, QSizePolicy, QTableWidget, QAbstractItemView,
                               QHeaderView, QTableWidgetItem)
from PySide6.QtCore import Qt, QTimer, QPoint, QSize, Signal
from PySide6.QtGui import QFont, QPixmap, QIcon, QPalette, QPainter, QCursor, QColor

from database.models import User
from services.inventory_service import InventoryService
from services.sales_service import SalesService
from services.customer_service import CustomerService
from datetime import datetime, timedelta
from ui.product_list_dialog import ProductListDialog

class ClickableCard(QFrame):
    clicked = Signal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.PointingHandCursor)

    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)

class DashboardScreen(QWidget):
    """Dashboard screen with summary cards and quick actions"""
    
    def __init__(self):
        super().__init__()
        self.current_user = None
        self.main_window = None  # Will be set by main window
        self.init_ui()
        
        # Update dashboard data
        self.update_dashboard()
        
        # Set up timer to update stats every 30 seconds
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_dashboard)
        self.timer.start(30000)  # Update every 30 seconds
    
    def init_ui(self):
        """Initialize the dashboard UI"""
        # Main layout with proper spacing as per design spec
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)  # Container margin as per spec
        main_layout.setSpacing(24)  # Section spacing as per spec
        
        # Header section with title
        header_widget = QFrame()
        header_widget.setObjectName("headerWidget")
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(16)
        
        # Page title with proper typography
        title_label = QLabel("Dashboard")
        title_label.setObjectName("pageTitle")
        header_layout.addWidget(title_label)

        # Last Cloud Sync Label
        self.sync_label = QLabel("Last Cloud Sync: Checking...")
        self.sync_label.setStyleSheet("font-size: 13px; color: #7F8C8D; font-style: italic;")
        header_layout.addSpacing(20)
        header_layout.addWidget(self.sync_label)
        
        header_layout.addStretch()
        
        main_layout.addWidget(header_widget)
        
        # Stats cards section with proper grid layout
        stats_widget = QFrame()
        stats_widget.setObjectName("statsWidget")
        stats_layout = QGridLayout(stats_widget)
        stats_layout.setContentsMargins(0, 0, 0, 0)
        stats_layout.setSpacing(16)  # Grid spacing as per spec
        
        # Create stats cards with design matching Customers screen cards
        # Inventory Stats (Admin Only)
        self.out_of_stock_card = self.create_kpi_card("Out of Stock", "0", "#E74C3C", self.show_out_of_stock_dialog)
        self.below_minimum_card = self.create_kpi_card("Near Expiry", "0", "#F39C12", self.show_near_expiry_dialog)
        self.low_stock_card = self.create_kpi_card("Low Stock", "0", "#AF7AC5", self.show_low_stock_dialog)
        self.standard_inventory_card = self.create_kpi_card("Expired Products", "0", "#2C3E50", self.show_expired_products_dialog)
        
        # Sales & Customer Overview Cards (Visible to all)
        self.total_sales_card = self.create_kpi_card("Today's Revenue", "GHS0", "#192A56", self.go_to_daily_sales)
        self.total_orders_card = self.create_kpi_card("Total Orders", "0", "#192A56")
        self.avg_sales_card = self.create_kpi_card("Average Sales", "GHS0", "#4A76D9")
        self.total_customers_card = self.create_kpi_card("Total Customers", "0", "#00BCD4", self.go_to_customers)
        
        # Add cards to grid
        stats_layout.addWidget(self.out_of_stock_card, 0, 0)
        stats_layout.addWidget(self.below_minimum_card, 0, 1)
        stats_layout.addWidget(self.low_stock_card, 0, 2)
        stats_layout.addWidget(self.standard_inventory_card, 0, 3)
        
        stats_layout.addWidget(self.total_sales_card, 1, 0)
        stats_layout.addWidget(self.total_orders_card, 1, 1)
        stats_layout.addWidget(self.avg_sales_card, 1, 2)
        stats_layout.addWidget(self.total_customers_card, 1, 3)
        
        # Set column stretch for equal distribution
        for col in range(4):
            stats_layout.setColumnStretch(col, 1)
        
        main_layout.addWidget(stats_widget)
        
        # Quick actions section
        actions_widget = QFrame()
        actions_widget.setObjectName("actionsWidget")
        actions_layout = QVBoxLayout(actions_widget)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(16)
        
        # Section heading
        actions_title = QLabel("Quick Actions")
        actions_title.setObjectName("sectionHeading")
        actions_layout.addWidget(actions_title)
        
        # Action buttons container
        buttons_container = QFrame()
        buttons_layout = QHBoxLayout(buttons_container)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.setSpacing(16)
        
        # Create action buttons with proper styling
        self.inventory_btn = self.create_action_button("Inventory", "#1976D2")
        self.inventory_btn.clicked.connect(self.on_inventory_clicked)
        buttons_layout.addWidget(self.inventory_btn)
        
        self.sales_btn = self.create_action_button("New Sale", "#4CAF50")
        self.sales_btn.clicked.connect(self.on_sales_clicked)
        buttons_layout.addWidget(self.sales_btn)
        
        self.customers_btn = self.create_action_button("Customers", "#9C27B0")
        self.customers_btn.clicked.connect(self.on_customers_clicked)
        buttons_layout.addWidget(self.customers_btn)
        
        self.reports_btn = self.create_action_button("Reports", "#FF9800")
        self.reports_btn.clicked.connect(self.on_reports_clicked)
        buttons_layout.addWidget(self.reports_btn)
        
        # Add Manage Stock button (Admin Only)
        self.manage_stock_btn = self.create_action_button("Manage Stock", "#436F80")
        self.manage_stock_btn.clicked.connect(self.on_manage_stock_clicked)
        self.manage_stock_btn.setVisible(False)
        buttons_layout.addWidget(self.manage_stock_btn)
        
        buttons_layout.addStretch()
        actions_layout.addWidget(buttons_container)
        main_layout.addWidget(actions_widget)
        
        # Recent activity section with proper card styling
        activity_widget = QFrame()
        activity_widget.setObjectName("activityWidget")
        activity_layout = QVBoxLayout(activity_widget)
        activity_layout.setContentsMargins(0, 0, 0, 0)
        activity_layout.setSpacing(16)
        
        # Section heading
        activity_label = QLabel("Recent Activity")
        activity_label.setObjectName("sectionHeading")
        activity_layout.addWidget(activity_label)
        
        # Recent activity card
        activity_frame = QFrame()
        activity_frame.setObjectName("recentActivityCard")
        activity_frame.setStyleSheet("""
            QFrame#recentActivityCard {
                background-color: white;
                border-radius: 12px;
                border: 1px solid #E0E0E0;
            }
        """)
        
        activity_card_layout = QVBoxLayout(activity_frame)
        activity_card_layout.setContentsMargins(15, 15, 15, 15)
        activity_card_layout.setSpacing(0)
        
        self.activity_table = QTableWidget()
        self.activity_table.setColumnCount(4)
        self.activity_table.setHorizontalHeaderLabels(["Time", "Activity", "User", "Status"])
        self.activity_table.setShowGrid(True)
        self.activity_table.setAlternatingRowColors(True)
        self.activity_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.activity_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.activity_table.verticalHeader().setVisible(False)
        self.activity_table.horizontalHeader().setHighlightSections(False)
        self.activity_table.setMinimumHeight(300)
        
        # Table Styling
        self.activity_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: none;
                gridline-color: #F0F0F0;
                font-size: 13px;
                color: #2C3E50;
            }
            QTableWidget::item {
                padding: 12px 8px;
                border-bottom: 1px solid #F0F0F0;
            }
            QHeaderView::section {
                background-color: #F8F9FA;
                color: #555555;
                padding: 10px;
                border: none;
                border-bottom: 2px solid #E0E0E0;
                font-weight: bold;
                font-size: 12px;
            }
        """)
        
        header = self.activity_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed) # Time
        header.setSectionResizeMode(1, QHeaderView.Stretch) # Activity
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents) # User
        header.setSectionResizeMode(3, QHeaderView.Fixed) # Status/Type icon
        
        self.activity_table.setColumnWidth(0, 80)
        self.activity_table.setColumnWidth(3, 100)
        
        activity_card_layout.addWidget(self.activity_table)
        
        activity_layout.addWidget(activity_frame)
        main_layout.addWidget(activity_widget, 1) # Set stretch factor to 1 to fill space
        
        # Removed main_layout.addStretch() to allow activity_widget to reach the bottom
    
    def create_kpi_card(self, title, value, bg_color, on_click=None):
        """Create a KPI card with a solid flat background color"""
        if on_click:
            card = ClickableCard()
            card.clicked.connect(on_click)
        else:
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
        title_label.setStyleSheet("""
            font-size: 14px;
            font-weight: 500;
            color: white;
            opacity: 0.9;
            background: transparent;
        """)
        layout.addWidget(title_label)
        
        # Value
        value_label = QLabel(value)
        value_label.setStyleSheet("""
            font-size: 28px;
            font-weight: bold;
            color: white;
            background: transparent;
        """)
        layout.addWidget(value_label)
        
        # Click hint
        if on_click:
            hint_label = QLabel("click to view")
            hint_label.setStyleSheet("""
                font-size: 10px;
                color: rgba(255, 255, 255, 0.7);
                font-style: italic;
                background: transparent;
            """)
            hint_label.setAlignment(Qt.AlignRight)
            layout.addWidget(hint_label)
        else:
            layout.addStretch()
        
        # Store reference for updates
        card.value_label = value_label
        
        return card
    
    def show_out_of_stock_dialog(self):
        products = InventoryService.get_all_products()
        out_of_stock = [p for p in products if p.get('quantity', 0) <= 0]
        dialog = ProductListDialog("Out of Stock Products", out_of_stock, self)
        dialog.exec()

    def show_low_stock_dialog(self):
        products = InventoryService.get_all_products()
        low_stock = [p for p in products if p.get('is_low_stock', False)]
        dialog = ProductListDialog("Low Stock Products", low_stock, self)
        dialog.exec()

    def show_near_expiry_dialog(self):
        products = InventoryService.get_expiring_products(days=30)
        dialog = ProductListDialog("Near Expiry Products", products, self)
        dialog.exec()

    def show_expired_products_dialog(self):
        products = InventoryService.get_expired_products()
        dialog = ProductListDialog("Expired Products", products, self)
        dialog.exec()

    def go_to_daily_sales(self):
        if self.main_window:
            self.main_window.show_reports()
            # Set the tab to 'Daily Sales' (Index 4)
            if hasattr(self.main_window.reports_screen, 'report_tabs'):
                self.main_window.reports_screen.report_tabs.setCurrentIndex(4)

    def go_to_customers(self):
        if self.main_window:
            self.main_window.show_customers()
    
    def create_action_button(self, text, color):
        """Create an action button with proper styling"""
        button = QPushButton(text)
        button.setObjectName("actionButton")
        button.setStyleSheet(f"""
            QPushButton#actionButton {{
                background-color: {color};
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: 600;
                min-height: 48px;
                min-width: 120px;
            }}
            QPushButton#actionButton:hover {{
                background-color: #1565C0;
            }}
            QPushButton#actionButton:pressed {{
                background-color: #0D47A1;
            }}
        """)
        return button
    
    def set_current_user(self, user: User):
        """Set the current user and update visible cards"""
        self.current_user = user
        
        # All cards are now visible to everyone as requested
        self.out_of_stock_card.setVisible(True)
        self.below_minimum_card.setVisible(True)
        self.low_stock_card.setVisible(True)
        self.standard_inventory_card.setVisible(True)
        
        # Keep Manage Stock button admin-only as it's a destructive/critical action
        if hasattr(self, 'manage_stock_btn'):
            is_admin = (user.role == "admin")
            self.manage_stock_btn.setVisible(is_admin)
        
        self.update_dashboard()

    def set_main_window(self, main_window):
        """Set the main window reference for navigation"""
        self.main_window = main_window
    
    def on_inventory_clicked(self):
        """Handle inventory button click"""
        if self.main_window:
            self.main_window.show_inventory()
    
    def on_manage_stock_clicked(self):
        """Handle manage stock button click"""
        from ui.manage_stock_dialog import ManageStockDialog
        dialog = ManageStockDialog(self, self.current_user)
        dialog.exec()
        self.update_dashboard()
        if self.main_window and hasattr(self.main_window, 'inventory_screen'):
            self.main_window.inventory_screen.load_inventory_data()
    
    def on_sales_clicked(self):
        """Handle sales button click"""
        if self.main_window:
            self.main_window.show_sales()
    
    def on_customers_clicked(self):
        """Handle customers button click"""
        if self.main_window:
            self.main_window.show_customers()
    
    def on_reports_clicked(self):
        """Handle reports button click"""
        if self.main_window:
            self.main_window.show_reports()
    
    def update_dashboard(self):
        """Update dashboard statistics"""
        if not self.current_user:
            return
            
        try:
            # Update Sync Label
            from database.database import DatabaseService
            sync_setting = DatabaseService.get_setting("last_cloud_sync")
            if sync_setting:
                self.sync_label.setText(f"Last Cloud Sync: {sync_setting.value}")

            # Calculate inventory statistics for ALL users now
            # Get all products for inventory calculations
            products = InventoryService.get_all_products()
            
            # Calculate inventory statistics with error handling
            out_of_stock = 0
            low_stock = 0
            
            for p in products:
                if p.get('quantity', 0) <= 0:
                    out_of_stock += 1
                if p.get('is_low_stock', False):
                    low_stock += 1
            
            near_expiry = len(InventoryService.get_expiring_products(30))
            expired = len(InventoryService.get_expired_products())
            
            # Update inventory cards
            self.out_of_stock_card.value_label.setText(str(out_of_stock))
            self.below_minimum_card.value_label.setText(str(near_expiry))
            self.low_stock_card.value_label.setText(str(low_stock))
            self.standard_inventory_card.value_label.setText(str(expired))
            
            # Get sales data for overview cards (visible to all)
            from datetime import datetime, timedelta
            today = datetime.now().date()
            
            # Calculate today's sales
            sales_summary = SalesService.get_daily_sales_summary(today)
            today_sales = sales_summary.get('total_revenue', 0.0) if sales_summary else 0.0
            
            # Calculate total orders (simplified - using recent sales as proxy)
            recent_sales = SalesService.get_recent_sales(30)
            total_orders = len(recent_sales) if recent_sales else 0
            
            # Calculate average sales, preventing division by zero
            if total_orders > 0:
                total_amount = sum(s.get('total_amount', 0.0) for s in recent_sales)
                avg_sales = total_amount / total_orders
            else:
                avg_sales = 0.0
            
            # Get total customers
            all_customers = CustomerService.get_all_customers()
            total_customers = len(all_customers) if all_customers else 0
            
            # Update overview cards
            self.total_sales_card.value_label.setText(f"GHS{today_sales:,.2f}")
            self.total_orders_card.value_label.setText(str(total_orders))
            self.avg_sales_card.value_label.setText(f"GHS{avg_sales:,.2f}")
            self.total_customers_card.value_label.setText(str(total_customers))
            
            # --- UPDATE RECENT ACTIVITY (Combined Sales and System Activities) ---
            from database.database import DatabaseService
            activities = DatabaseService.get_recent_activities(10)
            
            # Convert sales to a similar format
            combined_activities = []
            
            # Add general activities
            for act in activities:
                combined_activities.append({
                    'date': act['date'],
                    'description': act['description'],
                    'user': act['user'],
                    'type': act['type']
                })
                
            # Add recent sales
            for sale in (recent_sales or [])[:5]:
                customer_name = sale.get('customer_name', 'Walk-in')
                combined_activities.append({
                    'date': sale['date'],
                    'description': f"New Sale to {customer_name}: GHS {sale['total_amount']:.2f}",
                    'user': sale['cashier_user'],
                    'type': 'sale'
                })
                
            # Sort by date descending
            combined_activities.sort(key=lambda x: x['date'], reverse=True)
            
            self.activity_table.setRowCount(len(combined_activities[:15])) # Show up to 15
            
            if combined_activities:
                for row, act in enumerate(combined_activities[:15]):
                    # Time
                    date_val = str(act['date'])
                    time_str = date_val[11:16] if ' ' in date_val else (date_val.split('T')[1][:5] if 'T' in date_val else "N/A")
                    self.activity_table.setItem(row, 0, QTableWidgetItem(time_str))
                    
                    # Activity description
                    desc_item = QTableWidgetItem(act['description'])
                    self.activity_table.setItem(row, 1, desc_item)
                    
                    # User
                    user_item = QTableWidgetItem(f"👤 {act['user']}")
                    self.activity_table.setItem(row, 2, user_item)
                    
                    # Status/Type with style
                    status_text = "SYSTEM"
                    color = "#95A5A6"
                    if act['type'] == 'sale':
                        status_text = "💰 SALE"
                        color = "#27AE60"
                    elif act['type'] == 'price_change':
                        status_text = "🏷️ PRICE"
                        color = "#2980B9"
                    elif act['type'] == 'stock_correction':
                        status_text = "🔧 STOCK"
                        color = "#E67E22"
                    
                    status_item = QTableWidgetItem(status_text)
                    status_item.setForeground(QColor(color))
                    status_item.setFont(QFont("", weight=QFont.Bold))
                    status_item.setTextAlignment(Qt.AlignCenter)
                    self.activity_table.setItem(row, 3, status_item)
            else:
                # Optional: handle empty state
                pass
                
        except Exception as e:
            # Silent failure fixed: Alert user
            QMessageBox.critical(self, "Dashboard Error", f"Failed to update dashboard: {str(e)}")
            print(f"Error updating dashboard: {e}")

    def closeEvent(self, event):
        """Stop timer when screen is closed"""
        if hasattr(self, 'timer'):
            self.timer.stop()
        super().closeEvent(event)