#!/usr/bin/env python3
# File: test_button_clicks.py
# Path: /home/herb/Desktop/LLM-Tester/test_button_clicks.py
# Standard: AIDEV-PascalCase-2.1
# Created: 2025-10-03
# Last Modified: 2025-10-03 05:05PM

"""
Test script to verify Test Suite button functionality
"""

import sys
import time
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from LLM_Tester_Enhanced import LLMTesterEnhanced

def test_button_functionality():
    """Test that button connections work without errors"""
    print("🧪 Testing Test Suite Button Functionality...")

    app = QApplication(sys.argv)
    window = LLMTesterEnhanced()
    window.show()

    # Get the TestSuitesWidget
    test_widget = window.test_suites

    print(f"✅ Found {len(test_widget.suite_widgets)} test suites")

    # Test each suite's buttons
    for suite_data in test_widget.suite_widgets:
        suite_name = suite_data['name']
        print(f"\n📋 Testing Suite: {suite_name}")

        # Find buttons in this suite
        for widget in suite_data['widgets']:
            if hasattr(widget, 'text') and callable(widget.text):
                button_text = widget.text()
                if button_text in ["Edit", "Test", "Delete", "▶"]:
                    print(f"  🔘 Found button: {button_text}")
                    try:
                        # Simulate button click
                        widget.click()
                        QApplication.processEvents()  # Process the click event
                        print(f"  ✅ {button_text} button clicked successfully")
                    except Exception as e:
                        print(f"  ❌ {button_text} button error: {e}")

    print("\n🎯 Button functionality test completed!")
    print("Check the console output above for debug messages from button handlers.")

    # Keep window open for 5 seconds then close
    QTimer.singleShot(5000, app.quit)

    sys.exit(app.exec())

if __name__ == "__main__":
    test_button_functionality()