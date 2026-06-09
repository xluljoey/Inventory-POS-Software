import os
from PySide6.QtWidgets import (
    QWizard, QWizardPage, QVBoxLayout, QFormLayout, 
    QLineEdit, QLabel, QComboBox, QMessageBox, QCheckBox
)
from PySide6.QtCore import Qt
from database.database import DatabaseService
from services.auth_service import AuthService
from utils.cloud_service import CloudService
from database.models import User
from loguru import logger

class WelcomePage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Welcome to Inventory Management")
        layout = QVBoxLayout(self)
        msg = QLabel("This wizard will help you configure your inventory system for the first time.\n\n" 
                     "You will set up your business information, create an administrator account, "
                     "and optionally link your Google Drive for cloud backups.")
        msg.setWordWrap(True)
        layout.addWidget(msg)

class BusinessInfoPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Business Information")
        layout = QFormLayout(self)
        
        self.store_name = QLineEdit()
        self.address = QLineEdit()
        self.currency = QComboBox()
        self.currency.addItems(["GHS (GHS)", "USD ($)"])
        
        layout.addRow("Store Name*:", self.store_name)
        layout.addRow("Store Address:", self.address)
        layout.addRow("Preferred Currency:", self.currency)
        
        self.registerField("store_name*", self.store_name)
        self.registerField("address", self.address)

class AdminSetupPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Administrator Account")
        layout = QFormLayout(self)
        
        self.username = QLineEdit("admin")
        self.full_name = QLineEdit()
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)
        
        self.confirm_password = QLineEdit()
        self.confirm_password.setEchoMode(QLineEdit.Password)
        
        layout.addRow("Username:", self.username)
        layout.addRow("Full Name*:", self.full_name)
        layout.addRow("Password*:", self.password)
        layout.addRow("Confirm Password*:", self.confirm_password)
        
        self.registerField("admin_user*", self.username)
        self.registerField("admin_full_name*", self.full_name)
        self.registerField("admin_pass*", self.password)
        self.registerField("admin_confirm*", self.confirm_password)

        # Connect signals to check completion status
        self.password.textChanged.connect(self.completeChanged)
        self.confirm_password.textChanged.connect(self.completeChanged)

    def isComplete(self):
        """Check if all mandatory fields are filled and passwords match."""
        # QWizard handles mandatory fields if registered with '*', 
        # but we need custom logic for matching passwords.
        pass_text = self.password.text()
        confirm_text = self.confirm_password.text()
        
        # Check basic mandatory fields first
        if not self.full_name.text().strip() or not pass_text:
            return False
            
        return pass_text == confirm_text and len(pass_text) >= 4

    def validatePage(self):
        """Final validation before moving to next page."""
        if self.password.text() != self.confirm_password.text():
            QMessageBox.warning(self, "Password Mismatch", "The passwords entered do not match. Please try again.")
            return False
        return True

class CloudLinkPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Cloud Backup (Optional)")
        layout = QVBoxLayout(self)
        
        self.cloud_check = QCheckBox("Link Google Drive now for automated backups")
        layout.addWidget(self.cloud_check)
        
        self.note = QLabel("\nNote: Linking requires 'credentials.json' in the app folder.")
        self.note.setStyleSheet("color: #6B7280; font-size: 12px;")
        layout.addWidget(self.note)

class SetupWizard(QWizard):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Initial System Configuration")
        self.setFixedSize(600, 450)
        
        self.addPage(WelcomePage())
        self.addPage(BusinessInfoPage())
        self.addPage(AdminSetupPage())
        self.addPage(CloudLinkPage())
        
        self.setButtonText(QWizard.FinishButton, "Complete Setup")

    def accept(self):
        """Save setup data to the database securely and proceed."""
        try:
            # 1. Collect Data
            store_name = self.field("store_name")
            address = self.field("address")
            username = self.field("admin_user")
            full_name = self.field("admin_full_name")
            password = self.field("admin_pass")
            
            # 2. Database Atomic Update
            with DatabaseService.get_connection() as conn:
                # Update Business Settings
                conn.execute("UPDATE settings SET value=? WHERE key_name='business_name'", (store_name,))
                conn.execute("UPDATE settings SET value=? WHERE key_name='business_address'", (address,))
                
                # Update/Create Admin Account
                hashed_pass, salt = AuthService.hash_password(password)
                admin_user = DatabaseService.get_user_by_username(username)
                
                if admin_user:
                    conn.execute("UPDATE users SET full_name=?, password_hash=?, role='admin' WHERE username=?", 
                                (full_name, f"{salt}${hashed_pass}", username))
                else:
                    conn.execute("INSERT INTO users (username, full_name, password_hash, role) VALUES (?, ?, ?, 'admin')",
                                (username, full_name, f"{salt}${hashed_pass}"))
                
                conn.commit()
            
            # 3. Optional Cloud Link (Non-blocking fail-safe)
            if self.page(3).cloud_check.isChecked():
                try:
                    cs = CloudService()
                    # Only attempt if credentials exist
                    if os.path.exists('credentials.json'):
                        cs.authenticate()
                    else:
                        QMessageBox.warning(self, "Cloud Setup", "Google credentials.json not found. Skipping link.")
                except Exception as cloud_err:
                    logger.error(f"Fail-safe: Cloud linking error in wizard: {cloud_err}")
                    # We don't crash here, setup is still valid
            
            logger.info(f"System Setup successful for store: {store_name}")
            super().accept()
            
        except Exception as e:
            logger.error(f"CRITICAL SETUP ERROR: {e}")
            QMessageBox.critical(self, "Setup Failed", 
                                f"A database error occurred during setup:\n{str(e)}\n\nPlease contact support.")
            # Do NOT call super().accept() if database fails
