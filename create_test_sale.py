#!/usr/bin/env python3
"""Debug script to create test sales data"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.database import DatabaseService
from database.models import Sale, SaleItem
from datetime import datetime

def create_test_sale():
    """Create a test sale to verify the system works"""
    try:
        print("=== Creating Test Sale ===")
        
        # Create a test sale
        sale = Sale(
            date=datetime.now(),
            total_amount=150.50,
            payment_method="Cash",
            customer_id=None,
            cashier_user="test_user"
        )
        
        # Add test items
        item1 = SaleItem(
            product_id=1,
            product_name="Test Product 1",
            quantity=2,
            unit_price=50.25,
            subtotal=100.50
        )
        
        item2 = SaleItem(
            product_id=2,
            product_name="Test Product 2", 
            quantity=1,
            unit_price=50.00,
            subtotal=50.00
        )
        
        sale.items.append(item1)
        sale.items.append(item2)
        
        # Save to database
        sale_id = DatabaseService.create_sale(sale)
        print(f"Created test sale with ID: {sale_id}")
        
        # Verify it was saved
        with DatabaseService.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM sales WHERE id = ?", (sale_id,))
            result = cursor.fetchone()
            
            if result:
                print(f"Verified sale in database: ID={result[0]}, Date={result[1]}, Amount={result[2]}")
            else:
                print("ERROR: Sale not found in database")
        
        # Test retrieval
        from services.sales_service import SalesService
        today = datetime.now()
        start_date = datetime.combine(today.date(), datetime.min.time())
        end_date = datetime.combine(today.date(), datetime.max.time())
        
        sales_data = SalesService.get_sales_by_date_range(start_date, end_date)
        print(f"Retrieved {len(sales_data)} sales for today")
        
        for sale in sales_data:
            print(f"Sale: ID={sale['id']}, Amount={sale['total_amount']}, Items={len(sale['items'])}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_test_sale()
