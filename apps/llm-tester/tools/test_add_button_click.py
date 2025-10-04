#!/usr/bin/env python3
# File: test_add_button_click.py
# Path: /home/herb/Desktop/LLM-Tester/test_add_button_click.py
# Standard: AIDEV-PascalCase-2.1
# Created: 2025-10-04
# Last Modified: 2025-10-04 12:41AM

"""
Test script to actually click the + Add Prompt button and see what happens
"""

import sys
import time
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer, Qt
from LLM_Tester_Enhanced import LLMTesterEnhanced

def test_add_button_click():
    """Test clicking the actual + Add Prompt button"""
    print("🧪 Testing Actual + Add Prompt Button Click...")

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
                print(f"   ✅ Found + Add Prompt button")
                break

    if not add_button_found:
        print(f"   ❌ Could not find + Add Prompt button")
        # Look in all widgets
        print(f"   Available buttons in suite:")
        for i, widget in enumerate(first_suite['widgets']):
            if hasattr(widget, 'text') and callable(widget.text):
                print(f"     Widget {i}: '{widget.text()}'")
        return

    # Print state before click
    print(f"\n📊 Before clicking:")
    print(f"   Prompts in data: {len(first_suite['prompts'])}")
    print(f"   Widgets in suite: {len(first_suite['widgets'])}")

    # Click the + Add Prompt button
    print(f"\n🖱️  Clicking + Add Prompt button...")
    try:
        add_button.click()
        QApplication.processEvents()  # Process the click event
        print(f"   ✅ Button clicked successfully")

        # Give it a moment for the dialog to appear
        time.sleep(0.5)

        # Check if a dialog appeared
        all_widgets = QApplication.topLevelWidgets()
        dialog_found = False
        for widget in all_widgets:
            if hasattr(widget, 'isWindow') and widget.isWindow() and widget != window:
                if hasattr(widget, 'windowTitle') and 'Add Prompt' in widget.windowTitle():
                    dialog_found = True
                    print(f"   ✅ Found Add Prompt dialog: {widget.windowTitle()}")

                    # Fill in the dialog and accept it
                    from PySide6.QtWidgets import QTextEdit, QDialogButtonBox

                    # Find text edit in dialog
                    text_edit = None
                    buttons = None

                    for child in widget.children():
                        if isinstance(child, QTextEdit):
                            text_edit = child
                        elif isinstance(child, QDialogButtonBox):
                            buttons = child

                    if text_edit:
                        test_text = f"TEST FROM BUTTON CLICK: {time.strftime('%H:%M:%S')}"
                        text_edit.setPlainText(test_text)
                        print(f"   ✅ Entered text: '{test_text}'")

                        # Find and click OK button
                        if buttons:
                            from PySide6.QtWidgets import QPushButton
                            for button in buttons.buttons():
                                if button.text() == "OK":
                                    button.click()
                                    print(f"   ✅ Clicked OK button")
                                    break
                    break

        if not dialog_found:
            print(f"   ❌ No Add Prompt dialog found after click")

    except Exception as e:
        print(f"   ❌ Error clicking button: {e}")

    # Process events after dialog
    QApplication.processEvents()
    time.sleep(0.5)

    # Check state after
    print(f"\n📊 After clicking:")
    print(f"   Prompts in data: {len(first_suite['prompts'])}")
    print(f"   Widgets in suite: {len(first_suite['widgets'])}")

    if len(first_suite['prompts']) > original_prompt_count:
        print(f"   ✅ New prompt was added!")
        print(f"   New prompt: '{first_suite['prompts'][-1][:50]}...'")
    else:
        print(f"   ❌ No new prompt was added")

    print(f"\n🖱️  Manual Test Instructions:")
    print(f"   1. The application should be visible with the Test Suite tab active")
    print(f"   2. Look at the '{suite_name}' section")
    print(f"   3. You should see either:")
    print(f"      - An Add Prompt dialog (if it appeared but wasn't auto-closed)")
    print(f"      - A new prompt in the list (if it worked)")
    print(f"   4. Check if the dialog is open or if prompts were added")

    # Keep window open for 45 seconds for manual inspection
    QTimer.singleShot(45000, app.quit)
    sys.exit(app.exec())

if __name__ == "__main__":
    test_add_button_click()