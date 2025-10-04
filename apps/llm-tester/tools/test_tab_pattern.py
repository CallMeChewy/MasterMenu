#!/usr/bin/env python3
# File: test_tab_pattern.py
# Path: /home/herb/Desktop/LLM-Tester/test_tab_pattern.py
# Standard: AIDEV-PascalCase-2.1
# Created: 2025-10-04
# Last Modified: 2025-10-04 02:55AM

"""
Test with tab widget to see if that's causing visibility issues
"""

import sys
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QGroupBox, QScrollArea, QTabWidget
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

class TestSuitesWidgetWithTab(QWidget):
    """Test Suites Widget inside a tab"""
    def __init__(self):
        super().__init__()
        self.suite_widgets = []
        self.init_ui()
        self.load_default_suites()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Header
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("📝 Test Suites"))
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Test suite categories
        self.suites_scroll = QScrollArea()
        self.suites_widget = QWidget()
        self.suites_layout = QVBoxLayout(self.suites_widget)
        self.suites_scroll.setWidget(self.suites_widget)
        self.suites_scroll.setWidgetResizable(True)
        layout.addWidget(self.suites_scroll)

    def load_default_suites(self):
        default_suites = [
            {
                'name': 'Code Generation',
                'icon': '💻',
                'prompts': ['Test prompt 1', 'Test prompt 2']
            }
        ]

        for suite in default_suites:
            self.add_suite_group(suite)

    def add_suite_group(self, suite):
        print(f"🔧 Adding suite group: {suite['name']}")

        group_box = ClickableGroupBox(f"{suite['icon']} {suite['name']}", suite['name'], suite['prompts'])
        group_layout = QVBoxLayout()

        header_layout = QHBoxLayout()
        suite_label = QLabel(suite['name'])
        header_layout.addWidget(suite_label)

        add_prompt_btn = QPushButton("+ Add Prompt")
        add_prompt_btn.setStyleSheet("QPushButton { font-size: 11px; padding: 2px 8px; background-color: #17a2b8; color: white; border: 1px solid #138496; border-radius: 3px; }")
        header_layout.addWidget(add_prompt_btn)

        header_layout.addStretch()
        group_layout.addLayout(header_layout)
        group_box.setLayout(group_layout)
        self.suites_layout.addWidget(group_box)

        print(f"   ✅ Suite group added: {suite['name']}")
        print(f"   Add button visible: {add_prompt_btn.isVisible()}")

        return add_prompt_btn

def test_with_tabs():
    """Test with tab widget like the main application"""
    print("🧪 Testing with Tab Widget Pattern")

    app = QApplication(sys.argv)

    # Create main window with tabs (like main app)
    main_window = QWidget()
    main_layout = QVBoxLayout(main_window)

    tab_widget = QTabWidget()
    test_suites_widget = TestSuitesWidgetWithTab()

    # Add to tabs
    tab_widget.addTab(test_suites_widget, "Test Suites")
    tab_widget.addTab(QWidget(), "Other Tab")

    main_layout.addWidget(tab_widget)
    main_window.show()

    print("✅ Main window created with tabs")
    print(f"   Main window visible: {main_window.isVisible()}")
    print(f"   Tab widget visible: {tab_widget.isVisible()}")
    print(f"   Test suites widget visible: {test_suites_widget.isVisible()}")

    # Switch to Test Suites tab
    tab_widget.setCurrentIndex(0)
    app.processEvents()

    print(f"   After tab switch - Test suites widget visible: {test_suites_widget.isVisible()}")

    if test_suites_widget.suite_widgets:
        first_suite = test_suites_widget.suite_widgets[0]
        add_btn = first_suite.get('add_btn')
        if add_btn:
            print(f"   Add button visible: {add_btn.isVisible()}")

    print("🎯 Check console for QLayout errors above")
    print("   If no errors and widgets visible, tabs are not the issue.")

    # Keep window open briefly
    from PySide6.QtCore import QTimer
    QTimer.singleShot(3000, app.quit)
    app.exec()

    return True

if __name__ == "__main__":
    test_with_tabs()