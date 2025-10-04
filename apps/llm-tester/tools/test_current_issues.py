#!/usr/bin/env python3
# File: test_current_issues.py
# Path: /home/herb/Desktop/LLM-Tester/test_current_issues.py
# Standard: AIDEV-PascalCase-2.1
# Created: 2025-10-04
# Last Modified: 2025-10-04 12:35AM

"""
Test script to investigate current issues:
1. Add operation not showing widgets in UI
2. Test button functionality and model selection
3. Model population issues
"""

import sys
import time
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from LLM_Tester_Enhanced import LLMTesterEnhanced

def test_current_issues():
    """Test current issues reported by user"""
    print("🔍 Investigating Current Issues...")

    app = QApplication(sys.argv)
    window = LLMTesterEnhanced()
    window.show()

    # Get the TestSuitesWidget
    test_widget = window.test_suites
    model_library = window.model_library

    print(f"✅ Application started successfully")
    print(f"✅ Found {len(test_widget.suite_widgets)} test suites")

    # Check model library status
    selected_models = model_library.get_selected_models()
    print(f"🤖 Selected models: {len(selected_models)}")
    if selected_models:
        for model in selected_models:
            print(f"   - {model}")
    else:
        print("   ❌ No models selected - this explains Test button issue")

    # Check total available models
    if hasattr(model_library, 'all_models_data'):
        print(f"📊 Total models in library: {len(model_library.all_models_data)}")
        if model_library.all_models_data:
            print("   Available models:")
            for model_data in model_library.all_models_data[:5]:  # Show first 5
                print(f"   - {model_data.get('name', 'Unknown')}")
        else:
            print("   ❌ No models loaded in library")
    else:
        print("   ❌ Model library not properly initialized")

    # Test Add operation manually
    print(f"\n➕ Testing Add Operation...")
    first_suite = test_widget.suite_widgets[0]
    suite_name = first_suite['name']
    original_count = len(first_suite['prompts'])
    print(f"   Suite: '{suite_name}'")
    print(f"   Original prompt count: {original_count}")

    # Simulate adding a prompt
    new_prompt_text = "TEST ADD: This prompt was added during investigation"
    first_suite['prompts'].append(new_prompt_text)
    print(f"   ✅ Added to data structure: {original_count} → {len(first_suite['prompts'])}")

    # Check if we can find the group box
    group_box_found = False
    for i in range(test_widget.suites_layout.count()):
        widget = test_widget.suites_layout.itemAt(i).widget()
        if widget and hasattr(widget, 'title'):
            if suite_name in widget.title():
                group_box_found = True
                print(f"   ✅ Found group box for suite: '{suite_name}'")
                break

    if not group_box_found:
        print(f"   ❌ Could not find group box - this might be the Add issue")

    print(f"\n🎯 Investigation Summary:")
    print(f"   1. Application starts: ✅")
    print(f"   2. Test suites loaded: ✅ ({len(test_widget.suite_widgets)})")
    print(f"   3. Models selected: ❌ ({len(selected_models)} models)")
    print(f"   4. Models in library: {'✅' if hasattr(model_library, 'all_models_data') and model_library.all_models_data else '❌'}")
    print(f"   5. Add data structure: ✅ (prompts list updated)")
    print(f"   6. Group box found: {'✅' if group_box_found else '❌'}")

    print(f"\n📝 Root Cause Analysis:")
    if not selected_models:
        print(f"   - Test button doesn't work because no models are selected")
        print(f"   - Need to check model loading and selection mechanism")

    if not group_box_found:
        print(f"   - Add operation may not show UI because group box detection fails")
        print(f"   - Need to verify ClickableGroupBox detection logic")

    # Keep window open for manual testing
    print(f"\n🖱️  Manual Testing Instructions:")
    print(f"   1. Try clicking Test buttons - should show 'No models selected' in console")
    print(f"   2. Try clicking + Add Prompt - check if widgets appear in UI")
    print(f"   3. Check Model Selection tab - see if models are listed there")
    print(f"   4. Select some models and try Test buttons again")

    QTimer.singleShot(30000, app.quit)  # 30 seconds for manual testing
    sys.exit(app.exec())

if __name__ == "__main__":
    test_current_issues()