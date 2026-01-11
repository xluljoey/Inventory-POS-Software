# ui/navigation_bar.py
from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QFrame, QSizePolicy, QLabel, QGraphicsOpacityEffect
from PySide6.QtCore import Qt, Signal, QSize, QPropertyAnimation, QEasingCurve, QAbstractAnimation
from PySide6.QtGui import QIcon, QPixmap, QPainter, QFont, QColor
import os
from core import config
from core.config import ICON_DIR
from loguru import logger

class SyncStatusWidget(QWidget):
    """Heartbeat indicator for Premium Sync"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(10, 0, 10, 0)
        
        self.status_label = QLabel()
        self.status_label.setStyleSheet("color: white; font-weight: bold; font-size: 11px;")
        
        self.dot = QLabel("●")
        self.dot.setStyleSheet("font-size: 14px;")

        self.opacity_effect = QGraphicsOpacityEffect(self.dot)
        self.dot.setGraphicsEffect(self.opacity_effect)
        
        self.anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.anim.setDuration(1000)
        self.anim.setStartValue(1.0)
        self.anim.setEndValue(0.2)
        self.anim.setEasingCurve(QEasingCurve.InOutQuad)
        self.anim.setLoopCount(-1)

        self.layout.addWidget(self.dot)
        self.layout.addWidget(self.status_label)
        
        if config.IS_PREMIUM:
            self.update_status(False)
        else:
            self.dot.hide()
            self.status_label.setText("Local Only")
            self.status_label.setStyleSheet("color: #90A4AE;")

    def update_status(self, is_online: bool):
        if not config.IS_PREMIUM: return
        if is_online:
            self.dot.setStyleSheet("color: #4CAF50;") # Green
            self.status_label.setText("Cloud Sync Active")
            if self.anim.state() != QAbstractAnimation.Running:
                self.anim.start()
        else:
            self.anim.stop()
            self.opacity_effect.setOpacity(1.0)
            self.dot.setStyleSheet("color: #F44336;") # Red
            self.status_label.setText("Offline")

class NavButton(QPushButton):
    def __init__(self, text, icon_name, btn_id, parent=None):
        super().__init__(parent)
        self.nav_text = text
        self.icon_name = icon_name
        self.btn_id = btn_id
        self.is_active = False
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(44)
        self.setMinimumWidth(150)
        self.setText(f" {self.nav_text}")
        self._load_icon()
        self.update_style()

    def _load_icon(self):
        icon_path = os.path.join(ICON_DIR, f"{self.icon_name}.png")
        if os.path.exists(icon_path):
            self.setIcon(QIcon(icon_path))
            self.setIconSize(QSize(22, 22))

    def set_active(self, active):
        self.is_active = active
        self.setChecked(active)
        self.update_style()

    def update_style(self):
        if self.is_active:
            self.setStyleSheet("QPushButton { background-color: #FFFFFF; color: #1976D2; border-radius: 22px; font-weight: bold; }")
        else:
            self.setStyleSheet("QPushButton { background-color: rgba(255,255,255,0.1); color: #FFFFFF; border-radius: 22px; }")

class MainNavigationBar(QFrame):
    nav_changed = Signal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(85) 
        self.main_layout = QHBoxLayout(self)
        
        self.container = QFrame()
        self.container.setFixedHeight(60)
        self.container.setStyleSheet("background-color: #1976D2; border-radius: 30px;")
        
        self.container_layout = QHBoxLayout(self.container)
        self.container_layout.setContentsMargins(20, 0, 20, 0)
        
        self.main_layout.addStretch()
        self.main_layout.addWidget(self.container)
        self.main_layout.addStretch()
        
        self.buttons = []
        nav_items = [("Dashboard", "dashboard", 0), ("Inventory", "inventory", 1), ("Sales", "sales", 2), ("Customers", "customers", 3)]
        
        for text, icon, b_id in nav_items:
            btn = NavButton(text, icon, b_id)
            btn.clicked.connect(lambda chk=False, i=b_id: self.on_btn_clicked(i))
            self.container_layout.addWidget(btn)
            self.buttons.append(btn)
        
        self.container_layout.addStretch()
        self.sync_status = SyncStatusWidget()
        self.container_layout.addWidget(self.sync_status)
            
    def on_btn_clicked(self, btn_id):
        self.set_active_btn(btn_id)
        self.nav_changed.emit(btn_id)

    def set_active_btn(self, btn_id):
        for btn in self.buttons:
            btn.set_active(btn.btn_id == btn_id)

    def set_role(self, role): pass
