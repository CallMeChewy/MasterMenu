#!/usr/bin/env python3
# File: debug_add_button.py
# Path: /home/herb/Desktop/LLM-Tester/debug_add_button.py
# Standard: AIDEV-PascalCase-2.1
# Created: 2025-10-04
# Last Modified: 2025-10-04 02:05AM

"""
Debug the specific Add button suite name issue
"""

import sys
from PySide6.QtWidgets import QApplication
from LLM_Tester_Enhanced import LLMTesterEnhanced

def debug_add_button():
    """Debug why Add button receives 'False' as suite name"""
    print("🔍 DEBUG: Add Button Suite Name Issue")
    print("=" * 50)

    app = QApplication(sys.argv)
    window = LLMTesterEnhanced()
    window.show()

    test_widget = window.test_suites
    print(f"✅ Application started")

    # Switch to Test Suites tab
    window.tab_widget.setCurrentIndex(1)
    QApplication.processEvents()

    # Examine each suite
    for suite_idx, suite_data in enumerate(test_widget.suite_widgets):
        suite_name = suite_data['name']
        print(f"\n📋 Suite {suite_idx}: '{suite_name}'")
        print(f"   Prompts: {len(suite_data['prompts'])}")
        print(f"   Widgets: {len(suite_data['widgets'])}")

        # Find the + Add Prompt button in this suite
        add_button = None
        for widget_idx, widget in enumerate(suite_data['widgets']):
            if hasattr(widget, 'text') and callable(widget.text):
                button_text = widget.text()
                if "+ Add Prompt" in button_text:
                    add_button = widget
                    print(f"   ✅ Found + Add Prompt button at widget index {widget_idx}")
                    print(f"   Button text: '{button_text}'")
                    print(f"   Button visible: {widget.isVisible()}")
                    print(f"   Button enabled: {widget.isEnabled()}")
                    break

        if add_button:
            # Check the button's lambda connection
            print(f"   🔗 Testing button connection...")

            # Create a test to see what the lambda passes
            original_add_prompt = test_widget.add_prompt_to_suite

            def debug_add_prompt_to_suite(suite_name):
                print(f"   🎯 DEBUG: add_prompt_to_suite called with: '{suite_name}' (type: {type(suite_name)})")
                return original_add_prompt(suite_name)

            test_widget.add_prompt_to_suite = debug_add_prompt_to_suite

            # Click the button
            print(f"   🖱️  Clicking button...")
            add_button.click()
            QApplication.processEvents()

            # Restore original method
            test_widget.add_prompt_to_suite = original_add_prompt

            break  # Only test first suite

    print(f"\n📸 This debug shows exactly what's being passed to the Add function")

    # Keep window open briefly
    from PySide6.QtCore import QTimer
    QTimer.singleShot(5000, app.quit)
    sys.exit(app.exec())

if __name__ == "__main__":
    debug_add_button()