#!/usr/bin/env python3
# File: test_minimal_layout.py
# Path: /home/herb/Desktop/LLM-Tester/test_minimal_layout.py
# Standard: AIDEV-PascalCase-2.1
# Created: 2025-10-04
# Last Modified: 2025-10-04 01:10AM

"""
Minimal test to reproduce Qt layout violation
"""

import sys
from PySide6.QtWidgets import QApplication, QVBoxLayout, QHBoxLayout, QWidget, QGroupBox, QLabel, QPushButton

def test_minimal_layout():
    """Test minimal layout construction to identify violation"""
    print("🧪 Testing Minimal Layout Construction...")

    app = QApplication(sys.argv)

    # Test 1: Correct approach - what we want to work
    print("\n✅ Test 1: Correct layout construction")
    group_box = QGroupBox("Test Group")
    group_layout = QVBoxLayout()  # No parent initially

    header_layout = QHBoxLayout()
    header_layout.addWidget(QLabel("Header"))
    header_layout.addWidget(QPushButton("Button"))

    group_layout.addLayout(header_layout)  # Add layout to layout
    group_layout.addWidget(QLabel("Content"))

    group_box.setLayout(group_layout)  # Set layout on widget last
    print("   ✅ No error with correct approach")

    # Test 2: Incorrect approach - what causes the error
    print("\n❌ Test 2: Incorrect layout construction (causes violation)")
    try:
        group_box2 = QGroupBox("Test Group 2")
        group_layout2 = QVBoxLayout(group_box2)  # Set parent immediately

        header_layout2 = QHBoxLayout()
        header_layout2.addWidget(QLabel("Header 2"))
        header_layout2.addWidget(QPushButton("Button 2"))

        group_layout2.addLayout(header_layout2)  # This should cause the error
        print("   ❌ ERROR: This should have failed but didn't?")
    except Exception as e:
        print(f"   ✅ Expected error caught: {e}")

    print("\n🎯 Test completed - check for Qt layout violation errors above")

    # Show the working widget
    group_box.show()

    # Keep window open briefly to see if it appears
    from PySide6.QtCore import QTimer
    QTimer.singleShot(3000, app.quit)
    sys.exit(app.exec())

if __name__ == "__main__":
    test_minimal_layout()