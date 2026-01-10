import pytest
import sqlite3
from unittest.mock import patch, MagicMock
from PySide6.QtCore import Qt
from services.inventory_service import InventoryService
from services.sales_service import SalesService
from database.database import DatabaseService
from database.models import Product, Sale, SaleItem
from ui.custom_dialog import CustomErrorDialog

def test_data_integrity_rapid_add(temp_db):
    """
    Scenario 1: Attempt to add 1,000 items rapidly.
    Verify database responsiveness and no data loss.
    """
    initial_count = len(InventoryService.get_all_products())
    num_items = 1000
    
    for i in range(num_items):
        product_data = {
            'name': f"Stress Item {i}",
            'sku': f"SKU-STRESS-{i}",
            'category': "Stress Test",
            'unit_type': "pieces",
            'quantity': 100.0,
            'cost_price': 10.0,
            'selling_price': 15.0,
            'reorder_level': 5,
            'supplier': "Stress Supplier",
            'notes': "Stress test note",
            'expiry_date': None,
            'batch_number': f"BATCH-{i}"
        }
        InventoryService.add_product(product_data)
    
    all_products = InventoryService.get_all_products()
    assert len(all_products) == initial_count + num_items
    
    # Verify a random item to ensure data is correct
    test_item = next(p for p in all_products if p['sku'] == "SKU-STRESS-500")
    assert test_item['name'] == "Stress Item 500"

def test_negative_logic_oversell(temp_db):
    """
    Scenario 2: Attempt to sell more stock than available.
    Verify the app prevents the sale.
    """
    # Create a product with limited stock
    product_id = InventoryService.add_product({
        'name': "Limited Item",
        'sku': "SKU-LIMIT",
        'category': "Test",
        'unit_type': "pieces",
        'quantity': 10.0,
        'cost_price': 10.0,
        'selling_price': 20.0,
        'reorder_level': 2,
        'supplier': None,
        'notes': None,
        'expiry_date': None,
        'batch_number': None
    })
    
    # Try to sell more than available
    sale_data = {
        "date": "2026-01-10T12:00:00",
        "total_amount": 220.0,
        "payment_method": "cash",
        "amount_paid": 220.0,
        "customer_id": None,
        "cashier_user": "admin",
        "items": [
            {
                "product_id": product_id,
                "product_name": "Limited Item",
                "quantity": 11.0, # More than 10
                "unit_price": 20.0,
                "subtotal": 220.0
            }
        ]
    }
    
    # The service should raise ValueError for insufficient stock
    with pytest.raises(ValueError, match="Insufficient stock"):
        SalesService.process_payment(sale_data)

def test_security_access_control(main_window, sales_manager_user, qtbot):
    """
    Scenario 3: Simulate a 'Sales Manager' (sales_rep) accessing 'Settings' or 'Delete Stock'.
    Verify that these actions are blocked.
    """
    # Simulate login as Sales Rep
    main_window.on_login_success(sales_manager_user)
    
    # 1. Verify Settings Screen behavior
    main_window.show_settings()
    assert main_window.stacked_widget.currentWidget() == main_window.settings_screen
    # The settings screen should show the about page for non-admins
    assert main_window.settings_screen.content_stack.currentWidget() == main_window.settings_screen.about_page
    assert not main_window.settings_screen.sidebar_widget.isVisible()
    
    # 2. Verify Inventory Screen behavior
    main_window.show_inventory()
    # Manage Stock button should be hidden for Sales Rep
    assert not main_window.inventory_screen.manage_stock_btn.isVisible()
    
    # Even if they try to call the method directly, it should show a warning
    with patch('ui.custom_dialog.CustomWarningDialog.exec') as mock_warn_exec:
        main_window.inventory_screen.open_manage_stock_dialog()
        assert mock_warn_exec.called, "Security breach: Manage Stock dialog allowed for Sales Rep"

def test_crash_test_database_disconnection(main_window, admin_user, qtbot):
    """
    Scenario 4: Simulate a database disconnection mid-transaction.
    Verify that the app handles the error gracefully.
    
    Note: We need to ensure the UI catches the exception and shows a dialog.
    """
    main_window.on_login_success(admin_user)
    
    # Set up some data
    product_id = InventoryService.add_product({
        'name': "Crash Test Item",
        'sku': "SKU-CRASH",
        'category': "Test",
        'unit_type': "pieces",
        'quantity': 100.0,
        'cost_price': 10.0,
        'selling_price': 20.0,
        'reorder_level': 2,
        'supplier': None,
        'notes': None,
        'expiry_date': None
    })
    
    # Add item to cart in Sales Screen
    main_window.show_sales()
    sales_screen = main_window.sales_screen
    
    product = next(p for p in sales_screen.all_products if p['id'] == product_id)
    sales_screen.add_to_cart(product)
    sales_screen.tender_input.setText("20.0")
    
    # Mock SalesService.create_sale to raise a database error
    with patch('services.sales_service.SalesService.create_sale', side_effect=sqlite3.OperationalError("Database connection lost")):
        with patch('ui.custom_dialog.CustomErrorDialog.exec') as mock_error_exec:
            try:
                sales_screen.on_complete_sale_clicked()
            except sqlite3.OperationalError:
                pytest.fail("Application crashed due to unhandled sqlite3.OperationalError!")
            except Exception as e:
                pytest.fail(f"Application crashed with unexpected error: {str(e)}")
            
            # Verify that the error dialog was shown to the user
            assert mock_error_exec.called, "Error dialog was not shown during database failure"
