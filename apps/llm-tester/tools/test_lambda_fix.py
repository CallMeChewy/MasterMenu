#!/usr/bin/env python3
# File: test_lambda_fix.py
# Path: /home/herb/Desktop/LLM-Tester/test_lambda_fix.py
# Standard: AIDEV-PascalCase-2.1
# Created: 2025-10-04
# Last Modified: 2025-10-04 02:15AM

"""
Test if the lambda variable capture fixes resolve the Test/Play button errors
"""

import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from LLM_Tester_Enhanced import LLMTesterEnhanced

def test_lambda_fix():
    """Test if lambda fixes resolved the button errors"""
    print("🔧 TESTING LAMBDA FIXES")
    print("=" * 40)

    app = QApplication(sys.argv)
    window = LLMTesterEnhanced()
    window.show()

    test_widget = window.test_suites
    print(f"✅ Application started")

    # Switch to Test Suites tab
    window.tab_widget.setCurrentIndex(1)
    QApplication.processEvents()
    print(f"✅ Switched to Test Suites tab")

    # Get first suite
    first_suite = test_widget.suite_widgets[0]
    suite_name = first_suite['name']
    print(f"✅ Suite: '{suite_name}'")

    # Find Test button
    test_button = None
    test_prompt = None
    for i, widget in enumerate(first_suite['widgets']):
        if hasattr(widget, 'text') and callable(widget.text):
            if widget.text() == "Test":
                # Find corresponding prompt
                prompt_index = i // 5
                if prompt_index < len(first_suite['prompts']):
                    test_prompt = first_suite['prompts'][prompt_index]
                    test_button = widget
                    break

    # Find Play button
    play_button = None
    for i, widget in enumerate(first_suite['widgets']):
        if hasattr(widget, 'text') and callable(widget.text):
            if widget.text() == "▶":
                play_button = widget
                break

    print(f"\n🧪 TEST BUTTON:")
    if test_button:
        print(f"   ✅ Test button found: {test_button.isVisible()}")
        print(f"   📝 Prompt: '{test_prompt[:30] if test_prompt else 'None'}...'")

        # Mock the test function to see if it gets called correctly
        original_test = test_widget.test_single_prompt
        test_called_correctly = False

        def mock_test_single_prompt(prompt):
            nonlocal test_called_correctly
            test_called_correctly = True
            print(f"   ✅ Test function called with: '{prompt[:30]}...'")
            print(f"   ✅ Type: {type(prompt)}")
            print(f"   ✅ Length: {len(prompt)}")

        test_widget.test_single_prompt = mock_test_single_prompt

        # Click test button
        test_button.click()
        QApplication.processEvents()

        # Restore original
        test_widget.test_single_prompt = original_test

        if test_called_correctly:
            print(f"   🎉 TEST BUTTON: WORKING! ✅")
        else:
            print(f"   ❌ TEST BUTTON: FAILED")

    print(f"\n▶️  PLAY BUTTON:")
    if play_button:
        print(f"   ✅ Play button found: {play_button.isVisible()}")

        # Mock the run function to see if it gets called correctly
        original_run = test_widget.run_prompt
        run_called_correctly = False

        def mock_run_prompt(prompt):
            nonlocal run_called_correctly
            run_called_correctly = True
            print(f"   ✅ Run function called with: '{prompt[:30]}...'")
            print(f"   ✅ Type: {type(prompt)}")
            print(f"   ✅ Length: {len(prompt)}")

        test_widget.run_prompt = mock_run_prompt

        # Click play button
        play_button.click()
        QApplication.processEvents()

        # Restore original
        test_widget.run_prompt = original_run

        if run_called_correctly:
            print(f"   🎉 PLAY BUTTON: WORKING! ✅")
        else:
            print(f"   ❌ PLAY BUTTON: FAILED")

    print(f"\n🏁 SUMMARY:")
    print(f"   Test button: {'WORKING ✅' if 'test_called_correctly' in locals() and test_called_correctly else 'FAILED ❌'}")
    print(f"   Play button: {'WORKING ✅' if 'run_called_correctly' in locals() and run_called_correctly else 'FAILED ❌'}")

    print(f"\n📸 LAMBDA VARIABLE CAPTURE FIXES TESTED")
    print(f"⏰ Window will stay open for 5 seconds")

    QTimer.singleShot(5000, app.quit)
    sys.exit(app.exec())

if __name__ == "__main__":
    test_lambda_fix()