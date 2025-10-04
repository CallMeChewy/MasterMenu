#!/usr/bin/env python3
# File: test_tab_visibility.py
# Path: /home/herb/Desktop/LLM-Tester/test_tab_visibility.py
# Standard: AIDEV-PascalCase-2.1
# Created: 2025-10-04
# Last Modified: 2025-10-04 01:45AM

"""
Test to check if the Test Suites tab is visible and properly configured
"""

import sys
from PySide6.QtWidgets import QApplication
from LLM_Tester_Enhanced import LLMTesterEnhanced

def test_tab_visibility():
    """Check tab widget and Test Suites tab visibility"""
    print("🧪 Testing Tab Widget Visibility...")

    app = QApplication(sys.argv)
    window = LLMTesterEnhanced()
    window.show()

    print(f"✅ Application started")
    print(f"✅ Main window visible: {window.isVisible()}")

    # Check tab widget
    tab_widget = window.tab_widget
    print(f"✅ Tab widget visible: {tab_widget.isVisible()}")
    print(f"✅ Tab widget count: {tab_widget.count()}")
    print(f"✅ Current tab index: {tab_widget.currentIndex()}")

    # Find Test Suites tab
    test_suites_tab_index = -1
    for i in range(tab_widget.count()):
        tab_text = tab_widget.tabText(i)
        print(f"   Tab {i}: '{tab_text}'")
        if "Test Suites" in tab_text:
            test_suites_tab_index = i
            print(f"      ✅ Found Test Suites tab at index {i}")
            break

    if test_suites_tab_index >= 0:
        print(f"\n📋 Test Suites Tab Details:")
        test_suites_widget = tab_widget.widget(test_suites_tab_index)
        print(f"✅ Tab widget visible: {test_suites_widget.isVisible()}")
        print(f"✅ Tab widget enabled: {test_suites_widget.isEnabled()}")
        print(f"✅ Tab widget size: {test_suites_widget.size()}")
        print(f"✅ Tab widget geometry: {test_suites_widget.geometry()}")

        # Switch to Test Suites tab
        print(f"\n🔄 Switching to Test Suites tab...")
        tab_widget.setCurrentIndex(test_suites_tab_index)
        QApplication.processEvents()

        print(f"✅ Current tab index after switch: {tab_widget.currentIndex()}")
        print(f"✅ Test Suites widget visible after switch: {test_suites_widget.isVisible()}")

        # Force visibility
        print(f"\n🔧 Forcing Test Suites tab widget to be visible...")
        test_suites_widget.setVisible(True)
        test_suites_widget.show()
        QApplication.processEvents()

        print(f"✅ Test Suites widget visible after forcing: {test_suites_widget.isVisible()}")

        # Check the suites_widget inside the TestSuitesWidget
        if hasattr(test_suites_widget, 'suites_widget'):
            print(f"✅ suites_widget visible: {test_suites_widget.suites_widget.isVisible()}")

            # Force the entire hierarchy to be visible
            test_suites_widget.suites_widget.setVisible(True)
            test_suites_widget.suites_widget.show()
            QApplication.processEvents()

            print(f"✅ suites_widget visible after forcing: {test_suites_widget.suites_widget.isVisible()}")

        print(f"\n🖼️  The Test Suites tab should now be visible and functional")
        print(f"🖱️  Look for the Test Suites tab and click on it")

    else:
        print(f"❌ Could not find Test Suites tab")

    print(f"\n⏰ Window will stay open for 20 seconds")
    from PySide6.QtCore import QTimer
    QTimer.singleShot(20000, app.quit)
    sys.exit(app.exec())

if __name__ == "__main__":
    test_tab_visibility()