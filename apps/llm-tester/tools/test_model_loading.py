#!/usr/bin/env python3
# File: test_model_loading.py
# Path: /home/herb/Desktop/LLM-Tester/test_model_loading.py
# Standard: AIDEV-PascalCase-2.1
# Created: 2025-10-03
# Last Modified: 2025-10-03 11:17PM

import sys
import ollama
from PySide6.QtWidgets import QApplication, QTreeWidget, QTreeWidgetItem
from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QColor

def test_model_population():
    """Test model population logic"""
    app = QApplication(sys.argv)

    try:
        # Get models from Ollama
        models = ollama.list()
        print(f"Found {len(models['models'])} models")

        # Create tree widget
        tree = QTreeWidget()
        tree.setColumnCount(6)
        tree.setHeaderLabels(['Model', 'Size (GB)', 'Parameters', 'Specialty', 'VRAM (GB)', 'Speed'])

        # Process models
        all_models_data = []
        for model in models['models']:
            size_gb = model['size'] / (1024**3)
            parameters = model['details'].get('parameter_size', 'Unknown')
            family = model['details'].get('family', 'Unknown')

            data = {
                'name': model['name'],
                'size_gb': size_gb,
                'parameters': parameters,
                'specialty': family,
                'vram_estimate': size_gb * 1.2,
                'speed_icon': '🚀'
            }
            all_models_data.append(data)

        # Test adding items to tree
        for data in all_models_data:
            item = QTreeWidgetItem(tree)
            item.setText(0, data['name'])
            item.setText(1, f"{data['size_gb']:.1f}")
            item.setText(2, data['parameters'])
            item.setText(3, data['specialty'])
            item.setText(4, f"{data['vram_estimate']:.1f}GB")
            item.setText(5, data['speed_icon'])

            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(0, Qt.Unchecked)

            # Test background setting - this is where the error occurs
            if 'embed' in data['name'].lower():
                item.setFlags(item.flags() & ~Qt.ItemIsUserCheckable)
                item.setForeground(0, QBrush(QColor("#666666")))
            else:
                # Test with proper column parameter
                try:
                    item.setBackground(0, QBrush(QColor("#2a2a3a")))
                    item.setForeground(0, QBrush(QColor("#eee")))
                    print(f"✅ Background/Foreground set successfully for {data['name']}")
                except Exception as e:
                    print(f"❌ Background/Foreground error for {data['name']}: {e}")

        print("Model population test completed successfully")
        return True

    except Exception as e:
        print(f"Error in model population test: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        app.quit()

if __name__ == "__main__":
    test_model_population()