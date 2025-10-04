#!/usr/bin/env python3
# File: test_startup_sequence.py
# Path: /home/herb/Desktop/LLM-Tester/test_startup_sequence.py
# Standard: AIDEV-PascalCase-2.1
# Created: 2025-10-04
# Last Modified: 2025-10-04 03:05AM

"""
Test the main application startup sequence to see when widgets become invisible
"""

import sys
import time
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

def test_main_app_startup():
    """Test the main application startup sequence"""
    print("🧪 Testing Main Application Startup Sequence")

    app = QApplication(sys.argv)

    # Import after app creation
    from LLM_Tester_Enhanced import LLMTesterEnhanced

    print("🔧 Creating main window...")
    window = LLMTesterEnhanced()

    # Check visibility immediately after creation but before show
    test_widget = window.test_suites
    print(f"   Before show() - Test suites widget visible: {test_widget.isVisible()}")

    if test_widget.suite_widgets:
        first_suite = test_widget.suite_widgets[0]
        widgets = first_suite.get('widgets', [])
        if widgets:
            add_btn = widgets[0]  # First widget should be Add button
            print(f"   Before show() - Add button visible: {add_btn.isVisible()}")
            print(f"   Before show() - Add button geometry: {add_btn.geometry()}")

    print("🖼️  Showing main window...")
    window.show()

    # Check visibility after show() but before event processing
    print(f"   After show() - Test suites widget visible: {test_widget.isVisible()}")
    if test_widget.suite_widgets and test_widget.suite_widgets[0].get('widgets'):
        add_btn = test_widget.suite_widgets[0]['widgets'][0]
        print(f"   After show() - Add button visible: {add_btn.isVisible()}")
        print(f"   After show() - Add button geometry: {add_btn.geometry()}")

    # Process events and check again
    print("⚡ Processing events...")
    app.processEvents()

    print(f"   After processEvents() - Test suites widget visible: {test_widget.isVisible()}")
    if test_widget.suite_widgets and test_widget.suite_widgets[0].get('widgets'):
        add_btn = test_widget.suite_widgets[0]['widgets'][0]
        print(f"   After processEvents() - Add button visible: {add_btn.isVisible()}")
        print(f"   After processEvents() - Add button geometry: {add_btn.geometry()}")

    # Switch to Test Suites tab and check again
    print("📑 Switching to Test Suites tab...")
    window.tab_widget.setCurrentIndex(1)  # Test Suites tab
    app.processEvents()

    print(f"   After tab switch - Test suites widget visible: {test_widget.isVisible()}")
    if test_widget.suite_widgets and test_widget.suite_widgets[0].get('widgets'):
        add_btn = test_widget.suite_widgets[0]['widgets'][0]
        print(f"   After tab switch - Add button visible: {add_btn.isVisible()}")
        print(f"   After tab switch - Add button geometry: {add_btn.geometry()}")

    # Wait a moment and check one more time
    print("⏰ Waiting 1 second...")
    time.sleep(1)
    app.processEvents()

    print(f"   Final - Test suites widget visible: {test_widget.isVisible()}")
    if test_widget.suite_widgets and test_widget.suite_widgets[0].get('widgets'):
        add_btn = test_widget.suite_widgets[0]['widgets'][0]
        print(f"   Final - Add button visible: {add_btn.isVisible()}")
        print(f"   Final - Add button geometry: {add_btn.geometry()}")

    print("🎯 Startup sequence analysis complete")
    print("   This should show exactly when the widgets become invisible")

    # Keep window open briefly for manual verification
    QTimer.singleShot(5000, app.quit)
    app.exec()

    return True

if __name__ == "__main__":
    test_main_app_startup()