#!/usr/bin/env python3
"""Simple database initialization script"""

import sqlite3
import os
from datetime import datetime

def create_simple_database():
    """Create a simple database in the current directory"""
    db_path = "inventory_management.db"
    
    print(f"Creating database at: {db_path}")
    
    # Create database connection
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            total_amount REAL NOT NULL,
            payment_method TEXT,
            customer_id INTEGER,
            cashier_user TEXT NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sale_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sale_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity REAL NOT NULL,
            unit_price REAL NOT NULL,
            subtotal REAL NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            sku TEXT,
            category TEXT,
            quantity REAL DEFAULT 0,
            cost_price REAL,
            selling_price REAL
        )
    ''')
    
    # Insert test data
    cursor.execute('''
        INSERT INTO products (name, sku, category, quantity, cost_price, selling_price)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', ("Test Product 1", "TP001", "Electronics", 10, 25.00, 50.00))
    
    cursor.execute('''
        INSERT INTO products (name, sku, category, quantity, cost_price, selling_price)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', ("Test Product 2", "TP002", "Electronics", 5, 30.00, 60.00))
    
    # Create a test sale
    cursor.execute('''
        INSERT INTO sales (date, total_amount, payment_method, customer_id, cashier_user)
        VALUES (?, ?, ?, ?, ?)
    ''', (datetime.now().isoformat(), 150.50, "Cash", None, "test_user"))
    
    sale_id = cursor.lastrowid
    
    # Add sale items
    cursor.execute('''
        INSERT INTO sale_items (sale_id, product_id, quantity, unit_price, subtotal)
        VALUES (?, ?, ?, ?, ?)
    ''', (sale_id, 1, 2, 50.00, 100.00))
    
    cursor.execute('''
        INSERT INTO sale_items (sale_id, product_id, quantity, unit_price, subtotal)
        VALUES (?, ?, ?, ?, ?)
    ''', (sale_id, 2, 1, 50.50, 50.50))
    
    conn.commit()
    conn.close()
    
    print(f"Database created successfully at: {db_path}")
    print("Test data inserted:")
    print("- 2 products")
    print("- 1 sale with 2 items")
    
    # Verify data
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM sales")
    sales_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM products")
    products_count = cursor.fetchone()[0]
    
    print(f"Verification: {sales_count} sales, {products_count} products")
    
    conn.close()

if __name__ == "__main__":
    create_simple_database()
