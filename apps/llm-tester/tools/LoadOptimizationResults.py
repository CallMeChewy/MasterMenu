#!/usr/bin/env python3
# File: LoadOptimizationResults.py
# Path: /home/herb/Desktop/LLM-Tester/LoadOptimizationResults.py
# Standard: AIDEV-PascalCase-2.1
# Created: 2025-10-04
# Last Modified: 2025-10-04 6:40PM

"""
Load optimization results into the Parameter Optimization Lab for visualization
"""

import json
import sys
from PySide6.QtWidgets import QApplication, QMessageBox
from LLM_Tester_Enhanced import ParameterOptimizationLabWidget

def load_results_into_lab(json_file_path):
    """Load optimization results from JSON file into the Parameter Optimization Lab"""
    try:
        with open(json_file_path, 'r') as f:
            data = json.load(f)

        # Create application if not exists
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)

        # Create Optimization Lab widget
        lab = ParameterOptimizationLabWidget()

        # Parse the results from the JSON file
        detailed_results = data['detailed_results'].split('\n\n')
        results = []

        for result_str in detailed_results:
            if not result_str.strip():
                continue

            # Parse configuration string like "Config: T0.10_C2048_P512_R1.10_K25_P0.90 | Accuracy: 1.000 | Time: 2.80s"
            try:
                parts = result_str.split('|')
                config_part = parts[0].replace('Config: ', '').strip()
                accuracy_part = parts[1].replace('Accuracy: ', '').strip()
                time_part = parts[2].replace('Time: ', '').replace('s', '').strip()

                # Parse configuration parameters
                config_params = config_part.split('_')
                config_dict = {
                    'temperature': float(config_params[0][1:]) / 100,  # T0.10 -> 0.10
                    'num_ctx': int(config_params[1][1:]),               # C2048 -> 2048
                    'num_predict': int(config_params[2][1:]),           # P512 -> 512
                    'repeat_penalty': float(config_params[3][1:]) / 100, # R1.10 -> 1.10
                    'top_k': int(config_params[4][1:]),                 # K25 -> 25
                    'top_p': float(config_params[5][1:]) / 100          # P0.90 -> 0.90
                }

                result = {
                    'config': config_dict,
                    'accuracy': float(accuracy_part),
                    'time': float(time_part),
                    'efficiency': float(accuracy_part) / float(time_part)  # Simple efficiency metric
                }
                results.append(result)

            except Exception as e:
                print(f"Error parsing result: {result_str}, Error: {e}")
                continue

        # Set the prompt and model
        lab.prompt_edit.setPlainText(data['prompt'])
        model_index = lab.model_combo.findText(data['model'])
        if model_index >= 0:
            lab.model_combo.setCurrentIndex(model_index)

        # Load results into the lab
        lab.optimization_results = results

        # Create visualizations
        lab.create_performance_landscape(results)
        lab.create_optimization_path(results)
        lab.create_parameter_heatmap(results)
        lab.create_parallel_coordinates(results)

        # Show the widget
        lab.show()
        lab.raise_()
        lab.activateWindow()

        print(f"✅ Successfully loaded {len(results)} optimization results from {json_file_path}")
        print("📊 Visualization graphs have been created!")
        print("👀 Look for these tabs in the Parameter Optimization Lab:")
        print("   🌄 Performance Landscape - 3D surface plot")
        print("   🛤️ Optimization Path - Journey analysis")
        print("   🔥 Parameter Heatmap - Correlation heatmap")
        print("   📐 Parallel Coordinates - Multi-dimensional plot")

        return app.exec_()

    except Exception as e:
        print(f"❌ Error loading optimization results: {e}")
        return 1

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 LoadOptimizationResults.py <optimization_results.json>")
        sys.exit(1)

    json_file = sys.argv[1]
    sys.exit(load_results_into_lab(json_file))