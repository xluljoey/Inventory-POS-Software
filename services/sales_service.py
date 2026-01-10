from typing import List, Optional
from datetime import datetime
from loguru import logger
from database.database import DatabaseService
from database.models import Sale, SaleItem, CustomerPayment

class SalesService:
    """Service for sales and POS operations"""
    
    @staticmethod
    def create_sale(sale_data: dict) -> int:
        """Create a new sale"""
        # CRITICAL FIX #4: Calculate unpaid amount for partial payments
        amount_paid = sale_data.get('amount_paid', 0.0)
        total_amount = sale_data['total_amount']
        # unpaid_amount calculation moved to DatabaseService for atomicity
        
        # Prepare sale object with adjusted amount for credit balance
        sale = Sale(
            date=datetime.fromisoformat(sale_data['date']) if sale_data.get('date') else datetime.now(),
            total_amount=total_amount, # Store full sale value
            amount_paid=amount_paid,   # Store amount paid
            payment_method=sale_data['payment_method'],
            customer_id=sale_data.get('customer_id'),
            cashier_user=sale_data['cashier_user']
        )
        
        # Add items to the sale
        for item_data in sale_data['items']:
            item = SaleItem(
                product_id=item_data['product_id'],
                product_name=item_data['product_name'],
                quantity=item_data['quantity'],
                unit_price=item_data['unit_price'],
                subtotal=item_data['subtotal']
            )
            sale.items.append(item)
        
        sale_id = DatabaseService.create_sale(sale)
        if sale_id:
            logger.info(f"Sale completed: ID #{sale_id} | Total: {sale.total_amount} | Cashier: {sale.cashier_user}")

        # Handle partial payment for credit sales
        if sale.payment_method == 'credit' and sale.customer_id:
            amount_paid = sale_data.get('amount_paid', 0.0)
            if amount_paid > 0:
                payment = CustomerPayment(
                    customer_id=sale.customer_id,
                    amount=amount_paid,
                    date=sale.date,
                    payment_method='Cash',  # Assumed cash for partial payment
                    notes=f'Partial payment for Sale #{sale_id}'
                )
                DatabaseService.create_customer_payment(payment)
        
        return sale_id
    
    @staticmethod
    def get_sale_by_id(sale_id: int) -> Optional[dict]:
        """Get a sale by ID"""
        sale = DatabaseService.get_sale_by_id(sale_id)
        if sale:
            return {
                'id': sale.id,
                'date': sale.date.isoformat() if sale.date else None,
                'total_amount': sale.total_amount,
                'payment_method': sale.payment_method,
                'customer_id': sale.customer_id,
                'cashier_user': sale.cashier_user,
                'items': [
                    {
                        'id': item.id,
                        'sale_id': item.sale_id,
                        'product_id': item.product_id,
                        'product_name': item.product_name,
                        'quantity': item.quantity,
                        'unit_price': item.unit_price,
                        'subtotal': item.subtotal
                    }
                    for item in sale.items
                ]
            }
        return None
    
    @staticmethod
    def get_sales_by_date_range(start_date: datetime, end_date: datetime) -> List[dict]:
        """Get sales within a date range"""
        sales = DatabaseService.get_sales_by_date_range(start_date, end_date)
        return [
            {
                'id': sale.id,
                'date': sale.date.isoformat() if sale.date else None,
                'total_amount': sale.total_amount,
                'amount_paid': sale.amount_paid,
                'payment_method': sale.payment_method,
                'customer_id': sale.customer_id,
                'cashier_user': sale.cashier_user,
                'items': [
                    {
                        'id': item.id,
                        'sale_id': item.sale_id,
                        'product_id': item.product_id,
                        'product_name': item.product_name,
                        'quantity': item.quantity,
                        'unit_price': item.unit_price,
                        'subtotal': item.subtotal
                    }
                    for item in sale.items
                ]
            }
            for sale in sales
        ]

    @staticmethod
    def get_sales_by_customer(customer_id: int) -> List[dict]:
        """Get all sales for a specific customer"""
        sales = DatabaseService.get_sales_by_customer_id(customer_id)
        return [
            {
                'id': sale.id,
                'date': sale.date.isoformat() if sale.date else None,
                'total_amount': sale.total_amount,
                'amount_paid': sale.amount_paid,
                'payment_method': sale.payment_method,
                'customer_id': sale.customer_id,
                'cashier_user': sale.cashier_user,
                'items': [
                    {
                        'id': item.id,
                        'sale_id': item.sale_id,
                        'product_id': item.product_id,
                        'product_name': item.product_name,
                        'quantity': item.quantity,
                        'unit_price': item.unit_price,
                        'subtotal': item.subtotal
                    }
                    for item in sale.items
                ]
            }
            for sale in sales
        ]
    
    @staticmethod
    def get_daily_sales_summary(date: datetime) -> dict:
        """Get daily sales summary for a specific date"""
        return DatabaseService.get_daily_sales_summary(date)
    
    @staticmethod
    def get_total_daily_sales(date: datetime) -> float:
        """Get total sales amount for a specific date"""
        summary = DatabaseService.get_daily_sales_summary(date)
        return summary.get('total_revenue', 0.0)
    
    @staticmethod
    def get_daily_transaction_count(date: datetime) -> int:
        """Get number of transactions for a specific date"""
        summary = DatabaseService.get_daily_sales_summary(date)
        return summary.get('total_transactions', 0)
    
    @staticmethod
    def calculate_change(tendered_amount: float, total_amount: float) -> float:
        """Calculate change to give to customer"""
        return tendered_amount - total_amount
    
    @staticmethod
    def get_recent_sales(limit: int = 10) -> List[dict]:
        """Get recent sales ordered by date"""
        from datetime import datetime, timedelta
        from services.customer_service import CustomerService
        
        # Calculate date range for recent sales (last 7 days)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        # Get all sales in the date range
        all_sales = SalesService.get_sales_by_date_range(start_date, end_date)
        
        # Sort by date (most recent first) and limit results
        sorted_sales = sorted(all_sales, key=lambda x: x['date'], reverse=True)
        recent_sales = sorted_sales[:limit]
        
        # Add customer names to each sale
        for sale in recent_sales:
            if sale.get('customer_id'):
                customer = CustomerService.get_customer_by_id(sale['customer_id'])
                if customer:
                    sale['customer_name'] = customer['name']
                else:
                    sale['customer_name'] = 'Unknown'
            else:
                sale['customer_name'] = 'Walk-in Customer'
        
        return recent_sales
    
    @staticmethod
    def process_payment(sale_data: dict) -> int:
        """Process a payment and create a sale"""
        # Validate that we have enough stock for all items
        for item in sale_data['items']:
            product = DatabaseService.get_product_by_id(item['product_id'])
            if not product or product.quantity < item['quantity']:
                raise ValueError(f"Insufficient stock for product: {item['product_name']}")
        
        # Create the sale
        return SalesService.create_sale(sale_data)