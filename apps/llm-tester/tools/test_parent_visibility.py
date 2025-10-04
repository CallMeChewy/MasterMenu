#!/usr/bin/env python3
# File: test_parent_visibility.py
# Path: /home/herb/Desktop/LLM-Tester/test_parent_visibility.py
# Standard: AIDEV-PascalCase-2.1
# Created: 2025-10-04
# Last Modified: 2025-10-04 01:40AM

"""
Test to check if parent widgets are visible, which would make child widgets invisible
"""

import sys
from PySide6.QtWidgets import QApplication
from LLM_Tester_Enhanced import LLMTesterEnhanced

def test_parent_visibility():
    """Check visibility of entire widget hierarchy"""
    print("🧪 Testing Widget Hierarchy Visibility...")

    app = QApplication(sys.argv)
    window = LLMTesterEnhanced()
    window.show()

    test_widget = window.test_suites
    print(f"✅ Application started")
    print(f"✅ Main window visible: {window.isVisible()}")

    # Check TestSuitesWidget visibility
    print(f"✅ TestSuitesWidget visible: {test_widget.isVisible()}")

    # Check suites_widget (the container for all suites)
    print(f"✅ suites_widget visible: {test_widget.suites_widget.isVisible()}")

    # Get first suite
    first_suite = test_widget.suite_widgets[0]
    suite_name = first_suite['name']

    # Find the group box for this suite
    group_box = None
    for i in range(test_widget.suites_layout.count()):
        widget = test_widget.suites_layout.itemAt(i).widget()
        if widget and hasattr(widget, 'title') and suite_name in widget.title():
            group_box = widget
            break

    if group_box:
        print(f"\n📋 Suite: '{suite_name}'")
        print(f"✅ GroupBox visible: {group_box.isVisible()}")
        print(f"✅ GroupBox enabled: {group_box.isEnabled()}")
        print(f"✅ GroupBox geometry: {group_box.geometry()}")
        print(f"✅ GroupBox size: {group_box.size()}")

        # Check group_box layout
        layout = group_box.layout()
        if layout:
            print(f"✅ GroupBox layout exists: {layout is not None}")
            print(f"✅ Layout count: {layout.count()}")

        # Find the + Add Prompt button
        add_button = None
        for widget in first_suite['widgets']:
            if hasattr(widget, 'text') and callable(widget.text):
                if "+ Add Prompt" in widget.text():
                    add_button = widget
                    break

        if add_button:
            print(f"\n🖱️  + Add Prompt button:")
            print(f"   - Visible: {add_button.isVisible()}")
            print(f"   - Parent visible: {add_button.parent().isVisible()}")
            print(f"   - Parent enabled: {add_button.parent().isEnabled()}")
            print(f"   - Button geometry: {add_button.geometry()}")

            # Force entire hierarchy to be visible
            print(f"\n🔧 Forcing entire hierarchy to be visible...")
            test_widget.setVisible(True)
            test_widget.suites_widget.setVisible(True)
            group_box.setVisible(True)
            group_box.show()
            add_button.setVisible(True)
            add_button.show()

            # Apply bright red styling to group box and button
            group_box.setStyleSheet("""
                QGroupBox {
                    background-color: yellow !important;
                    border: 3px solid red !important;
                    font-size: 16px !important;
                    font-weight: bold !important;
                }
            """)

            add_button.setStyleSheet("""
                QPushButton {
                    background-color: red !important;
                    color: white !important;
                    border: 2px solid blue !important;
                    font-size: 14px !important;
                    font-weight: bold !important;
                }
            """)

            QApplication.processEvents()

            print(f"   After forcing:")
            print(f"   - GroupBox visible: {group_box.isVisible()}")
            print(f"   - Button visible: {add_button.isVisible()}")

            print(f"\n🖼️  Look for YELLOW group box with RED button in '{suite_name}' section")

    else:
        print(f"❌ Could not find group box for suite '{suite_name}'")

    print(f"\n⏰ Window will stay open for 15 seconds")
    from PySide6.QtCore import QTimer
    QTimer.singleShot(15000, app.quit)
    sys.exit(app.exec())

if __name__ == "__main__":
    test_parent_visibility()