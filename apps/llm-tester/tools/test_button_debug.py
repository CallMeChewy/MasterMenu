#!/usr/bin/env python3
# File: test_button_debug.py
# Path: /home/herb/Desktop/LLM-Tester/test_button_debug.py
# Standard: AIDEV-PascalCase-2.1
# Created: 2025-10-03
# Last Modified: 2025-10-03 07:40PM

"""
Button Debugging Test Script

Tests if button click handlers are properly connected and working
"""

import sys
from PySide6.QtWidgets import QApplication, QPushButton, QVBoxLayout, QWidget, QLabel
from PySide6.QtCore import QObject

def test_basic_button_functionality():
    """Test basic button functionality"""
    print("🧪 Testing basic button functionality...")

    app = QApplication(sys.argv)

    # Create test window
    window = QWidget()
    layout = QVBoxLayout(window)

    # Track clicks
    click_count = 0

    def on_button_click():
        nonlocal click_count
        click_count += 1
        print(f"✅ Button clicked! Total clicks: {click_count}")

    # Create button
    button = QPushButton("Test Button")
    button.clicked.connect(on_button_click)
    layout.addWidget(button)

    # Status label
    status_label = QLabel("Click the button to test")
    layout.addWidget(status_label)

    window.show()

    # Simulate button click
    button.click()

    # Check if click was registered
    if click_count > 0:
        print("✅ Basic button functionality working")
        return True
    else:
        print("❌ Basic button functionality failed")
        return False

def test_signal_connection():
    """Test Qt signal connections"""
    print("\n🧪 Testing Qt signal connections...")

    app = QApplication(sys.argv)

    # Create test button
    button = QPushButton("Signal Test")

    # Track signal emissions
    signal_received = False

    def on_signal():
        nonlocal signal_received
        signal_received = True
        print("✅ Signal received!")

    # Connect signal
    connection = button.clicked.connect(on_signal)

    # Check connection
    if button.receivers(button.clicked) > 0:
        print("✅ Signal connection established")

        # Emit signal
        button.click()

        if signal_received:
            print("✅ Signal emission working")
            return True
        else:
            print("❌ Signal emission failed")
            return False
    else:
        print("❌ Signal connection failed")
        return False

def test_lambda_connections():
    """Test lambda function connections with loop variables"""
    print("\n🧪 Testing lambda connections...")

    app = QApplication(sys.argv)

    results = []

    # Create multiple buttons like in the real app
    for i in range(3):
        button = QPushButton(f"Button {i}")

        # This mimics the pattern used in LLM-Tester
        button.clicked.connect(lambda checked, idx=i: results.append(f"Button {idx} clicked"))

    # Click each button
    for i in range(3):
        # Find the button and click it (simplified)
        button = QApplication.instance().findChild(QPushButton, f"Button {i}")
        if button:
            button.click()

    # Check results
    if len(results) == 3:
        print("✅ Lambda connections working correctly")
        for result in results:
            print(f"  📝 {result}")
        return True
    else:
        print(f"❌ Lambda connections failed. Expected 3 results, got {len(results)}")
        return False

def main():
    """Run all debugging tests"""
    print("=" * 60)
    print("🧪 Button Functionality Debugging Tests")
    print("=" * 60)

    tests = [
        ("Basic Button Functionality", test_basic_button_functionality),
        ("Signal Connection", test_signal_connection),
        ("Lambda Connections", test_lambda_connections)
    ]

    results = {}
    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = result
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"🎯 {test_name}: {status}")
        except Exception as e:
            results[test_name] = False
            print(f"❌ {test_name}: ERROR - {e}")

    # Summary
    passed = sum(1 for result in results.values() if result)
    total = len(results)

    print(f"\n📊 Debug Test Summary: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All button functionality tests passed!")
        print("If real buttons aren't working, the issue might be:")
        print("  - UI not properly refreshed")
        print("  - Buttons disabled or hidden")
        print("  - Event loop issues")
        print("  - Parent widget problems")
    else:
        print("⚠️  Some basic button tests failed - Qt may have issues")

    return passed == total

if __name__ == "__main__":
    sys.exit(main())