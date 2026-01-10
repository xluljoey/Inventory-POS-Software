from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QGraphicsDropShadowEffect)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor


class CustomWarningDialog(QDialog):
    """Custom warning dialog matching design specifications"""
    
    def __init__(self, title="Warning", message="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("")
        self.setModal(True)
        self.setFixedSize(380, 200)
        
        # Remove default window decorations
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        
        # Main container with styling
        self.setStyleSheet("""
            QDialog {
                background-color: #FFFFFF;
                border-radius: 25px;
                border: none;
            }
        """)
        
        # Add drop shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 5)
        self.setGraphicsEffect(shadow)
        
        self.init_ui(title, message)
    
    def init_ui(self, title, message):
        """Initialize dialog UI components"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # Title label
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #2C3E50;
                text-align: center;
            }
        """)
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # Message label
        message_label = QLabel(message)
        message_label.setStyleSheet("""
            QLabel {
                font-size: 13px;
                color: #2C3E50;
                text-align: center;
                line-height: 1.4;
            }
        """)
        message_label.setAlignment(Qt.AlignCenter)
        message_label.setWordWrap(True)
        main_layout.addWidget(message_label)
        
        main_layout.addStretch()
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        button_layout.addStretch()
        
        cancel_button = QPushButton("Cancel")
        cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF;
                color: #555555;
                border: 1px solid #CCCCCC;
                border-radius: 6px;
                padding: 6px 16px;
                font-size: 12px;
                font-weight: 500;
                min-width: 70px;
            }
            QPushButton:hover {
                background-color: #F5F5F5;
            }
        """)
        cancel_button.setCursor(Qt.PointingHandCursor)
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        ok_button = QPushButton("OK")
        ok_button.setStyleSheet("""
            QPushButton {
                background-color: #E74C3C;
                color: #FFFFFF;
                border: none;
                border-radius: 6px;
                padding: 6px 16px;
                font-size: 12px;
                font-weight: 500;
                min-width: 70px;
            }
            QPushButton:hover {
                background-color: #C0392B;
            }
            QPushButton:pressed {
                background-color: #A93226;
            }
        """)
        ok_button.setCursor(Qt.PointingHandCursor)
        ok_button.clicked.connect(self.accept)
        button_layout.addWidget(ok_button)
        
        button_layout.addStretch()
        main_layout.addLayout(button_layout)


class CustomErrorDialog(QDialog):
    """Custom error dialog matching design specifications"""
    
    def __init__(self, title="Error", message="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("")
        self.setModal(True)
        self.setFixedSize(380, 200)
        
        # Remove default window decorations
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        
        # Main container with styling
        self.setStyleSheet("""
            QDialog {
                background-color: #FFFFFF;
                border-radius: 25px;
                border: none;
            }
        """)
        
        # Add drop shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 5)
        self.setGraphicsEffect(shadow)
        
        self.init_ui(title, message)
    
    def init_ui(self, title, message):
        """Initialize dialog UI components"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # Title label
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #2C3E50;
                text-align: center;
            }
        """)
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # Message label
        message_label = QLabel(message)
        message_label.setStyleSheet("""
            QLabel {
                font-size: 13px;
                color: #2C3E50;
                text-align: center;
                line-height: 1.4;
            }
        """)
        message_label.setAlignment(Qt.AlignCenter)
        message_label.setWordWrap(True)
        main_layout.addWidget(message_label)
        
        main_layout.addStretch()
        
        # OK button
        ok_button = QPushButton("OK")
        ok_button.setStyleSheet("""
            QPushButton {
                background-color: #E74C3C;
                color: #FFFFFF;
                border: none;
                border-radius: 6px;
                padding: 6px 16px;
                font-size: 12px;
                font-weight: 500;
                min-width: 70px;
            }
            QPushButton:hover {
                background-color: #C0392B;
            }
            QPushButton:pressed {
                background-color: #A93226;
            }
        """)
        ok_button.setCursor(Qt.PointingHandCursor)
        ok_button.clicked.connect(self.accept)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(ok_button)
        button_layout.addStretch()
        main_layout.addLayout(button_layout)


class CustomInfoDialog(QDialog):
    """Custom info dialog matching design specifications"""
    
    def __init__(self, title="Information", message="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("")
        self.setModal(True)
        self.setFixedSize(500, 250)
        
        # Remove default window decorations
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        
        # Main container with styling
        self.setStyleSheet("""
            QDialog {
                background-color: #FFFFFF;
                border-radius: 25px;
                border: none;
            }
        """)
        
        # Add drop shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 5)
        self.setGraphicsEffect(shadow)
        
        self.init_ui(title, message)
    
    def init_ui(self, title, message):
        """Initialize dialog UI components"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(25, 25, 25, 25)
        main_layout.setSpacing(20)
        
        # Title label
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #2C3E50;
                text-align: center;
            }
        """)
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # Message label
        message_label = QLabel(message)
        message_label.setStyleSheet("""
            QLabel {
                font-size: 13px;
                color: #2C3E50;
                text-align: center;
                line-height: 1.4;
            }
        """)
        message_label.setAlignment(Qt.AlignCenter)
        message_label.setWordWrap(True)
        main_layout.addWidget(message_label)
        
        main_layout.addStretch()
        
        # OK button
        ok_button = QPushButton("OK")
        ok_button.setStyleSheet("""
            QPushButton {
                background-color: #4A76D9;
                color: #FFFFFF;
                border: none;
                border-radius: 6px;
                padding: 6px 16px;
                font-size: 12px;
                font-weight: 500;
                min-width: 100px;
                max-width: 100px;
                height: 36px;
            }
            QPushButton:hover {
                background-color: #3A5FA9;
            }
            QPushButton:pressed {
                background-color: #2A4A89;
            }
        """)
        ok_button.setCursor(Qt.PointingHandCursor)
        ok_button.clicked.connect(self.accept)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(ok_button)
        button_layout.addStretch()
        main_layout.addLayout(button_layout)


class CustomConfirmDialog(QDialog):
    """Custom confirmation dialog with Yes/No buttons"""
    
    def __init__(self, title="Confirmation", message="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("")
        self.setModal(True)
        self.setFixedSize(380, 200)
        
        # Remove default window decorations
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        
        # Main container with styling
        self.setStyleSheet("""
            QDialog {
                background-color: #FFFFFF;
                border-radius: 25px;
                border: 1px solid #E0E0E0;
            }
        """)
        
        # Add drop shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 5)
        self.setGraphicsEffect(shadow)
        
        self.init_ui(title, message)
    
    def init_ui(self, title, message):
        """Initialize dialog UI components"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # Title label
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #2C3E50;")
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # Message label
        message_label = QLabel(message)
        message_label.setStyleSheet("font-size: 13px; color: #2C3E50;")
        message_label.setAlignment(Qt.AlignCenter)
        message_label.setWordWrap(True)
        main_layout.addWidget(message_label)
        
        main_layout.addStretch()
        
        # Buttons layout
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        button_layout.addStretch()
        
        # No button
        no_button = QPushButton("No")
        no_button.setObjectName("secondaryButton")
        no_button.setCursor(Qt.PointingHandCursor)
        no_button.clicked.connect(self.reject)
        no_button.setFixedSize(80, 32)
        button_layout.addWidget(no_button)
        
        # Yes button
        yes_button = QPushButton("Yes")
        yes_button.setObjectName("dangerButton")
        yes_button.setCursor(Qt.PointingHandCursor)
        yes_button.clicked.connect(self.accept)
        yes_button.setFixedSize(80, 32)
        button_layout.addWidget(yes_button)
        
        button_layout.addStretch()
        main_layout.addLayout(button_layout)
