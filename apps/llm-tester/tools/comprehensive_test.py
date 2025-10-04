#!/usr/bin/env python3
# File: comprehensive_test.py
# Path: /home/herb/Desktop/LLM-Tester/comprehensive_test.py
# Standard: AIDEV-PascalCase-2.1
# Created: 2025-10-04
# Last Modified: 2025-10-04 02:00AM

"""
Comprehensive test of Add and Test functions with concrete proof
"""

import sys
import time
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from LLM_Tester_Enhanced import LLMTesterEnhanced

def comprehensive_test():
    """Test both Add and Test functions with concrete evidence"""
    print("🧪 COMPREHENSIVE TEST: Add and Test Functions")
    print("=" * 60)

    app = QApplication(sys.argv)
    window = LLMTesterEnhanced()
    window.show()

    test_widget = window.test_suites
    print(f"✅ Application started")
    print(f"✅ Found {len(test_widget.suite_widgets)} test suites")

    # TEST 1: Check initial state
    first_suite = test_widget.suite_widgets[0]
    suite_name = first_suite['name']
    original_prompt_count = len(first_suite['prompts'])
    original_widget_count = len(first_suite['widgets'])

    print(f"\n📋 TEST 1: Initial State")
    print(f"   Suite: '{suite_name}'")
    print(f"   Prompts in data: {original_prompt_count}")
    print(f"   Widgets in UI: {original_widget_count}")

    # TEST 2: Try to use Add button
    print(f"\n➕ TEST 2: Testing Add Function")

    # Find + Add Prompt button
    add_button = None
    for widget in first_suite['widgets']:
        if hasattr(widget, 'text') and callable(widget.text):
            if "+ Add Prompt" in widget.text():
                add_button = widget
                break

    if add_button:
        print(f"   ✅ Found + Add Prompt button")
        print(f"   Button visible: {add_button.isVisible()}")
        print(f"   Button enabled: {add_button.isEnabled()}")

        # Force Test Suites tab to be visible
        window.tab_widget.setCurrentIndex(1)  # Test Suites tab
        QApplication.processEvents()

        print(f"   Switched to Test Suites tab")
        print(f"   Button visible after tab switch: {add_button.isVisible()}")

        if add_button.isVisible():
            print(f"   🖱️  Clicking + Add Prompt button...")
            add_button.click()
            QApplication.processEvents()

            # Wait a moment for dialog
            time.sleep(1)

            # Check if dialog appeared
            all_widgets = QApplication.topLevelWidgets()
            dialog_found = False
            for widget in all_widgets:
                if hasattr(widget, 'isWindow') and widget.isWindow() and widget != window:
                    if hasattr(widget, 'windowTitle') and 'Add Prompt' in widget.windowTitle():
                        dialog_found = True
                        print(f"   ✅ Add Prompt dialog appeared!")

                        # Fill in test prompt
                        from PySide6.QtWidgets import QTextEdit, QDialogButtonBox
                        for child in widget.children():
                            if isinstance(child, QTextEdit):
                                test_text = f"TEST PROMPT: This is a test at {time.strftime('%H:%M:%S')}"
                                child.setPlainText(test_text)
                                print(f"   ✅ Entered test text: '{test_text}'")
                                break

                        # Click OK
                        for child in widget.children():
                            if isinstance(child, QDialogButtonBox):
                                from PySide6.QtWidgets import QPushButton
                                for button in child.buttons():
                                    if button.text() == "OK":
                                        button.click()
                                        print(f"   ✅ Clicked OK button")
                                        break
                                break

                        QApplication.processEvents()
                        time.sleep(1)
                        break

            if not dialog_found:
                print(f"   ❌ Add Prompt dialog did NOT appear")
        else:
            print(f"   ❌ + Add Prompt button is NOT visible")
    else:
        print(f"   ❌ + Add Prompt button NOT found")

    # Check final state after Add attempt
    final_prompt_count = len(first_suite['prompts'])
    final_widget_count = len(first_suite['widgets'])

    print(f"\n📊 TEST 3: Results After Add Attempt")
    print(f"   Prompts in data: {final_prompt_count} (was {original_prompt_count})")
    print(f"   Widgets in UI: {final_widget_count} (was {original_widget_count})")

    if final_prompt_count > original_prompt_count:
        print(f"   ✅ SUCCESS: New prompt was added to data!")
        print(f"   New prompt: '{first_suite['prompts'][-1][:50]}...'")
    else:
        print(f"   ❌ FAILURE: No new prompt added to data")

    # TEST 3: Try to use Test button
    print(f"\n🧪 TEST 4: Testing Test Function")

    # Find a Test button
    test_button = None
    test_prompt = None
    for i, widget in enumerate(first_suite['widgets']):
        if hasattr(widget, 'text') and callable(widget.text):
            if widget.text() == "Test":
                # Find the corresponding prompt
                prompt_index = i // 5  # Each prompt has 5 widgets (label + 4 buttons)
                if prompt_index < len(first_suite['prompts']):
                    test_prompt = first_suite['prompts'][prompt_index]
                    test_button = widget
                    break

    if test_button and test_prompt:
        print(f"   ✅ Found Test button")
        print(f"   Test prompt: '{test_prompt[:50]}...'")
        print(f"   Button visible: {test_button.isVisible()}")

        # Check if any models are selected
        selected_models = window.model_library.get_selected_models()
        print(f"   Selected models: {len(selected_models)}")

        if len(selected_models) > 0:
            print(f"   Models selected: {[m.get('name', 'Unknown') for m in selected_models[:3]]}")

            if test_button.isVisible():
                print(f"   🖱️  Clicking Test button...")

                # Check current tab
                current_tab = window.tab_widget.currentIndex()
                print(f"   Current tab: {current_tab} (3=Results tab)")

                # Click test button
                test_button.click()
                QApplication.processEvents()

                # Wait for processing
                time.sleep(2)

                # Check if tab switched to Results
                new_tab = window.tab_widget.currentIndex()
                print(f"   Tab after click: {new_tab}")

                if new_tab == 3:
                    print(f"   ✅ Auto-switched to Results tab")

                    # Check if results appeared
                    results_widget = window.results
                    if hasattr(results_widget, 'results_table'):
                        row_count = results_widget.results_table.rowCount()
                        print(f"   Results table rows: {row_count}")

                        if row_count > 0:
                            print(f"   ✅ Results appeared in table!")
                        else:
                            print(f"   ❌ No results in table")
                else:
                    print(f"   ❌ Did NOT switch to Results tab")
            else:
                print(f"   ❌ Test button is NOT visible")
        else:
            print(f"   ❌ No models selected - Test button won't work")
    else:
        print(f"   ❌ Test button NOT found")

    # Final summary
    print(f"\n🎯 FINAL SUMMARY:")
    print(f"   Add button visible: {add_button.isVisible() if add_button else 'Not found'}")
    print(f"   Add functionality: {'WORKED' if final_prompt_count > original_prompt_count else 'FAILED'}")
    print(f"   Test button visible: {test_button.isVisible() if test_button else 'Not found'}")
    print(f"   Models selected: {len(selected_models) if 'selected_models' in locals() else 0}")
    print(f"   Test functionality: {'WORKED' if 'new_tab' in locals() and new_tab == 3 else 'FAILED'}")

    print(f"\n📸 This test provides concrete evidence of what's working/broken")
    print(f"⏰ Window will stay open for 10 seconds for manual verification")

    QTimer.singleShot(10000, app.quit)
    sys.exit(app.exec())

if __name__ == "__main__":
    comprehensive_test()