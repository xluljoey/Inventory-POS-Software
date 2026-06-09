import tempfile
import os
from datetime import datetime
from typing import Dict, List
from config.app_config import AppConfig

class ReceiptPrinter:
    """Service for generating and printing receipts"""
    
    @staticmethod
    def generate_receipt(sale_data: Dict) -> str:
        """Generate a receipt as a string"""
        config = AppConfig()
        
        # Get business settings
        business_name = config.BUSINESS_NAME
        receipt_header = config.RECEIPT_HEADER
        receipt_footer = config.RECEIPT_FOOTER
        currency_symbol = "GHS"
        
        # Create receipt content
        receipt_lines = []
        receipt_lines.append(f"{business_name.center(40)}")
        receipt_lines.append("=" * 40)
        receipt_lines.append(f"Receipt #: {sale_data.get('id', 'N/A')}")
        receipt_lines.append(f"Date: {sale_data.get('date', datetime.now().strftime(config.DATE_FORMAT))}")
        receipt_lines.append(f"Cashier: {sale_data.get('cashier_user', 'N/A')}")
        receipt_lines.append("-" * 40)
        
        # Add items
        items = sale_data.get('items', [])
        for item in items:
            name = item.get('product_name', '')[:25]  # Limit name length
            qty = item.get('quantity', 0)
            price = item.get('unit_price', 0)
            subtotal = item.get('subtotal', 0)
            receipt_lines.append(f"{name:<25} {qty:>5} @ {currency_symbol}{price:>6.2f}")
            receipt_lines.append(f"{'':<30} {currency_symbol}{subtotal:>8.2f}")
        
        receipt_lines.append("-" * 40)
        receipt_lines.append(f"{'TOTAL:':<30} {currency_symbol}{sale_data.get('total_amount', 0):>8.2f}")
        
        if sale_data.get('payment_method'):
            receipt_lines.append(f"Payment Method: {sale_data.get('payment_method')}")
        
        receipt_lines.append("=" * 40)
        receipt_lines.append(receipt_header.center(40))
        receipt_lines.append(receipt_footer.center(40))
        receipt_lines.append("\n")
        
        return "\n".join(receipt_lines)
    
    @staticmethod
    def print_receipt(sale_data: Dict) -> bool:
        """Print a receipt to the default printer"""
        try:
            receipt_content = ReceiptPrinter.generate_receipt(sale_data)
            
            # Create a temporary file with the receipt content
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as temp_file:
                temp_file.write(receipt_content)
                temp_filename = temp_file.name
            
            # Print the file using system-specific commands
            import platform
            system = platform.system()
            
            if system == "Windows":
                # On Windows, we can use the 'print' command
                os.system(f'notepad /p "{temp_filename}"')
            elif system == "Darwin":  # macOS
                os.system(f'lpr "{temp_filename}"')
            else:  # Linux and other Unix-like systems
                os.system(f'lpr "{temp_filename}"')
            
            # Clean up the temporary file after a short delay
            import time
            time.sleep(1)  # Wait a moment for the print job to start
            os.remove(temp_filename)
            
            return True
        except Exception as e:
            print(f"Error printing receipt: {e}")
            return False
    
    @staticmethod
    def save_receipt_to_file(sale_data: Dict, filename: str = None) -> str:
        """Save receipt to a text file"""
        try:
            receipt_content = ReceiptPrinter.generate_receipt(sale_data)
            
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"receipt_{timestamp}.txt"
            
            # Ensure the directory exists
            os.makedirs(os.path.dirname(filename) if os.path.dirname(filename) else '.', exist_ok=True)
            
            with open(filename, 'w') as file:
                file.write(receipt_content)
            
            return filename
        except Exception as e:
            print(f"Error saving receipt to file: {e}")
            return None

class ReportPrinter:
    """Service for generating and printing reports"""
    
    @staticmethod
    def generate_daily_sales_report(date: datetime, sales_data: List[Dict]) -> str:
        """Generate a daily sales report as a string"""
        config = AppConfig()
        business_name = config.BUSINESS_NAME
        currency_symbol = config.CURRENCY_SYMBOL
        
        # Calculate totals
        total_revenue = sum(sale.get('total_amount', 0) for sale in sales_data)
        total_transactions = len(sales_data)
        
        report_lines = []
        report_lines.append(f"{business_name.center(60)}")
        report_lines.append("=" * 60)
        report_lines.append(f"DAILY SALES REPORT".center(60))
        report_lines.append(f"Date: {date.strftime(config.DATE_FORMAT)}".center(60))
        report_lines.append("=" * 60)
        report_lines.append("")
        
        # Add sales details
        report_lines.append(f"Total Transactions: {total_transactions}")
        report_lines.append(f"Total Revenue: {currency_symbol}{total_revenue:,.2f}")
        report_lines.append("")
        report_lines.append("-" * 60)
        report_lines.append(f"{'#':<5} {'Time':<12} {'Cashier':<15} {'Amount':<12}")
        report_lines.append("-" * 60)
        
        for i, sale in enumerate(sales_data, 1):
            sale_time = datetime.fromisoformat(sale['date']).strftime("%H:%M") if sale.get('date') else "N/A"
            cashier = sale.get('cashier_user', 'N/A')
            amount = sale.get('total_amount', 0)
            report_lines.append(f"{i:<5} {sale_time:<12} {cashier:<15} {currency_symbol}{amount:<11.2f}")
        
        report_lines.append("-" * 60)
        report_lines.append("\nGenerated on: " + datetime.now().strftime(config.DATETIME_FORMAT))
        
        return "\n".join(report_lines)
    
    @staticmethod
    def print_daily_sales_report(date: datetime, sales_data: List[Dict]) -> bool:
        """Print a daily sales report"""
        try:
            report_content = ReportPrinter.generate_daily_sales_report(date, sales_data)
            
            # Create a temporary file with the report content
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as temp_file:
                temp_file.write(report_content)
                temp_filename = temp_file.name
            
            # Print the file using system-specific commands
            import platform
            system = platform.system()
            
            if system == "Windows":
                os.system(f'notepad /p "{temp_filename}"')
            elif system == "Darwin":  # macOS
                os.system(f'lpr "{temp_filename}"')
            else:  # Linux and other Unix-like systems
                os.system(f'lpr "{temp_filename}"')
            
            # Clean up the temporary file after a short delay
            import time
            time.sleep(1)  # Wait a moment for the print job to start
            os.remove(temp_filename)
            
            return True
        except Exception as e:
            print(f"Error printing report: {e}")
            return False
