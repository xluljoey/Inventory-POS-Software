# ui/navigation_bar.py
from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QFrame, QSizePolicy, QLabel, QGraphicsOpacityEffect
from PySide6.QtCore import Qt, Signal, QSize, QPropertyAnimation, QEasingCurve, QAbstractAnimation
from PySide6.QtGui import QIcon, QPixmap, QPainter, QFont, QColor
import os
from core import config
from core.config import ICON_DIR
from loguru import logger

class SyncStatusWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(10, 0, 10, 0)
        
        self.status_label = QLabel()
        self.status_label.setStyleSheet("color: white; font-weight: bold;")
        
        if config.IS_PREMIUM:
            self.pulse_icon = QLabel("●") # Dot character
            self.pulse_icon.setStyleSheet("color: #4CAF50; font-size: 16px;")
            
            # Pulse Animation
            self.opacity_effect = QGraphicsOpacityEffect(self.pulse_icon)
            self.pulse_icon.setGraphicsEffect(self.opacity_effect)
            
            self.anim = QPropertyAnimation(self.opacity_effect, b"opacity")
            self.anim.setDuration(1000)
            self.anim.setStartValue(1.0)
            self.anim.setEndValue(0.3)
            self.anim.setEasingCurve(QEasingCurve.InOutQuad)
            self.anim.setLoopCount(-1) # Infinite loop
            self.anim.start()
            
            self.status_label.setText("Sync Active")
            self.layout.addWidget(self.pulse_icon)
        else:
            self.status_label.setText("Basic Mode")
            self.status_label.setStyleSheet("color: #B0BEC5;")
            
        self.layout.addWidget(self.status_label)

class NavButton(QPushButton):
    """Custom navigation button with pill shape and PNG icon"""
    def __init__(self, text, icon_name, btn_id, parent=None):
        super().__init__(parent)
        self.nav_text = text
        self.icon_name = icon_name
        self.btn_id = btn_id
        self.is_active = False
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.setFixedHeight(44)
        self.setMinimumWidth(150)
        
        # Setup text and icon
        self.setText(f" {self.nav_text}")
        self._load_icon()
        self.update_style()

    def _load_icon(self):
        """Loads PNG icon from assets directory"""
        icon_path = os.path.join(ICON_DIR, f"{self.icon_name}.png")
        
        if os.path.exists(icon_path):
            self.setIcon(QIcon(icon_path))
            self.setIconSize(QSize(22, 22))
        else:
            logger.warning(f"Icon not found: {icon_path}")
            # Fallback or leave without icon

    def set_active(self, active):
        self.is_active = active
        self.setChecked(active)
        self.update_style()

    def update_style(self):
        if self.is_active:
            self.setStyleSheet("""
                QPushButton {
                    background-color: #FFFFFF;
                    color: #1976D2;
                    border-radius: 22px;
                    padding: 0px 15px;
                    font-size: 13px;
                    font-weight: bold;
                    border: 2px solid #FFFFFF;
                    text-align: center;
                }
            """)
        else:
            self.setStyleSheet("""
                QPushButton {
                    background-color: rgba(255, 255, 255, 0.1);
                    color: #FFFFFF;
                    border-radius: 22px;
                    padding: 0px 15px;
                    font-size: 13px;
                    font-weight: 500;
                    border: 1px solid rgba(255, 255, 255, 0.2);
                    text-align: center;
                }
                QPushButton:hover {
                    background-color: rgba(255, 255, 255, 0.25);
                    border: 1px solid #FFFFFF;
                }
            """)

class MainNavigationBar(QFrame):
    """Capsule-shaped primary navigation bar matching modern design reference"""
    nav_changed = Signal(int) # btn_id
    logout_requested = Signal()
    settings_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("navBar")
        self.setFixedHeight(85) 
        self.setStyleSheet("QFrame#navBar { background: transparent; border: none; }")
        
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 10, 0, 10)
        
        self.container = QFrame()
        self.container.setObjectName("navContainer")
        self.container.setFixedHeight(60)
        self.container.setMinimumWidth(800)
        self.container.setStyleSheet("""
            QFrame#navContainer {
                background-color: #1976D2;
                border-radius: 30px;
                border: none;
            }
        """)
        
        self.container_layout = QHBoxLayout(self.container)
        self.container_layout.setContentsMargins(25, 0, 25, 0)
        self.container_layout.setSpacing(12)
        
        self.main_layout.addStretch()
        self.main_layout.addWidget(self.container)
        self.main_layout.addStretch()
        
        self.buttons = []
        
        # Format: (Display Text, Icon Filename Base, Button ID)
        nav_items = [
            ("Dashboard", "dashboard", 0),
            ("Inventory", "inventory", 1),
            ("Sales", "sales", 2),
            ("Customers", "customers", 3),
            ("Reports", "reports", 4)
        ]
        
        for text, icon_name, btn_id in nav_items:
            btn = NavButton(text, icon_name, btn_id)
            btn.clicked.connect(lambda checked=False, b_id=btn_id: self.on_btn_clicked(b_id))
            self.container_layout.addWidget(btn)
            self.buttons.append(btn)
            
        # Add Sync Status Widget
        self.container_layout.addStretch()
        self.sync_status = SyncStatusWidget()
        self.container_layout.addWidget(self.sync_status)
            
    def on_btn_clicked(self, btn_id):
        self.set_active_btn(btn_id)
        self.nav_changed.emit(btn_id)

    def set_active_btn(self, btn_id):
        for btn in self.buttons:
            btn.set_active(btn.btn_id == btn_id)
            
    def set_role(self, role):
        """RBAC: Handled by showing/hiding screens, but keeping method for compatibility"""
        pass