from PySide6.QtPrintSupport import QPrinter, QPrintDialog
from PySide6.QtGui import QTextDocument
from PySide6.QtCore import Qt
from datetime import datetime
from PySide6.QtWidgets import QMessageBox

from config.app_config import AppConfig
from database.database import DatabaseService

class ReceiptPrinter:
    """Handles printing of sales receipts."""

    @staticmethod
    def print_receipt(sales_data: dict, parent_widget=None):
        """
        Generates and prints a receipt from sales data.
        sales_data is expected to be a dictionary representing a Sale object (from Sale.to_dict()).
        """
        printer = QPrinter(QPrinter.HighResolution)
        print_dialog = QPrintDialog(printer, parent_widget)

        if print_dialog.exec() == QPrintDialog.Accepted:
            document = QTextDocument()
            html_content = ReceiptPrinter._generate_receipt_html(sales_data)
            document.setHtml(html_content)
            document.print_(printer)
            QMessageBox.information(parent_widget, "Print Status", "Receipt sent to printer.")
        else:
            QMessageBox.information(parent_widget, "Print Status", "Printing cancelled.")

    @staticmethod
    def _generate_receipt_html(sales_data: dict) -> str:
        """
        Generates HTML content for a sales receipt.
        """
        store_name = AppConfig.get_setting("business_name", AppConfig.BUSINESS_NAME)
        currency_symbol = AppConfig.get_setting("currency_symbol", AppConfig.CURRENCY_SYMBOL)
        receipt_header = AppConfig.get_setting("receipt_header", AppConfig.RECEIPT_HEADER)
        receipt_footer = AppConfig.get_setting("receipt_footer", AppConfig.RECEIPT_FOOTER)

        sale_date_str = datetime.fromisoformat(sales_data.get('date')).strftime("%Y-%m-%d %H:%M:%S") if sales_data.get('date') else "N/A"
        
        customer_name = "Walk-in Customer"
        if sales_data.get('customer_id'):
            customer = DatabaseService.get_customer_by_id(sales_data['customer_id'])
            if customer:
                customer_name = customer['name']

        items_html = ""
        for item in sales_data.get('items', []):
            items_html += f"""
            <tr>
                <td style="text-align: left;">{item.get('product_name', '')}</td>
                <td style="text-align: center;">{item.get('quantity', 0):.2f}</td>
                <td style="text-align: right;">{currency_symbol}{item.get('unit_price', 0):.2f}</td>
                <td style="text-align: right;">{currency_symbol}{item.get('subtotal', 0):.2f}</td>
            </tr>
            """

        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: 'Consolas', 'Courier New', monospace; font-size: 10pt; width: 80mm; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
                th, td {{ padding: 3px 2px; border-bottom: 1px dotted #ccc; }}
                .header, .footer {{ text-align: center; margin-bottom: 5px; }}
                .title {{ font-size: 14pt; font-weight: bold; margin-bottom: 10px; }}
                .subtitle {{ font-size: 9pt; margin-bottom: 5px; }}
                .total {{ font-size: 12pt; font-weight: bold; text-align: right; }}
                .cashier {{ font-size: 9pt; text-align: left; margin-top: 10px; }}
                .customer {{ font-size: 9pt; text-align: left; margin-top: 5px; }}
                .text-right {{ text-align: right; }}
                .text-left {{ text-align: left; }}
            </style>
        </head>
        <body>
            <div class="header">
                <div class="title">{store_name.upper()}</div>
                <div class="subtitle">{receipt_header}</div>
                <hr style="border-top: 1px dashed #000; margin: 5px 0;">
            </div>

            <p class="subtitle"><strong>Date:</strong> {sale_date_str}</p>
            <p class="subtitle"><strong>Cashier:</strong> {sales_data.get('cashier_user', 'N/A')}</p>
            <p class="subtitle"><strong>Customer:</strong> {customer_name}</p>
            <hr style="border-top: 1px dashed #000; margin: 5px 0;">

            <table>
                <thead>
                    <tr>
                        <th style="text-align: left;">Item</th>
                        <th style="text-align: center;">Qty</th>
                        <th style="text-align: right;">Price</th>
                        <th style="text-align: right;">Total</th>
                    </tr>
                </thead>
                <tbody>
                    {items_html}
                </tbody>
            </table>
            <hr style="border-top: 1px dashed #000; margin: 5px 0;">

            <p class="total">Subtotal: {currency_symbol}{sales_data.get('total_amount', 0):.2f}</p>
            <p class="total">Amount Paid: {currency_symbol}{sales_data.get('amount_paid', 0):.2f}</p>
            <p class="total">Balance Due: {currency_symbol}{sales_data.get('total_amount', 0) - sales_data.get('amount_paid', 0):.2f}</p>
            <p class="total">Payment Method: {sales_data.get('payment_method', 'N/A')}</p>
            
            <hr style="border-top: 1px dashed #000; margin: 5px 0;">
            <div class="footer">
                <div class="subtitle">{receipt_footer}</div>
                <p>Thank you for shopping with us!</p>
            </div>
        </body>
        </html>
        """
        return html
