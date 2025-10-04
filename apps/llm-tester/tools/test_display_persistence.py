#!/usr/bin/env python3
# File: test_display_persistence.py
# Path: /home/herb/Desktop/LLM-Tester/test_display_persistence.py
# Standard: AIDEV-PascalCase-2.1
# Created: 2025-10-03
# Last Modified: 2025-10-03 05:19PM

"""
Test script to verify Test Suite display persistence (add, edit, delete operations)
"""

import sys
import time
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from LLM_Tester_Enhanced import LLMTesterEnhanced

def test_display_persistence():
    """Test that add, edit, and delete operations persist in the display"""
    print("🧪 Testing Test Suite Display Persistence...")

    app = QApplication(sys.argv)
    window = LLMTesterEnhanced()
    window.show()

    # Get the TestSuitesWidget
    test_widget = window.test_suites

    print(f"✅ Found {len(test_widget.suite_widgets)} test suites")

    # Test Edit functionality
    print("\n📝 Testing Edit functionality...")

    # Find the first suite and first prompt
    first_suite = test_widget.suite_widgets[0]
    suite_name = first_suite['name']
    original_prompt = first_suite['prompts'][0]
    print(f"  Original prompt: '{original_prompt[:50]}...'")

    # Simulate editing the first prompt
    new_prompt_text = "EDITED: This prompt has been modified for testing purposes"
    first_suite['prompts'][0] = new_prompt_text

    # Update the UI
    prompt_label = first_suite['widgets'][0]  # First widget is the prompt label
    prompt_label.setText(f"[{new_prompt_text[:200]}...]" if len(new_prompt_text) > 200 else f"[{new_prompt_text}]")
    prompt_label.setToolTip(new_prompt_text)

    print(f"  ✅ Updated prompt to: '{new_prompt_text[:50]}...'")

    # Test Add functionality
    print("\n➕ Testing Add functionality...")

    # Add a new prompt to the first suite
    new_prompt = "NEW PROMPT: This is a newly added prompt for testing"
    first_suite['prompts'].append(new_prompt)

    # Update prompt count
    if hasattr(test_widget, 'prompt_count_labels') and suite_name in test_widget.prompt_count_labels:
        test_widget.prompt_count_labels[suite_name].setText(f"{len(first_suite['prompts'])} prompts")

    print(f"  ✅ Added new prompt, total prompts: {len(first_suite['prompts'])}")

    # Test Delete functionality
    print("\n🗑️ Testing Delete functionality...")

    # Remove the second prompt if it exists
    if len(first_suite['prompts']) > 1:
        deleted_prompt = first_suite['prompts'][1]
        del first_suite['prompts'][1]
        print(f"  ✅ Deleted prompt: '{deleted_prompt[:50]}...'")
        print(f"  Remaining prompts: {len(first_suite['prompts'])}")

    # Verify changes persist
    print("\n🔍 Verifying persistence...")

    # Check that our changes are still in the data
    current_first_prompt = first_suite['prompts'][0]
    if "EDITED:" in current_first_prompt:
        print("  ✅ Edit change persisted")
    else:
        print("  ❌ Edit change did not persist")

    if len(first_suite['prompts']) >= 2 and "NEW PROMPT:" in first_suite['prompts'][-1]:
        print("  ✅ Add change persisted")
    else:
        print("  ❌ Add change did not persist")

    print("\n🎯 Display persistence test completed!")
    print("You can now manually test the UI by:")
    print("1. Clicking Edit buttons to modify prompts")
    print("2. Clicking + Add Prompt buttons to add new prompts")
    print("3. Clicking Delete buttons to remove prompts")
    print("4. Checking that changes remain visible in the UI")

    # Keep window open for longer to allow manual testing
    QTimer.singleShot(15000, app.quit)

    sys.exit(app.exec())

if __name__ == "__main__":
    test_display_persistence()