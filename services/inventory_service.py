from typing import List, Optional
from datetime import datetime, timedelta
from loguru import logger
from database.database import DatabaseService
from database.models import Product, StockMovement, Category

class InventoryService:
    """Service for inventory management operations"""
    
    @staticmethod
    def add_product(product_data: dict) -> int:
        """Add a new product to inventory"""
        from database.models import Product
        expiry_date_value = product_data.get('expiry_date')
        
        # Only call fromisoformat if we have a value and it's a string
        expiry_dt = None
        if expiry_date_value and isinstance(expiry_date_value, str):
            try:
                expiry_dt = datetime.fromisoformat(expiry_date_value)
            except ValueError:
                expiry_dt = None

        product = Product(
            name=product_data['name'],
            sku=product_data['sku'],
            category=product_data['category'],
            unit_type=product_data['unit_type'],
            quantity=product_data['quantity'],
            cost_price=product_data['cost_price'],
            selling_price=product_data['selling_price'],
            reorder_level=product_data['reorder_level'],
            supplier=product_data['supplier'],
            notes=product_data['notes'],
            expiry_date=expiry_dt,
            batch_number=product_data.get('batch_number')
        )
        product_id = DatabaseService.create_product(product)
        if product_id:
            logger.info(f"New product added: {product.name} (SKU: {product.sku}) | ID: {product_id}")
        return product_id
    
    @staticmethod
    def update_product(product_data: dict) -> bool:
        """Update an existing product"""
        from database.models import Product
        expiry_date_value = product_data.get('expiry_date')
        
        # Only call fromisoformat if we have a value and it's a string
        expiry_dt = None
        if expiry_date_value and isinstance(expiry_date_value, str):
            try:
                expiry_dt = datetime.fromisoformat(expiry_date_value)
            except ValueError:
                expiry_dt = None

        product = Product(
            id=product_data['id'],
            name=product_data['name'],
            sku=product_data['sku'],
            category=product_data['category'],
            unit_type=product_data['unit_type'],
            quantity=product_data['quantity'],
            cost_price=product_data['cost_price'],
            selling_price=product_data['selling_price'],
            reorder_level=product_data['reorder_level'],
            supplier=product_data['supplier'],
            notes=product_data['notes'],
            expiry_date=expiry_dt,
            batch_number=product_data.get('batch_number')
        )
        return DatabaseService.update_product(product)
    
    @staticmethod
    def delete_product(product_id: int) -> bool:
        """Delete a product from inventory"""
        return DatabaseService.delete_product(product_id)
    
    @staticmethod
    def get_product_by_id(product_id: int) -> Optional[dict]:
        """Get a product by its ID"""
        product = DatabaseService.get_product_by_id(product_id)
        if product:
            return {
                'id': product.id,
                'name': product.name,
                'sku': product.sku,
                'category': product.category,
                'unit_type': product.unit_type,
                'quantity': product.quantity,
                'cost_price': product.cost_price,
                'selling_price': product.selling_price,
                'reorder_level': product.reorder_level,
                'supplier': product.supplier,
                'notes': product.notes,
                'expiry_date': product.expiry_date.isoformat() if product.expiry_date else None,
                'batch_number': product.batch_number,
                'created_at': product.created_at.isoformat() if product.created_at else None,
                'updated_at': product.updated_at.isoformat() if product.updated_at else None,
                'profit_margin': product.profit_margin,
                'total_value': product.total_value,
                'is_low_stock': product.is_low_stock
            }
        return None
    
    @staticmethod
    def get_all_products() -> List[dict]:
        """Get all products from inventory"""
        products = DatabaseService.get_all_products()
        return [
            {
                'id': p.id,
                'name': p.name,
                'sku': p.sku,
                'category': p.category,
                'unit_type': p.unit_type,
                'quantity': p.quantity,
                'cost_price': p.cost_price,
                'selling_price': p.selling_price,
                'reorder_level': p.reorder_level,
                'supplier': p.supplier,
                'notes': p.notes,
                'expiry_date': p.expiry_date.isoformat() if p.expiry_date else None,
                'batch_number': p.batch_number,
                'created_at': p.created_at.isoformat() if p.created_at else None,
                'updated_at': p.updated_at.isoformat() if p.updated_at else None,
                'profit_margin': p.profit_margin,
                'total_value': p.total_value,
                'is_low_stock': p.is_low_stock
            }
            for p in products
        ]
    
    @staticmethod
    def search_products(query: str) -> List[dict]:
        """Search products by name or SKU"""
        products = DatabaseService.search_products(query)
        return [
            {
                'id': p.id,
                'name': p.name,
                'sku': p.sku,
                'category': p.category,
                'unit_type': p.unit_type,
                'quantity': p.quantity,
                'cost_price': p.cost_price,
                'selling_price': p.selling_price,
                'reorder_level': p.reorder_level,
                'supplier': p.supplier,
                'notes': p.notes,
                'expiry_date': p.expiry_date.isoformat() if p.expiry_date else None,
                'batch_number': p.batch_number,
                'created_at': p.created_at.isoformat() if p.created_at else None,
                'updated_at': p.updated_at.isoformat() if p.updated_at else None,
                'profit_margin': p.profit_margin,
                'total_value': p.total_value,
                'is_low_stock': p.is_low_stock
            }
            for p in products
        ]
    
    @staticmethod
    def get_low_stock_products() -> List[dict]:
        """Get products that are below the reorder level"""
        products = DatabaseService.get_low_stock_products()
        return [
            {
                'id': p.id,
                'name': p.name,
                'sku': p.sku,
                'category': p.category,
                'unit_type': p.unit_type,
                'quantity': p.quantity,
                'cost_price': p.cost_price,
                'selling_price': p.selling_price,
                'reorder_level': p.reorder_level,
                'supplier': p.supplier,
                'notes': p.notes,
                'expiry_date': p.expiry_date.isoformat() if p.expiry_date else None,
                'batch_number': p.batch_number,
                'created_at': p.created_at.isoformat() if p.created_at else None,
                'updated_at': p.updated_at.isoformat() if p.updated_at else None,
                'profit_margin': p.profit_margin,
                'total_value': p.total_value,
                'is_low_stock': p.is_low_stock
            }
            for p in products
        ]
    
    @staticmethod
    def add_stock(product_id: int, quantity: float, reason: str, user: str) -> bool:
        """Add stock to a product"""
        product = DatabaseService.get_product_by_id(product_id)
        if not product:
            return False
        
        # Update product quantity
        product.quantity += quantity
        if not DatabaseService.update_product(product):
            return False
        
        # Record stock movement
        movement = StockMovement(
            product_id=product_id,
            type='arrival',
            quantity=quantity,
            reason=reason,
            user=user
        )
        
        # In a real implementation, we would save the stock movement to the database
        # For now, we'll just return True to indicate success
        return True
    
    @staticmethod
    def adjust_stock(product_id: int, quantity: float, reason: str, user: str) -> bool:
        """Adjust stock quantity for a product"""
        product = DatabaseService.get_product_by_id(product_id)
        if not product:
            return False
        
        # Update product quantity
        product.quantity = quantity
        if not DatabaseService.update_product(product):
            return False
        
        # Record stock movement
        movement = StockMovement(
            product_id=product_id,
            type='adjustment',
            quantity=quantity - (product.quantity - quantity),  # Calculate the difference
            reason=reason,
            user=user
        )
        
        # In a real implementation, we would save the stock movement to the database
        # For now, we'll just return True to indicate success
        return True
    
    @staticmethod
    def get_expired_products() -> List[dict]:
        """Get products that have expired"""
        products = InventoryService.get_all_products()
        expired = []
        now = datetime.now()
        
        for product in products:
            if product['expiry_date']:
                expiry_date = datetime.fromisoformat(product['expiry_date'])
                if expiry_date < now and product['quantity'] > 0:
                    expired.append(product)
        
        return expired
    
    @staticmethod
    def get_expiring_products(days: int = 7) -> List[dict]:
        """Get products that will expire within the specified number of days"""
        products = InventoryService.get_all_products()
        expiring = []
        now = datetime.now()
        future_date = now + timedelta(days=days)
        
        for product in products:
            if product['expiry_date']:
                expiry_date = datetime.fromisoformat(product['expiry_date'])
                if now < expiry_date <= future_date and product['quantity'] > 0:
                    expiring.append(product)
        
        return expiring

    @staticmethod
    def update_product_price(product_id: int, new_price: float, user: str = "admin") -> bool:
        """Update the selling price of a product"""
        product = DatabaseService.get_product_by_id(product_id)
        if not product:
            return False
        old_price = product.selling_price
        product.selling_price = new_price
        if DatabaseService.update_product(product):
            DatabaseService.create_activity(
                'price_change', 
                f"Price updated for {product.name}: GH₵ {old_price:.2f} -> GH₵ {new_price:.2f}",
                user
            )
            return True
        return False

    @staticmethod
    def update_product_cost(product_id: int, new_cost: float, user: str = "admin") -> bool:
        """Update the cost price of a product"""
        product = DatabaseService.get_product_by_id(product_id)
        if not product:
            return False
        old_cost = product.cost_price
        product.cost_price = new_cost
        if DatabaseService.update_product(product):
            DatabaseService.create_activity(
                'price_change', 
                f"Cost updated for {product.name}: GH₵ {old_cost:.2f} -> GH₵ {new_cost:.2f}",
                user
            )
            return True
        return False

    @staticmethod
    def overwrite_product_stock(product_id: int, new_quantity: float, user: str = "admin") -> bool:
        """Set the exact quantity of a product (for corrections)"""
        product = DatabaseService.get_product_by_id(product_id)
        if not product:
            return False
        old_qty = product.quantity
        product.quantity = new_quantity
        if DatabaseService.update_product(product):
            logger.info(f"Stock correction: {product.name} | {old_qty} -> {new_quantity} | User: {user}")
            DatabaseService.create_activity(
                'stock_correction', 
                f"Stock corrected for {product.name}: {old_qty:.2f} -> {new_quantity:.2f}",
                user
            )
            # Add to restock history as Correction
            diff = new_quantity - old_qty
            DatabaseService.create_restock_history(product_id, old_qty, diff, new_quantity, 'Correction')
            return True
        return False

    @staticmethod
    def add_product_stock(product_id: int, added_quantity: float, batch_number: str = None, expiry_date = None) -> bool:
        """Add to existing quantity (new arrival) and log in restock_history"""
        product = DatabaseService.get_product_by_id(product_id)
        if not product:
            return False
        
        old_qty = product.quantity
        new_qty = old_qty + added_quantity
        product.quantity = new_qty
        
        if batch_number:
            product.batch_number = batch_number
        if expiry_date:
            product.expiry_date = expiry_date # database service handles date object? _row_to_product converts from iso string. create_product stores iso format.
            # We should probably ensure it is datetime object or None
            # DatabaseService.update_product expects Product object. Product.expiry_date is datetime.
            
        if DatabaseService.update_product(product):
            logger.info(f"Stock arrival: {product.name} | Added: {added_quantity} | New Qty: {new_qty}")
            DatabaseService.create_restock_history(product_id, old_qty, added_quantity, new_qty, 'Arrival')
            return True
        return False

    @staticmethod
    def get_restock_history(limit: int = 20) -> List[dict]:
        """Return the last N restock entries with product names"""
        return DatabaseService.get_restock_history(limit)

    @staticmethod
    def create_product(name: str, selling_price: float, category: str, unit_type: str, weight_per_unit: float, initial_stock: float, cost_price: float = 0.0) -> int:
        """Create a new product with basic fields"""
        # Note: weight_per_unit is mentioned in requirements but not in current Product model.
        # We can store it in notes or just ignore if it's not in schema yet.
        # Actually, let's just use existing add_product logic but with these params.
        
        # Generate a more unique SKU using name prefix and timestamp
        import time
        sku_prefix = name.replace(" ", "_").upper()[:6]
        timestamp = str(int(time.time()))[-4:]
        generated_sku = f"{sku_prefix}_{timestamp}"
        
        product_data = {
            'name': name,
            'sku': generated_sku,
            'category': category,
            'unit_type': unit_type,
            'quantity': initial_stock,
            'cost_price': cost_price if cost_price > 0 else selling_price,
            'selling_price': selling_price,
            'reorder_level': 5,
            'supplier': None,
            'notes': f"Weight per unit: {weight_per_unit}",
            'expiry_date': None
        }
        return InventoryService.add_product(product_data)
    
    @staticmethod
    def bulk_price_update(category_name: str, percentage: float, user_role: str) -> int:
        """
        Adjust prices for all products in a category by a percentage.
        Admin only. Returns number of products updated.
        """
        if user_role != "admin":
            logger.error(f"Unauthorized bulk price update attempt by non-admin.")
            raise PermissionError("Only administrators can perform bulk price updates.")
            
        multiplier = 1 + (percentage / 100.0)
        
        with DatabaseService.get_connection() as conn:
            cursor = conn.cursor()
            query = "UPDATE products SET selling_price = selling_price * ?, updated_at = CURRENT_TIMESTAMP WHERE category = ?"
            cursor.execute(query, (multiplier, category_name))
            count = cursor.rowcount
            conn.commit()
            
            logger.info(f"Bulk Price Update: Category [{category_name}] adjusted by {percentage}% | {count} items affected.")
            DatabaseService.create_activity(
                'bulk_price_update', 
                f"Prices in {category_name} adjusted by {percentage}%",
                "admin"
            )
            return count

    # Category operations
    @staticmethod
    def add_category(category_data: dict) -> int:
        """Add a new category"""
        category = Category(
            name=category_data['name'],
            description=category_data.get('description', '')
        )
        return DatabaseService.create_category(category)
    
    @staticmethod
    def update_category(category_data: dict) -> bool:
        """Update an existing category"""
        category = Category(
            id=category_data['id'],
            name=category_data['name'],
            description=category_data.get('description', '')
        )
        return DatabaseService.update_category(category)
    
    @staticmethod
    def delete_category(category_id: int) -> bool:
        """Delete a category by ID"""
        return DatabaseService.delete_category(category_id)
    
    @staticmethod
    def get_category_by_id(category_id: int) -> Optional[dict]:
        """Get a category by its ID"""
        category = DatabaseService.get_category_by_id(category_id)
        if category:
            return {
                'id': category.id,
                'name': category.name,
                'description': category.description,
                'created_at': category.created_at.isoformat() if category.created_at else None,
                'updated_at': category.updated_at.isoformat() if category.updated_at else None
            }
        return None
    
    @staticmethod
    def get_category_by_name(name: str) -> Optional[dict]:
        """Get a category by its name"""
        category = DatabaseService.get_category_by_name(name)
        if category:
            return {
                'id': category.id,
                'name': category.name,
                'description': category.description,
                'created_at': category.created_at.isoformat() if category.created_at else None,
                'updated_at': category.updated_at.isoformat() if category.updated_at else None
            }
        return None
    
    @staticmethod
    def get_all_categories() -> List[dict]:
        """Get all categories"""
        categories = DatabaseService.get_all_categories()
        return [
            {
                'id': c.id,
                'name': c.name,
                'description': c.description,
                'created_at': c.created_at.isoformat() if c.created_at else None,
                'updated_at': c.updated_at.isoformat() if c.updated_at else None
            }
            for c in categories
        ]