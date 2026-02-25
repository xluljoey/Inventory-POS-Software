import sqlite3
from contextlib import contextmanager
from typing import Generator
from loguru import logger
from pathlib import Path # Added import

class DatabaseConfig:
    """Database configuration and connection management"""
    
    @staticmethod
    @contextmanager
    def get_db_connection() -> Generator[sqlite3.Connection, None, None]:
        """Get a database connection with proper context management"""
        conn = None
        try:
            from config.app_config import AppConfig
            conn = sqlite3.connect(AppConfig.get_db_path())
            conn.row_factory = sqlite3.Row  # Enable column access by name
            yield conn
        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            logger.error(f"Database connection error: {str(e)}")
            raise e
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def init_database():
        """Initialize the database with all required tables and indexes"""
        from config.app_config import AppConfig
        db_path = AppConfig.get_db_path()
        
        # Ensure the data directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True) # Ensure parent directories exist
        
        with sqlite3.connect(db_path) as conn:
            # Create tables
            conn.executescript('''
                -- Products table
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    sku TEXT UNIQUE NOT NULL,
                    category TEXT,
                    unit_type TEXT DEFAULT 'pieces',
                    quantity REAL DEFAULT 0,
                    cost_price REAL NOT NULL,
                    selling_price REAL NOT NULL,
                    reorder_level INTEGER DEFAULT 0,
                    supplier TEXT,
                    notes TEXT,
                    expiry_date DATE,
                    batch_number TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                -- Sales table
                CREATE TABLE IF NOT EXISTS sales (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    total_amount REAL NOT NULL,
                    amount_paid REAL DEFAULT 0,
                    payment_method TEXT,
                    customer_id INTEGER,
                    cashier_user TEXT NOT NULL,
                    sync_status TEXT DEFAULT 'pending',
                    FOREIGN KEY (customer_id) REFERENCES customers (id)
                );
                
                -- Sale items table
                CREATE TABLE IF NOT EXISTS sale_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sale_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL,
                    quantity REAL NOT NULL,
                    unit_price REAL NOT NULL,
                    subtotal REAL NOT NULL,
                    FOREIGN KEY (sale_id) REFERENCES sales (id),
                    FOREIGN KEY (product_id) REFERENCES products (id)
                );
                
                -- Customers table
                CREATE TABLE IF NOT EXISTS customers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    phone TEXT UNIQUE,
                    email TEXT,
                    address TEXT,
                    credit_limit REAL DEFAULT 0,
                    outstanding_balance REAL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                -- Customer payments table
                CREATE TABLE IF NOT EXISTS customer_payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_id INTEGER NOT NULL,
                    amount REAL NOT NULL,
                    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    payment_method TEXT,
                    notes TEXT,
                    FOREIGN KEY (customer_id) REFERENCES customers (id)
                );
                
                -- Stock movements table
                CREATE TABLE IF NOT EXISTS stock_movements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER NOT NULL,
                    type TEXT NOT NULL CHECK(type IN ('arrival', 'adjustment', 'sale')),
                    quantity REAL NOT NULL,
                    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    reason TEXT,
                    user TEXT NOT NULL,
                    FOREIGN KEY (product_id) REFERENCES products (id)
                );
                
                -- Users table
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL CHECK(role IN ('admin', 'sales_rep')),
                    full_name TEXT NOT NULL,
                    pin_hash TEXT,  -- For admin access
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                -- Categories table
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                -- Restock history table
                CREATE TABLE IF NOT EXISTS restock_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER,
                    old_qty REAL,
                    added_qty REAL,
                    new_qty REAL,
                    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    record_type TEXT DEFAULT 'Arrival', -- SPRINT 5: Add record_type
                    FOREIGN KEY(product_id) REFERENCES products (id)
                );
                
                -- Activities table for general logging
                CREATE TABLE IF NOT EXISTS activities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type TEXT NOT NULL, -- 'price_change', 'stock_correction', 'system', etc.
                    description TEXT NOT NULL,
                    user TEXT NOT NULL,
                    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                                
                -- Settings table
                CREATE TABLE IF NOT EXISTS settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key_name TEXT UNIQUE NOT NULL,
                    value TEXT NOT NULL,
                    description TEXT
                );

                -- System Info table for versioning and other system-level info
                CREATE TABLE IF NOT EXISTS system_info (
                    version_key TEXT PRIMARY KEY,
                    version_value TEXT
                );
                
                -- Sync_Log table (Premium Sync)
                CREATE TABLE IF NOT EXISTS Sync_Log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    table_name TEXT NOT NULL,
                    record_id INTEGER NOT NULL,
                    sync_status INTEGER DEFAULT 0, -- 0: Unsynced, 1: Synced
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                -- Create indexes for performance
                CREATE INDEX IF NOT EXISTS idx_products_sku ON products(sku);
                CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
                CREATE INDEX IF NOT EXISTS idx_products_quantity ON products(quantity);
                CREATE INDEX IF NOT EXISTS idx_sales_date ON sales(date);
                CREATE INDEX IF NOT EXISTS idx_sale_items_sale_id ON sale_items(sale_id);
                CREATE INDEX IF NOT EXISTS idx_sale_items_product_id ON sale_items(product_id);
                CREATE INDEX IF NOT EXISTS idx_customers_phone ON customers(phone);
                CREATE INDEX IF NOT EXISTS idx_categories_name ON categories(name);
                
                -- Insert default settings
                INSERT OR IGNORE INTO settings (key_name, value, description) VALUES
                ('business_name', 'Inventory Management System', 'Name of the business'),
                ('business_address', '', 'The physical address of the business'),
                ('currency_symbol', 'GH₵', 'Currency symbol to use in the application'),
                ('tax_rate', '0.0', 'Default tax rate as decimal (e.g., 0.15 for 15%)'),
                ('global_markup', '0.0', 'Default markup percentage to apply to products'),
                ('receipt_header', 'Thank you for your purchase!', 'Header text for receipts'),
                ('receipt_footer', 'We appreciate your business', 'Footer text for receipts'),
                ('low_stock_threshold', '10', 'Default low stock threshold'),
                ('backup_frequency_days', '1', 'How often to create backups (in days)'),
                ('backup_retention_days', '30', 'How many days of backups to keep'),
                ('allow_sales_rep_discounts', '0', 'Permission for sales rep to apply discounts'),
                ('show_reports_to_sales_rep', '0', 'Permission for sales rep to view reports'),
                ('show_cost_to_sales_rep', '0', 'Permission for sales rep to view cost price'),
                ('last_cloud_sync', 'Never', 'Timestamp of the last successful cloud backup');
                
                -- Insert default categories
                INSERT OR IGNORE INTO categories (name, description) VALUES
                ('Electronics', 'Electronic devices and accessories'),
                ('Clothing', 'Apparel and fashion items'),
                ('Food', 'Food and beverages'),
                ('Other', 'Miscellaneous items');
                
            ''')
            
            # --- Schema Migrations ---
            # Migration: Add record_type to restock_history if not exists
            try:
                conn.execute("ALTER TABLE restock_history ADD COLUMN record_type TEXT DEFAULT 'Arrival'")
            except sqlite3.OperationalError:
                pass # Column likely already exists
            
            # Migration: Add amount_paid to sales if not exists
            try:
                conn.execute("ALTER TABLE sales ADD COLUMN amount_paid REAL DEFAULT 0")
            except sqlite3.OperationalError:
                pass
            
            # Migration: Add batch_number to products if not exists
            try:
                conn.execute("ALTER TABLE products ADD COLUMN batch_number TEXT")
            except sqlite3.OperationalError:
                pass

            # Migration: Add sync_status to sales if not exists
            try:
                conn.execute("ALTER TABLE sales ADD COLUMN sync_status TEXT DEFAULT 'pending'")
            except sqlite3.OperationalError:
                pass

            # SPRINT 5: Insert database version
            conn.execute("INSERT OR IGNORE INTO system_info (version_key, version_value) VALUES (?, ?)", 
                         ('database_version', '1.0'))
                
            conn.commit()