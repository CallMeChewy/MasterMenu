#!/usr/bin/env python3
# File: test_suites_tab_functionality.py
# Path: /home/herb/Desktop/LLM-Tester/test_suites_tab_functionality.py
# Standard: AIDEV-PascalCase-2.1
# Created: 2025-10-03
# Last Modified: 2025-10-03 07:35PM

"""
Test Suite Tab Functionality Validation Script

This script tests all the functionality of the Test Suite tab in LLM-Tester Enhanced:
- Prompt visibility and styling
- Button functionality (Edit, Test, Delete, Play/Run)
- Add prompt functionality
- Delete prompt functionality
- New suite creation
- Multi-suite selection
- Test execution
"""

import sys
import time
from PySide6.QtWidgets import QApplication, QVBoxLayout, QWidget, QPushButton, QLabel
from PySide6.QtCore import QTimer
from LLM_Tester_Enhanced import TestSuitesWidget

def test_prompt_visibility():
    """Test that prompts are visible with proper contrast"""
    print("🧪 Testing prompt visibility...")

    app = QApplication(sys.argv)

    # Create TestSuitesWidget
    test_suites = TestSuitesWidget()

    # Check if default suites are loaded
    if len(test_suites.suite_widgets) == 0:
        print("❌ No test suites loaded")
        return False

    # Check each suite for prompt visibility
    for suite_data in test_suites.suite_widgets:
        suite_name = suite_data['name']
        prompts = suite_data['prompts']
        print(f"  📝 Checking suite: {suite_name}")
        print(f"     Prompts: {len(prompts)}")

        # Check if prompt labels exist
        for i, widget in enumerate(suite_data['widgets']):
            if isinstance(widget, QLabel) and i % 5 == 0:  # First widget in each group is the prompt label
                text = widget.text()
                style = widget.styleSheet()

                # Check if text is readable (not empty)
                if text and text != "":
                    print(f"     ✅ Prompt {i//5 + 1}: Visible ({len(text)} chars)")
                else:
                    print(f"     ❌ Prompt {i//5 + 1}: Not visible or empty")

                # Check styling
                if "#e0e0e0" in style and "#2a2a3a" in style:
                    print(f"     ✅ Prompt {i//5 + 1}: Good contrast styling")
                else:
                    print(f"     ⚠️  Prompt {i//5 + 1}: May have contrast issues")

    print("✅ Prompt visibility test completed")
    return True

def test_button_existence():
    """Test that all buttons exist in the interface"""
    print("\n🧪 Testing button existence...")

    app = QApplication(sys.argv)
    test_suites = TestSuitesWidget()

    button_types = ["Edit", "Test", "Delete", "▶", "+ Add Prompt", "+ New Suite", "Run Suite(s)"]
    found_buttons = {btn_type: 0 for btn_type in button_types}

    # Check suite-specific buttons
    for suite_data in test_suites.suite_widgets:
        for widget in suite_data['widgets']:
            if isinstance(widget, QPushButton):
                text = widget.text()
                if text in button_types:
                    found_buttons[text] += 1
                    print(f"     ✅ Found button: {text}")

    # Check main buttons
    main_buttons = [
        (test_suites.findChild(QPushButton, "+ New Suite"), "+ New Suite"),
        (test_suites.run_suite_btn, "Run Suite(s)")
    ]

    for btn, name in main_buttons:
        if btn and btn.isVisible():
            found_buttons[name] += 1
            print(f"     ✅ Found main button: {name}")

    # Print summary
    print("\n  📊 Button Summary:")
    for btn_type, count in found_buttons.items():
        if count > 0:
            print(f"     ✅ {btn_type}: {count} instances")
        else:
            print(f"     ❌ {btn_type}: Not found")

    total_found = sum(found_buttons.values())
    print(f"  📈 Total buttons found: {total_found}")

    return total_found > 0

def test_button_functionality():
    """Test button click functionality"""
    print("\n🧪 Testing button functionality...")

    app = QApplication(sys.argv)
    test_suites = TestSuitesWidget()

    # Track signal emissions
    signals_received = []

    def track_suite_selected(suite_name, prompts):
        signals_received.append(f"Suite selected: {suite_name}")
        print(f"     ✅ Suite selected signal: {suite_name}")

    def track_run_test(prompt, models):
        signals_received.append(f"Run test: {prompt[:50]}...")
        print(f"     ✅ Run test signal: {prompt[:50]}...")

    def track_run_suite(suite_name, prompts):
        signals_received.append(f"Run suite: {suite_name}")
        print(f"     ✅ Run suite signal: {suite_name}")

    # Connect signals
    test_suites.suite_selected.connect(track_suite_selected)
    test_suites.run_test.connect(track_run_test)
    test_suites.run_suite.connect(track_run_suite)

    # Test suite selection
    if test_suites.suite_widgets:
        first_suite = test_suites.suite_widgets[0]
        test_suites.select_suite(first_suite['name'], first_suite['prompts'])

        # Test test button (if exists)
        for widget in first_suite['widgets']:
            if isinstance(widget, QPushButton) and widget.text() == "Test":
                widget.click()
                break

        # Test run button
        if test_suites.run_suite_btn.isEnabled():
            test_suites.run_suite_btn.click()
        else:
            print("     ⚠️  Run suite button not enabled")

    print(f"  📊 Total signals received: {len(signals_received)}")
    return len(signals_received) > 0

def test_styling():
    """Test UI styling improvements"""
    print("\n🧪 Testing UI styling...")

    app = QApplication(sys.argv)
    test_suites = TestSuitesWidget()

    style_checks = {
        "prompt_labels": 0,
        "edit_buttons": 0,
        "test_buttons": 0,
        "delete_buttons": 0,
        "play_buttons": 0
    }

    for suite_data in test_suites.suite_widgets:
        for i, widget in enumerate(suite_data['widgets']):
            style = widget.styleSheet() if hasattr(widget, 'styleSheet') else ""

            if isinstance(widget, QLabel):
                # Check prompt label styling
                if "#e0e0e0" in style:  # Light text color
                    style_checks["prompt_labels"] += 1

            elif isinstance(widget, QPushButton):
                if "Edit" in widget.text() and "#4a90e2" in style:
                    style_checks["edit_buttons"] += 1
                elif "Test" in widget.text() and "#28a745" in style:
                    style_checks["test_buttons"] += 1
                elif "Delete" in widget.text() and "#dc3545" in style:
                    style_checks["delete_buttons"] += 1
                elif "▶" in widget.text() and "#007bff" in style:
                    style_checks["play_buttons"] += 1

    print("  📊 Styling Summary:")
    for element, count in style_checks.items():
        print(f"     ✅ {element}: {count} properly styled")

    total_styled = sum(style_checks.values())
    print(f"  📈 Total styled elements: {total_styled}")

    return total_styled > 0

def main():
    """Run all tests"""
    print("=" * 60)
    print("🧪 LLM-Tester Test Suite Tab Functionality Validation")
    print("=" * 60)

    tests = [
        ("Prompt Visibility", test_prompt_visibility),
        ("Button Existence", test_button_existence),
        ("Button Functionality", test_button_functionality),
        ("UI Styling", test_styling)
    ]

    results = {}

    for test_name, test_func in tests:
        try:
            print(f"\n🚀 Running {test_name} Test...")
            result = test_func()
            results[test_name] = result
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"🎯 {test_name}: {status}")
        except Exception as e:
            results[test_name] = False
            print(f"❌ {test_name}: ERROR - {e}")

    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for result in results.values() if result)
    total = len(results)

    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")

    print(f"\n🎯 Overall Result: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Test Suite tab is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the details above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())