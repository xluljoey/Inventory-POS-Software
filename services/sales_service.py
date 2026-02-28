from typing import List, Optional
from datetime import datetime, timedelta
from loguru import logger
from database.database import DatabaseService
from database.models import Sale, SaleItem, CustomerPayment
from services.customer_service import CustomerService # SPRINT FIX: Import CustomerService
from config.app_config import AppConfig # Added

class SalesService:
    """Service for sales and POS operations"""
    
    @staticmethod
    def get_currency_symbol(): # Added method
        return AppConfig.get_setting("currency_symbol", AppConfig.CURRENCY_SYMBOL)

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

        # The logic to handle outstanding balance update is now in DatabaseService.create_sale
        # and partial payments are handled there by calculating unpaid_amount.
        # No need to create a separate CustomerPayment here for the 'amount_paid' part of a credit sale.
        
        return sale_id
    
    @staticmethod
    def process_payment(sale_data: dict) -> int:
        """Process a payment and create a sale, including credit limit checks."""
        # Validate that we have enough stock for all items
        for item in sale_data['items']:
            product = DatabaseService.get_product_by_id(item['product_id'])
            if not product or product.quantity < item['quantity']:
                raise ValueError(f"Insufficient stock for product: {item['product_name']}")
        
        # SPRINT FIX: Credit limit check for credit sales
        if sale_data['payment_method'] == 'credit':
            customer_id = sale_data.get('customer_id')
            if not customer_id:
                raise ValueError("Credit sale requires a customer.")
            
            customer = CustomerService.get_customer_by_id(customer_id)
            if not customer:
                raise ValueError(f"Customer with ID {customer_id} not found.")
            
            total_sale_amount = sale_data['total_amount']
            amount_paid_now = sale_data.get('amount_paid', 0.0)
            amount_to_add_to_credit = total_sale_amount - amount_paid_now

            new_outstanding_balance = customer['outstanding_balance'] + amount_to_add_to_credit
            
            if new_outstanding_balance > customer['credit_limit']:
                raise ValueError(
                    f"Credit limit exceeded for {customer['name']}. "
                    f"Available credit: {SalesService.get_currency_symbol()}{customer['available_credit']:.2f}, "
                    f"Sale amount: {SalesService.get_currency_symbol()}{total_sale_amount:.2f}, "
                    f"New outstanding: {SalesService.get_currency_symbol()}{new_outstanding_balance:.2f}."
                )
        
        # Create the sale
        return SalesService.create_sale(sale_data)

    @staticmethod
    def get_sales_by_customer(customer_id: int) -> List[dict]:
        """Get all sales for a specific customer"""
        return DatabaseService.get_sales_by_customer_id(customer_id)

    @staticmethod
    def get_recent_sales(days: int = 30) -> List[dict]:
        """Get sales from the last N days."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # DatabaseService.get_sales_by_date_range now returns dictionaries
        sales = DatabaseService.get_sales_by_date_range(start_date, end_date)
        
        # Add customer_name to each sale dictionary if customer_id is present
        result = []
        for sale_dict in sales: # 'sale_dict' is already a dictionary
            if sale_dict.get('customer_id'):
                customer = DatabaseService.get_customer_by_id(sale_dict['customer_id']) # Returns Customer object
                if customer:
                    sale_dict['customer_name'] = customer.name # Access attribute directly
            result.append(sale_dict)
        return result