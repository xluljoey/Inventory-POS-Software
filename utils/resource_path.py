# utils/resource_path.py
import os
import sys

def get_resource_path(relative_path):
    """
    Get absolute path to resource, works for dev and for PyInstaller.
    Extremely defensive implementation to prevent 'Ghost Process' / Silent Crashes.
    """
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    
    path = os.path.join(base_path, relative_path)
    return path if os.path.exists(path) else None
