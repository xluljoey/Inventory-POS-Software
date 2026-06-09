import os
import platform
from datetime import datetime, timedelta
from typing import Dict, Any
import json

def format_currency(amount: float, currency_symbol: str = "GHS") -> str:
    """Format a number as currency"""
    return f"{currency_symbol}{amount:,.2f}"

def format_percentage(value: float) -> str:
    """Format a decimal as a percentage"""
    return f"{value:.2f}%"

def format_datetime(dt: datetime, date_format: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Format a datetime object as a string"""
    return dt.strftime(date_format)

def format_date(dt: datetime, date_format: str = "%Y-%m-%d") -> str:
    """Format a date object as a string"""
    return dt.strftime(date_format)

def get_current_datetime() -> datetime:
    """Get the current datetime"""
    return datetime.now()

def get_current_date() -> datetime:
    """Get the current date (without time)"""
    return datetime.now().date()

def get_start_of_day(dt: datetime) -> datetime:
    """Get the start of the day for a given datetime"""
    return dt.replace(hour=0, minute=0, second=0, microsecond=0)

def get_end_of_day(dt: datetime) -> datetime:
    """Get the end of the day for a given datetime"""
    return dt.replace(hour=23, minute=59, second=59, microsecond=999999)

def calculate_age(birth_date: datetime) -> int:
    """Calculate age from birth date"""
    today = datetime.now().date()
    birth = birth_date.date()
    age = today.year - birth.year
    if today.month < birth.month or (today.month == birth.month and today.day < birth.day):
        age -= 1
    return age

def sanitize_filename(filename: str) -> str:
    """Remove invalid characters from filename"""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename

def get_file_size(file_path: str) -> int:
    """Get the size of a file in bytes"""
    return os.path.getsize(file_path)

def is_file_older_than(file_path: str, days: int) -> bool:
    """Check if a file is older than specified number of days"""
    file_time = os.path.getmtime(file_path)
    file_date = datetime.fromtimestamp(file_time)
    return (datetime.now() - file_date).days > days

def get_app_data_dir() -> str:
    """Get the appropriate app data directory for the platform"""
    if platform.system() == "Windows":
        appdata = os.getenv('APPDATA')
        if appdata:
            return os.path.join(appdata, "InventoryManagement")
    else:
        # Use ~/.local/share on Linux
        home = os.path.expanduser("~")
        return os.path.join(home, ".local", "share", "InventoryManagement")
    
    # Fallback to current directory if platform-specific directories fail
    return os.path.join(os.getcwd(), "data")

def create_backup_filename(prefix: str = "backup", extension: str = "db") -> str:
    """Create a timestamped backup filename"""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    return f"{prefix}_{timestamp}.{extension}"

def get_past_days_list(days: int = 7) -> list:
    """Get a list of past days from today"""
    today = datetime.now().date()
    return [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(days-1, -1, -1)]

def calculate_total(items: list, field: str) -> float:
    """Calculate total of a specific field in a list of dictionaries"""
    return sum(item.get(field, 0) for item in items)

def calculate_percentage(part: float, whole: float) -> float:
    """Calculate percentage of part relative to whole"""
    if whole == 0:
        return 0.0
    return (part / whole) * 100

def dict_to_json(data: Dict[str, Any]) -> str:
    """Convert a dictionary to JSON string"""
    return json.dumps(data, default=str)

def json_to_dict(json_str: str) -> Dict[str, Any]:
    """Convert a JSON string to dictionary"""
    return json.loads(json_str)

def safe_divide(numerator: float, denominator: float) -> float:
    """Safely divide two numbers, returning 0 if denominator is 0"""
    if denominator == 0:
        return 0.0
    return numerator / denominator

def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """Truncate text to a maximum length"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix