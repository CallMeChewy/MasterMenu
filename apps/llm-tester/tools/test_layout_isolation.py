#!/usr/bin/env python3
# File: test_layout_isolation.py
# Path: /home/herb/Desktop/LLM-Tester/test_layout_isolation.py
# Standard: AIDEV-PascalCase-2.1
# Created: 2025-10-04
# Last Modified: 2025-10-04 02:45AM

"""
Test Qt layout construction in isolation to find the exact issue
"""

import sys
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QGroupBox, QScrollArea
from PySide6.QtCore import Qt

def test_simple_layout():
    """Test the simplest possible layout construction"""
    print("🧪 Testing Simple Layout Construction")

    app = QApplication(sys.argv)

    # Create main window
    main_window = QWidget()
    main_layout = QVBoxLayout(main_window)

    # Create scroll area
    scroll = QScrollArea()
    scroll_widget = QWidget()
    scroll_layout = QVBoxLayout(scroll_widget)
    scroll.setWidget(scroll_widget)
    scroll.setWidgetResizable(True)
    main_layout.addWidget(scroll)

    # Test 1: Simple group box with layout
    print("📋 Test 1: Simple group box")
    group1 = QGroupBox("Test Group 1")
    group_layout = QVBoxLayout()  # No parent
    label1 = QLabel("Label 1")
    group_layout.addWidget(label1)
    group1.setLayout(group_layout)  # Set layout after adding widgets
    scroll_layout.addWidget(group1)

    # Test 2: Group box with header layout
    print("📋 Test 2: Group box with header layout")
    group2 = QGroupBox("Test Group 2")
    group2_layout = QVBoxLayout()  # No parent

    header_layout = QHBoxLayout()
    header_label = QLabel("Header")
    header_btn = QPushButton("Button")
    header_layout.addWidget(header_label)
    header_layout.addWidget(header_btn)
    header_layout.addStretch()

    group2_layout.addLayout(header_layout)  # This might be the issue
    group2.setLayout(group2_layout)
    scroll_layout.addWidget(group2)

    main_window.show()
    print("✅ Layout created successfully")
    print(f"   Group1 visible: {group1.isVisible()}")
    print(f"   Group1 children: {group1.children()}")
    print(f"   Group2 visible: {group2.isVisible()}")
    print(f"   Group2 children: {group2.children()}")

    # Check for layout violations in console
    app.processEvents()

    print("🎯 Test completed - check console for QLayout errors")
    app.quit()
    return True

def test_clickable_groupbox():
    """Test with ClickableGroupBox to see if that's the issue"""
    print("\n🧪 Testing ClickableGroupBox")

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    try:
        from LLM_Tester_Enhanced import ClickableGroupBox

        main_window = QWidget()
        main_layout = QVBoxLayout(main_window)

        scroll = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll.setWidget(scroll_widget)
        scroll.setWidgetResizable(True)
        main_layout.addWidget(scroll)

        # Test with ClickableGroupBox
        group = ClickableGroupBox("Test Clickable", "test_suite", ["prompt1", "prompt2"])
        group_layout = QVBoxLayout()

        header_layout = QHBoxLayout()
        header_label = QLabel("Header")
        header_btn = QPushButton("Add")
        header_layout.addWidget(header_label)
        header_layout.addWidget(header_btn)
        header_layout.addStretch()

        print("   Adding header layout to group layout...")
        group_layout.addLayout(header_layout)

        print("   Setting layout on group...")
        group.setLayout(group_layout)

        print("   Adding group to scroll layout...")
        scroll_layout.addWidget(group)

        main_window.show()
        print("✅ ClickableGroupBox created successfully")
        print(f"   Group visible: {group.isVisible()}")
        print(f"   Group children: {group.children()}")

        app.processEvents()
        print("🎯 ClickableGroupBox test completed")
        return True

    except Exception as e:
        print(f"❌ ClickableGroupBox test failed: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Qt Layout Isolation Tests")
    print("=" * 40)

    # Test 1: Simple layout
    test_simple_layout()

    # Test 2: ClickableGroupBox
    test_clickable_groupbox()

    print("\n📸 Isolation tests completed")