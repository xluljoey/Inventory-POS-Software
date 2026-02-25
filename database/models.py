from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List

@dataclass
class Product:
    """Product model representing an inventory item"""
    id: Optional[int] = None
    name: str = ""
    sku: str = ""
    category: Optional[str] = None
    unit_type: str = "pieces"  # pieces, kg, liters, boxes, etc.
    quantity: float = 0.0
    cost_price: float = 0.0
    selling_price: float = 0.0
    reorder_level: int = 0
    supplier: Optional[str] = None
    notes: Optional[str] = None
    expiry_date: Optional[datetime] = None
    batch_number: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @property
    def profit_margin(self) -> float:
        """Calculate profit margin as a percentage"""
        if self.cost_price == 0:
            return 0.0
        return ((self.selling_price - self.cost_price) / self.cost_price) * 100
    
    @property
    def total_value(self) -> float:
        """Calculate total value of inventory for this product"""
        return self.quantity * self.cost_price
    
    @property
    def is_low_stock(self) -> bool:
        """Check if product is below reorder level"""
        return self.quantity <= self.reorder_level

@dataclass
class User:
    """User model for authentication"""
    id: Optional[int] = None
    username: str = ""
    password_hash: str = ""
    role: str = "sales_rep"  # admin or sales_rep
    full_name: str = ""
    pin_hash: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @property
    def is_admin(self) -> bool:
        """Check if user has admin role"""
        return self.role == "admin"

@dataclass
class Customer:
    """Customer model"""
    id: Optional[int] = None
    name: str = ""
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    credit_limit: float = 0.0
    outstanding_balance: float = 0.0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @property
    def available_credit(self) -> float:
        """Calculate available credit"""
        return self.credit_limit - self.outstanding_balance

    def to_dict(self):
        """Convert Customer object to a dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "phone": self.phone,
            "email": self.email,
            "address": self.address,
            "credit_limit": self.credit_limit,
            "outstanding_balance": self.outstanding_balance,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "available_credit": self.available_credit
        }

@dataclass
class Sale:
    """Sale model"""
    id: Optional[int] = None
    date: Optional[datetime] = None
    total_amount: float = 0.0
    amount_paid: float = 0.0
    payment_method: Optional[str] = None
    customer_id: Optional[int] = None
    cashier_user: str = ""
    sync_status: str = "pending"
    items: List['SaleItem'] = None
    
    def __post_init__(self):
        if self.items is None:
            self.items = []
        if self.date is None:
            self.date = datetime.now()

    def to_dict(self):
        """Convert Sale object to a dictionary."""
        return {
            "id": self.id,
            "date": self.date.isoformat() if self.date else None,
            "total_amount": self.total_amount,
            "amount_paid": self.amount_paid,
            "payment_method": self.payment_method,
            "customer_id": self.customer_id,
            "cashier_user": self.cashier_user,
            "sync_status": self.sync_status,
            "items": [item.to_dict() for item in self.items] # Assuming SaleItem also has to_dict
        }

@dataclass
class SaleItem:
    """Sale item model"""
    id: Optional[int] = None
    sale_id: Optional[int] = None
    product_id: int = 0
    product_name: str = ""  # For display purposes
    quantity: float = 0.0
    unit_price: float = 0.0
    subtotal: float = 0.0

    def to_dict(self):
        """Convert SaleItem object to a dictionary."""
        return {
            "id": self.id,
            "sale_id": self.sale_id,
            "product_id": self.product_id,
            "product_name": self.product_name,
            "quantity": self.quantity,
            "unit_price": self.unit_price,
            "subtotal": self.subtotal,
        }

@dataclass
class StockMovement:
    """Stock movement model"""
    id: Optional[int] = None
    product_id: int = 0
    type: str = ""  # arrival, adjustment, sale
    quantity: float = 0.0
    date: Optional[datetime] = None
    reason: Optional[str] = None
    user: str = ""
    
    def __post_init__(self):
        if self.date is None:
            self.date = datetime.now()

@dataclass
class CustomerPayment:
    """Customer payment model"""
    id: Optional[int] = None
    customer_id: int = 0
    amount: float = 0.0
    date: Optional[datetime] = None
    payment_method: Optional[str] = None
    notes: Optional[str] = None
    
    def __post_init__(self):
        if self.date is None:
            self.date = datetime.now()

@dataclass
class Category:
    """Category model for product categorization"""
    id: Optional[int] = None
    name: str = ""
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

@dataclass
class Setting:
    """Setting model for application configuration"""
    id: Optional[int] = None
    key_name: str = ""
    value: str = ""
    description: Optional[str] = None