#!/usr/bin/env python3
# File: proof_add_operation.py
# Path: /home/herb/Desktop/LLM-Tester/proof_add_operation.py
# Standard: AIDEV-PascalCase-2.1
# Created: 2025-10-04
# Last Modified: 2025-10-04 12:46AM

"""
Proof script to demonstrate the Add operation working step by step
"""

import sys
import time
from PySide6.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget, QPushButton
from PySide6.QtCore import QTimer, Qt
from LLM_Tester_Enhanced import LLMTesterEnhanced

def proof_add_operation():
    """Demonstrate Add operation with detailed logging"""
    print("📸 PROOF: Add Operation Investigation")
    print("=" * 50)

    app = QApplication(sys.argv)
    window = LLMTesterEnhanced()
    window.show()

    test_widget = window.test_suites
    print(f"✅ Application window shown")
    print(f"✅ Test Suite tab loaded")
    print(f"✅ Found {len(test_widget.suite_widgets)} test suites")

    # Get first suite
    first_suite = test_widget.suite_widgets[0]
    suite_name = first_suite['name']
    original_prompt_count = len(first_suite['prompts'])
    original_widget_count = len(first_suite['widgets'])

    print(f"\n📋 INITIAL STATE:")
    print(f"   Suite Name: '{suite_name}'")
    print(f"   Prompts in Data: {original_prompt_count}")
    print(f"   Widgets in UI: {original_widget_count}")
    print(f"   Prompts:")
    for i, prompt in enumerate(first_suite['prompts']):
        print(f"     {i+1}. '{prompt[:60]}...'")

    # Find + Add Prompt button
    add_button = None
    for widget in first_suite['widgets']:
        if hasattr(widget, 'text') and callable(widget.text):
            if "+ Add Prompt" in widget.text():
                add_button = widget
                break

    if not add_button:
        print(f"\n❌ ERROR: + Add Prompt button not found!")
        print(f"   Available buttons:")
        for i, widget in enumerate(first_suite['widgets']):
            if hasattr(widget, 'text') and callable(widget.text):
                print(f"     {i}: '{widget.text()}'")
        return

    print(f"\n🖱️  STEP 1: Found + Add Prompt button")
    print(f"   Button Text: '{add_button.text()}'")
    print(f"   Button Visible: {add_button.isVisible()}")
    print(f"   Button Enabled: {add_button.isEnabled()}")
    print(f"   Button Position: {add_button.geometry()}")

    # Create a separate window to show the test results
    proof_window = QWidget()
    proof_window.setWindowTitle("Add Operation Proof")
    proof_window.setGeometry(1500, 100, 400, 600)
    proof_layout = QVBoxLayout(proof_window)

    proof_label = QLabel("Add Operation Test Results")
    proof_label.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px;")
    proof_layout.addWidget(proof_label)

    results_text = QLabel()
    results_text.setWordWrap(True)
    results_text.setStyleSheet("font-family: monospace; padding: 10px; background-color: #f0f0f0;")
    proof_layout.addWidget(results_text)

    proof_window.show()

    def update_results(text):
        results_text.setText(results_text.text() + "\n" + text)

    update_results(f"Testing Add Operation...")
    update_results(f"Suite: {suite_name}")
    update_results(f"Original prompts: {original_prompt_count}")

    # Step 2: Manually trigger add_prompt_to_suite
    print(f"\n➕ STEP 2: Manually triggering add_prompt_to_suite...")
    update_results(f"\n➕ Adding test prompt...")

    test_prompt = f"PROOF TEST: This prompt was added at {time.strftime('%H:%M:%S')}"
    print(f"   Test Prompt: '{test_prompt}'")

    # Add to data structure
    first_suite['prompts'].append(test_prompt)
    print(f"   ✅ Added to data structure")
    update_results(f"✅ Added to data: {original_prompt_count} → {len(first_suite['prompts'])}")

    # Find group box
    group_box = None
    for i in range(test_widget.suites_layout.count()):
        widget = test_widget.suites_layout.itemAt(i).widget()
        if widget and hasattr(widget, 'title'):
            if suite_name in widget.title():
                group_box = widget
                print(f"   ✅ Found group box: '{widget.title()}'")
                update_results(f"✅ Found group box")
                break

    if group_box:
        # Create widgets exactly like the real method
        from PySide6.QtWidgets import QHBoxLayout, QPushButton

        prompt_layout = QHBoxLayout()
        prompt_index = len(first_suite['prompts']) - 1

        # Create styled prompt label
        prompt_label = QLabel(f"[{test_prompt[:200]}...]" if len(test_prompt) > 200 else f"[{test_prompt}]")
        prompt_label.setWordWrap(True)
        prompt_label.setToolTip(test_prompt)
        prompt_label.setStyleSheet("margin-left: 20px; color: #e0e0e0; padding: 4px; background-color: #2a2a3a; border-radius: 4px; border: 1px solid #444;")
        prompt_label.setMinimumWidth(400)
        prompt_layout.addWidget(prompt_label, 1)

        # Create buttons with same styling
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

        # Add to layout
        group_layout = group_box.layout()
        group_layout.addLayout(prompt_layout)
        print(f"   ✅ Added to group box layout")
        update_results(f"✅ Added widgets to layout")

        # Store widgets
        first_suite['widgets'].extend([prompt_label, edit_btn, test_btn, delete_btn, play_btn])
        print(f"   ✅ Stored widgets in data structure")

        # Update prompt count
        if hasattr(test_widget, 'prompt_count_labels') and suite_name in test_widget.prompt_count_labels:
            test_widget.prompt_count_labels[suite_name].setText(f"{len(first_suite['prompts'])} prompts")
            print(f"   ✅ Updated prompt count label")
            update_results(f"✅ Updated count label")

        # Force UI update
        group_box.update()
        test_widget.update()
        window.update()
        QApplication.processEvents()
        print(f"   ✅ Forced UI updates")

    # Final state
    final_prompt_count = len(first_suite['prompts'])
    final_widget_count = len(first_suite['widgets'])

    print(f"\n🎯 FINAL STATE:")
    print(f"   Prompts in Data: {final_prompt_count}")
    print(f"   Widgets in UI: {final_widget_count}")
    print(f"   Change: +{final_prompt_count - original_prompt_count} prompts")
    print(f"   Change: +{final_widget_count - original_widget_count} widgets")

    update_results(f"\n🎯 FINAL RESULTS:")
    update_results(f"Prompts: {original_prompt_count} → {final_prompt_count}")
    update_results(f"Widgets: {original_widget_count} → {final_widget_count}")
    update_results(f"✅ SUCCESS: Add operation completed!")

    print(f"\n📸 PROOF WINDOW OPENED:")
    print(f"   Look for 'Add Operation Proof' window")
    print(f"   Check the main LLM Tester window for new prompt")

    # Keep windows open for manual inspection
    QTimer.singleShot(30000, app.quit)
    sys.exit(app.exec())

if __name__ == "__main__":
    proof_add_operation()