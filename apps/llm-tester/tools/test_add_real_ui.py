#!/usr/bin/env python3
# File: test_add_real_ui.py
# Path: /home/herb/Desktop/LLM-Tester/test_add_real_ui.py
# Standard: AIDEV-PascalCase-2.1
# Created: 2025-10-04
# Last Modified: 2025-10-04 12:40AM

"""
Test script to actually trigger the Add operation and see what happens in the UI
"""

import sys
import time
from PySide6.QtWidgets import QApplication, QDialog, QVBoxLayout, QTextEdit, QDialogButtonBox, QLabel
from PySide6.QtCore import QTimer, Qt
from LLM_Tester_Enhanced import LLMTesterEnhanced

def test_add_real_ui():
    """Test Add operation by actually triggering it"""
    print("🧪 Testing REAL Add Operation...")

    app = QApplication(sys.argv)
    window = LLMTesterEnhanced()
    window.show()

    test_widget = window.test_suites
    print(f"✅ Application started")
    print(f"✅ Found {len(test_widget.suite_widgets)} test suites")

    # Get first suite
    first_suite = test_widget.suite_widgets[0]
    suite_name = first_suite['name']
    original_prompt_count = len(first_suite['prompts'])
    print(f"📋 Suite: '{suite_name}'")
    print(f"   Original prompts: {original_prompt_count}")

    # Print original prompts for comparison
    print(f"   Original prompt list:")
    for i, prompt in enumerate(first_suite['prompts']):
        print(f"     {i+1}. '{prompt[:50]}...'")

    # Manually trigger the add_prompt_to_suite method with a test prompt
    print(f"\n➕ Manually triggering add_prompt_to_suite...")

    # Create a test prompt dialog and accept it immediately
    test_prompt = f"TEST ADD PROMPT: This is a test added at {time.strftime('%H:%M:%S')}"

    # Simulate what the add_prompt_to_suite method does
    print(f"   Adding prompt: '{test_prompt}'")

    # Add to data structure
    first_suite['prompts'].append(test_prompt)
    print(f"   ✅ Added to data structure: {original_prompt_count} → {len(first_suite['prompts'])}")

    # Find the group box for this suite
    group_box = None
    for i in range(test_widget.suites_layout.count()):
        widget = test_widget.suites_layout.itemAt(i).widget()
        if widget and hasattr(widget, 'title'):
            if suite_name in widget.title():
                group_box = widget
                print(f"   ✅ Found group box: {widget.title()}")
                break

    if group_box:
        # Create new prompt widgets exactly like the add_prompt_to_suite method does
        from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton

        prompt_layout = QHBoxLayout()
        prompt_index = len(first_suite['prompts']) - 1

        # Prompt label
        prompt_label = QLabel(f"[{test_prompt[:200]}...]" if len(test_prompt) > 200 else f"[{test_prompt}]")
        prompt_label.setWordWrap(True)
        prompt_label.setToolTip(test_prompt)
        prompt_label.setStyleSheet("margin-left: 20px; color: #e0e0e0; padding: 4px; background-color: #2a2a3a; border-radius: 4px; border: 1px solid #444;")
        prompt_label.setMinimumWidth(400)
        prompt_layout.addWidget(prompt_label, 1)

        # Create buttons
        edit_btn = QPushButton("Edit")
        edit_btn.setMaximumWidth(60)
        edit_btn.setStyleSheet("QPushButton { font-size: 11px; padding: 4px; background-color: #4a90e2; color: white; border: 1px solid #357abd; border-radius: 3px; } QPushButton:hover { background-color: #357abd; }")
        edit_btn.clicked.connect(lambda p=test_prompt, i=prompt_index: test_widget.edit_prompt(suite_name, i, p))
        prompt_layout.addWidget(edit_btn)

        test_btn = QPushButton("Test")
        test_btn.setMaximumWidth(60)
        test_btn.setStyleSheet("QPushButton { font-size: 11px; padding: 4px; background-color: #28a745; color: white; border: 1px solid #1e7e34; border-radius: 3px; } QPushButton:hover { background-color: #218838; }")
        test_btn.clicked.connect(lambda p=test_prompt: test_widget.test_single_prompt(p))
        prompt_layout.addWidget(test_btn)

        delete_btn = QPushButton("Delete")
        delete_btn.setMaximumWidth(70)
        delete_btn.setStyleSheet("QPushButton { font-size: 11px; padding: 4px; background-color: #dc3545; color: white; border: 1px solid #c82333; border-radius: 3px; } QPushButton:hover { background-color: #c82333; }")
        delete_btn.clicked.connect(lambda s=suite_name, i=prompt_index: test_widget.delete_prompt(s, i))
        prompt_layout.addWidget(delete_btn)

        play_btn = QPushButton("▶")
        play_btn.setMaximumWidth(40)
        play_btn.setStyleSheet("QPushButton { font-size: 11px; padding: 4px; background-color: #007bff; color: white; border: 1px solid #0056b3; border-radius: 3px; } QPushButton:hover { background-color: #0056b3; }")
        play_btn.clicked.connect(lambda p=test_prompt: test_widget.run_prompt(p))
        prompt_layout.addWidget(play_btn)

        # Add to group box layout
        group_layout = group_box.layout()
        group_layout.addLayout(prompt_layout)

        # Store widgets in suite data
        first_suite['widgets'].extend([prompt_label, edit_btn, test_btn, delete_btn, play_btn])

        print(f"   ✅ Created and added widgets to layout")
        print(f"   ✅ Widgets stored in suite data")

        # Force UI update
        group_box.update()
        group_box.show()
        test_widget.update()
        window.update()

        print(f"   ✅ Forced UI updates")

    # Update prompt count
    if hasattr(test_widget, 'prompt_count_labels') and suite_name in test_widget.prompt_count_labels:
        test_widget.prompt_count_labels[suite_name].setText(f"{len(first_suite['prompts'])} prompts")
        print(f"   ✅ Updated prompt count label")

    print(f"\n🎯 Final State:")
    print(f"   Data structure prompts: {len(first_suite['prompts'])}")
    print(f"   Widgets in suite: {len(first_suite['widgets'])}")

    print(f"\n📋 Updated prompt list:")
    for i, prompt in enumerate(first_suite['prompts']):
        print(f"     {i+1}. '{prompt[:50]}...'")

    print(f"\n🖱️  Manual Test Instructions:")
    print(f"   1. Look at the '{suite_name}' section in the Test Suite tab")
    print(f"   2. You should see a new prompt: '{test_prompt[:30]}...'")
    print(f"   3. It should have Edit, Test, Delete, and ▶ buttons")
    print(f"   4. If you don't see it, there's a UI display issue")

    # Keep window open for 60 seconds for manual verification
    QTimer.singleShot(60000, app.quit)
    sys.exit(app.exec())

if __name__ == "__main__":
    test_add_real_ui()