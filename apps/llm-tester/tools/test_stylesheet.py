#!/usr/bin/env python3
# File: test_stylesheet.py
# Path: /home/herb/Desktop/LLM-Tester/test_stylesheet.py
# Standard: AIDEV-PascalCase-2.1
# Created: 2025-10-04
# Last Modified: 2025-10-04 03:00AM

"""
Test if the global stylesheet is causing the visibility issue
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

class TestSuitesWidgetWithStylesheet(QWidget):
    """Test Suites Widget with the same stylesheet as main app"""
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
        print(f"   Before stylesheet - Add button visible: {add_prompt_btn.isVisible()}")
        print(f"   Before stylesheet - Group box visible: {group_box.isVisible()}")

        suite_data = {
            'name': suite['name'],
            'add_btn': add_prompt_btn,
            'group_box': group_box
        }
        self.suite_widgets.append(suite_data)

        return add_prompt_btn, group_box

def test_with_stylesheet():
    """Test with the exact same stylesheet as main application"""
    print("🧪 Testing with Application Stylesheet")

    app = QApplication(sys.argv)

    # Create main window with EXACT same stylesheet
    main_window = QWidget()
    main_window.setStyleSheet("""
        QMainWindow {
            background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                              stop: 0 #1a1a2e, stop: 1 #16213e);
            color: #eee;
        }
        QTabWidget::pane {
            border: 1px solid #555;
            background-color: #0f3460;
        }
        QTabBar::tab {
            background-color: #533483;
            color: white;
            padding: 8px 16px;
            margin-right: 2px;
        }
        QTabBar::tab:selected {
            background-color: #e94560;
        }
        QWidget {
            font-size: 12pt;
            background-color: transparent;
        }
        QTreeWidget, QTableWidget {
            background-color: #0f3460;
            alternate-background-color: #16213e;
            gridline-color: #333;
            color: #eee;
        }
        QHeaderView::section {
            background-color: #533483;
            color: white;
            padding: 4px;
            border: 1px solid #333;
        }
        QPushButton {
            background-color: #e94560;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
        }
        QPushButton:hover {
            background-color: #ff6b6b;
        }
        QPushButton:disabled {
            background-color: #555;
            color: #888;
        }
        QLabel {
            color: #eee;
        }
        QGroupBox {
            color: #eee;
            border: 2px solid #533483;
            border-radius: 5px;
            margin-top: 10px;
            padding-top: 10px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px 0 5px;
        }
        QSlider::groove:horizontal {
            background-color: #533483;
            height: 6px;
            border-radius: 3px;
        }
        QSlider::handle:horizontal {
            background-color: #e94560;
            width: 18px;
            margin: -6px 0;
            border-radius: 9px;
        }
    """)

    main_layout = QVBoxLayout(main_window)

    tab_widget = QTabWidget()
    test_suites_widget = TestSuitesWidgetWithStylesheet()

    tab_widget.addTab(test_suites_widget, "Test Suites")
    main_layout.addWidget(tab_widget)
    main_window.show()

    print("✅ Main window created with stylesheet")
    print(f"   Main window visible: {main_window.isVisible()}")

    # Check widget visibility after stylesheet is applied
    app.processEvents()

    if test_suites_widget.suite_widgets:
        first_suite = test_suites_widget.suite_widgets[0]
        add_btn, group_box = first_suite.get('add_btn'), first_suite.get('group_box')
        if add_btn and group_box:
            print(f"   After stylesheet - Add button visible: {add_btn.isVisible()}")
            print(f"   After stylesheet - Group box visible: {group_box.isVisible()}")
            print(f"   Add button geometry: {add_btn.geometry()}")
            print(f"   Group box geometry: {group_box.geometry()}")

    print("🎯 If widgets become invisible after stylesheet, that's the issue!")

    # Keep window open briefly
    from PySide6.QtCore import QTimer
    QTimer.singleShot(3000, app.quit)
    app.exec()

    return True

if __name__ == "__main__":
    test_with_stylesheet()