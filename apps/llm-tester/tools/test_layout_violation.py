#!/usr/bin/env python3
# File: test_layout_violation.py
# Path: /home/herb/Desktop/LLM-Tester/test_layout_violation.py
# Standard: AIDEV-PascalCase-2.1
# Created: 2025-10-04
# Last Modified: 2025-10-04 01:35AM

"""
Test to isolate Qt layout violations by creating TestSuitesWidget in isolation
"""

import sys
from PySide6.QtWidgets import QApplication, QMainWindow
from LLM_Tester_Enhanced import TestSuitesWidget

def test_layout_violation():
    """Test if TestSuitesWidget creates layout violations when isolated"""
    print("🧪 Testing for Qt Layout Violations...")

    app = QApplication(sys.argv)

    # Create main window
    window = QMainWindow()
    window.setWindowTitle("Layout Violation Test")
    window.setGeometry(100, 100, 800, 600)

    print("✅ Creating TestSuitesWidget...")
    test_widget = TestSuitesWidget()
    print("✅ TestSuitesWidget created")

    # Set as central widget
    window.setCentralWidget(test_widget)

    print("✅ Showing window...")
    window.show()

    print("\n🎯 Check above for any Qt layout violation errors:")
    print("   Look for: 'QLayout: Cannot add parent widget'")
    print("   If no errors appear above, the layout violations are fixed!")

    # Keep window open briefly
    from PySide6.QtCore import QTimer
    QTimer.singleShot(5000, app.quit)
    sys.exit(app.exec())

if __name__ == "__main__":
    test_layout_violation()