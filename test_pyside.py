
import sys
from PySide6.QtWidgets import QApplication, QWidget

def test_pyside():
    try:
        app = QApplication(sys.argv)
        print("QApplication initialized successfully")
        window = QWidget()
        window.setWindowTitle("Test Window")
        window.show()
        print("Window shown successfully")
        # Exit immediately for test
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    test_pyside()
