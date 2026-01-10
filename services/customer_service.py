from typing import List, Optional
from datetime import datetime
from database.database import DatabaseService
from database.models import Customer, CustomerPayment

class CustomerService:
    """Service for customer management operations"""
    
    @staticmethod
    def add_customer(customer_data: dict) -> int:
        """Add a new customer (alias for create_customer)"""
        return CustomerService.create_customer(customer_data)
    
    @staticmethod
    def create_customer(customer_data: dict) -> int:
        """Create a new customer"""
        customer = Customer(
            name=customer_data['name'],
            phone=customer_data['phone'],
            email=customer_data['email'],
            address=customer_data['address'],
            credit_limit=customer_data['credit_limit'],
            outstanding_balance=0.0  # New customers start with 0 balance
        )
        return DatabaseService.create_customer(customer)
    
    @staticmethod
    def update_customer(customer_data: dict) -> bool:
        """Update an existing customer"""
        # Use the existing outstanding balance if not provided in the update
        outstanding_balance = customer_data.get('outstanding_balance', 0.0)
        
        customer = Customer(
            id=customer_data['id'],
            name=customer_data['name'],
            phone=customer_data['phone'],
            email=customer_data['email'],
            address=customer_data['address'],
            credit_limit=customer_data['credit_limit'],
            outstanding_balance=outstanding_balance
        )
        return DatabaseService.update_customer(customer)
    
    @staticmethod
    def get_customer_by_id(customer_id: int) -> Optional[dict]:
        """Get a customer by ID"""
        customer = DatabaseService.get_customer_by_id(customer_id)
        if customer:
            return {
                'id': customer.id,
                'name': customer.name,
                'phone': customer.phone,
                'email': customer.email,
                'address': customer.address,
                'credit_limit': customer.credit_limit,
                'outstanding_balance': customer.outstanding_balance,
                'available_credit': customer.available_credit,
                'created_at': customer.created_at.isoformat() if customer.created_at else None,
                'updated_at': customer.updated_at.isoformat() if customer.updated_at else None
            }
        return None
    
    @staticmethod
    def get_customer_by_phone(phone: str) -> Optional[dict]:
        """Get a customer by phone number"""
        customer = DatabaseService.get_customer_by_phone(phone)
        if customer:
            return {
                'id': customer.id,
                'name': customer.name,
                'phone': customer.phone,
                'email': customer.email,
                'address': customer.address,
                'credit_limit': customer.credit_limit,
                'outstanding_balance': customer.outstanding_balance,
                'available_credit': customer.available_credit,
                'created_at': customer.created_at.isoformat() if customer.created_at else None,
                'updated_at': customer.updated_at.isoformat() if customer.updated_at else None
            }
        return None
    
    @staticmethod
    def get_all_customers() -> List[dict]:
        """Get all customers"""
        customers = DatabaseService.get_all_customers()
        return [
            {
                'id': c.id,
                'name': c.name,
                'phone': c.phone,
                'email': c.email,
                'address': c.address,
                'credit_limit': c.credit_limit,
                'outstanding_balance': c.outstanding_balance,
                'available_credit': c.available_credit,
                'created_at': c.created_at.isoformat() if c.created_at else None,
                'updated_at': c.updated_at.isoformat() if c.updated_at else None
            }
            for c in customers
        ]
    
    @staticmethod
    def search_customers(query: str) -> List[dict]:
        """Search customers by name or phone"""
        # For now, we'll just return all customers
        # In a real implementation, we would search by name or phone
        all_customers = CustomerService.get_all_customers()
        return [
            c for c in all_customers
            if query.lower() in c['name'].lower() or (c['phone'] and query in c['phone'])
        ]
    
    @staticmethod
    def add_customer_payment(payment_data: dict) -> int:
        """Add a payment from a customer"""
        payment = CustomerPayment(
            customer_id=payment_data['customer_id'],
            amount=payment_data['amount'],
            date=datetime.fromisoformat(payment_data['date']) if payment_data.get('date') else datetime.now(),
            payment_method=payment_data['payment_method'],
            notes=payment_data.get('notes', '')
        )
        return DatabaseService.create_customer_payment(payment)

    @staticmethod
    def get_customer_payments(customer_id: int) -> List[dict]:
        """Get all payments for a specific customer"""
        payments = DatabaseService.get_payments_by_customer_id(customer_id)
        return [
            {
                'id': p.id,
                'customer_id': p.customer_id,
                'amount': p.amount,
                'date': p.date.isoformat() if p.date else None,
                'payment_method': p.payment_method,
                'notes': p.notes
            }
            for p in payments
        ]
    
    @staticmethod
    def get_customer_outstanding_balance(customer_id: int) -> float:
        """Get the outstanding balance for a customer"""
        customer = DatabaseService.get_customer_by_id(customer_id)
        if customer:
            return customer.outstanding_balance
        return 0.0
        
    @staticmethod
    def get_total_paid(customer_id: int) -> float:
        """Get total amount paid by a customer"""
        return DatabaseService.get_customer_total_paid(customer_id)
        
    @staticmethod
    def get_overdue_customers() -> List[dict]:
        """Get customers with overdue payments (outstanding balance > credit limit)"""
        customers = CustomerService.get_all_customers()
        return [
            c for c in customers
            if c['outstanding_balance'] > c['credit_limit'] and c['credit_limit'] > 0
        ]
    
    @staticmethod
    def delete_customer(customer_id: int) -> bool:
        """Delete a customer by ID"""
        return DatabaseService.delete_customer(customer_id)
        
    @staticmethod
    def get_top_customer() -> Optional[dict]:
        """Get the customer with the highest total sales"""
        result = DatabaseService.get_top_customer_by_sales()
        if result:
            return {
                'name': result[0], 
                'total_sales': result[1],
                'transaction_count': result[2]
            }
        return None
        
    @staticmethod
    def get_new_customer_count(days: int = 30) -> dict:
        """Get the count of new customers created in the last N days"""
        count = DatabaseService.get_new_customer_count(days)
        return {'count': count}

    @staticmethod
    def get_total_sales_count() -> dict:
        """Get the total number of sales transactions"""
        count = DatabaseService.get_total_sales_count()
        return {'count': count}
    
    @staticmethod
    def get_credit_utilization(customers: List[dict]) -> List[dict]:
        """Get credit utilization for customers"""
        utilization = []
        for customer in customers:
            if customer['credit_limit'] > 0:
                utilization_percent = (customer['outstanding_balance'] / customer['credit_limit']) * 100
                utilization.append({
                    'id': customer['id'],
                    'name': customer['name'],
                    'credit_limit': customer['credit_limit'],
                    'outstanding_balance': customer['outstanding_balance'],
                    'utilization_percent': utilization_percent
                })
        return utilization