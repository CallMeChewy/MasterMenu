#!/usr/bin/env python3
# File: test_isolated_layout.py
# Path: /home/herb/Desktop/LLM-Tester/test_isolated_layout.py
# Standard: AIDEV-PascalCase-2.1
# Created: 2025-10-04
# Last Modified: 2025-10-04 01:15AM

"""
Isolated test of the exact add_suite_group logic to identify the Qt layout violation
"""

import sys
from PySide6.QtWidgets import (QApplication, QVBoxLayout, QHBoxLayout, QWidget,
                               QGroupBox, QLabel, QPushButton, QCheckBox, QScrollArea)

class ClickableGroupBox(QGroupBox):
    """A QGroupBox that can be clicked to select a test suite"""
    def __init__(self, title, suite_name, prompts):
        super().__init__(title)
        self.suite_name = suite_name
        self.prompts = prompts

    def mousePressEvent(self, event):
        """Handle mouse press events"""
        super().mousePressEvent(event)

def test_isolated_add_suite_group():
    """Test the exact logic from add_suite_group"""
    print("🧪 Testing Isolated add_suite_group Logic...")

    app = QApplication(sys.argv)

    # Create main widget similar to TestSuiteWidget
    main_widget = QWidget()
    main_widget.setWindowTitle("Layout Test")
    main_widget.setGeometry(100, 100, 800, 600)

    layout = QVBoxLayout(main_widget)

    # Test suite categories (similar to TestSuiteWidget)
    suites_scroll = QScrollArea()
    suites_widget = QWidget()
    suites_layout = QVBoxLayout(suites_widget)
    suites_scroll.setWidget(suites_widget)
    suites_scroll.setWidgetResizable(True)
    layout.addWidget(suites_scroll)

    # Test suite data
    suite = {
        'icon': '🔧',
        'name': 'Code Generation',
        'prompts': [
            'Create a Python function that calculates factorial',
            'Write a program to sort an array',
            'Create a function that validates email addresses',
            'Write a recursive function for Fibonacci sequence',
            'Create a class representing a bank account'
        ]
    }

    print(f"✅ Creating suite: {suite['name']}")

    # Exact logic from add_suite_group
    print("   🏗️  Creating ClickableGroupBox...")
    group_box = ClickableGroupBox(f"{suite['icon']} {suite['name']}", suite['name'], suite['prompts'])
    print("   ✅ ClickableGroupBox created")

    print("   🏗️  Creating group_layout without parent...")
    group_layout = QVBoxLayout()  # Don't set parent yet
    print("   ✅ group_layout created")

    print("   🏗️  Creating header_layout...")
    # Add selection checkbox for multi-suite mode
    header_layout = QHBoxLayout()
    suite_checkbox = QCheckBox()
    suite_checkbox.setObjectName(f"checkbox_{suite['name']}")
    header_layout.addWidget(suite_checkbox)
    print("   ✅ checkbox added to header_layout")

    suite_label = QLabel(suite['name'])
    suite_label.setStyleSheet("font-weight: bold;")
    header_layout.addWidget(suite_label)
    print("   ✅ label added to header_layout")

    # Add prompt button (before stretch so it's visible)
    add_prompt_btn = QPushButton("+ Add Prompt")
    add_prompt_btn.setStyleSheet("QPushButton { font-size: 11px; padding: 2px 8px; background-color: #17a2b8; color: white; border: 1px solid #138496; border-radius: 3px; } QPushButton:hover { background-color: #138496; }")
    add_prompt_btn.setParent(group_box)  # Set parent explicitly
    add_prompt_btn.setVisible(True)  # Ensure button is visible
    add_prompt_btn.setEnabled(True)  # Ensure button is enabled
    header_layout.addWidget(add_prompt_btn)
    header_layout.update()  # Force layout update
    print("   ✅ + Add Prompt button added to header_layout")

    # Prompt count
    prompt_count_label = QLabel(f"{len(suite['prompts'])} prompts")
    prompt_count_label.setStyleSheet("color: gray; font-size: 10px;")
    prompt_count_label.setObjectName(f"count_{suite['name']}")
    header_layout.addWidget(prompt_count_label)
    print("   ✅ prompt count label added to header_layout")

    # Add stretch at the end to push everything to the left
    header_layout.addStretch()
    print("   ✅ stretch added to header_layout")

    print("   🔗 Adding header_layout to group_layout...")
    group_layout.addLayout(header_layout)
    print("   ✅ header_layout added to group_layout")

    print("   📝 Adding prompts...")
    for i, prompt in enumerate(suite['prompts']):
        print(f"      Adding prompt {i+1}: '{prompt[:30]}...'")
        prompt_layout = QHBoxLayout()

        # Prompt label with tooltip
        prompt_label = QLabel(f"[{prompt[:200]}...]" if len(prompt) > 200 else f"[{prompt}]")
        prompt_label.setWordWrap(True)
        prompt_label.setToolTip(prompt)
        prompt_label.setStyleSheet("margin-left: 20px; color: #e0e0e0; padding: 4px; background-color: #2a2a3a; border-radius: 4px; border: 1px solid #444;")
        prompt_label.setMinimumWidth(400)
        prompt_layout.addWidget(prompt_label, 1)

        # Control buttons
        edit_btn = QPushButton("Edit")
        edit_btn.setMaximumWidth(60)
        edit_btn.setStyleSheet("QPushButton { font-size: 11px; padding: 4px; background-color: #4a90e2; color: white; border: 1px solid #357abd; border-radius: 3px; } QPushButton:hover { background-color: #357abd; }")
        prompt_layout.addWidget(edit_btn)

        test_btn = QPushButton("Test")
        test_btn.setMaximumWidth(60)
        test_btn.setStyleSheet("QPushButton { font-size: 11px; padding: 4px; background-color: #28a745; color: white; border: 1px solid #1e7e34; border-radius: 3px; } QPushButton:hover { background-color: #218838; }")
        prompt_layout.addWidget(test_btn)

        delete_btn = QPushButton("Delete")
        delete_btn.setMaximumWidth(70)
        delete_btn.setStyleSheet("QPushButton { font-size: 11px; padding: 4px; background-color: #dc3545; color: white; border: 1px solid #c82333; border-radius: 3px; } QPushButton:hover { background-color: #c82333; }")
        prompt_layout.addWidget(delete_btn)

        play_btn = QPushButton("▶")
        play_btn.setMaximumWidth(40)
        play_btn.setStyleSheet("QPushButton { font-size: 11px; padding: 4px; background-color: #007bff; color: white; border: 1px solid #0056b3; border-radius: 3px; } QPushButton:hover { background-color: #0056b3; }")
        prompt_layout.addWidget(play_btn)

        print(f"      🔗 Adding prompt_layout {i+1} to group_layout...")
        group_layout.addLayout(prompt_layout)
        print(f"      ✅ prompt_layout {i+1} added")

    print("   🎯 Setting group_layout on group_box...")
    # Set the layout on the group box after all child layouts are added
    group_box.setLayout(group_layout)
    print("   ✅ Layout set on group_box")

    print("   📦 Adding group_box to suites_layout...")
    suites_layout.addWidget(group_box)
    print("   ✅ group_box added to suites_layout")

    print("   🖼️  Showing main widget...")
    main_widget.show()

    print("\n🎯 Test completed - check for Qt layout violation errors above")
    print("   If no errors, the issue might be elsewhere in the code")

    # Keep window open to see if widgets are visible
    from PySide6.QtCore import QTimer
    QTimer.singleShot(10000, app.quit)
    sys.exit(app.exec())

if __name__ == "__main__":
    test_isolated_add_suite_group()