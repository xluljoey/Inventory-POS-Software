from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, 
    QScrollArea, QDialog, QTextEdit, QDialogButtonBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

class LicenseModal(QDialog):
    """Clean, readable modal for the legal license agreement."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("End User License Agreement")
        self.setMinimumSize(600, 500)
        self.setStyleSheet("background-color: white;")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        title = QLabel("Software License Agreement")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2C3E50; margin-bottom: 10px;")
        layout.addWidget(title)
        
        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)
        self.text_area.setStyleSheet("""
            QTextEdit {
                border: 1px solid #E5E7EB;
                border-radius: 8px;
                padding: 15px;
                font-family: 'Segoe UI', sans-serif;
                font-size: 13px;
                line-height: 1.6;
                color: #374151;
            }
        """)
        
        license_text = """
INVENTORY MANAGEMENT SYSTEM - VERSION 1.0.0
Author: Joachim Korang Amponsah | Build: 2026.03

MIT LICENSE / AS-IS CLAUSE

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

DATA OWNERSHIP & PRIVACY:
The user maintains 100% ownership of all data entered into this system. As an offline-first application, no data is transmitted to third-party servers. The developers do not have access to your inventory, sales, or customer records.

(c) 2026 Inventory Management Systems. All local data is your property.
        """
        self.text_area.setText(license_text.strip())
        layout.addWidget(self.text_area)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

class AboutScreen(QWidget):
    """
    About & Licensing screen providing transparency on system roles,
    data security, and local data ownership.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        # Main layout matches the modern Settings aesthetics
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(32, 24, 32, 24)
        main_layout.setSpacing(20)
        main_layout.setAlignment(Qt.AlignTop)

        # Header: App Name and Version
        header_frame = QFrame()
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(0, 0, 0, 10)
        
        app_title = QLabel("Inventory Management System")
        app_title.setStyleSheet("font-size: 28px; font-weight: bold; color: #1976D2;")
        
        version_label = QLabel("Version 1.0.0 (Stable Production Build)")
        version_label.setStyleSheet("font-size: 14px; color: #6B7280; font-weight: 500;")
        
        header_layout.addWidget(app_title)
        header_layout.addWidget(version_label)
        main_layout.addWidget(header_frame)

        # Scroll Area for Content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(25)
        content_layout.setAlignment(Qt.AlignTop)

        # SECTION 1: Developer Information
        dev_card = self._create_section_card(
            "👨‍💻 Developer Information",
            "This application was designed and developed by **Joachim Korang Amponsah (Xluljoey)**.\n\n"
            "Focused on creating high-performance, secure, and user-centric business solutions."
        )
        content_layout.addWidget(dev_card)

        # SECTION 2: User Roles
        roles_card = self._create_section_card(
            "👥 System User Roles",
            "This application utilizes a strict Role-Based Access Control (RBAC) architecture "
            "to ensure business security and data integrity.\n\n"
            "• Admin (Business Owner): Exclusive administrative rights. Only Admins can perform "
            "critical functions such as updating product prices, adding or removing stock, "
            "and correcting quantity discrepancies.\n\n"
            "• Sales Representative: Access is limited to POS (Point of Sale) operations and "
            "customer management. Standard users are blocked from altering master data or "
            "viewing sensitive cost metrics."
        )
        content_layout.addWidget(roles_card)

        # SECTION 2: Data Security
        security_card = self._create_section_card(
            "🛡️ Data Security & Sovereignty",
            "Designed for complete data ownership, this application is built with an 'Offline-First' "
            "philosophy.\n\n"
            "• Local Storage: All inventory, sales, and customer data reside strictly on your local hardware. "
            "There are no cloud dependencies, ensuring zero external exposure.\n\n"
            "• Role-Based Protection: Integrated security layers prevent unauthorized access from "
            "Sales Representatives to master configurations, preserving the accuracy of your business data."
        )
        content_layout.addWidget(security_card)

        # SECTION 3: Licensing Summary
        license_card = self._create_section_card(
            "📜 License & Ownership",
            "Software provided 'as-is' with a focus on commercial reliability and local data ownership. "
            "You retain 100% control over your database files and local configuration."
        )
        
        # Add "View License" button inside the license card
        view_license_btn = QPushButton("View Full License")
        view_license_btn.setFixedWidth(160)
        view_license_btn.setFixedHeight(36)
        view_license_btn.setCursor(Qt.PointingHandCursor)
        view_license_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF;
                color: #1976D2;
                border: 1px solid #1976D2;
                border-radius: 6px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #EFF6FF;
            }
        """)
        view_license_btn.clicked.connect(self.show_license_modal)
        license_card.layout().addWidget(view_license_btn)
        
        content_layout.addWidget(license_card)

        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)

    def _create_section_card(self, title, text):
        """Helper to create a styled information card."""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 12px;
                border: 1px solid #E5E7EB;
            }
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #2C3E50; border: none;")
        
        desc_label = QLabel(text)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("font-size: 14px; color: #4B5563; line-height: 1.5; border: none;")
        
        layout.addWidget(title_label)
        layout.addWidget(desc_label)
        return card

    def show_license_modal(self):
        modal = LicenseModal(self)
        modal.exec()
