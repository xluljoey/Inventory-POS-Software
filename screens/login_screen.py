from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, 
                               QLineEdit, QPushButton, QLabel, QFrame, 
                               QTabWidget, QTabBar, QSizePolicy, QStackedWidget, QDialog)
from PySide6.QtCore import Signal, Qt, QSize, QPropertyAnimation, QEasingCurve, QPoint
from PySide6.QtGui import QFont, QPalette, QLinearGradient, QBrush, QPixmap

from services.auth_service import AuthService
from database.models import User
from database.database import DatabaseService


class LoginScreen(QWidget):
    """Login screen widget with tab-based role selection"""
    
    # Signal emitted when login is successful
    login_successful = Signal(User)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_user = None
        self.current_role = "sales_rep"  # Default to sales rep
        self.init_ui()
        
    def init_ui(self):
        """Initialize the login screen UI"""
        # Set up main layout with gradient background
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create a central widget container with gradient background
        container = QWidget()
        container.setObjectName("loginContainer")
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        
        # Add gradient background
        self.setStyleSheet("""
            QWidget#loginContainer {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1, 
                                          stop: 0 #1976D2, stop: 1 #424242);
            }
        """)
        
        # Add stretch to center the login card vertically
        container_layout.addStretch()
        
        # Create login card
        login_card = QFrame()
        login_card.setObjectName("loginCard")
        login_card.setFixedWidth(450)  # Slightly narrower for better tab fit
        
        card_layout = QVBoxLayout(login_card)
        card_layout.setContentsMargins(40, 40, 40, 40)
        card_layout.setSpacing(24)
        
        # Company title
        from config.app_config import AppConfig # Temporarily import AppConfig to get CURRENCY_SYMBOL
        
        # DEFENSIVE: Handle case where DB isn't fully initialized or settings table is missing
        try:
            store_name_setting = DatabaseService.get_setting("business_name")
            store_name = store_name_setting.value if store_name_setting and store_name_setting.value.strip() else "INVENTORY SYSTEM"
        except Exception:
            # Fallback to AppConfig or a default if DB fails
            store_name = getattr(AppConfig, "BUSINESS_NAME", "INVENTORY SYSTEM")
        
        title_label = QLabel(store_name.upper())
        title_label.setObjectName("loginTitle")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            QLabel#loginTitle {
                font-size: 24pt;
                font-weight: bold;
                color: #111827; /* Updated color */
                margin-bottom: 10px;
            }
        """)
        
        card_layout.addWidget(title_label)
        
        # Subtitle
        subtitle_label = QLabel("INVENTORY MANAGEMENT SYSTEM")
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #757575;
                margin-bottom: 30px;
            }
        """)
        card_layout.addWidget(subtitle_label)
        
        # Role selection tabs (Admin/Sales Rep) - Styled as Segmented Control
        self.role_tab_widget = QTabWidget()
        self.role_tab_widget.setTabPosition(QTabWidget.North)
        self.role_tab_widget.setFixedHeight(50)
        self.role_tab_widget.setFixedWidth(340) # Fixed width to allow centering in layout
        
        self.role_tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background-color: transparent;
            }
            QTabBar {
                background-color: #F5F5F5;
                border-radius: 22px;
            }
            QTabBar::tab {
                background-color: transparent;
                color: #757575;
                padding: 0px;
                margin: 4px;
                border-radius: 18px;
                font-size: 12px;
                font-weight: bold;
                width: 162px; /* Equal width for both tabs */
                height: 36px;
            }
            QTabBar::tab:selected {
                background-color: #1976D2;
                color: white;
            }
            QTabBar::tab:hover:!selected {
                background-color: #E0E0E0;
            }
        """)
        
        # Create dummy pages for the tabs
        admin_page = QWidget()
        sales_page = QWidget()
        
        self.role_tab_widget.addTab(sales_page, "SALES REP")
        self.role_tab_widget.addTab(admin_page, "ADMIN")
        
        # Initially select Sales Rep tab
        self.role_tab_widget.setCurrentIndex(0)
        self.current_role = "sales_rep"
        
        # Connect tab change
        self.role_tab_widget.currentChanged.connect(self.on_role_tab_changed)
        
        # Center the tab widget using a horizontal layout
        tab_container_layout = QHBoxLayout()
        tab_container_layout.addStretch()
        tab_container_layout.addWidget(self.role_tab_widget)
        tab_container_layout.addStretch()
        
        card_layout.addLayout(tab_container_layout)
        
        # Password field (always shown)
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setObjectName("inputField")
        self.password_input.setFixedHeight(40)
        
        card_layout.addWidget(QLabel("Password"))
        card_layout.addWidget(self.password_input)
        
        # Login button
        self.login_button = QPushButton("CONTINUE")
        self.login_button.setObjectName("primaryButton")
        self.login_button.setFixedHeight(45)
        self.login_button.clicked.connect(self.on_login_clicked)
        
        card_layout.addWidget(self.login_button)
        
        # Add the card to the container
        container_layout.addWidget(login_card, 0, Qt.AlignCenter)
        container_layout.addStretch()
        
        # Add container to main layout
        main_layout.addWidget(container)
        
        # Error message label
        self.error_label = QLabel()
        self.error_label.setAlignment(Qt.AlignCenter)
        self.error_label.setStyleSheet("color: #f44336; font-size: 12px; margin-top: 10px;")
        self.error_label.setVisible(False)
        card_layout.addWidget(self.error_label)
        
        # Set focus to password field
        self.password_input.setFocus()
        
        # Connect Enter key to login
        self.password_input.returnPressed.connect(self.on_login_clicked)
    
    def on_role_tab_changed(self, index):
        """Handle role tab change"""
        if index == 0:  # Sales Rep tab
            self.current_role = "sales_rep"
        else:  # Admin tab
            self.current_role = "admin"
    
    def on_login_clicked(self):
        """Handle login button click"""
        password = self.password_input.text()
        
        if not password:
            self.show_error("Please enter password")
            return
        
        username = "admin" if self.current_role == "admin" else "sales_rep"
        
        # Attempt to authenticate user
        user = AuthService.authenticate_user(username, password)
        
        if user:
            if user.role == self.current_role:
                # Login successful
                self.current_user = user
                self.login_successful.emit(user)
                return
            else:
                self.show_error("Role mismatch - user role does not match selected role")
                return
        else:
            self.show_error("Invalid password")
            return
    
    def show_error(self, message):
        """Show error message"""
        self.error_label.setText(message)
        self.error_label.setVisible(True)
        
        # Hide error after 5 seconds
        from PySide6.QtCore import QTimer
        timer = QTimer(self)
        timer.setSingleShot(True)
        timer.timeout.connect(lambda: self.error_label.setVisible(False))
        timer.start(5000)
    
    def clear_fields(self):
        """Clear all input fields"""
        self.password_input.clear()
        self.error_label.setVisible(False)
        self.password_input.setFocus()
