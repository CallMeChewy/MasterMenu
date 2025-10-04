#!/usr/bin/env python3
# File: optimization_lab_gui.py
# Path: /home/herb/Desktop/LLM-Tester/optimization_lab_gui.py
# Standard: AIDEV-PascalCase-2.1
# Created: 2025-10-04
# Last Modified: 2025-10-04 04:35AM

"""
Parameter Optimization Lab GUI - Dedicated application for finding optimal LLM parameters
Runs exhaustive testing until achieving 100% accuracy with consistent minimum time
"""

import sys
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTextEdit, QProgressBar, QSpinBox,
    QComboBox, QCheckBox, QGroupBox, QFormLayout, QSplitter,
    QTabWidget, QTableWidgetItem, QTableWidget, QHeaderView,
    QMessageBox, QFileDialog, QLineEdit, QDoubleSpinBox, QSystemTrayIcon,
    QMenu
)
from PySide6.QtCore import Qt, QThread, pyqtSignal, QTimer, QMutex, QMutexLocker
from PySide6.QtGui import QIcon, QFont, QPixmap, QPainter, QColor
import matplotlib.pyplot as plt
import matplotlib.backends.backend_qtagg as plot_qtagg
from matplotlib.figure import Figure
import numpy as np

from parameter_optimization_lab import (
    ParameterOptimizationLab, OptimizationTarget, OptimizationStatus,
    ParameterConfig, TestResult
)

class OptimizationWorker(QThread):
    """Background worker for parameter optimization"""

    progress_update = pyqtSignal(dict)  # Progress updates
    result_found = pyqtSignal(dict)      # New best result found
    optimization_complete = pyqtSignal(dict)  # Final results
    error_occurred = pyqtSignal(str)      # Error messages

    def __init__(self, target, model_function):
        super().__init__()
        self.target = target
        self.model_function = model_function
        self.lab = None
        self.should_stop = False
        self.mutex = QMutex()

    def run(self):
        """Run the optimization process"""
        try:
            self.lab = ParameterOptimizationLab(self.target, self.model_function)

            # Connect to progress queue
            def progress_monitor():
                while not self.should_stop:
                    try:
                        # Check for progress updates
                        if hasattr(self.lab, 'test_results'):
                            progress = OptimizationProgress(
                                status=self.lab.current_status,
                                current_iteration=len(self.lab.test_results),
                                total_tests_run=len(self.lab.test_results),
                                best_config_found=self.lab.best_config,
                                best_accuracy=self.lab.best_accuracy,
                                best_time=self.lab.best_time,
                                convergence_score=min(1.0, self.lab.best_accuracy),
                                estimated_time_remaining=timedelta(hours=1),  # Placeholder
                                current_test="Testing configurations..."
                            )

                            self.progress_update.emit({
                                'type': 'progress',
                                'progress': progress
                            })

                            # Emit result if we have a best config
                            if self.lab.best_config:
                                self.result_found.emit({
                                    'config': self.lab.best_config,
                                    'accuracy': self.lab.best_accuracy,
                                    'time': self.lab.best_time
                                })

                        time.sleep(0.5)  # Update every 500ms

                    except Exception as e:
                        self.error_occurred.emit(f"Progress monitor error: {e}")
                        break

            # Start progress monitor in a separate thread
            import threading
            monitor_thread = threading.Thread(target=progress_monitor)
            monitor_thread.daemon = True
            monitor_thread.start()

            # Run optimization
            final_progress = self.lab.run_exhaustive_optimization()

            # Emit final results
            self.optimization_complete.emit({
                'progress': final_progress,
                'test_results': self.lab.test_results,
                'results_file': self.lab.save_results()
            })

        except Exception as e:
            self.error_occurred.emit(f"Optimization error: {e}")

    def stop(self):
        """Stop the optimization process"""
        with QMutexLocker(self.mutex):
            self.should_stop = True
        if self.lab:
            self.lab.stop_optimization()

class OptimizationLabGUI(QMainWindow):
    """Main GUI for the Parameter Optimization Lab"""

    def __init__(self):
        super().__init__()
        self.current_optimization = None
        self.optimization_results = []

        self.init_ui()
        self.setup_tray_icon()

    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Parameter Optimization Lab")
        self.setGeometry(100, 100, 1400, 900)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QHBoxLayout(central_widget)

        # Left panel - Configuration
        left_panel = self.create_configuration_panel()

        # Right panel - Results and visualization
        right_panel = self.create_results_panel()

        # Splitter
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([400, 1000])

        main_layout.addWidget(splitter)

        # Status bar
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready to optimize parameters")

    def create_configuration_panel(self):
        """Create the configuration panel"""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Title
        title = QLabel("🧪 Optimization Configuration")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50; padding: 10px;")
        layout.addWidget(title)

        # Model selection
        model_group = QGroupBox("Model Configuration")
        model_layout = QFormLayout(model_group)

        self.model_combo = QComboBox()
        self.model_combo.addItems(["phi3:3.8b", "phi3:14b", "llama3.2", "qwen2.5"])
        model_layout.addRow("Model:", self.model_combo)

        layout.addWidget(model_group)

        # Target configuration
        target_group = QGroupBox("Optimization Target")
        target_layout = QFormLayout(target_group)

        self.prompt_text = QTextEdit()
        self.prompt_text.setMaximumHeight(100)
        self.prompt_text.setPlainText("Create a Python function to calculate the area of a circle given its radius.")
        target_layout.addRow("Prompt:", self.prompt_text)

        self.target_accuracy = QDoubleSpinBox()
        self.target_accuracy.setRange(0.5, 1.0)
        self.target_accuracy.setValue(1.0)
        self.target_accuracy.setSingleStep(0.05)
        self.target_accuracy.setDecimals(2)
        target_layout.addRow("Target Accuracy:", self.target_accuracy)

        self.consistency_threshold = QDoubleSpinBox()
        self.consistency_threshold.setRange(0.8, 1.0)
        self.consistency_threshold.setValue(0.95)
        self.consistency_threshold.setSingleStep(0.01)
        self.consistency_threshold.setDecimals(2)
        target_layout.addRow("Consistency Threshold:", self.consistency_threshold)

        self.max_time = QSpinBox()
        self.max_time.setRange(10, 600)
        self.max_time.setValue(60)
        self.max_time.setSuffix(" seconds")
        target_layout.addRow("Max Test Time:", self.max_time)

        layout.addWidget(target_group)

        # Advanced settings
        advanced_group = QGroupBox("Advanced Settings")
        advanced_layout = QFormLayout(advanced_group)

        self.validation_cycles = QSpinBox()
        self.validation_cycles.setRange(3, 50)
        self.validation_cycles.setValue(10)
        advanced_layout.addRow("Validation Cycles:", self.validation_cycles)

        self.timeout_enabled = QCheckBox("Enable timeout")
        self.timeout_enabled.setChecked(True)
        advanced_layout.addRow("Timeout Protection:", self.timeout_enabled)

        layout.addWidget(advanced_group)

        # Control buttons
        button_layout = QVBoxLayout()

        self.start_button = QPushButton("🚀 Start Optimization")
        self.start_button.clicked.connect(self.start_optimization)
        self.start_button.setStyleSheet("QPushButton { background-color: #27ae60; color: white; font-weight: bold; padding: 10px; }")
        button_layout.addWidget(self.start_button)

        self.stop_button = QPushButton("⏹️ Stop Optimization")
        self.stop_button.clicked.connect(self.stop_optimization)
        self.stop_button.setEnabled(False)
        self.stop_button.setStyleSheet("QPushButton { background-color: #e74c3c; color: white; font-weight: bold; padding: 10px; }")
        button_layout.addWidget(self.stop_button)

        self.save_button = QPushButton("💾 Save Results")
        self.save_button.clicked.connect(self.save_results)
        self.save_button.setEnabled(False)
        button_layout.addWidget(self.save_button)

        layout.addLayout(button_layout)

        layout.addStretch()

        return panel

    def create_results_panel(self):
        """Create the results and visualization panel"""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Title
        title = QLabel("📊 Optimization Results")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50; padding: 10px;")
        layout.addWidget(title)

        # Progress section
        progress_group = QGroupBox("Optimization Progress")
        progress_layout = QVBoxLayout(progress_group)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        progress_layout.addWidget(self.progress_bar)

        # Status labels
        status_layout = QHBoxLayout()

        self.status_label = QLabel("Status: Ready")
        self.status_label.setStyleSheet("font-weight: bold;")
        status_layout.addWidget(self.status_label)

        self.iteration_label = QLabel("Tests: 0")
        status_layout.addWidget(self.iteration_label)

        self.accuracy_label = QLabel("Best Accuracy: 0.000")
        status_layout.addWidget(self.accuracy_label)

        progress_layout.addLayout(status_layout)

        # Current test info
        self.current_test_label = QLabel("Ready to start optimization...")
        self.current_test_label.setWordWrap(True)
        self.current_test_label.setStyleSheet("color: #7f8c8d; font-style: italic;")
        progress_layout.addWidget(self.current_test_label)

        layout.addWidget(progress_group)

        # Tabbed results
        results_tabs = QTabWidget()

        # Real-time results tab
        realtime_tab = self.create_realtime_tab()
        results_tabs.addTab(realtime_tab, "Real-time Results")

        # Visualization tab
        viz_tab = self.create_visualization_tab()
        results_tabs.addTab(viz_tab, "Visualizations")

        # Detailed results tab
        details_tab = self.create_details_tab()
        results_tabs.addTab(details_tab, "Detailed Results")

        layout.addWidget(results_tabs)

        return panel

    def create_realtime_tab(self):
        """Create real-time results tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Best results table
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(5)
        self.results_table.setHorizontalHeaderLabels(["Configuration", "Accuracy", "Time (s)", "Tokens", "Status"])
        self.results_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.results_table)

        # Console output
        console_group = QGroupBox("Optimization Console")
        console_layout = QVBoxLayout(console_group)

        self.console_output = QTextEdit()
        self.console_output.setReadOnly(True)
        self.console_output.setMaximumHeight(200)
        console_layout.addWidget(self.console_output)

        layout.addWidget(console_group)

        return tab

    def create_visualization_tab(self):
        """Create visualization tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Create matplotlib figure
        self.figure = Figure(figsize=(12, 8))
        self.canvas = plot_qtagg.FigureCanvasQTAgg(self.figure)
        layout.addWidget(self.canvas)

        return tab

    def create_details_tab(self):
        """Create detailed results tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Detailed results table
        self.details_table = QTableWidget()
        self.details_table.setColumnCount(8)
        self.details_table.setHorizontalHeaderLabels([
            "Timestamp", "Temperature", "Context", "Predict", "Repeat", "Top K", "Top P", "Accuracy"
        ])
        self.details_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.details_table)

        return tab

    def setup_tray_icon(self):
        """Setup system tray icon for background operation"""
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray_icon = QSystemTrayIcon(self)

            # Create a simple icon
            pixmap = QPixmap(32, 32)
            pixmap.fill(QColor('#3498db'))
            painter = QPainter(pixmap)
            painter.setPen(QColor('white'))
            painter.drawText(pixmap.rect(), Qt.AlignCenter, "🧪")
            painter.end()

            self.tray_icon.setIcon(QIcon(pixmap))

            # Create tray menu
            tray_menu = QMenu()
            show_action = tray_menu.addAction("Show Window")
            show_action.triggered.connect(self.show)
            stop_action = tray_menu.addAction("Stop Optimization")
            stop_action.triggered.connect(self.stop_optimization)
            quit_action = tray_menu.addAction("Quit")
            quit_action.triggered.connect(self.close)

            self.tray_icon.setContextMenu(tray_menu)
            self.tray_icon.show()

    def log_message(self, message):
        """Log message to console"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.console_output.append(f"[{timestamp}] {message}")

        # Scroll to bottom
        scrollbar = self.console_output.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def start_optimization(self):
        """Start the optimization process"""
        try:
            # Get configuration
            prompt = self.prompt_text.toPlainText().strip()
            if not prompt:
                QMessageBox.warning(self, "No Prompt", "Please enter a prompt to optimize.")
                return

            # Create optimization target
            target = OptimizationTarget(
                prompt=prompt,
                model=self.model_combo.currentText(),
                target_accuracy=self.target_accuracy.value(),
                max_time_seconds=self.max_time.value(),
                consistency_threshold=self.consistency_threshold.value()
            )

            # Mock model function (replace with actual integration)
            def mock_model_function(model, prompt, parameters):
                time.sleep(parameters['temperature'] * 0.5 + parameters['num_predict'] / 1000)

                if "circle" in prompt.lower():
                    if parameters['temperature'] < 0.3:
                        return """```python
import math

def circle_area(radius):
    return math.pi * radius ** 2
```"""
                    else:
                        return """```python
import math
def circle_area(r):
    return math.pi * r * r
```"""
                else:
                    return f"# Response for {prompt[:30]}"

            # Create and start worker
            self.current_optimization = OptimizationWorker(target, mock_model_function)

            # Connect signals
            self.current_optimization.progress_update.connect(self.update_progress)
            self.current_optimization.result_found.connect(self.update_result)
            self.current_optimization.optimization_complete.connect(self.optimization_finished)
            self.current_optimization.error_occurred.connect(self.optimization_error)

            # Update UI
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)

            # Clear previous results
            self.results_table.setRowCount(0)
            self.details_table.setRowCount(0)
            self.console_output.clear()

            self.log_message("🚀 Starting parameter optimization...")
            self.log_message(f"📝 Prompt: {prompt[:50]}...")
            self.log_message(f"🤖 Model: {target.model}")
            self.log_message(f"🎯 Target: {target.target_accuracy*100:.0f}% accuracy")

            # Start optimization
            self.current_optimization.start()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to start optimization: {e}")

    def stop_optimization(self):
        """Stop the optimization process"""
        if self.current_optimization:
            self.log_message("🛑 Stopping optimization...")
            self.current_optimization.stop()

            # Update UI
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.progress_bar.setVisible(False)

    def update_progress(self, progress_data):
        """Update progress display"""
        if progress_data['type'] == 'progress':
            progress = progress_data['progress']

            # Update progress bar
            if hasattr(progress, 'current_iteration') and hasattr(progress, 'total_tests_run'):
                percentage = min(100, (progress.total_tests_run / 100) * 100)  # Normalize to expected tests
                self.progress_bar.setValue(int(percentage))

            # Update labels
            self.status_label.setText(f"Status: {progress.status.value.replace('_', ' ').title()}")
            self.iteration_label.setText(f"Tests: {progress.total_tests_run}")
            self.accuracy_label.setText(f"Best Accuracy: {progress.best_accuracy:.3f}")

            if progress.current_test:
                self.current_test_label.setText(f"Current: {progress.current_test}")

            # Update status bar
            self.status_bar.showMessage(f"Optimization in progress - {progress.total_tests_run} tests completed")

    def update_result(self, result_data):
        """Update when a new best result is found"""
        config = result_data['config']

        self.log_message(f"🏆 New best found: {config}")
        self.log_message(f"   Accuracy: {result_data['accuracy']:.3f}")
        self.log_message(f"   Time: {result_data['time']:.2f}s")

        # Add to results table
        row = self.results_table.rowCount()
        self.results_table.insertRow(row)

        self.results_table.setItem(row, 0, QTableWidgetItem(str(config)))
        self.results_table.setItem(row, 1, QTableWidgetItem(f"{result_data['accuracy']:.3f}"))
        self.results_table.setItem(row, 2, QTableWidgetItem(f"{result_data['time']:.2f}"))
        self.results_table.setItem(row, 3, QTableWidgetItem("0"))  # Placeholder
        self.results_table.setItem(row, 4, QTableWidgetItem("New Best"))

        # Highlight best row
        for col in range(5):
            item = self.results_table.item(row, col)
            if item:
                item.setBackground(QColor('#d5f4e6'))

    def optimization_finished(self, result_data):
        """Handle optimization completion"""
        progress = result_data['progress']
        results = result_data['test_results']
        results_file = result_data['results_file']

        self.log_message("✅ Optimization completed!")
        self.log_message(f"🏆 Final Status: {progress.status.value}")
        self.log_message(f"📊 Total Tests: {len(results)}")
        self.log_message(f"💾 Results saved to: {results_file}")

        # Update UI
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.progress_bar.setVisible(False)
        self.save_button.setEnabled(True)

        # Show completion message
        if progress.status == OptimizationStatus.CONVERGED:
            QMessageBox.information(self, "Optimization Complete",
                f"Successfully converged on optimal parameters!\n\n"
                f"Best Configuration: {progress.best_config_found}\n"
                f"Final Accuracy: {progress.best_accuracy:.3f}\n"
                f"Total Tests: {progress.total_tests_run}")
        else:
            QMessageBox.warning(self, "Optimization Finished",
                f"Optimization completed but did not converge.\n\n"
                f"Final Status: {progress.status.value}\n"
                f"Best Accuracy: {progress.best_accuracy:.3f}\n"
                f"Total Tests: {progress.total_tests_run}")

        # Update visualizations
        self.update_visualizations(results)

        # Update detailed results
        self.update_detailed_results(results)

    def optimization_error(self, error_message):
        """Handle optimization errors"""
        self.log_message(f"❌ Error: {error_message}")

        # Update UI
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.progress_bar.setVisible(False)

        QMessageBox.critical(self, "Optimization Error", f"An error occurred during optimization:\n\n{error_message}")

    def update_visualizations(self, results):
        """Update visualization plots"""
        try:
            self.figure.clear()

            # Create subplots
            ax1 = self.figure.add_subplot(2, 2, 1)
            ax2 = self.figure.add_subplot(2, 2, 2)
            ax3 = self.figure.add_subplot(2, 2, 3)
            ax4 = self.figure.add_subplot(2, 2, 4)

            if results:
                # Extract data
                timestamps = [r.timestamp for r in results]
                accuracies = [r.accuracy_score for r in results]
                times = [r.response_time for r in results]
                temperatures = [r.config.temperature for r in results]

                # 1. Accuracy over time
                ax1.plot(range(len(accuracies)), accuracies, 'b-', linewidth=2)
                ax1.set_title('Accuracy Progress')
                ax1.set_xlabel('Test Number')
                ax1.set_ylabel('Accuracy Score')
                ax1.grid(True, alpha=0.3)

                # 2. Response time distribution
                ax2.hist(times, bins=20, alpha=0.7, color='green', edgecolor='black')
                ax2.set_title('Response Time Distribution')
                ax2.set_xlabel('Time (seconds)')
                ax2.set_ylabel('Frequency')
                ax2.grid(True, alpha=0.3)

                # 3. Temperature vs Accuracy
                ax3.scatter(temperatures, accuracies, alpha=0.6, s=50)
                ax3.set_title('Temperature vs Accuracy')
                ax3.set_xlabel('Temperature')
                ax3.set_ylabel('Accuracy Score')
                ax3.grid(True, alpha=0.3)

                # 4. Parameter performance summary
                param_names = ['Temperature', 'Context', 'Predict', 'Repeat', 'Top K', 'Top P']
                param_values = [
                    np.mean([r.config.temperature for r in results]),
                    np.mean([r.config.num_ctx for r in results]),
                    np.mean([r.config.num_predict for r in results]),
                    np.mean([r.config.repeat_penalty for r in results]),
                    np.mean([r.config.top_k for r in results]),
                    np.mean([r.config.top_p for r in results])
                ]

                ax4.bar(param_names, param_values, color='orange', alpha=0.7)
                ax4.set_title('Average Parameter Values')
                ax4.set_ylabel('Average Value')
                ax4.tick_params(axis='x', rotation=45)
                ax4.grid(True, alpha=0.3)

            self.figure.tight_layout()
            self.canvas.draw()

        except Exception as e:
            self.log_message(f"❌ Visualization error: {e}")

    def update_detailed_results(self, results):
        """Update detailed results table"""
        self.details_table.setRowCount(len(results))

        for row, result in enumerate(results):
            self.details_table.setItem(row, 0, QTableWidgetItem(result.timestamp.strftime("%H:%M:%S")))
            self.details_table.setItem(row, 1, QTableWidgetItem(f"{result.config.temperature:.2f}"))
            self.details_table.setItem(row, 2, QTableWidgetItem(str(result.config.num_ctx)))
            self.details_table.setItem(row, 3, QTableWidgetItem(str(result.config.num_predict)))
            self.details_table.setItem(row, 4, QTableWidgetItem(f"{result.config.repeat_penalty:.2f}"))
            self.details_table.setItem(row, 5, QTableWidgetItem(str(result.config.top_k)))
            self.details_table.setItem(row, 6, QTableWidgetItem(f"{result.config.top_p:.2f}"))
            self.details_table.setItem(row, 7, QTableWidgetItem(f"{result.accuracy_score:.3f}"))

    def save_results(self):
        """Save optimization results"""
        if not self.optimization_results:
            QMessageBox.warning(self, "No Results", "No optimization results to save.")
            return

        filename, _ = QFileDialog.getSaveFileName(
            self, "Save Optimization Results",
            f"optimization_results_{int(time.time())}.json",
            "JSON Files (*.json)"
        )

        if filename:
            try:
                with open(filename, 'w') as f:
                    json.dump(self.optimization_results, f, indent=2, default=str)

                self.log_message(f"💾 Results saved to: {filename}")
                QMessageBox.information(self, "Success", f"Results saved to:\n{filename}")

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save results:\n{e}")

    def closeEvent(self, event):
        """Handle application close"""
        if self.current_optimization and self.current_optimization.isRunning():
            reply = QMessageBox.question(
                self, "Confirm Exit",
                "Optimization is still running. Stop and exit?",
                QMessageBox.Yes | QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                self.stop_optimization()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

def main():
    """Main function to run the optimization lab"""
    app = QApplication(sys.argv)

    # Set application style
    app.setStyle('Fusion')

    # Create and show main window
    window = OptimizationLabGUI()
    window.show()

    # Show system tray notification
    if hasattr(window, 'tray_icon'):
        window.tray_icon.showMessage(
            "Parameter Optimization Lab",
            "Optimization Lab is ready to find perfect parameters!",
            QSystemTrayIcon.Information,
            3000
        )

    sys.exit(app.exec())

if __name__ == "__main__":
    main()