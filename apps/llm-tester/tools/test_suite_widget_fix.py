#!/usr/bin/env python3
# File: test_suite_widget_fix.py
# Path: /home/herb/Desktop/LLM-Tester/test_suite_widget_fix.py
# Standard: AIDEV-PascalCase-2.1
# Created: 2025-10-04
# Last Modified: 2025-10-04 01:20AM

"""
Test if the TestSuiteWidget fix works by creating it in isolation
"""

import sys
from PySide6.QtWidgets import QApplication, QMainWindow
from LLM_Tester_Enhanced import TestSuitesWidget

def test_suite_widget_fix():
    """Test if the TestSuiteWidget layout fix works"""
    print("🧪 Testing TestSuiteWidget Fix...")

    app = QApplication(sys.argv)

    # Create main window
    window = QMainWindow()
    window.setWindowTitle("TestSuiteWidget Fix Test")
    window.setGeometry(100, 100, 1000, 800)

    # Create TestSuitesWidget
    test_widget = TestSuitesWidget()
    print(f"✅ TestSuiteWidget created")

    # Check how many suites it created
    print(f"✅ Found {len(test_widget.suite_widgets)} test suites")

    # Get first suite
    if test_widget.suite_widgets:
        first_suite = test_widget.suite_widgets[0]
        suite_name = first_suite['name']
        print(f"✅ First suite: '{suite_name}'")
        print(f"   Total widgets: {len(first_suite['widgets'])}")

        # Check widget visibility
        visible_count = 0
        invisible_count = 0
        for i, widget in enumerate(first_suite['widgets']):
            if hasattr(widget, 'isVisible') and widget.isVisible():
                visible_count += 1
            else:
                invisible_count += 1

        print(f"   Visible widgets: {visible_count}")
        print(f"   Invisible widgets: {invisible_count}")

        if visible_count > 0:
            print(f"   ✅ SUCCESS: Some widgets are visible!")
        else:
            print(f"   ❌ ISSUE: All widgets are still invisible")

    # Set as central widget and show
    window.setCentralWidget(test_widget)
    window.show()

    print(f"\n🖼️  Window should be visible now")
    print(f"   Look for the Test Suite tab content")

    # Keep window open briefly to see if it appears
    from PySide6.QtCore import QTimer
    QTimer.singleShot(8000, app.quit)
    sys.exit(app.exec())

if __name__ == "__main__":
    test_suite_widget_fix()