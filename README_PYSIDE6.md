# Inventory Management System - PySide6/QML Implementation

This project has been successfully migrated from Flet to PySide6 with Qt Quick/QML for the UI. This addresses the compatibility issues with Fedora 43 while providing a modern, professional interface.

## Features

- **Modern UI**: Built with PySide6 and Qt Quick/QML for a native, responsive experience
- **Material Design**: Following Material Design guidelines with proper styling
- **Smooth Animations**: Including hover effects, transitions, and loading animations
- **Responsive Layout**: Adapts to different screen sizes
- **Dark Mode Support**: Optional dark theme for comfortable viewing
- **Complete Functionality**: All original features preserved:
  - User authentication with role-based access
  - Inventory management
 - Point of Sale system
  - Customer management
  - Reporting and analytics
  - Settings management

## Architecture

- **UI Layer**: PySide6 with Qt Quick/QML (Material Design components)
- **Business Logic**: Preserved from original implementation
- **Service Layer**: All services (auth, inventory, sales, customer) remain unchanged
- **Database Layer**: Original database schema and models preserved

## File Structure

```
.
├── main.py                 # PySide6 application entry point
├── requirements.txt        # PySide6 dependencies
├── qml/                    # QML UI files
│   ├── main.qml           # Main application window
│   ├── Login.qml          # Login screen
│   ├── Dashboard.qml      # Dashboard screen
│   ├── Inventory.qml      # Inventory management
│   ├── Sales.qml          # Point of sale
│   ├── Customers.qml      # Customer management
│   ├── Reports.qml        # Reporting
│   ├── Settings.qml       # Settings
│   └── Components.qml     # Custom UI components
├── config/                # Configuration files
├── database/              # Database models and service
├── services/              # Business logic services
└── utils/                 # Utility functions
```

## Installation

1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   
   Or if using system Python:
   ```bash
   python3 -m pip install -r requirements.txt
   ```

2. Run the application:
   ```bash
   python3 main.py
   ```
   
   Or if using a virtual environment:
   ```bash
   python main.py
   ```

**Note**: If you encounter "ModuleNotFoundError: No module named 'PySide6'", ensure you're using the correct Python environment where PySide6 is installed. You can check with:
```bash
python3 -c "import PySide6; print(PySide6.__version__)"
```

## Key Improvements

1. **Fedora 43 Compatibility**: Resolved the blank window issue that occurred with Flet
2. **Performance**: More efficient rendering and better resource management
3. **Native Look**: Better integration with the native desktop environment
4. **Modern UI**: Material Design components with animations and transitions
5. **Maintainability**: Clear separation between UI (QML) and logic (Python)

## UI Components

The application includes:
- Custom Material Design styled components
- Animated transitions between views
- Responsive layouts that adapt to screen size
- Interactive cards with hover effects
- Professional navigation patterns
- Toast notifications and dialog confirmations

## Usage

The application maintains the same workflow as the original:
1. Login with username/password or admin PIN
2. Navigate between dashboard, inventory, sales, customers, and reports
3. Perform business operations as needed
4. Logout when finished

All existing business logic, database operations, and service integrations remain unchanged, ensuring data integrity and functionality consistency.