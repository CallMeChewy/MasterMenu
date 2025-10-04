#!/usr/bin/env python3
# File: test_exact_pattern.py
# Path: /home/herb/Desktop/LLM-Tester/test_exact_pattern.py
# Standard: AIDEV-PascalCase-2.1
# Created: 2025-10-04
# Last Modified: 2025-10-04 02:50AM

"""
Test the exact pattern used in the main application to reproduce the issue
"""

import sys
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QGroupBox, QScrollArea
from PySide6.QtCore import Qt, Signal

class ClickableGroupBox(QGroupBox):
    """A QGroupBox that can be clicked to select a test suite"""
    suite_selected = Signal(str, list)
    def __init__(self, title, suite_name, prompts):
        super().__init__(title)
        self.suite_name = suite_name
        self.prompts = prompts
    def mousePressEvent(self, event):
        """Handle mouse press events"""
        if event.button() == Qt.LeftButton:
            self.suite_selected.emit(self.suite_name, self.prompts)
        super().mousePressEvent(event)

class TestSuitesWidgetExact(QWidget):
    """Exact replica of TestSuitesWidget pattern"""
    def __init__(self):
        super().__init__()
        self.suite_widgets = []
        self.init_ui()
        self.load_default_suites()

    def init_ui(self):
        layout = QVBoxLayout(self)  # Parent set immediately

        # Header
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("📝 Test Suites"))
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Test suite categories - EXACT same pattern as main app
        self.suites_scroll = QScrollArea()
        self.suites_widget = QWidget()
        self.suites_layout = QVBoxLayout(self.suites_widget)  # Parent set immediately
        self.suites_scroll.setWidget(self.suites_widget)
        self.suites_scroll.setWidgetResizable(True)
        layout.addWidget(self.suites_scroll)

    def load_default_suites(self):
        """Load default test suites - EXACT same pattern"""
        default_suites = [
            {
                'name': 'Code Generation',
                'icon': '💻',
                'prompts': [
                    'Create a Python function that calculates fibonacci numbers',
                    'Write a program to sort a list of numbers',
                    'Create a function to validate email addresses',
                    'Write a program that reads a CSV file',
                    'Create a function to generate random passwords'
                ]
            }
        ]

        for suite in default_suites:
            self.add_suite_group(suite)

    def add_suite_group(self, suite):
        """EXACT same pattern as main app - this should reproduce the issue"""
        print(f"🔧 Adding suite group: {suite['name']}")

        group_box = ClickableGroupBox(f"{suite['icon']} {suite['name']}", suite['name'], suite['prompts'])
        group_layout = QVBoxLayout()  # Create layout without parent first

        # Add selection checkbox for multi-suite mode
        header_layout = QHBoxLayout()
        suite_checkbox = QLabel("Checkbox")  # Simplified
        header_layout.addWidget(suite_checkbox)

        suite_label = QLabel(suite['name'])
        suite_label.setStyleSheet("font-weight: bold;")
        header_layout.addWidget(suite_label)

        # Add prompt button (before stretch so it's visible)
        add_prompt_btn = QPushButton("+ Add Prompt")
        add_prompt_btn.setStyleSheet("QPushButton { font-size: 11px; padding: 2px 8px; background-color: #17a2b8; color: white; border: 1px solid #138496; border-radius: 3px; }")
        header_layout.addWidget(add_prompt_btn)

        # Prompt count
        prompt_count_label = QLabel(f"{len(suite['prompts'])} prompts")
        prompt_count_label.setStyleSheet("color: gray; font-size: 10px;")
        header_layout.addWidget(prompt_count_label)

        header_layout.addStretch()

        print("   Adding header layout to group layout...")
        group_layout.addLayout(header_layout)

        # Add some prompt layouts
        for i, prompt in enumerate(suite['prompts'][:2]):  # Just 2 for testing
            prompt_layout = QHBoxLayout()

            prompt_label = QLabel(f"[{prompt[:50]}...]" if len(prompt) > 50 else f"[{prompt}]")
            prompt_layout.addWidget(prompt_label, 1)

            edit_btn = QPushButton("Edit")
            prompt_layout.addWidget(edit_btn)

            test_btn = QPushButton("Test")
            prompt_layout.addWidget(test_btn)

            print(f"   Adding prompt layout {i} to group layout...")
            group_layout.addLayout(prompt_layout)

        # Set the layout on the group box after all child layouts are added
        print("   Setting layout on group box...")
        group_box.setLayout(group_layout)

        print("   Adding group box to suites layout...")
        self.suites_layout.addWidget(group_box)

        suite_data = {
            'name': suite['name'],
            'prompts': suite['prompts'],
            'widgets': [add_prompt_btn, prompt_count_label],
            'checkbox': suite_checkbox
        }
        self.suite_widgets.append(suite_data)

        print(f"   ✅ Suite group added: {suite['name']}")

def test_exact_pattern():
    """Test the exact pattern that causes the issue"""
    print("🧪 Testing Exact Application Pattern")

    app = QApplication(sys.argv)
    widget = TestSuitesWidgetExact()
    widget.show()

    print("✅ Widget created and shown")
    print(f"   Widget visible: {widget.isVisible()}")
    print(f"   Suite widgets: {len(widget.suite_widgets)}")

    if widget.suite_widgets:
        first_suite = widget.suite_widgets[0]
        print(f"   First suite widgets: {len(first_suite['widgets'])}")
        for i, w in enumerate(first_suite['widgets'][:3]):  # Check first 3 widgets
            print(f"   Widget {i}: Visible={w.isVisible()}, Text={getattr(w, 'text', lambda: 'N/A')()}")

    app.processEvents()

    print("🎯 Check console for QLayout errors above")
    print("   If no errors, the pattern works. If errors, this reproduces the issue.")

    # Keep window open briefly to see
    from PySide6.QtCore import QTimer
    QTimer.singleShot(3000, app.quit)
    app.exec()

    return True

if __name__ == "__main__":
    test_exact_pattern()