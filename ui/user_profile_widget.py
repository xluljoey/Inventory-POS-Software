from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QFrame, QGraphicsDropShadowEffect, QDialog)
from PySide6.QtCore import Qt, Signal, QPoint, QPropertyAnimation, QParallelAnimationGroup, QEasingCurve, QSize
from PySide6.QtGui import QPixmap, QPainter, QColor, QPen, QBrush

from database.models import User
from ui.custom_dialog import CustomConfirmDialog

class ProfileDropdownCard(QFrame):
    """SaaS-style high-fidelity dropdown card"""
    logout_requested = Signal()
    settings_requested = Signal()
    
    def __init__(self, user: User, parent=None):
        super().__init__(parent)
        self.user = user
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Calculate size based on role (Admin has extra button)
        width = 260
        height = 220 if user.role == "admin" else 160
        self.setFixedSize(width, height)
        
        # Main container with subtle border
        self.container = QFrame(self)
        self.container.setObjectName("container")
        self.container.setGeometry(5, 5, width-10, height-10) # Leave room for shadow
        self.container.setStyleSheet("""
            QFrame#container {
                background-color: #FFFFFF;
                border-radius: 16px;
                border: 1px solid #F3F4F6;
            }
        """)
        
        # Soft Large Blur Shadow ('2xl')
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 40))
        shadow.setOffset(0, 6)
        self.container.setGraphicsEffect(shadow)
        
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(20, 20, 20, 20) # 20px internal padding
        layout.setSpacing(0)
        
        # --- Header Section ---
        # Role: Smaller, light gray, uppercase, letter spacing
        role_label = QLabel(self.user.role.upper())
        role_label.setStyleSheet("""
            color: #64748B; 
            font-size: 10px; 
            font-weight: 800; 
            letter-spacing: 1px;
            background: transparent;
            border: none;
        """)
        layout.addWidget(role_label)
        
        # User Name: Bold, navy/dark-slate color, size 1.1rem
        name_label = QLabel(self.user.full_name)
        name_label.setStyleSheet("""
            color: #111827; 
            font-size: 16px; 
            font-weight: 600;
            background: transparent;
            border: none;
            margin-top: 4px;
        """)
        layout.addWidget(name_label)
        
        layout.addSpacing(16)
        
        # Divider: Thin, light-gray horizontal line
        divider = QFrame()
        divider.setFixedHeight(1)
        divider.setStyleSheet("background-color: #E5E7EB; border: none;") # #E5E7EB is standard Tailwind gray-200
        layout.addWidget(divider)
        
        layout.addSpacing(12)
        
        # --- Actions Section ---
        # Settings: Admin Only
        if self.user.role == "admin":
            self.settings_btn = QPushButton("⚙️  Settings")
            self.settings_btn.setStyleSheet("""
                QPushButton {
                    text-align: left;
                    background-color: transparent;
                    color: #374151;
                    border: none;
                    border-radius: 8px;
                    padding: 12px;
                    font-size: 13px;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background-color: #F3F4F6;
                }
            """)
            self.settings_btn.setCursor(Qt.PointingHandCursor)
            self.settings_btn.clicked.connect(self.on_settings_clicked)
            layout.addWidget(self.settings_btn)
            layout.addSpacing(8)
        
        # Logout: Soft Red button
        logout_btn = QPushButton("🚪 Logout")
        logout_btn.setStyleSheet("""
            QPushButton {
                text-align: center;
                background-color: #FFF1F2; /* Light pink */
                color: #BE123C; /* Bold red (Rose-700) */
                border: none;
                border-radius: 10px;
                padding: 12px;
                font-size: 13px;
                font-weight: 700;
            }
            QPushButton:hover {
                background-color: #FFE4E6;
            }
        """)
        logout_btn.setCursor(Qt.PointingHandCursor)
        logout_btn.clicked.connect(self.on_logout_clicked)
        layout.addWidget(logout_btn)
        
        layout.addStretch()
        
    def show_animated(self, pos):
        """Spring / Fade-in transition"""
        self.move(pos.x(), pos.y() - 15)
        self.setWindowOpacity(0.0)
        self.show()
        
        self.fade_anim = QPropertyAnimation(self, b"windowOpacity")
        self.fade_anim.setDuration(200)
        self.fade_anim.setStartValue(0.0)
        self.fade_anim.setEndValue(1.0)
        
        self.slide_anim = QPropertyAnimation(self, b"pos")
        self.slide_anim.setDuration(250)
        self.slide_anim.setStartValue(QPoint(pos.x(), pos.y() - 15))
        self.slide_anim.setEndValue(pos)
        self.slide_anim.setEasingCurve(QEasingCurve.OutBack)
        
        self.anim_group = QParallelAnimationGroup()
        self.anim_group.addAnimation(self.fade_anim)
        self.anim_group.addAnimation(self.slide_anim)
        self.anim_group.start()

    def on_settings_clicked(self):
        self.hide()
        self.settings_requested.emit()
        
    def on_logout_clicked(self):
        self.hide()
        confirm = CustomConfirmDialog("Confirm Logout", "Are you sure you want to logout?", self.parent())
        if confirm.exec() == QDialog.Accepted:
            self.logout_requested.emit()

class UserProfileWidget(QWidget):
    """Circular profile avatar that stays perfectly round"""
    logout_requested = Signal()
    settings_requested = Signal()

    def __init__(self, user: User, parent=None):
        super().__init__(parent)
        self.user = user
        self.dropdown = None
        # Fixed square size to ensure circle
        self.setFixedSize(48, 48)
        self.init_ui()
        
    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignCenter)
        
        # Creating a wrapper frame for the circle (Profile Trigger)
        self.circle_container = QFrame()
        self.circle_container.setFixedSize(40, 40) # Aspect ratio 1/1
        self.circle_container.setCursor(Qt.PointingHandCursor)
        
        # Force the circle shape via QSS
        # Perfect Circle: border-radius = 50% of 40px = 20px
        # 2px white border
        # Gradient background
        self.circle_container.setStyleSheet("""
            QFrame {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #6366f1, stop:1 #a855f7);
                border-radius: 20px;
                border: 2px solid white;
            }
        """)
        
        # Internal layout for the icon label
        icon_layout = QVBoxLayout(self.circle_container)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        icon_layout.setAlignment(Qt.AlignCenter)
        
        self.icon_label = QLabel()
        self.icon_label.setAlignment(Qt.AlignCenter)
        
        # Generate the silhouette (Centered user SVG/icon representation)
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QBrush(Qt.white))
        painter.setPen(Qt.NoPen)
        
        # Draw a simple user shape
        painter.drawEllipse(11, 5, 10, 10) # Head
        painter.drawPie(5, 16, 22, 18, 0, 180 * 16) # Shoulders
        painter.end()
        
        self.icon_label.setPixmap(pixmap)
        icon_layout.addWidget(self.icon_label)
        
        # Transparent button overlay to handle clicks
        self.trigger_btn = QPushButton(self.circle_container)
        self.trigger_btn.setGeometry(0, 0, 40, 40)
        self.trigger_btn.setStyleSheet("background: transparent; border: none; border-radius: 20px;")
        self.trigger_btn.setCursor(Qt.PointingHandCursor)
        self.trigger_btn.clicked.connect(self.toggle_dropdown)
        
        layout.addWidget(self.circle_container)
        
    def toggle_dropdown(self):
        if self.dropdown:
            self.dropdown.close()
            self.dropdown = None
            return
            
        self.dropdown = ProfileDropdownCard(self.user, self.window())
        self.dropdown.logout_requested.connect(self.logout_requested.emit)
        self.dropdown.settings_requested.connect(self.settings_requested.emit)
            
        # Position the dropdown below the profile icon
        pos = self.mapToGlobal(QPoint(0, self.height() + 5))
        
        # Ensure it stays on screen
        screen_rect = self.screen().availableGeometry()
        if pos.x() + self.dropdown.width() > screen_rect.right():
            pos.setX(screen_rect.right() - self.dropdown.width() - 20)
            
        self.dropdown.show_animated(pos)

    def update_user_info(self, user: User):
        self.user = user
        if self.dropdown:
            self.dropdown.close()
            self.dropdown = None
