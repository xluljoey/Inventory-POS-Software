import os
import subprocess
import sys

def build():
    """Execute PyInstaller build with specific production flags"""
    print("Starting production build process...")
    
    # Use python -m PyInstaller to avoid PATH issues
    pyinstaller_cmd = [sys.executable, '-m', 'PyInstaller']
    
    # 1. Define base command
    cmd = pyinstaller_cmd + [
        '--noconsole',
        '--onedir',
        '--name=InventoryManager',
        '--icon=assets/app_icon.ico',
        '--version-file=version_info.txt',
        '--add-data=assets;assets',
        '--add-data=database;database',
        '--hidden-import=PySide6.QtPrintSupport',
        '--hidden-import=sqlite3',
        '--clean',
        '--noconfirm', # Overwrite existing
        'main.py'
    ]
    
    # 2. Add extra data files if needed
    if os.path.exists('styles.qss'):
        cmd.append('--add-data=styles.qss;.')

    print(f"Executing: {' '.join(cmd)}")
    
    try:
        subprocess.run(cmd, check=True)
        print("\nBuild successful! Files are in the 'dist/InventoryManager' folder.")
        print("You can now use Inno Setup with 'setup.iss' to create the installer.")
    except subprocess.CalledProcessError as e:
        print(f"\nBuild failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    build()
