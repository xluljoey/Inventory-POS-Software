from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                               QLabel, QPushButton, QFrame, QSizePolicy)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

class ClearDebtConfirmationDialog(QDialog):
    """Custom styled confirmation dialog for clearing debt"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Confirm Action")
        self.setModal(True)
        self.setFixedWidth(420)
        self.setStyleSheet("""
            QDialog {
                background-color: #FFFFFF;
                border-radius: 12px;
            }
        """)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        # Warning Icon Container (Circle)
        icon_container = QFrame()
        icon_container.setFixedSize(60, 60)
        icon_container.setStyleSheet("""
            QFrame {
                background-color: #FEE4E2;
                border-radius: 30px;
            }
        """)
        icon_layout = QVBoxLayout(icon_container)
        icon_layout.setContentsMargins(0,0,0,0)
        icon_layout.setAlignment(Qt.AlignCenter)
        
        warning_icon = QLabel("⚠️")
        warning_icon.setStyleSheet("font-size: 24px; color: #D92D20;")
        icon_layout.addWidget(warning_icon)
        
        layout.addWidget(icon_container, 0, Qt.AlignCenter)

        # Title
        title = QLabel("Clear Entire Debt?")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #101828;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Message
        msg = QLabel("This will clear the entire debt/arrears of this customer.\nThis action will be recorded and cannot be undone.")
        msg.setWordWrap(True)
        msg.setStyleSheet("font-size: 14px; color: #667085; line-height: 1.4;")
        msg.setAlignment(Qt.AlignCenter)
        layout.addWidget(msg)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setCursor(Qt.PointingHandCursor)
        self.cancel_btn.setFixedHeight(40)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF;
                color: #344054;
                border: 1px solid #D0D5DD;
                border-radius: 8px;
                font-weight: 600;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #F9FAFB; }
        """)
        self.cancel_btn.clicked.connect(self.reject)

        self.confirm_btn = QPushButton("Yes, Clear Debt")
        self.confirm_btn.setCursor(Qt.PointingHandCursor)
        self.confirm_btn.setFixedHeight(40)
        self.confirm_btn.setStyleSheet("""
            QPushButton {
                background-color: #D92D20;
                color: #FFFFFF;
                border: 1px solid #D92D20;
                border-radius: 8px;
                font-weight: 600;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #B42318; border-color: #B42318; }
        """)
        self.confirm_btn.clicked.connect(self.accept)

        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.confirm_btn)
        layout.addLayout(btn_layout)
