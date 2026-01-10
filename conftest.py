import os
import pytest
import sqlite3
from unittest.mock import patch, MagicMock
from pathlib import Path
from PySide6.QtWidgets import QApplication
from main import MainWindow
from config.app_config import AppConfig
from database.init_db import init_database_with_default_admin
from database.database import DatabaseService
from database.models import User

@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app

@pytest.fixture
def temp_db(tmp_path):
    """Fixture for a clean, temporary database for each test."""
    db_path = tmp_path / "test_inventory.db"
    
    with patch.object(AppConfig, 'get_db_path', return_value=db_path):
        init_database_with_default_admin()
        yield db_path
        if db_path.exists():
            try:
                os.remove(db_path)
            except PermissionError:
                pass

@pytest.fixture
def main_window(qapp, temp_db, qtbot):
    """Fixture for the main application window."""
    window = MainWindow()
    qtbot.addWidget(window)
    return window

@pytest.fixture
def admin_user():
    """Returns a mock admin user."""
    return User(id=1, username="admin", role="admin", full_name="System Admin")

@pytest.fixture
def sales_manager_user():
    """Returns a mock sales manager (sales_rep) user."""
    return User(id=2, username="manager", role="sales_rep", full_name="Sales Manager")
