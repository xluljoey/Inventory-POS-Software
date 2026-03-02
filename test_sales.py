import pytest
from unittest.mock import patch
from datetime import datetime, timedelta
from services.sales_service import SalesService
from services.inventory_service import InventoryService
from services.customer_service import CustomerService
from database.database import DatabaseService # For direct DB access if needed

# Assuming 'temp_db' fixture from conftest.py is available
# It ensures a clean database for each test

@pytest.fixture
def test_product(temp_db):
    """Fixture to create and return a test product."""
    product_data = {
        'name': "Credit Test Item",
        'sku': "CTI-001",
        'category': "Test",
        'unit_type': "pieces",
        'quantity': 100.0,
        'cost_price': 5.0,
        'selling_price': 10.0,
        'reorder_level': 10,
        'supplier': "Test Supplier",
        'notes': "For credit limit testing",
        'expiry_date': None,
        'batch_number': None
    }
    product_id = InventoryService.add_product(product_data)
    assert product_id is not None
    return InventoryService.get_product_by_id(product_id)

@pytest.fixture
def test_customer(temp_db):
    """Fixture to create and return a test customer with a credit limit."""
    customer_data = {
        'name': "Credit Customer",
        'phone': "1234567890",
        'email': "credit@example.com",
        'address': "123 Credit Lane",
        'credit_limit': 100.0,
        'outstanding_balance': 0.0
    }
    customer_id = CustomerService.add_customer(customer_data)
    assert customer_id is not None
    return CustomerService.get_customer_by_id(customer_id)


def test_credit_sale_within_limit(temp_db, test_product, test_customer):
    """
    Verify a credit sale goes through successfully when within the customer's limit.
    """
    sale_amount = 50.0 # Within 100.0 limit
    sale_data = {
        "date": datetime.now().isoformat(),
        "total_amount": sale_amount,
        "amount_paid": 0.0, # Full credit
        "payment_method": "credit",
        "customer_id": test_customer['id'],
        "cashier_user": "test_cashier",
        "items": [
            {
                "product_id": test_product['id'],
                "product_name": test_product['name'],
                "quantity": 5.0, # 5 * 10 = 50
                "unit_price": test_product['selling_price'],
                "subtotal": sale_amount
            }
        ]
    }

    sale_id = SalesService.process_payment(sale_data)
    assert sale_id is not None, "Sale should have been created successfully."

    # Verify customer's outstanding balance updated
    updated_customer = CustomerService.get_customer_by_id(test_customer['id'])
    assert updated_customer['outstanding_balance'] == sale_amount
    assert updated_customer['available_credit'] == test_customer['credit_limit'] - sale_amount


def test_credit_sale_exceeds_limit(temp_db, test_product, test_customer):
    """
    Verify a credit sale is blocked when it exceeds the customer's limit.
    """
    sale_amount = 120.0 # Exceeds 100.0 limit
    sale_data = {
        "date": datetime.now().isoformat(),
        "total_amount": sale_amount,
        "amount_paid": 0.0, # Full credit
        "payment_method": "credit",
        "customer_id": test_customer['id'],
        "cashier_user": "test_cashier",
        "items": [
            {
                "product_id": test_product['id'],
                "product_name": test_product['name'],
                "quantity": 12.0, # 12 * 10 = 120
                "unit_price": test_product['selling_price'],
                "subtotal": sale_amount
            }
        ]
    }

    with pytest.raises(ValueError, match="Credit limit exceeded"):
        SalesService.process_payment(sale_data)
    
    # Verify customer's outstanding balance is UNCHANGED
    unchanged_customer = CustomerService.get_customer_by_id(test_customer['id'])
    assert unchanged_customer['outstanding_balance'] == test_customer['outstanding_balance']


def test_credit_sale_partial_payment_within_limit(temp_db, test_product, test_customer):
    """
    Verify a credit sale with partial payment goes through when the remaining credit
    is within the customer's limit.
    """
    sale_amount = 100.0
    paid_amount = 20.0
    remaining_credit = sale_amount - paid_amount # 80.0
    
    sale_data = {
        "date": datetime.now().isoformat(),
        "total_amount": sale_amount,
        "amount_paid": paid_amount,
        "payment_method": "credit",
        "customer_id": test_customer['id'],
        "cashier_user": "test_cashier",
        "items": [
            {
                "product_id": test_product['id'],
                "product_name": test_product['name'],
                "quantity": 10.0,
                "unit_price": test_product['selling_price'],
                "subtotal": sale_amount
            }
        ]
    }

    sale_id = SalesService.process_payment(sale_data)
    assert sale_id is not None

    # Verify customer's outstanding balance updated by remaining credit amount
    updated_customer = CustomerService.get_customer_by_id(test_customer['id'])
    assert updated_customer['outstanding_balance'] == remaining_credit
    assert updated_customer['available_credit'] == test_customer['credit_limit'] - remaining_credit


def test_credit_sale_partial_payment_exceeds_limit(temp_db, test_product, test_customer):
    """
    Verify a credit sale with partial payment is blocked if the remaining credit
    exceeds the customer's limit.
    """
    sale_amount = 100.0
    paid_amount = 5.0
    # Remaining credit is 95.0. Customer has 100.0 limit. Available is 100.0.
    # New outstanding would be 95.0, which is fine. This test needs adjustment.
    
    # Let's modify customer state to have some outstanding balance first
    initial_outstanding = 30.0
    CustomerService.update_customer({
        'id': test_customer['id'],
        'name': test_customer['name'],
        'phone': test_customer['phone'],
        'email': test_customer['email'],
        'address': test_customer['address'],
        'credit_limit': test_customer['credit_limit'], # 100.0
        'outstanding_balance': initial_outstanding # 30.0
    })
    
    # Now, customer has 70.0 available credit (100 - 30)
    # Sale amount is 100.0, paid 5.0, so 95.0 is added to credit
    # New outstanding would be 30.0 + 95.0 = 125.0, which exceeds 100.0 limit.
    sale_amount_total = 100.0
    amount_paid_by_customer = 5.0
    
    sale_data = {
        "date": datetime.now().isoformat(),
        "total_amount": sale_amount_total,
        "amount_paid": amount_paid_by_customer,
        "payment_method": "credit",
        "customer_id": test_customer['id'],
        "cashier_user": "test_cashier",
        "items": [
            {
                "product_id": test_product['id'],
                "product_name": test_product['name'],
                "quantity": 10.0,
                "unit_price": test_product['selling_price'],
                "subtotal": sale_amount_total
            }
        ]
    }

    with pytest.raises(ValueError, match="Credit limit exceeded"):
        SalesService.process_payment(sale_data)

    # Verify customer's outstanding balance is reverted to initial state
    reverted_customer = CustomerService.get_customer_by_id(test_customer['id'])
    assert reverted_customer['outstanding_balance'] == initial_outstanding
    assert reverted_customer['available_credit'] == test_customer['credit_limit'] - initial_outstanding

