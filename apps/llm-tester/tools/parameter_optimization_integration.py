#!/usr/bin/env python3
# File: parameter_optimization_integration.py
# Path: /home/herb/Desktop/LLM-Tester/parameter_optimization_integration.py
# Standard: AIDEV-PascalCase-2.1
# Created: 2025-10-04
# Last Modified: 2025-10-04 03:08AM

"""
Integration of Adaptive Parameter Optimizer with LLM-Tester main application
"""

import sys
import time
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QComboBox, QSpinBox, QTextEdit, QProgressBar, QGroupBox,
    QCheckBox, QFormLayout, QMessageBox
)
from PySide6.QtCore import Qt, Signal, QThread, pyqtSignal
from adaptive_parameter_optimizer import (
    AdaptiveParameterOptimizer,
    OptimizationStrategy,
    ParameterSet,
    TestResult
)

class ParameterOptimizationThread(QThread):
    """Background thread for parameter optimization"""

    progress_update = pyqtSignal(int, str)  # progress, message
    result_found = pyqtSignal(dict)  # best parameters
    optimization_complete = pyqtSignal(bool)  # success status

    def __init__(self, model_name, prompt, test_model_func, strategy, max_iterations, target_accuracy):
        super().__init__()
        self.model_name = model_name
        self.prompt = prompt
        self.test_model_func = test_model_func
        self.strategy = strategy
        self.max_iterations = max_iterations
        self.target_accuracy = target_accuracy
        self.optimizer = None
        self.should_stop = False

    def run(self):
        """Run the optimization in background"""
        try:
            self.progress_update.emit(0, f"Initializing optimizer for {self.model_name}...")

            self.optimizer = AdaptiveParameterOptimizer(
                model_name=self.model_name,
                optimization_strategy=self.strategy
            )

            self.progress_update.emit(5, "Starting parameter optimization...")

            # Custom optimization loop with progress updates
            current_params = self.optimizer.start_params
            best_params = current_params
            best_score = 0.0

            for iteration in range(self.max_iterations):
                if self.should_stop:
                    break

                progress = int((iteration / self.max_iterations) * 90) + 5
                self.progress_update.emit(progress, f"Iteration {iteration + 1}/{self.max_iterations}")

                # Test current parameters
                result = self.optimizer.evaluate_parameters(
                    self.prompt,
                    current_params,
                    self.test_model_func
                )

                # Calculate fitness score
                current_score = self.optimizer._calculate_fitness_score(result)

                # Update best result
                if current_score > best_score:
                    best_score = current_score
                    best_params = current_params

                    # Emit result update
                    self.result_found.emit({
                        'parameters': best_params.to_dict(),
                        'score': best_score,
                        'accuracy': result.accuracy_score,
                        'time': result.response_time,
                        'iteration': iteration + 1
                    })

                    # Check target accuracy
                    if result.accuracy_score >= self.target_accuracy:
                        self.progress_update.emit(100, f"Target accuracy achieved! ({result.accuracy_score:.3f})")
                        break

                # Generate variations for next iteration
                if iteration < self.max_iterations - 1:
                    variations = self.optimizer.generate_parameter_variations(current_params, iteration + 1)

                    # Test variations and pick best
                    best_variation_score = current_score
                    best_variation_params = current_params

                    for var_params in variations:
                        if self.should_stop:
                            break

                        var_result = self.optimizer.evaluate_parameters(
                            self.prompt,
                            var_params,
                            self.test_model_func
                        )
                        var_score = self.optimizer._calculate_fitness_score(var_result)

                        if var_score > best_score:
                            best_score = var_score
                            best_params = var_params
                            best_variation_score = var_score
                            best_variation_params = var_params

                            self.result_found.emit({
                                'parameters': best_params.to_dict(),
                                'score': best_score,
                                'accuracy': var_result.accuracy_score,
                                'time': var_result.response_time,
                                'iteration': iteration + 1
                            })

                    current_params = best_variation_params

            self.progress_update.emit(100, "Optimization complete!")
            self.optimization_complete.emit(True)

        except Exception as e:
            self.progress_update.emit(0, f"Error: {str(e)}")
            self.optimization_complete.emit(False)

    def stop(self):
        """Stop the optimization process"""
        self.should_stop = True

class ParameterOptimizationWidget(QWidget):
    """Widget for parameter optimization in LLM-Tester"""

    parameters_optimized = Signal(str, dict)  # model_name, optimized_parameters

    def __init__(self, model_library, test_worker):
        super().__init__()
        self.model_library = model_library
        self.test_worker = test_worker
        self.optimization_thread = None
        self.init_ui()

    def init_ui(self):
        """Initialize the UI"""
        layout = QVBoxLayout(self)

        # Header
        header_label = QLabel("🎯 Adaptive Parameter Optimization")
        header_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #e94560; padding: 10px;")
        layout.addWidget(header_label)

        # Configuration Group
        config_group = QGroupBox("Optimization Configuration")
        config_layout = QFormLayout(config_group)

        # Model selection
        self.model_combo = QComboBox()
        self.update_model_list()
        config_layout.addRow("Model:", self.model_combo)

        # Strategy selection
        self.strategy_combo = QComboBox()
        self.strategy_combo.addItems([
            "Balanced (Accuracy + Speed)",
            "Accuracy First (Must be Perfect)",
            "Speed First (Fast as Possible)"
        ])
        config_layout.addRow("Strategy:", self.strategy_combo)

        # Target accuracy
        self.target_accuracy_spin = QSpinBox()
        self.target_accuracy_spin.setRange(80, 100)
        self.target_accuracy_spin.setValue(95)
        self.target_accuracy_spin.setSuffix("%")
        config_layout.addRow("Target Accuracy:", self.target_accuracy_spin)

        # Max iterations
        self.max_iterations_spin = QSpinBox()
        self.max_iterations_spin.setRange(3, 20)
        self.max_iterations_spin.setValue(10)
        config_layout.addRow("Max Iterations:", self.max_iterations_spin)

        layout.addWidget(config_group)

        # Test prompt
        prompt_group = QGroupBox("Test Prompt")
        prompt_layout = QVBoxLayout(prompt_group)

        self.prompt_text = QTextEdit()
        self.prompt_text.setMaximumHeight(100)
        self.prompt_text.setPlainText("Create a Python function to calculate the area of a circle given its radius.")
        prompt_layout.addWidget(QLabel("Enter a representative prompt to optimize against:"))
        prompt_layout.addWidget(self.prompt_text)

        layout.addWidget(prompt_group)

        # Progress section
        progress_group = QGroupBox("Optimization Progress")
        progress_layout = QVBoxLayout(progress_group)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        progress_layout.addWidget(self.progress_bar)

        self.status_label = QLabel("Ready to start optimization")
        self.status_label.setStyleSheet("color: #eee;")
        progress_layout.addWidget(self.status_label)

        # Results display
        self.results_text = QTextEdit()
        self.results_text.setMaximumHeight(150)
        self.results_text.setVisible(False)
        progress_layout.addWidget(self.results_text)

        layout.addWidget(progress_group)

        # Control buttons
        button_layout = QHBoxLayout()

        self.start_button = QPushButton("🚀 Start Optimization")
        self.start_button.clicked.connect(self.start_optimization)
        button_layout.addWidget(self.start_button)

        self.stop_button = QPushButton("⏹️ Stop")
        self.stop_button.clicked.connect(self.stop_optimization)
        self.stop_button.setEnabled(False)
        button_layout.addWidget(self.stop_button)

        self.apply_button = QPushButton("✅ Apply Parameters")
        self.apply_button.clicked.connect(self.apply_optimized_parameters)
        self.apply_button.setEnabled(False)
        button_layout.addWidget(self.apply_button)

        layout.addLayout(button_layout)

        # Info section
        info_label = QLabel("ℹ️ This will test different parameter combinations to find the optimal balance between accuracy and speed for your selected model and use case.")
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #aaa; font-size: 11px; padding: 10px;")
        layout.addWidget(info_label)

    def update_model_list(self):
        """Update the model selection combo box"""
        self.model_combo.clear()
        available_models = self.model_library.get_selected_models()
        if available_models:
            self.model_combo.addItems(available_models)
        else:
            self.model_combo.addItems(["phi3:3.8b", "phi3:14b"])  # Default options

    def get_strategy_from_combo(self) -> OptimizationStrategy:
        """Get optimization strategy from combo box selection"""
        index = self.strategy_combo.currentIndex()
        strategies = [
            OptimizationStrategy.BALANCED,
            OptimizationStrategy.ACCURACY_FIRST,
            OptimizationStrategy.SPEED_FIRST
        ]
        return strategies[index]

    def start_optimization(self):
        """Start the parameter optimization"""
        model_name = self.model_combo.currentText()
        if not model_name:
            QMessageBox.warning(self, "No Model Selected", "Please select a model to optimize.")
            return

        prompt = self.prompt_text.toPlainText().strip()
        if not prompt:
            QMessageBox.warning(self, "No Prompt", "Please enter a test prompt.")
            return

        # Get configuration
        strategy = self.get_strategy_from_combo()
        target_accuracy = self.target_accuracy_spin.value() / 100.0
        max_iterations = self.max_iterations_spin.value()

        # Create test function
        def test_model_func(prompt_text: str, params: dict) -> str:
            """Test function that calls the actual model"""
            # Create a temporary task
            task_id = hash(f"opt_{model_name}_{time.time()}") % 1000000

            # Prepare task for test worker
            task = (model_name, prompt_text, params, task_id, 0)

            # For now, return a mock response
            # In a real implementation, you'd integrate with the test worker
            time.sleep(2.0)  # Simulate model response time

            if params.get('temperature', 0.5) < 0.3:
                return "```python\nimport math\ndef circle_area(radius):\n    return math.pi * radius ** 2\n```"
            elif params.get('temperature', 0.5) > 0.7:
                return "```python\nimport maths\ndef circle_area(r):\n    return maths.pi * r ** 2\n```"
            else:
                return "```python\nimport math\ndef circle_area(radius):\n    return math.pi * radius ** 2\n```"

        # Start optimization thread
        self.optimization_thread = ParameterOptimizationThread(
            model_name=model_name,
            prompt=prompt,
            test_model_func=test_model_func,
            strategy=strategy,
            max_iterations=max_iterations,
            target_accuracy=target_accuracy
        )

        # Connect signals
        self.optimization_thread.progress_update.connect(self.update_progress)
        self.optimization_thread.result_found.connect(self.display_result)
        self.optimization_thread.optimization_complete.connect(self.optimization_finished)

        # Update UI
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.apply_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.results_text.clear()
        self.results_text.setVisible(True)
        self.best_parameters = None

        # Start thread
        self.optimization_thread.start()

    def stop_optimization(self):
        """Stop the current optimization"""
        if self.optimization_thread:
            self.optimization_thread.stop()
            self.optimization_thread.wait()

        self.optimization_finished(False)

    def update_progress(self, progress: int, message: str):
        """Update progress display"""
        self.progress_bar.setValue(progress)
        self.status_label.setText(message)

    def display_result(self, result: dict):
        """Display optimization result"""
        params = result['parameters']
        message = (
            f"Iteration {result['iteration']}: "
            f"Score: {result['score']:.3f} | "
            f"Accuracy: {result['accuracy']:.3f} | "
            f"Time: {result['time']:.1f}s\n"
            f"  Temp: {params['temperature']:.2f}, "
            f"Ctx: {params['num_ctx']}, "
            "Pred: {params['num_predict']}"
        )

        self.results_text.append(message)
        self.best_parameters = result

    def optimization_finished(self, success: bool):
        """Handle optimization completion"""
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.progress_bar.setVisible(False)

        if success and self.best_parameters:
            self.apply_button.setEnabled(True)
            self.status_label.setText("✅ Optimization complete! Click 'Apply Parameters' to use the optimized settings.")
        else:
            self.status_label.setText("❌ Optimization failed or was stopped.")

    def apply_optimized_parameters(self):
        """Apply the optimized parameters to the current configuration"""
        if not self.best_parameters:
            return

        model_name = self.model_combo.currentText()
        optimized_params = self.best_parameters['parameters']

        # Emit signal to apply parameters
        self.parameters_optimized.emit(model_name, optimized_params)

        QMessageBox.information(
            self,
            "Parameters Applied",
            f"Optimized parameters have been applied to {model_name}!\n\n"
            f"Temperature: {optimized_params['temperature']:.2f}\n"
            f"Context: {optimized_params['num_ctx']}\n"
            f"Max Output: {optimized_params['num_predict']}\n"
            f"Score: {self.best_parameters['score']:.3f}"
        )

def demo_integration():
    """Demo the parameter optimization integration"""
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    # Create mock model library and test worker
    class MockModelLibrary:
        def get_selected_models(self):
            return ["phi3:3.8b", "phi3:14b"]

    class MockTestWorker:
        pass

    # Create widget
    widget = ParameterOptimizationWidget(MockModelLibrary(), MockTestWorker())
    widget.show()

    app.exec()

if __name__ == "__main__":
    demo_integration()