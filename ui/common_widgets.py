# ui/common_widgets.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt

class EmptyStateWidget(QWidget):
    """
    A reusable widget to display a placeholder message when a view (e.g., a table)
    has no data to show.
    """
    def __init__(self, icon, message, parent=None):
        super().__init__(parent)
        self.setObjectName("emptyStateWidget")

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(10)

        # 1. Icon/Graphic (Emoji or SVG character)
        icon_label = QLabel(icon)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("font-size: 48px;")
        
        # 2. Message Text
        message_label = QLabel(message)
        message_label.setAlignment(Qt.AlignCenter)
        message_label.setWordWrap(True)
        message_label.setStyleSheet("""
            color: #9CA3AF; 
            font-size: 12pt;
            font-style: italic;
        """)

        layout.addWidget(icon_label)
        layout.addWidget(message_label)

        self.setVisible(False) # Hidden by default
