#!/usr/bin/env python3
# File: test_force_visibility.py
# Path: /home/herb/Desktop/LLM-Tester/test_force_visibility.py
# Standard: AIDEV-PascalCase-2.1
# Created: 2025-10-04
# Last Modified: 2025-10-04 01:38AM

"""
Test to force + Add Prompt button visibility and check if it works
"""

import sys
from PySide6.QtWidgets import QApplication
from LLM_Tester_Enhanced import LLMTesterEnhanced

def test_force_visibility():
    """Force + Add Prompt button to be visible and test functionality"""
    print("🧪 Testing Forced + Add Prompt Button Visibility...")

    app = QApplication(sys.argv)
    window = LLMTesterEnhanced()
    window.show()

    test_widget = window.test_suites
    print(f"✅ Application started")
    print(f"✅ Found {len(test_widget.suite_widgets)} test suites")

    # Get first suite
    first_suite = test_widget.suite_widgets[0]
    suite_name = first_suite['name']
    print(f"📋 Suite: '{suite_name}'")

    # Find the + Add Prompt button
    add_button = None
    for widget in first_suite['widgets']:
        if hasattr(widget, 'text') and callable(widget.text):
            if "+ Add Prompt" in widget.text():
                add_button = widget
                break

    if add_button:
        print(f"✅ Found + Add Prompt button")
        print(f"   Initial state:")
        print(f"   - Visible: {add_button.isVisible()}")
        print(f"   - Enabled: {add_button.isEnabled()}")
        print(f"   - Geometry: {add_button.geometry()}")
        print(f"   - Size: {add_button.size()}")
        print(f"   - Parent: {type(add_button.parent()).__name__}")

        # Force visibility with multiple methods
        print(f"\n🔧 Forcing button visibility...")
        add_button.show()
        add_button.raise_()
        add_button.repaint()
        add_button.update()

        # Try setting explicit geometry
        add_button.setGeometry(10, 10, 100, 30)

        # Force parent widget updates
        parent = add_button.parent()
        if parent:
            parent.update()
            parent.repaint()

        # Force application update
        test_widget.update()
        window.update()
        QApplication.processEvents()

        print(f"   After forcing:")
        print(f"   - Visible: {add_button.isVisible()}")
        print(f"   - Geometry: {add_button.geometry()}")
        print(f"   - Size: {add_button.size()}")

        # Try to make it more visible with bright background
        add_button.setStyleSheet("""
            QPushButton {
                background-color: red !important;
                color: white !important;
                border: 2px solid yellow !important;
                font-size: 14px !important;
                font-weight: bold !important;
            }
        """)

        print(f"\n✅ Applied bright red styling to make button visible")
        print(f"🖱️  Look for a RED + Add Prompt button in the '{suite_name}' section")

    else:
        print(f"❌ Could not find + Add Prompt button")

    print(f"\n⏰ Window will stay open for 15 seconds for manual inspection")

    # Keep window open longer for manual inspection
    from PySide6.QtCore import QTimer
    QTimer.singleShot(15000, app.quit)
    sys.exit(app.exec())

if __name__ == "__main__":
    test_force_visibility()