import sqlite3
from typing import List, Optional
from datetime import datetime
from .models import Product, User, Customer, Sale, SaleItem, StockMovement, CustomerPayment, Setting, Category
from config.database_config import DatabaseConfig

class DatabaseService:
    """Main database service for all CRUD operations"""
    
    @staticmethod
    def get_connection():
        """Get a database connection using the config"""
        return DatabaseConfig.get_db_connection()
    
    # Product operations
    @staticmethod
    def create_product(product: Product) -> int:
        """Create a new product in the database"""
        with DatabaseService.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO products (name, sku, category, unit_type, quantity, 
                cost_price, selling_price, reorder_level, supplier, notes, expiry_date,
                batch_number, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ''', (
                product.name, product.sku, product.category, product.unit_type,
                product.quantity, product.cost_price, product.selling_price,
                product.reorder_level, product.supplier, product.notes, 
                product.expiry_date.isoformat() if product.expiry_date else None,
                product.batch_number
            ))
            conn.commit()
            return cursor.lastrowid
    
    @staticmethod
    def get_product_by_id(product_id: int) -> Optional[Product]:
        """Get a product by its ID"""
        with DatabaseService.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM products WHERE id = ?', (product_id,))
            row = cursor.fetchone()
            if row:
                return DatabaseService._row_to_product(row)
            return None
    
    @staticmethod
    def get_product_by_sku(sku: str) -> Optional[Product]:
        """Get a product by its SKU"""
        with DatabaseService.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM products WHERE sku = ?', (sku,))
            row = cursor.fetchone()
            if row:
                return DatabaseService._row_to_product(row)
            return None
    
    @staticmethod
    def get_all_products() -> List[Product]:
        """Get all products from the database"""
        with DatabaseService.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM products ORDER BY name')
            rows = cursor.fetchall()
            return [DatabaseService._row_to_product(row) for row in rows]
    
    @staticmethod
    def update_product(product: Product) -> bool:
        """Update an existing product"""
        with DatabaseService.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE products SET name=?, sku=?, category=?, unit_type=?, 
                quantity=?, cost_price=?, selling_price=?, reorder_level=?, 
                supplier=?, notes=?, expiry_date=?, batch_number=?, updated_at=CURRENT_TIMESTAMP
                WHERE id=?
            ''', (
                product.name, product.sku, product.category, product.unit_type,
                product.quantity, product.cost_price, product.selling_price,
                product.reorder_level, product.supplier, product.notes,
                product.expiry_date.isoformat() if product.expiry_date else None,
                product.batch_number,
                product.id
            ))
            conn.commit()
            return cursor.rowcount > 0
    
    @staticmethod
    def delete_product(product_id: int) -> bool:
        """Delete a product by ID"""
        with DatabaseService.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM products WHERE id = ?', (product_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    @staticmethod
    def search_products(query: str) -> List[Product]:
        """Search products by name or SKU"""
        with DatabaseService.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM products 
                WHERE name LIKE ? OR sku LIKE ?
                ORDER BY name
            ''', (f'%{query}%', f'%{query}%'))
            rows = cursor.fetchall()
            return [DatabaseService._row_to_product(row) for row in rows]
    
    @staticmethod
    def get_low_stock_products() -> List[Product]:
        """Get products that are below the reorder level"""
        with DatabaseService.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM products 
                WHERE quantity <= reorder_level AND quantity > 0
            ''')
            rows = cursor.fetchall()
            return [DatabaseService._row_to_product(row) for row in rows]
    
    # User operations
    @staticmethod
    def create_user(user: User) -> int:
        """Create a new user"""
        with DatabaseService.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO users (username, password_hash, role, full_name, pin_hash)
                VALUES (?, ?, ?, ?, ?)
            ''', (user.username, user.password_hash, user.role, user.full_name, user.pin_hash))
            conn.commit()
            return cursor.lastrowid
    
    @staticmethod
    def get_user_by_username(username: str) -> Optional[User]:
        """Get a user by username"""
        with DatabaseService.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
            row = cursor.fetchone()
            if row:
                return DatabaseService._row_to_user(row)
            return None
    
    @staticmethod
    def get_user_by_id(user_id: int) -> Optional[User]:
        """Get a user by ID"""
        with DatabaseService.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
            row = cursor.fetchone()
            if row:
                return DatabaseService._row_to_user(row)
            return None
    
    @staticmethod
    def get_all_users() -> List[User]:
        """Get all users from the database"""
        with DatabaseService.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users ORDER BY username')
            rows = cursor.fetchall()
            return [DatabaseService._row_to_user(row) for row in rows]
    
    @staticmethod
    def update_user_password(user_id: int, password_hash: str) -> bool:
        """Update user's password"""
        with DatabaseService.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE users SET password_hash=?, updated_at=CURRENT_TIMESTAMP WHERE id=?', 
                          (password_hash, user_id))
            conn.commit()
            return cursor.rowcount > 0
    
    # Customer operations
    @staticmethod
    def create_customer(customer: Customer) -> int:
        """Create a new customer"""
        with DatabaseService.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO customers (name, phone, email, address, credit_limit, outstanding_balance)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (customer.name, customer.phone, customer.email, customer.address, 
                  customer.credit_limit, customer.outstanding_balance))
            conn.commit()
            return cursor.lastrowid
    
    @staticmethod
    def get_customer_by_id(customer_id: int) -> Optional[Customer]:
        """Get a customer by ID"""
        with DatabaseService.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM customers WHERE id = ?', (customer_id,))
            row = cursor.fetchone()
            if row:
                return DatabaseService._row_to_customer(row)
            return None
    
    @staticmethod
    def get_customer_by_phone(phone: str) -> Optional[Customer]:
        """Get a customer by phone number"""
        with DatabaseService.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM customers WHERE phone = ?', (phone,))
            row = cursor.fetchone()
            if row:
                return DatabaseService._row_to_customer(row)
            return None
    
    @staticmethod
    def get_all_customers() -> List[Customer]:
        """Get all customers"""
        with DatabaseService.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM customers ORDER BY name')
            rows = cursor.fetchall()
            return [DatabaseService._row_to_customer(row) for row in rows]
    
    @staticmethod
    def update_customer(customer: Customer) -> bool:
        """Update customer information"""
        with DatabaseService.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE customers SET name=?, phone=?, email=?, address=?, 
                credit_limit=?, outstanding_balance=?, updated_at=CURRENT_TIMESTAMP
                WHERE id=?
            ''', (customer.name, customer.phone, customer.email, customer.address,
                  customer.credit_limit, customer.outstanding_balance, customer.id))
            conn.commit()
            return cursor.rowcount > 0
    
    @staticmethod
    def delete_customer(customer_id: int) -> bool:
        """Delete a customer by ID"""
        with DatabaseService.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM customers WHERE id = ?', (customer_id,))
            conn.commit()
            return cursor.rowcount > 0
            
    @staticmethod
    def get_new_customer_count(days: int = 30) -> int:
        """Count customers added in the last N days"""
        with DatabaseService.get_connection() as conn:
            cursor = conn.cursor()
            # SQLite CURRENT_TIMESTAMP is in UTC. created_at is also TIMESTAMP.
            cursor.execute("SELECT COUNT(*) FROM customers WHERE created_at >= datetime('now', ?)", (f'-{days} days',))
            return cursor.fetchone()[0] or 0

    @staticmethod
    def get_total_sales_count() -> int:
        """Get the total number of sales transactions across all customers"""
        with DatabaseService.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM sales")
            return cursor.fetchone()[0] or 0
    
    # Sale operations
    @staticmethod
    def create_sale(sale: Sale) -> int:
        """Create a new sale and its items"""
        with DatabaseService.get_connection() as conn:
            cursor = conn.cursor()
            
            # Insert the sale - store date as ISO string for consistent comparison
            cursor.execute('''
                INSERT INTO sales (date, total_amount, amount_paid, payment_method, customer_id, cashier_user, sync_status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (sale.date.isoformat() if sale.date else datetime.now().isoformat(), 
                   sale.total_amount, sale.amount_paid, sale.payment_method, sale.customer_id, sale.cashier_user, sale.sync_status))
            sale_id = cursor.lastrowid
            
            # Insert sale items
            for item in sale.items:
                # CRITICAL FIX #1: Check stock availability BEFORE deduction (prevents race condition)
                cursor.execute('SELECT quantity FROM products WHERE id = ?', (item.product_id,))
                stock_row = cursor.fetchone()
                if not stock_row or stock_row[0] < item.quantity:
                    conn.rollback()
                    raise ValueError(f"Insufficient stock for product ID {item.product_id}. Available: {stock_row[0] if stock_row else 0}, Required: {item.quantity}")
                
                cursor.execute('''
                    INSERT INTO sale_items (sale_id, product_id, quantity, unit_price, subtotal)
                    VALUES (?, ?, ?, ?, ?)
                ''', (sale_id, item.product_id, item.quantity, item.unit_price, item.subtotal))
                
                # Update product quantity with atomic check
                cursor.execute('''
                    UPDATE products SET quantity = quantity - ?, updated_at = CURRENT_TIMESTAMP 
                    WHERE id = ? AND quantity >= ?
                ''', (item.quantity, item.product_id, item.quantity))
                
                # Verify update succeeded
                if cursor.rowcount == 0:
                    conn.rollback()
                    raise ValueError(f"Stock depleted during transaction for product ID {item.product_id}")
                
                # Record stock movement
                cursor.execute('''
                    INSERT INTO stock_movements (product_id, type, quantity, reason, user)
                    VALUES (?, 'sale', ?, 'Sale', ?)
                ''', (item.product_id, -item.quantity, sale.cashier_user))
            
            # CRITICAL FIX #4: Update Customer Debt correctly for partial payments
            # Only add unpaid amount to balance, not total amount
            if sale.payment_method == 'credit' and sale.customer_id:
                # Calculate unpaid amount based on total vs paid
                unpaid_amount = sale.total_amount - sale.amount_paid
                if unpaid_amount > 0:
                    cursor.execute('''
                        UPDATE customers SET outstanding_balance = outstanding_balance + ?
                        WHERE id = ?
                    ''', (unpaid_amount, sale.customer_id))

            conn.commit()
            return sale_id
    
    @staticmethod
    def get_sale_by_id(sale_id: int) -> Optional[Sale]:
        """Get a sale by ID with its items"""
        with DatabaseService.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get the sale
            cursor.execute('SELECT * FROM sales WHERE id = ?', (sale_id,))
            sale_row = cursor.fetchone()
            if not sale_row:
                return None
            
            sale = DatabaseService._row_to_sale(sale_row)
            
            # Get sale items
            cursor.execute('''
                SELECT si.*, p.name as product_name
                FROM sale_items si
                JOIN products p ON si.product_id = p.id
                WHERE si.sale_id = ?
            ''', (sale_id,))
            item_rows = cursor.fetchall()
            sale.items = [DatabaseService._row_to_sale_item(row) for row in item_rows]
            
            return sale
    
    @staticmethod
    def get_sales_by_date_range(start_date: datetime, end_date: datetime) -> List[Sale]:
        """Get sales within a date range with their items"""
        with DatabaseService.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get sales - compare ISO strings directly since dates are stored as ISO strings
            cursor.execute('''
                SELECT * FROM sales 
                WHERE date BETWEEN ? AND ?
                ORDER BY date DESC
            ''', (start_date.isoformat(), end_date.isoformat()))
            sale_rows = cursor.fetchall()
            
            # Create sale objects
            sales = []
            for row in sale_rows:
                sale = DatabaseService._row_to_sale(row)
                
                # Get items for this sale
                cursor.execute('''
                    SELECT si.*, p.name as product_name
                    FROM sale_items si
                    JOIN products p ON si.product_id = p.id
                    WHERE si.sale_id = ?
                ''', (sale.id,))
                item_rows = cursor.fetchall()
                sale.items = [DatabaseService._row_to_sale_item(row) for row in item_rows]
                
                sales.append(sale)
            
            return sales

    @staticmethod
    def get_sales_by_customer_id(customer_id: int) -> List[Sale]:
        """Get all sales for a specific customer"""
        with DatabaseService.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM sales 
                WHERE customer_id = ?
                ORDER BY date DESC
            ''', (customer_id,))
            sale_rows = cursor.fetchall()
            
            sales = []
            for row in sale_rows:
                sale = DatabaseService._row_to_sale(row)
                # Get items
                cursor.execute('''
                    SELECT si.*, p.name as product_name
                    FROM sale_items si
                    JOIN products p ON si.product_id = p.id
                    WHERE si.sale_id = ?
                ''', (sale.id,))
                item_rows = cursor.fetchall()
                sale.items = [DatabaseService._row_to_sale_item(row) for row in item_rows]
                sales.append(sale)
            
            return sales
    
    @staticmethod
    def get_daily_sales_summary(date: datetime) -> dict:
        """Get daily sales summary for a specific date"""
        with DatabaseService.get_connection() as conn:
            cursor = conn.cursor()
            
            # Format date to match the database timestamp format for the day
            # Use date range comparison for better safety
            # Handle both datetime and date objects by extracting components
            start_of_day = datetime(date.year, date.month, date.day, 0, 0, 0, 0)
            end_of_day = datetime(date.year, date.month, date.day, 23, 59, 59, 999999)
            
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_transactions,
                    SUM(total_amount) as total_revenue
                FROM sales 
                WHERE date >= ? AND date <= ?
            ''', (start_of_day.isoformat(), end_of_day.isoformat()))
            row = cursor.fetchone()
            
            if row:
                return {
                    'total_transactions': row[0] or 0,
                    'total_revenue': row[1] or 0.0
                }
            return {'total_transactions': 0, 'total_revenue': 0.0}
    
    # Customer payment operations
    @staticmethod
    def create_customer_payment(payment: CustomerPayment) -> int:
        """Create a customer payment and update customer balance"""
        with DatabaseService.get_connection() as conn:
            cursor = conn.cursor()
            
            # Insert payment
            cursor.execute('''
                INSERT INTO customer_payments (customer_id, amount, date, payment_method, notes)
                VALUES (?, ?, ?, ?, ?)
            ''', (payment.customer_id, payment.amount, payment.date, payment.payment_method, payment.notes))
            payment_id = cursor.lastrowid
            
            # Update customer's outstanding balance
            cursor.execute('''
                UPDATE customers SET outstanding_balance = outstanding_balance - ?
                WHERE id = ?
            ''', (payment.amount, payment.customer_id))
            
            # Log activity
            # Fetch customer name for better log
            cursor.execute("SELECT name FROM customers WHERE id = ?", (payment.customer_id,))
            customer_name = cursor.fetchone()[0]
            
            DatabaseService.create_activity(
                'payment', 
                f"Payment received from {customer_name}: {payment.amount:.2f}",
                "system", # or passed user if available
                cursor
            )
            
            conn.commit()
            return payment_id

    @staticmethod
    def get_payments_by_customer_id(customer_id: int) -> List[CustomerPayment]:
        """Get all payments for a specific customer"""
        with DatabaseService.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM customer_payments 
                WHERE customer_id = ?
                ORDER BY date DESC
            ''', (customer_id,))
            rows = cursor.fetchall()
            return [CustomerPayment(
                id=row['id'],
                customer_id=row['customer_id'],
                amount=row['amount'],
                date=datetime.fromisoformat(row['date']) if row['date'] else None,
                payment_method=row['payment_method'],
                notes=row['notes']
            ) for row in rows]
            
    @staticmethod
    def get_customer_total_paid(customer_id: int) -> float:
        """Get total amount paid by a customer (Sales + Payments)"""
        with DatabaseService.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT SUM(amount) FROM customer_payments WHERE customer_id = ?", (customer_id,))
            payments_sum = cursor.fetchone()[0] or 0.0
            
            cursor.execute("SELECT SUM(amount_paid) FROM sales WHERE customer_id = ?", (customer_id,))
            sales_sum = cursor.fetchone()[0] or 0.0
            
            return payments_sum + sales_sum

    @staticmethod
    def get_top_customer_by_sales() -> Optional[tuple]:
        """Get the customer with the highest total sales amount"""
        with DatabaseService.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT c.name, SUM(s.total_amount) as total_sales, COUNT(s.id) as transaction_count
                FROM sales s
                JOIN customers c ON s.customer_id = c.id
                WHERE s.customer_id IS NOT NULL
                GROUP BY s.customer_id
                ORDER BY total_sales DESC
                LIMIT 1
            ''')
            return cursor.fetchone()
    
    # Settings operations
    @staticmethod
    def get_setting(key_name: str) -> Optional[Setting]:
        """Get a setting by key name"""
        with DatabaseService.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM settings WHERE key_name = ?', (key_name,))
            row = cursor.fetchone()
            if row:
                return DatabaseService._row_to_setting(row)
            return None
    
    @staticmethod
    def update_setting(key_name: str, value: str) -> bool:
        """Update a setting value"""
        with DatabaseService.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE settings SET value = ? WHERE key_name = ?', (value, key_name))
            conn.commit()
            return cursor.rowcount > 0
    
    @staticmethod
    def get_all_settings() -> List[Setting]:
        """Get all settings"""
        with DatabaseService.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM settings')
            rows = cursor.fetchall()
            return [DatabaseService._row_to_setting(row) for row in rows]
    
    # Category operations
    @staticmethod
    def create_category(category: 'Category') -> int:
        """Create a new category in the database"""
        with DatabaseService.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO categories (name, description)
                VALUES (?, ?)
            ''', (category.name, category.description))
            conn.commit()
            return cursor.lastrowid
    
    @staticmethod
    def get_category_by_id(category_id: int) -> Optional['Category']:
        """Get a category by its ID"""
        with DatabaseService.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM categories WHERE id = ?', (category_id,))
            row = cursor.fetchone()
            if row:
                return DatabaseService._row_to_category(row)
            return None
    
    @staticmethod
    def get_category_by_name(name: str) -> Optional['Category']:
        """Get a category by its name"""
        with DatabaseService.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM categories WHERE name = ?', (name,))
            row = cursor.fetchone()
            if row:
                return DatabaseService._row_to_category(row)
            return None
    
    @staticmethod
    def get_all_categories() -> List['Category']:
        """Get all categories from the database"""
        with DatabaseService.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM categories ORDER BY name')
            rows = cursor.fetchall()
            return [DatabaseService._row_to_category(row) for row in rows]
    
    @staticmethod
    def update_category(category: 'Category') -> bool:
        """Update an existing category"""
        with DatabaseService.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE categories SET name=?, description=?, updated_at=CURRENT_TIMESTAMP
                WHERE id=?
            ''', (category.name, category.description, category.id))
            conn.commit()
            return cursor.rowcount > 0
    
    @staticmethod
    def delete_category(category_id: int) -> bool:
        """Delete a category by ID"""
        with DatabaseService.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM categories WHERE id = ?', (category_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    # Restock history operations
    @staticmethod
    def create_restock_history(product_id: int, old_qty: float, added_qty: float, new_qty: float, record_type: str = 'Arrival') -> int:
        """Create a new restock history entry"""
        with DatabaseService.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO restock_history (product_id, old_qty, added_qty, new_qty, record_type)
                VALUES (?, ?, ?, ?, ?)
            ''', (product_id, old_qty, added_qty, new_qty, record_type))
            conn.commit()
            return cursor.lastrowid

    @staticmethod
    def get_restock_history(limit: int = 20) -> List[dict]:
        """Get the last N restock history entries with product names"""
        with DatabaseService.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT rh.*, p.name as product_name
                FROM restock_history rh
                JOIN products p ON rh.product_id = p.id
                ORDER BY rh.date DESC
                LIMIT ?
            ''', (limit,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    # Activity operations
    @staticmethod
    def create_activity(type: str, description: str, user: str, cursor=None) -> int:
        """Create a new activity log entry"""
        if cursor:
            cursor.execute('''
                INSERT INTO activities (type, description, user)
                VALUES (?, ?, ?)
            ''', (type, description, user))
            return cursor.lastrowid
        else:
            with DatabaseService.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO activities (type, description, user)
                    VALUES (?, ?, ?)
                ''', (type, description, user))
                conn.commit()
                return cursor.lastrowid

    @staticmethod
    def get_recent_activities(limit: int = 20) -> List[dict]:
        """Get the most recent activities"""
        with DatabaseService.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM activities 
                ORDER BY date DESC 
                LIMIT ?
            ''', (limit,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    # Utility methods to convert database rows to model objects
    @staticmethod
    def _row_to_category(row) -> 'Category':
        """Convert a database row to a Category object"""
        return Category(
            id=row['id'],
            name=row['name'],
            description=row['description'],
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
            updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None
        )
    
    # Utility methods to convert database rows to model objects
    @staticmethod
    def _row_to_product(row) -> Product:
        """Convert a database row to a Product object"""
        # Handle potentially missing columns for backward compatibility
        unit_type = row['unit_type'] if 'unit_type' in row.keys() else 'pieces'
        reorder_level = row['reorder_level'] if 'reorder_level' in row.keys() else 0
        supplier = row['supplier'] if 'supplier' in row.keys() else None
        notes = row['notes'] if 'notes' in row.keys() else None
        expiry_date = row['expiry_date'] if 'expiry_date' in row.keys() and row['expiry_date'] else None
        batch_number = row['batch_number'] if 'batch_number' in row.keys() else None
        created_at = row['created_at'] if 'created_at' in row.keys() and row['created_at'] else None
        updated_at = row['updated_at'] if 'updated_at' in row.keys() and row['updated_at'] else None
        
        return Product(
            id=row['id'],
            name=row['name'],
            sku=row['sku'],
            category=row['category'] if 'category' in row.keys() else None,
            unit_type=unit_type,  # Default to 'pieces' if column doesn't exist
            quantity=row['quantity'],
            cost_price=row['cost_price'],
            selling_price=row['selling_price'],
            reorder_level=reorder_level,  # Default to 0 if column doesn't exist
            supplier=supplier,  # Default to None if column doesn't exist
            notes=notes, # Default to None if column doesn't exist
            expiry_date=datetime.fromisoformat(expiry_date) if expiry_date else None,
            batch_number=batch_number,
            created_at=datetime.fromisoformat(created_at) if created_at else None,
            updated_at=datetime.fromisoformat(updated_at) if updated_at else None
        )
    
    @staticmethod
    def _row_to_user(row) -> User:
        """Convert a database row to a User object"""
        return User(
            id=row['id'],
            username=row['username'],
            password_hash=row['password_hash'],
            role=row['role'],
            full_name=row['full_name'],
            pin_hash=row['pin_hash'],
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
            updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None
        )
    
    @staticmethod
    def _row_to_customer(row) -> Customer:
        """Convert a database row to a Customer object"""
        return Customer(
            id=row['id'],
            name=row['name'],
            phone=row['phone'],
            email=row['email'],
            address=row['address'],
            credit_limit=row['credit_limit'],
            outstanding_balance=row['outstanding_balance'],
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
            updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None
        )
    
    @staticmethod
    def _row_to_sale(row) -> Sale:
        """Convert a database row to a Sale object"""
        # Handle amount_paid if it exists in row (for backward compatibility)
        amount_paid = row['amount_paid'] if 'amount_paid' in row.keys() else 0.0
        sync_status = row['sync_status'] if 'sync_status' in row.keys() else "pending"
        
        return Sale(
            id=row['id'],
            date=datetime.fromisoformat(row['date']) if row['date'] else None,
            total_amount=row['total_amount'],
            amount_paid=amount_paid,
            payment_method=row['payment_method'],
            customer_id=row['customer_id'],
            cashier_user=row['cashier_user'],
            sync_status=sync_status
        )
    
    @staticmethod
    def _row_to_sale_item(row) -> SaleItem:
        """Convert a database row to a SaleItem object"""
        return SaleItem(
            id=row['id'],
            sale_id=row['sale_id'],
            product_id=row['product_id'],
            product_name=row['product_name'] if 'product_name' in row.keys() else '',
            quantity=row['quantity'],
            unit_price=row['unit_price'],
            subtotal=row['subtotal']
        )
    
    @staticmethod
    def _row_to_setting(row) -> Setting:
        """Convert a database row to a Setting object"""
        return Setting(
            id=row['id'],
            key_name=row['key_name'],
            value=row['value'],
            description=row['description']
        )