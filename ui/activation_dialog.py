from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QFrame, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor
from utils.licensing import LicenseManager

class ActivationDialog(QDialog):
    """Initial activation dialog to ensure software is purchased/authorized"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Software Activation")
        self.setFixedSize(500, 350)
        self.setWindowFlags(Qt.Window | Qt.WindowTitleHint | Qt.CustomizeWindowHint)
        self.setStyleSheet("background-color: #F9FAFB;")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # Header
        title = QLabel("Product Activation")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #111827;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        desc = QLabel("Please enter your unique license key to activate the software. "
                     "This key is specific to your hardware.")
        desc.setWordWrap(True)
        desc.setStyleSheet("font-size: 13px; color: #4B5563;")
        desc.setAlignment(Qt.AlignCenter)
        layout.addWidget(desc)

        # Machine ID Card
        mid_card = QFrame()
        mid_card.setStyleSheet("background-color: #F3F4F6; border-radius: 8px; padding: 10px;")
        mid_layout = QVBoxLayout(mid_card)
        
        mid_label = QLabel(f"<b>Machine ID:</b><br>{LicenseManager.get_machine_id()}")
        mid_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        mid_label.setAlignment(Qt.AlignCenter)
        mid_label.setStyleSheet("font-family: monospace; font-size: 12px; color: #374151;")
        
        mid_layout.addWidget(mid_label)
        layout.addWidget(mid_card)

        # Key Input
        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText("XXXX-XXXX-XXXX-XXXX-XXXX")
        self.key_input.setFixedHeight(45)
        self.key_input.setAlignment(Qt.AlignCenter)
        self.key_input.setStyleSheet("""
            QLineEdit {
                border: 2px solid #D1D5DB;
                border-radius: 8px;
                font-size: 16px;
                font-family: monospace;
                letter-spacing: 2px;
                background-color: white;
            }
            QLineEdit:focus {
                border-color: #2563EB;
            }
        """)
        layout.addWidget(self.key_input)

        # Buttons
        btn_layout = QHBoxLayout()
        
        exit_btn = QPushButton("Exit Application")
        exit_btn.setFixedHeight(40)
        exit_btn.setStyleSheet("color: #6B7280; border: none; font-weight: 500;")
        exit_btn.clicked.connect(self.reject)
        
        activate_btn = QPushButton("Activate Now")
        activate_btn.setFixedHeight(40)
        activate_btn.setStyleSheet("""
            QPushButton {
                background-color: #2563EB;
                color: white;
                border-radius: 6px;
                font-weight: bold;
                padding: 0 20px;
            }
            QPushButton:hover { background-color: #1D4ED8; }
        """)
        activate_btn.clicked.connect(self.handle_activation)
        
        btn_layout.addWidget(exit_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(activate_btn)
        layout.addLayout(btn_layout)

        footer = QLabel("Developed by Joachim Korang Amponsah")
        footer.setStyleSheet("font-size: 11px; color: #9CA3AF;")
        footer.setAlignment(Qt.AlignCenter)
        layout.addWidget(footer)

    def handle_activation(self):
        key = self.key_input.text().strip()
        if not key:
            QMessageBox.warning(self, "Invalid Key", "Please enter your license key.")
            return

        if LicenseManager.activate(key):
            QMessageBox.information(self, "Success", "Software activated successfully!")
            self.accept()
        else:
            QMessageBox.critical(self, "Activation Failed", 
                                "The license key provided is invalid for this machine.\n"
                                "Please contact Joachim Korang Amponsah for a valid key.\n\n"
                                "Phone: +233598433482\n"
                                "Email: jerryjoachim632@gmail.com")
