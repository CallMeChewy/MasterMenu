#!/usr/bin/env python3
# File: test_add_dialog.py
# Path: /home/herb/Desktop/LLM-Tester/test_add_dialog.py
# Standard: AIDEV-PascalCase-2.1
# Created: 2025-10-04
# Last Modified: 2025-10-04 01:30AM

"""
Test script to check if the Add Prompt dialog appears and works
"""

import sys
from PySide6.QtWidgets import QApplication
from LLM_Tester_Enhanced import LLMTesterEnhanced

def test_add_dialog():
    """Test if the Add Prompt dialog appears and works"""
    print("🧪 Testing Add Prompt Dialog...")

    app = QApplication(sys.argv)
    window = LLMTesterEnhanced()
    window.show()

    test_widget = window.test_suites
    print(f"✅ Application started")
    print(f"✅ Found {len(test_widget.suite_widgets)} test suites")

    # Get first suite
    first_suite = test_widget.suite_widgets[0]
    suite_name = first_suite['name']
    original_prompt_count = len(first_suite['prompts'])
    print(f"📋 Suite: '{suite_name}'")
    print(f"   Original prompts: {original_prompt_count}")

    # Find the + Add Prompt button for the first suite
    add_button_found = False
    add_button = None

    # Look for the + Add Prompt button in the suite's widgets
    for widget in first_suite['widgets']:
        if hasattr(widget, 'text') and callable(widget.text):
            button_text = widget.text()
            if "+ Add Prompt" in button_text:
                add_button = widget
                add_button_found = True
                print(f"   ✅ Found + Add Prompt button: '{button_text}'")
                print(f"   Button visible: {add_button.isVisible()}")
                print(f"   Button enabled: {add_button.isEnabled()}")
                print(f"   Button position: {add_button.geometry()}")
                break

    if not add_button_found:
        print(f"   ❌ Could not find + Add Prompt button")
        return

    # Manually trigger the add_prompt_to_suite method
    print(f"\n➕ Manually triggering add_prompt_to_suite for '{suite_name}'...")
    test_widget.add_prompt_to_suite(suite_name)

    # Check if a dialog appeared
    all_widgets = QApplication.topLevelWidgets()
    dialog_found = False
    for widget in all_widgets:
        if hasattr(widget, 'isWindow') and widget.isWindow() and widget != window:
            if hasattr(widget, 'windowTitle') and 'Add Prompt' in widget.windowTitle():
                dialog_found = True
                print(f"   ✅ Found Add Prompt dialog: '{widget.windowTitle()}'")
                print(f"   Dialog visible: {widget.isVisible()}")
                print(f"   Dialog geometry: {widget.geometry()}")
                break

    if not dialog_found:
        print(f"   ❌ No Add Prompt dialog found")
    else:
        print(f"   ✅ Dialog appeared successfully!")

    print(f"\n🖱️  Manual Instructions:")
    print(f"   1. Look for any Add Prompt dialogs that appeared")
    print(f"   2. If you see one, try entering text and clicking OK")
    print(f"   3. Check if new prompts appear in the '{suite_name}' section")

    # Keep window open for manual inspection
    from PySide6.QtCore import QTimer
    QTimer.singleShot(15000, app.quit)
    sys.exit(app.exec())

if __name__ == "__main__":
    test_add_dialog()