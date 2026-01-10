
import sys
import os
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout
from PySide6.QtCore import QTimer, Qt
from ui.navigation_bar import MainNavigationBar

def capture():
    app = QApplication(sys.argv)
    
    # Create a wrapper to hold the nav bar on a white background for better contrast
    window = QWidget()
    window.setFixedSize(1000, 200)
    window.setStyleSheet("background-color: white;")
    layout = QVBoxLayout(window)
    
    nav = MainNavigationBar()
    layout.addWidget(nav)
    
    window.show()
    
    # Wait for rendering
    QTimer.singleShot(1000, lambda: save_and_exit(window, app))
    sys.exit(app.exec())

def save_and_exit(window, app):
    pixmap = window.grab()
    pixmap.save("nav_test.png")
    print("Screenshot saved to nav_test.png")
    app.quit()

if __name__ == "__main__":
    capture()
