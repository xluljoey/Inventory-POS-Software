import re
from typing import Optional

def validate_email(email: str) -> bool:
    """Validate email address format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone: str) -> bool:
    """Validate phone number format (simple validation)"""
    # Remove common separators
    phone = re.sub(r'[\s\-\(\)\+]', '', phone)
    # Check if it contains only digits and is of reasonable length
    return re.match(r'^[\d\+]{10,15}$', phone) is not None

def validate_sku(sku: str) -> bool:
    """Validate SKU format (alphanumeric with hyphens and underscores)"""
    pattern = r'^[A-Za-z0-9_-]+$'
    return re.match(pattern, sku) is not None

def validate_price(price: str) -> bool:
    """Validate price format (positive number with optional decimal)"""
    try:
        price_float = float(price)
        return price_float >= 0
    except ValueError:
        return False

def validate_quantity(quantity: str) -> bool:
    """Validate quantity format (positive number)"""
    try:
        quantity_float = float(quantity)
        return quantity_float >= 0
    except ValueError:
        return False

def validate_date(date_string: str) -> bool:
    """Validate date format (YYYY-MM-DD)"""
    pattern = r'^\d{4}-\d{2}-\d{2}$'
    if not re.match(pattern, date_string):
        return False
    
    # Additional validation to check if it's a valid date
    try:
        from datetime import datetime
        datetime.strptime(date_string, '%Y-%m-%d')
        return True
    except ValueError:
        return False

def validate_password(password: str) -> tuple[bool, Optional[str]]:
    """
    Validate password strength
    Returns: (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r'\d', password):
        return False, "Password must contain at least one digit"
    
    return True, None

def validate_pin(pin: str) -> bool:
    """Validate PIN format (4-8 digits)"""
    pattern = r'^\d{4,8}$'
    return re.match(pattern, pin) is not None

def validate_name(name: str) -> bool:
    """Validate name format (letters, spaces, hyphens, and apostrophes)"""
    if len(name.strip()) < 1:
        return False
    pattern = r"^[A-Za-z\s\-\'\.]+$"
    return re.match(pattern, name) is not None

def validate_url(url: str) -> bool:
    """Validate URL format"""
    pattern = r'^https?://(?:[-\w.])+(?:\:[0-9]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:\#(?:[\w.])*)?)?$'
    return re.match(pattern, url) is not None

def validate_percentage(percentage: str) -> bool:
    """Validate percentage format (0-100)"""
    try:
        value = float(percentage)
        return 0 <= value <= 100
    except ValueError:
        return False