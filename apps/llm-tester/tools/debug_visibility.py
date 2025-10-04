#!/usr/bin/env python3
# File: debug_visibility.py
# Path: /home/herb/Desktop/LLM-Tester/debug_visibility.py
# Standard: AIDEV-PascalCase-2.1
# Created: 2025-10-04
# Last Modified: 2025-10-04 12:50AM

"""
Debug script to check widget visibility
"""

import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from LLM_Tester_Enhanced import LLMTesterEnhanced

def debug_visibility():
    """Debug widget visibility issues"""
    print("🔍 Debugging Widget Visibility...")

    app = QApplication(sys.argv)
    window = LLMTesterEnhanced()
    window.show()

    test_widget = window.test_suites
    first_suite = test_widget.suite_widgets[0]
    suite_name = first_suite['name']

    print(f"✅ Suite: '{suite_name}'")
    print(f"   Total widgets: {len(first_suite['widgets'])}")

    # Check each widget's visibility
    print(f"\n📊 Widget Visibility Analysis:")
    for i, widget in enumerate(first_suite['widgets']):
        if hasattr(widget, 'text') and callable(widget.text):
            text = widget.text()
            visible = widget.isVisible()
            enabled = widget.isEnabled()
            geometry = widget.geometry()
            parent = widget.parent()
            parent_name = type(parent).__name__ if parent else "None"

            print(f"   {i:2d}. '{text[:20]:20s}' | Visible: {visible} | Enabled: {enabled} | Pos: {geometry.x()},{geometry.y()} | Size: {geometry.width()}x{geometry.height()} | Parent: {parent_name}")

    # Focus on the + Add Prompt button
    add_button = None
    for widget in first_suite['widgets']:
        if hasattr(widget, 'text') and callable(widget.text):
            if "+ Add Prompt" in widget.text():
                add_button = widget
                break

    if add_button:
        print(f"\n🎯 + Add Prompt Button Details:")
        print(f"   Visible: {add_button.isVisible()}")
        print(f"   Enabled: {add_button.isEnabled()}")
        print(f"   Geometry: {add_button.geometry()}")
        print(f"   Size Hint: {add_button.sizeHint()}")
        print(f"   Minimum Size: {add_button.minimumSize()}")
        print(f"   Maximum Size: {add_button.maximumSize()}")
        print(f"   Style Sheet: {add_button.styleSheet()}")
        print(f"   Parent: {type(add_button.parent()).__name__ if add_button.parent() else 'None'}")

        # Try to force visibility
        print(f"\n🔧 Forcing visibility...")
        add_button.show()
        add_button.raise_()
        add_button.update()
        add_button.repaint()
        QApplication.processEvents()

        print(f"   After show() - Visible: {add_button.isVisible()}")
        print(f"   Geometry after show(): {add_button.geometry()}")

    print(f"\n🖱️  Manual Instructions:")
    print(f"   Look at the '{suite_name}' section in the Test Suite tab")
    print(f"   Check if you can see any cyan/blue '+ Add Prompt' buttons")

    QTimer.singleShot(20000, app.quit)
    sys.exit(app.exec())

if __name__ == "__main__":
    debug_visibility()