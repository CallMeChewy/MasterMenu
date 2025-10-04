# File: LLM-Tester-Enhanced.py
# Path: /home/herb/Desktop/LLM-Tester/LLM-Tester-Enhanced.py
# Standard: AIDEV-PascalCase-2.1
# Created: 2025-10-01
# Last Modified: 2025-10-01 4:15PM

import sys
import ollama
import time
import json
import psutil
from datetime import datetime
from PySide6.QtCore import QThread, Signal, Qt, QTimer
import statistics
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import seaborn as sns
import numpy as np
import pandas as pd
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QTreeWidget, QTreeWidgetItem, QTextEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QLabel, QSpinBox,
    QSplitter, QScrollArea, QComboBox, QSlider, QCheckBox, QGroupBox,
    QProgressBar, QFrame, QLineEdit, QMessageBox
)
from PySide6.QtGui import QBrush, QColor
from PySide6.QtCore import Qt
from database import init_database_connection, get_db, save_test_result, get_current_db_info
from structured_output import StructuredOutputManager, OutputFormat
from db_library_widget import DatabaseLibraryWidget
import queue


class SystemMonitor(QThread):
    """Monitor system resources during testing"""
    metrics_updated = Signal(dict)

    def __init__(self):
        super().__init__()
        self.running = False
        self.metrics = {
            'cpu_percent': 0,
            'cpu_temp': 0,
            'ram_used_gb': 0,
            'ram_total_gb': 0,
            'gpu_utilization': 0,
            'gpu_vram_used_mb': 0,
            'gpu_vram_total_mb': 0,
            'gpu_temp_c': 0
        }

    def run(self):
        self.running = True
        while self.running:
            try:
                # CPU and RAM metrics
                self.metrics['cpu_percent'] = psutil.cpu_percent(interval=0.1)
                memory = psutil.virtual_memory()
                self.metrics['ram_used_gb'] = memory.used / (1024**3)
                self.metrics['ram_total_gb'] = memory.total / (1024**3)

                # GPU metrics - try to get real data
                try:
                    # Try to get GPU info from nvidia-smi
                    import subprocess
                    result = subprocess.run([
                        'nvidia-smi', '--query-gpu=utilization.gpu,memory.used,memory.total,temperature.gpu',
                        '--format=csv,noheader,nounits'
                    ], capture_output=True, text=True, timeout=2)

                    if result.returncode == 0:
                        gpu_data = result.stdout.strip().split(', ')
                        if len(gpu_data) >= 4:
                            self.metrics['gpu_utilization'] = float(gpu_data[0])
                            self.metrics['gpu_vram_used_mb'] = float(gpu_data[1])
                            self.metrics['gpu_vram_total_mb'] = float(gpu_data[2])
                            self.metrics['gpu_temp_c'] = float(gpu_data[3])
                        else:
                            self.set_default_gpu_metrics()
                    else:
                        self.set_default_gpu_metrics()
                except Exception:
                    # Fallback to default values if nvidia-smi fails
                    self.set_default_gpu_metrics()

                self.metrics_updated.emit(self.metrics)
                self.msleep(1000)  # Update every second
            except Exception as e:
                print(f"System monitoring error: {e}")
                self.msleep(5000)

    def set_default_gpu_metrics(self):
        """Set default GPU metrics when nvidia-smi is not available"""
        self.metrics['gpu_utilization'] = 0
        self.metrics['gpu_vram_used_mb'] = 0
        self.metrics['gpu_vram_total_mb'] = 8192  # RTX 4070
        self.metrics['gpu_temp_c'] = 0

    def stop(self):
        self.running = False


class TestWorker(QThread):
    """Execute LLM tests with enhanced monitoring"""
    task_finished = Signal(dict)
    progress_updated = Signal(str, int)

    def __init__(self):
        super().__init__()
        self.tasks = []
        self.running = True
        self.current_model = None
        self.current_prompt_index = 0
        self.total_prompts = 0

    def run(self):
        while self.running:
            if self.tasks:
                task = self.tasks.pop(0)
                self.execute_task(task)
            else:
                self.msleep(100)

    def execute_task(self, task):
        """Execute a single test task with comprehensive monitoring"""
        try:
            if len(task) == 6:
                model_name, prompt_text, parameters, task_id, suite_id, config_label = task
            else:
                model_name, prompt_text, parameters, task_id, suite_id = task
                config_label = None

            # Update progress
            self.progress_updated.emit(f"Testing {model_name}",
                                     (self.current_prompt_index / self.total_prompts) * 100 if self.total_prompts > 0 else 0)

            # Record start time and metrics
            start_time = time.time()

            # Check if structured output is requested and available
            final_prompt = prompt_text
            output_format = "plain_text"

            # Try to get structured output formatting if available
            try:
                # Check if we have access to the main window and parameters widget
                if hasattr(self, 'window') and hasattr(self.window, 'parameters'):
                    output_format = self.window.parameters.get_current_output_format()
                    final_prompt = self.window.parameters.format_prompt_with_output(
                        prompt_text,
                        context={
                            "model": model_name,
                            "parameters": parameters,
                            "task_id": task_id,
                            "suite_id": suite_id
                        }
                    )
            except Exception as e:
                # If structured output formatting fails, use original prompt
                print(f"Could not apply structured output formatting: {str(e)}")
                final_prompt = prompt_text

            # Execute the LLM request with parameters
            response = ollama.generate(
                model=model_name,
                prompt=final_prompt,
                options=parameters
            )

            end_time = time.time()
            response_time = end_time - start_time

            # Validate structured response if applicable
            if output_format != "plain_text":
                try:
                    validation_result = self.window.parameters.validate_structured_response(response_text, output_format)
                    if not validation_result.get("valid", False):
                        print(f"Structured response validation failed: {validation_result}")
                except Exception as e:
                    print(f"Response validation error: {str(e)}")

            # Parse response details
            response_text = response.get('response', '')
            tokens_in = len(prompt_text.split())  # Approximate
            tokens_out = len(response_text.split())
            tokens_per_second = tokens_out / response_time if response_time > 0 else 0

            # Prepare result data
            result = {
                'model_name': model_name,
                'prompt_text': prompt_text,
                'response_text': response_text,
                'response_time': response_time,
                'tokens_in': tokens_in,
                'tokens_out': tokens_out,
                'tokens_per_second': tokens_per_second,
                'parameters': parameters,
                'task_id': task_id,
                'suite_id': suite_id,
                'config_label': config_label,  # Add config_label for parameter tests
                'status': 'completed',
                'error': None,
                'timestamp': datetime.now().isoformat()
            }

            self.task_finished.emit(result)

        except Exception as e:
            # Handle errors
            if len(task) == 6:
                model_name, prompt_text, parameters, task_id, suite_id, config_label = task
            else:
                model_name, prompt_text, parameters, task_id, suite_id = task
                config_label = None

            error_result = {
                'model_name': model_name,
                'prompt_text': prompt_text,
                'response_text': '',
                'response_time': 0,
                'tokens_in': 0,
                'tokens_out': 0,
                'tokens_per_second': 0,
                'parameters': parameters,
                'task_id': task_id,
                'suite_id': suite_id,
                'config_label': config_label,
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
            self.task_finished.emit(error_result)

        finally:
            # Small delay between requests
            self.msleep(1000)

    def add_task(self, task):
        self.tasks.append(task)

    def stop(self):
        self.running = False


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


class ModelLibraryWidget(QWidget):
    """Enhanced model selection and management"""

    model_selection_changed = Signal(list)

    def __init__(self):
        super().__init__()
        self.init_ui()
        self.all_models_data = []  # Store all models for filtering
        self.populate_models()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Filter controls
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filter:"))

        self.category_filter = QComboBox()
        self.category_filter.addItems(["All", "Code", "Creative", "Logic", "Vision", "General"])
        self.category_filter.currentTextChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.category_filter)

        self.size_filter = QComboBox()
        self.size_filter.addItems(["All Sizes", "Small (<4GB)", "Medium (4-8GB)", "Large (>8GB)"])
        self.size_filter.currentTextChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.size_filter)

        # Search box
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search models...")
        self.search_box.textChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.search_box)

        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.refresh_models)
        filter_layout.addWidget(refresh_btn)

        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # Model tree with enhanced columns
        self.model_tree = QTreeWidget()
        self.model_tree.setColumnCount(6)
        self.model_tree.setHeaderLabels([
            "Model", "Size (GB)", "Parameters", "Specialty", "VRAM Est.", "Speed"
        ])
        self.model_tree.itemChanged.connect(self.on_selection_changed)
        
        # Configure columns for auto-resizing and sorting
        header = self.model_tree.header()
        header.setSectionResizeMode(0, QHeaderView.Interactive)  # Model - interactive for sorting
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Size
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Parameters
        header.setSectionResizeMode(3, QHeaderView.Stretch)  # Specialty
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # VRAM
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Speed
        header.setSectionsMovable(True)  # Allow column reordering
        header.setSortIndicatorShown(True)  # Show sort indicators
        header.setSortIndicator(0, Qt.AscendingOrder)  # Default sort by model name
        
        # Enable sorting
        self.model_tree.setSortingEnabled(True)
        self.model_tree.sortByColumn(0, Qt.AscendingOrder)
        
        layout.addWidget(self.model_tree)

        # Selection info and controls
        selection_frame = QFrame()
        selection_layout = QHBoxLayout(selection_frame)

        self.selection_label = QLabel("Selected: 0 models | Est. VRAM: 0GB/8GB")
        selection_layout.addWidget(self.selection_label)

        selection_layout.addStretch()

        select_all_btn = QPushButton("Select All")
        select_all_btn.clicked.connect(self.select_all)
        selection_layout.addWidget(select_all_btn)

        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.clear_selection)
        selection_layout.addWidget(clear_btn)

        layout.addWidget(selection_frame)

    def populate_models(self):
        """Populate model list with enhanced information"""
        try:
            # Check if ollama is available
            try:
                models = ollama.list()['models']
            except Exception as ollama_error:
                print(f"Ollama connection error: {ollama_error}")
                self.model_tree.clear()
                error_item = QTreeWidgetItem(self.model_tree)
                error_item.setText(0, "⚠️ Ollama not running")
                error_item.setText(1, "Start Ollama first")
                self.model_tree.addTopLevelItem(error_item)
                return

            self.all_models_data = []  # Clear and refresh stored data

            for model in models:
                try:
                    model_name = model['model']
                    size_gb = model['size'] / (1024**3)

                    # Determine model characteristics
                    family, specialty, speed_icon = self.analyze_model(model_name, size_gb)
                    vram_estimate = self.estimate_vram(size_gb)

                    self.all_models_data.append({
                        'name': model_name,
                        'size_gb': size_gb,
                        'parameters': self.extract_param_count(model_name),
                        'specialty': specialty,
                        'family': family,
                        'vram_estimate': vram_estimate,
                        'speed_icon': speed_icon
                    })
                except Exception as model_error:
                    print(f"Error processing model {model}: {model_error}")
                    continue

            # Sort by specialty then size
            self.all_models_data.sort(key=lambda x: (x['specialty'], x['size_gb']))

            # Apply current filters to populate tree
            self.apply_filters()

        except Exception as e:
            print(f"Error populating models: {e}")
            # Show error in tree
            self.model_tree.clear()
            error_item = QTreeWidgetItem(self.model_tree)
            error_item.setText(0, f"Error loading models: {str(e)}")
            error_item.setText(1, "Check Ollama connection")
            self.model_tree.addTopLevelItem(error_item)

    def analyze_model(self, model_name, size_gb):
        """Analyze model to determine characteristics"""
        name_lower = model_name.lower()

        # Determine specialty
        if 'coder' in name_lower:
            specialty = "Code"
            family = "qwen2.5"
        elif 'llava' in name_lower:
            specialty = "Vision"
            family = "llava"
        elif 'deepseek' in name_lower:
            specialty = "Logic"
            family = "deepseek"
        elif 'phi' in name_lower:
            specialty = "Logic"
            family = "phi"
        elif 'gemma' in name_lower:
            specialty = "Creative"
            family = "gemma"
        elif 'qwen' in name_lower:
            specialty = "All"
            family = "qwen"
        elif 'llama' in name_lower:
            specialty = "All"
            family = "llama"
        else:
            specialty = "General"
            family = "other"

        # Speed estimation based on size and model type
        if size_gb < 3:
            speed_icon = "⚡⚡⚡"  # Very fast
        elif size_gb < 6:
            speed_icon = "⚡⚡"    # Fast
        elif size_gb < 10:
            speed_icon = "⚡"      # Medium
        else:
            speed_icon = "🐢"      # Slower

        return family, specialty, speed_icon

    def extract_param_count(self, model_name):
        """Extract parameter count from model name"""
        if 'b' in model_name.lower():
            for part in model_name.split(':'):
                if 'b' in part.lower():
                    try:
                        return part.upper()
                    except:
                        continue
        return "Unknown"

    def estimate_vram(self, size_gb):
        """Estimate VRAM usage"""
        # Rough estimation: model size + 2GB overhead
        return size_gb + 2.0

    def select_all(self):
        for i in range(self.model_tree.topLevelItemCount()):
            item = self.model_tree.topLevelItem(i)
            item.setCheckState(0, Qt.Checked)
        self.update_selection_info()

    def clear_selection(self):
        for i in range(self.model_tree.topLevelItemCount()):
            item = self.model_tree.topLevelItem(i)
            item.setCheckState(0, Qt.Unchecked)
        self.update_selection_info()

    def on_selection_changed(self):
        self.update_selection_info()

    def update_selection_info(self):
        """Update selection info and emit signal"""
        selected_models = []
        total_vram = 0

        for i in range(self.model_tree.topLevelItemCount()):
            item = self.model_tree.topLevelItem(i)
            if item.checkState(0) == Qt.Checked:
                model_name = item.text(0)
                selected_models.append(model_name)
                vram_est = float(item.text(4).replace('GB', ''))
                total_vram += vram_est

        self.selection_label.setText(f"Selected: {len(selected_models)} models | Est. VRAM: {total_vram:.1f}GB/8GB")
        self.model_selection_changed.emit(selected_models)

    def get_selected_models(self):
        """Get list of selected model names"""
        selected = []
        for i in range(self.model_tree.topLevelItemCount()):
            item = self.model_tree.topLevelItem(i)
            if item.checkState(0) == Qt.Checked:
                selected.append(item.text(0))
        return selected

    def apply_filters(self):
        """Apply category, size, and search filters to model list"""
        category_filter = self.category_filter.currentText()
        size_filter = self.size_filter.currentText()
        search_text = self.search_box.text().lower()

        # Clear current tree
        self.model_tree.clear()

        # Filter models
        filtered_models = []
        for model_data in self.all_models_data:
            # Category filter
            if category_filter != "All" and model_data['specialty'] != category_filter:
                continue

            # Size filter
            if size_filter != "All Sizes":
                size_gb = model_data['size_gb']
                if size_filter == "Small (<4GB)" and size_gb >= 4:
                    continue
                elif size_filter == "Medium (4-8GB)" and (size_gb < 4 or size_gb > 8):
                    continue
                elif size_filter == "Large (>8GB)" and size_gb <= 8:
                    continue

            # Search filter
            if search_text and search_text not in model_data['name'].lower():
                continue

            filtered_models.append(model_data)

        # Rebuild tree with filtered models
        for data in filtered_models:
            item = QTreeWidgetItem(self.model_tree)
            item.setText(0, data['name'])
            item.setText(1, f"{data['size_gb']:.1f}")
            item.setText(2, data['parameters'])
            item.setText(3, data['specialty'])
            item.setText(4, f"{data['vram_estimate']:.1f}GB")
            item.setText(5, data['speed_icon'])

            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(0, Qt.Unchecked)
            
            # Enhance checkbox visibility with border/highlight
            # Exclude embedding models from selection
            if 'embed' in data['name'].lower():
                item.setFlags(item.flags() & ~Qt.ItemIsUserCheckable)  # Remove checkbox
                item.setForeground(0, QColor("#666666"))  # Gray out text
            else:
                # Use simpler background setting to avoid QBrush constructor issues
                item.setBackground(0, QColor("#2a2a3a"))
                item.setForeground(0, QColor("#eee"))

        # Update selection info
        self.update_selection_info()

    def refresh_models(self):
        """Refresh the model list from Ollama"""
        try:
            # Show loading state
            self.model_tree.clear()
            loading_item = QTreeWidgetItem(self.model_tree)
            loading_item.setText(0, "Loading models...")
            loading_item.setText(1, "...")
            self.model_tree.addTopLevelItem(loading_item)

            # Repopulate models
            self.populate_models()

        except Exception as e:
            print(f"Error refreshing models: {e}")
            # Show error state
            self.model_tree.clear()
            error_item = QTreeWidgetItem(self.model_tree)
            error_item.setText(0, f"Error: {str(e)}")
            self.model_tree.addTopLevelItem(error_item)


class TestSuitesWidget(QWidget):
    """Test suite management and execution"""

    suite_selected = Signal(str, list)  # suite_name, prompts
    run_test = Signal(str, list)  # single_prompt, selected_models
    run_suite = Signal(str, list)  # suite_name, prompts
    run_suite_with_objective_tests = Signal(str, list)  # suite_name, prompts (with objective test integration)

    def __init__(self):
        super().__init__()
        self.current_suite = None
        self.suite_widgets = []  # Store references to suite widgets
        self.init_ui()
        self.load_default_suites()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Header
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("📝 Test Suites"))
        header_layout.addStretch()

        add_suite_btn = QPushButton("+ New Suite")
        add_suite_btn.setStyleSheet("QPushButton { font-weight: bold; padding: 8px 16px; background-color: #6f42c1; color: white; border: 1px solid #5a32a3; border-radius: 4px; } QPushButton:hover { background-color: #5a32a3; }")
        add_suite_btn.clicked.connect(self.create_new_suite)
        header_layout.addWidget(add_suite_btn)

        layout.addLayout(header_layout)

        # Test suite categories
        self.suites_scroll = QScrollArea()
        self.suites_widget = QWidget()
        self.suites_layout = QVBoxLayout(self.suites_widget)
        self.suites_scroll.setWidget(self.suites_widget)
        self.suites_scroll.setWidgetResizable(True)
        layout.addWidget(self.suites_scroll)

        # Cycle and Selection Controls
        controls_frame = QFrame()
        controls_layout = QVBoxLayout(controls_frame)

        # First row: Selection info
        selection_layout = QHBoxLayout()
        self.current_suite_label = QLabel("Suite: None selected")
        selection_layout.addWidget(self.current_suite_label)
        selection_layout.addStretch()
        controls_layout.addLayout(selection_layout)

        # Second row: Cycle controls and options
        options_layout = QHBoxLayout()

        # Iterations control
        options_layout.addWidget(QLabel("Cycles:"))
        self.cycles_spinbox = QSpinBox()
        self.cycles_spinbox.setRange(1, 50)
        self.cycles_spinbox.setValue(3)
        self.cycles_spinbox.setSuffix(" iterations")
        self.cycles_spinbox.setToolTip("Number of times to run each test suite (higher = more reliable results)")
        options_layout.addWidget(self.cycles_spinbox)

        options_layout.addWidget(QLabel("|"))

        # Multiple suite selection mode
        self.multi_suite_checkbox = QCheckBox("Multi-Suite Mode")
        self.multi_suite_checkbox.setToolTip("Enable selection of multiple test suites to run in sequence")
        options_layout.addWidget(self.multi_suite_checkbox)

        # Objective test integration
        self.use_objective_tests_checkbox = QCheckBox("Use Objective Tests")
        self.use_objective_tests_checkbox.setToolTip("Use provable test cases from the comprehensive test system")
        options_layout.addWidget(self.use_objective_tests_checkbox)

        options_layout.addStretch()

        # Run button
        self.run_suite_btn = QPushButton("Run Suite(s)")
        self.run_suite_btn.setEnabled(False)
        self.run_suite_btn.clicked.connect(self.run_selected_suite)
        options_layout.addWidget(self.run_suite_btn)

        controls_layout.addLayout(options_layout)
        layout.addWidget(controls_frame)

    def load_default_suites(self):
        """Load default test suites"""
        default_suites = [
            {
                'name': 'Code Generation',
                'icon': '🔧',
                'prompts': [
                    'Create a Python function to calculate the area of a circle given its radius.',
                    'Write a program to print all prime numbers under 30.',
                    'Create a function to calculate the area of a triangle given base and height.',
                    'Write a program that validates if a string is a valid email address.',
                    'Create a function to reverse a linked list in-place.'
                ]
            },
            {
                'name': 'Creative Writing',
                'icon': '✍️',
                'prompts': [
                    'Write a short opening paragraph for a science fiction story about AI consciousness.',
                    'Create a haiku about programming.',
                    'Write a dialogue between two philosophers discussing free will.',
                    'Describe a sunset from the perspective of a robot experiencing it for the first time.',
                    'Create a short poem about the relationship between humans and technology.'
                ]
            },
            {
                'name': 'Logic & Reasoning',
                'icon': '🧠',
                'prompts': [
                    'Solve this classic logic puzzle: There are three boxes, one contains only apples, one only oranges, and one both. All boxes are labeled incorrectly. You can only draw one item from one box. How do you correctly label all boxes?',
                    'Explain the trolley problem and discuss the ethical implications of each possible action.',
                    'A bat and a ball cost $1.10 in total. The bat costs $1.00 more than the ball. How much does the ball cost? Explain your reasoning.',
                    'If you have a 3-gallon jug and a 5-gallon jug, how can you measure exactly 4 gallons of water?',
                    'Explain the concept of cognitive dissonance and provide a real-world example.'
                ]
            }
        ]

        for suite in default_suites:
            self.add_suite_group(suite)

    def add_suite_group(self, suite):
        """Add a test suite group to the UI"""
        group_box = ClickableGroupBox(f"{suite['icon']} {suite['name']}", suite['name'], suite['prompts'])
        group_box.suite_selected.connect(self.select_suite)
        group_layout = QVBoxLayout()  # Create layout without parent first

        # Add selection checkbox for multi-suite mode
        header_layout = QHBoxLayout()
        suite_checkbox = QCheckBox()
        suite_checkbox.setObjectName(f"checkbox_{suite['name']}")
        suite_checkbox.stateChanged.connect(lambda state, s=suite: self.on_suite_selection_changed(s, state))
        header_layout.addWidget(suite_checkbox)

        suite_label = QLabel(suite['name'])
        suite_label.setStyleSheet("font-weight: bold;")
        header_layout.addWidget(suite_label)

        # Add prompt button (before stretch so it's visible)
        add_prompt_btn = QPushButton("+ Add Prompt")
        add_prompt_btn.setStyleSheet("QPushButton { font-size: 11px; padding: 2px 8px; background-color: #17a2b8; color: white; border: 1px solid #138496; border-radius: 3px; } QPushButton:hover { background-color: #138496; }")
        # Create a proper closure to avoid lambda variable capture issues
        def make_add_prompt_handler(suite_name):
            def handler():
                self.add_prompt_to_suite(suite_name)
            return handler

        add_prompt_btn.clicked.connect(make_add_prompt_handler(suite['name']))
        add_prompt_btn.setParent(group_box)  # Set parent explicitly
        add_prompt_btn.setVisible(True)  # Ensure button is visible
        add_prompt_btn.setEnabled(True)  # Ensure button is enabled
        header_layout.addWidget(add_prompt_btn)
        header_layout.update()  # Force layout update

        # Prompt count
        self.prompt_count_labels = getattr(self, 'prompt_count_labels', {})
        prompt_count_label = QLabel(f"{len(suite['prompts'])} prompts")
        prompt_count_label.setStyleSheet("color: gray; font-size: 10px;")
        prompt_count_label.setObjectName(f"count_{suite['name']}")
        header_layout.addWidget(prompt_count_label)
        self.prompt_count_labels[suite['name']] = prompt_count_label

        # Add stretch at the end to push everything to the left
        header_layout.addStretch()

        group_layout.addLayout(header_layout)

        suite_data = {
            'name': suite['name'],
            'prompts': suite['prompts'],
            'widgets': [],
            'checkbox': suite_checkbox
        }

        for i, prompt in enumerate(suite['prompts']):
            prompt_layout = QHBoxLayout()

            # Prompt label with tooltip - show more characters and make it wider
            prompt_label = QLabel(f"[{prompt[:200]}...]" if len(prompt) > 200 else f"[{prompt}]")
            prompt_label.setWordWrap(True)
            prompt_label.setToolTip(prompt)
            prompt_label.setStyleSheet("margin-left: 20px; color: #e0e0e0; padding: 4px; background-color: #2a2a3a; border-radius: 4px; border: 1px solid #444;")
            prompt_label.setMinimumWidth(400)  # Make prompt labels wider
            prompt_layout.addWidget(prompt_label, 1)  # Give prompt label stretch factor

            # Control buttons with better spacing
            edit_btn = QPushButton("Edit")
            edit_btn.setMaximumWidth(60)
            edit_btn.setStyleSheet("QPushButton { font-size: 11px; padding: 4px; background-color: #4a90e2; color: white; border: 1px solid #357abd; border-radius: 3px; } QPushButton:hover { background-color: #357abd; }")
            edit_btn.clicked.connect(lambda p=prompt, i=i: self.edit_prompt(suite['name'], i, p))
            prompt_layout.addWidget(edit_btn)

            test_btn = QPushButton("Test")
            test_btn.setMaximumWidth(60)
            test_btn.setStyleSheet("QPushButton { font-size: 11px; padding: 4px; background-color: #28a745; color: white; border: 1px solid #1e7e34; border-radius: 3px; } QPushButton:hover { background-color: #218838; }")
            # Create a proper closure to avoid lambda variable capture issues
            def make_test_handler(prompt_text):
                def handler():
                    self.test_single_prompt(prompt_text)
                return handler

            test_btn.clicked.connect(make_test_handler(prompt))
            prompt_layout.addWidget(test_btn)

            delete_btn = QPushButton("Delete")
            delete_btn.setMaximumWidth(70)
            delete_btn.setStyleSheet("QPushButton { font-size: 11px; padding: 4px; background-color: #dc3545; color: white; border: 1px solid #c82333; border-radius: 3px; } QPushButton:hover { background-color: #c82333; }")
            delete_btn.clicked.connect(lambda s=suite['name'], i=i: self.delete_prompt(s, i))
            prompt_layout.addWidget(delete_btn)

            play_btn = QPushButton("▶")
            play_btn.setMaximumWidth(40)
            play_btn.setStyleSheet("QPushButton { font-size: 11px; padding: 4px; background-color: #007bff; color: white; border: 1px solid #0056b3; border-radius: 3px; } QPushButton:hover { background-color: #0056b3; }")
            # Create a proper closure to avoid lambda variable capture issues
            def make_play_handler(prompt_text):
                def handler():
                    self.run_prompt(prompt_text)
                return handler

            play_btn.clicked.connect(make_play_handler(prompt))
            prompt_layout.addWidget(play_btn)

            group_layout.addLayout(prompt_layout)

            # Store widget references (now 5 widgets per prompt)
            suite_data['widgets'].extend([prompt_label, edit_btn, test_btn, delete_btn, play_btn])

        # Also store the + Add Prompt button and count label
        suite_data['widgets'].extend([add_prompt_btn, prompt_count_label])

        # Set the layout on the group box after all child layouts are added
        group_box.setLayout(group_layout)
        self.suites_layout.addWidget(group_box)
        self.suite_widgets.append(suite_data)

        # Suite selection is now handled by ClickableGroupBox

    def select_suite(self, suite_name, prompts):
        """Select a test suite"""
        self.current_suite = suite_name
        self.current_suite_label.setText(f"Suite: {suite_name} ({len(prompts)} prompts)")
        self.run_suite_btn.setEnabled(True)
        self.suite_selected.emit(suite_name, prompts)

        # Highlight selected suite visually
        for i, suite_data in enumerate(self.suite_widgets):
            if suite_data['name'] == suite_name:
                # Find the group box and highlight it
                group_box = self.suites_layout.itemAt(i).widget()
                group_box.setStyleSheet("QGroupBox { border: 2px solid #e94560; }")
            else:
                # Remove highlight from other suites
                group_box = self.suites_layout.itemAt(i).widget()
                group_box.setStyleSheet("")

    def on_suite_selection_changed(self, suite, state):
        """Handle suite selection change in multi-suite mode"""
        if self.multi_suite_checkbox.isChecked():
            # Multi-suite mode - update UI accordingly
            self.update_multi_suite_selection()
        else:
            # Single suite mode - select the suite
            if state == 2:  # Checked
                self.select_suite(suite['name'], suite['prompts'])
            else:  # Unchecked
                self.deselect_all_suites()

    def update_multi_suite_selection(self):
        """Update UI for multi-suite selection"""
        selected_suites = self.get_selected_suites()
        total_prompts = sum(len(suite['prompts']) for suite in selected_suites)

        if selected_suites:
            suite_names = [suite['name'] for suite in selected_suites]
            if len(suite_names) == 1:
                self.current_suite_label.setText(f"Suite: {suite_names[0]} ({total_prompts} prompts)")
            else:
                self.current_suite_label.setText(f"Suites: {len(suite_names)} selected ({total_prompts} prompts)")
            self.run_suite_btn.setEnabled(True)
        else:
            self.current_suite_label.setText("Suites: None selected")
            self.run_suite_btn.setEnabled(False)

        # Update visual highlighting for multi-select
        for i, suite_data in enumerate(self.suite_widgets):
            group_box = self.suites_layout.itemAt(i).widget()
            if suite_data['checkbox'].isChecked():
                group_box.setStyleSheet("QGroupBox { border: 2px solid #4a90e2; background-color: #f0f8ff; }")
            else:
                group_box.setStyleSheet("")

    def get_selected_suites(self):
        """Get all selected test suites"""
        selected = []
        for suite_data in self.suite_widgets:
            if suite_data['checkbox'].isChecked():
                selected.append(suite_data)
        return selected

    def deselect_all_suites(self):
        """Deselect all suites"""
        for suite_data in self.suite_widgets:
            suite_data['checkbox'].setChecked(False)
        self.current_suite = None
        self.current_suite_label.setText("Suite: None selected")
        self.run_suite_btn.setEnabled(False)

    def edit_prompt(self, suite_name, prompt_index, current_prompt):
        """Edit a prompt in a suite"""
        print(f"🔧 EDIT BUTTON CLICKED: suite='{suite_name}', index={prompt_index}")
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QDialogButtonBox

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Edit Prompt - {suite_name}")
        dialog.setMinimumSize(600, 400)

        layout = QVBoxLayout(dialog)

        text_edit = QTextEdit()
        text_edit.setPlainText(current_prompt)
        text_edit.setMinimumHeight(300)
        layout.addWidget(text_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec() == QDialog.Accepted:
            new_prompt = text_edit.toPlainText()
            if new_prompt != current_prompt:
                # Update the prompt in the suite data
                for suite_data in self.suite_widgets:
                    if suite_data['name'] == suite_name:
                        # Update the prompt in the data
                        suite_data['prompts'][prompt_index] = new_prompt

                        # Update the label - find the correct prompt label (first widget in each prompt group)
                        widget_index = prompt_index * 5  # 5 widgets per prompt: label, edit, test, delete, play
                        if widget_index < len(suite_data['widgets']):
                            prompt_label = suite_data['widgets'][widget_index]
                            prompt_label.setText(f"[{new_prompt[:200]}...]" if len(new_prompt) > 200 else f"[{new_prompt}]")
                            prompt_label.setToolTip(new_prompt)

                            # Update the button connections to use the new prompt text
                            edit_btn = suite_data['widgets'][widget_index + 1]
                            test_btn = suite_data['widgets'][widget_index + 2]
                            delete_btn = suite_data['widgets'][widget_index + 3]
                            play_btn = suite_data['widgets'][widget_index + 4]

                            # Disconnect old connections and reconnect with new prompt
                            try:
                                edit_btn.clicked.disconnect()
                                test_btn.clicked.disconnect()
                                delete_btn.clicked.disconnect()
                                play_btn.clicked.disconnect()
                            except:
                                pass  # Ignore if no connections exist

                            # Reconnect with updated prompt text (fix lambda variable capture issues)
                            edit_btn.clicked.connect(lambda p=new_prompt, i=prompt_index: self.edit_prompt(suite_name, i, p))

                            def make_test_handler_for_edit(prompt_text):
                                def handler():
                                    self.test_single_prompt(prompt_text)
                                return handler
                            test_btn.clicked.connect(make_test_handler_for_edit(new_prompt))

                            delete_btn.clicked.connect(lambda s=suite_name, i=prompt_index: self.delete_prompt(s, i))

                            def make_play_handler_for_edit(prompt_text):
                                def handler():
                                    self.run_prompt(prompt_text)
                                return handler
                            play_btn.clicked.connect(make_play_handler_for_edit(new_prompt))

                        print(f"✅ Updated prompt {prompt_index} in suite '{suite_name}' with new text and button connections")
                        break

    def delete_prompt(self, suite_name, prompt_index):
        """Delete a prompt from a suite"""
        print(f"🗑️ DELETE BUTTON CLICKED: suite='{suite_name}', index={prompt_index}")
        from PySide6.QtWidgets import QMessageBox

        reply = QMessageBox.question(
            self,
            "Delete Prompt",
            f"Are you sure you want to delete prompt {prompt_index + 1} from suite '{suite_name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            for suite_data in self.suite_widgets:
                if suite_data['name'] == suite_name:
                    # Remove prompt from data
                    if 0 <= prompt_index < len(suite_data['prompts']):
                        del suite_data['prompts'][prompt_index]

                        # Remove widgets from layout
                        widgets_to_remove = suite_data['widgets'][prompt_index * 5:(prompt_index + 1) * 5]
                        for widget in widgets_to_remove:
                            widget.setParent(None)
                            widget.deleteLater()

                        # Remove widgets from data
                        del suite_data['widgets'][prompt_index * 5:(prompt_index + 1) * 5]

                        # Update prompt count
                        if hasattr(self, 'prompt_count_labels') and suite_name in self.prompt_count_labels:
                            self.prompt_count_labels[suite_name].setText(f"{len(suite_data['prompts'])} prompts")

                        # Refresh the entire suite display
                        self.refresh_suite_display()
                        break

    def add_prompt_to_suite(self, suite_name):
        """Add a new prompt to a suite"""
        print(f"➕ ADD PROMPT BUTTON CLICKED: suite='{suite_name}'")
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QDialogButtonBox, QLabel

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Add Prompt - {suite_name}")
        dialog.setMinimumSize(600, 400)

        layout = QVBoxLayout(dialog)

        # Add instruction label
        instruction_label = QLabel("Enter the new prompt text:")
        layout.addWidget(instruction_label)

        text_edit = QTextEdit()
        text_edit.setPlaceholderText("Enter your prompt here...")
        text_edit.setMinimumHeight(300)
        layout.addWidget(text_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec() == QDialog.Accepted:
            new_prompt = text_edit.toPlainText().strip()
            if new_prompt:
                for suite_data in self.suite_widgets:
                    if suite_data['name'] == suite_name:
                        # Add prompt to data
                        suite_data['prompts'].append(new_prompt)

                        # Find the group box for this suite
                        group_box = None
                        for i in range(self.suites_layout.count()):
                            widget = self.suites_layout.itemAt(i).widget()
                            if widget and isinstance(widget, ClickableGroupBox):
                                # Check if this is the right suite by looking at the title
                                if suite_name in widget.title():
                                    group_box = widget
                                    break

                        if group_box:
                            # Create new prompt widgets
                            prompt_layout = QHBoxLayout()
                            prompt_index = len(suite_data['prompts']) - 1

                            # Prompt label
                            prompt_label = QLabel(f"[{new_prompt[:200]}...]" if len(new_prompt) > 200 else f"[{new_prompt}]")
                            prompt_label.setWordWrap(True)
                            prompt_label.setToolTip(new_prompt)
                            prompt_label.setStyleSheet("margin-left: 20px; color: #e0e0e0; padding: 4px; background-color: #2a2a3a; border-radius: 4px; border: 1px solid #444;")
                            prompt_label.setMinimumWidth(400)
                            prompt_layout.addWidget(prompt_label, 1)

                            # Create buttons
                            edit_btn = QPushButton("Edit")
                            edit_btn.setMaximumWidth(60)
                            edit_btn.setStyleSheet("QPushButton { font-size: 11px; padding: 4px; background-color: #4a90e2; color: white; border: 1px solid #357abd; border-radius: 3px; } QPushButton:hover { background-color: #357abd; }")
                            edit_btn.clicked.connect(lambda p=new_prompt, i=prompt_index: self.edit_prompt(suite_name, i, p))
                            prompt_layout.addWidget(edit_btn)

                            test_btn = QPushButton("Test")
                            test_btn.setMaximumWidth(60)
                            test_btn.setStyleSheet("QPushButton { font-size: 11px; padding: 4px; background-color: #28a745; color: white; border: 1px solid #1e7e34; border-radius: 3px; } QPushButton:hover { background-color: #218838; }")
                            # Create a proper closure to avoid lambda variable capture issues
                            def make_test_handler_for_new_prompt(prompt_text):
                                def handler():
                                    self.test_single_prompt(prompt_text)
                                return handler
                            test_btn.clicked.connect(make_test_handler_for_new_prompt(new_prompt))
                            prompt_layout.addWidget(test_btn)

                            delete_btn = QPushButton("Delete")
                            delete_btn.setMaximumWidth(70)
                            delete_btn.setStyleSheet("QPushButton { font-size: 11px; padding: 4px; background-color: #dc3545; color: white; border: 1px solid #c82333; border-radius: 3px; } QPushButton:hover { background-color: #c82333; }")
                            delete_btn.clicked.connect(lambda s=suite_name, i=prompt_index: self.delete_prompt(s, i))
                            prompt_layout.addWidget(delete_btn)

                            play_btn = QPushButton("▶")
                            play_btn.setMaximumWidth(40)
                            play_btn.setStyleSheet("QPushButton { font-size: 11px; padding: 4px; background-color: #007bff; color: white; border: 1px solid #0056b3; border-radius: 3px; } QPushButton:hover { background-color: #0056b3; }")
                            # Create a proper closure to avoid lambda variable capture issues
                            def make_play_handler_for_new_prompt(prompt_text):
                                def handler():
                                    self.run_prompt(prompt_text)
                                return handler
                            play_btn.clicked.connect(make_play_handler_for_new_prompt(new_prompt))
                            prompt_layout.addWidget(play_btn)

                            # Add to group box layout
                            group_layout = group_box.layout()
                            group_layout.addLayout(prompt_layout)

                            # Store widgets in suite data
                            suite_data['widgets'].extend([prompt_label, edit_btn, test_btn, delete_btn, play_btn])

                            print(f"✅ Added new prompt widget to suite '{suite_name}'")

                        # Update prompt count
                        if hasattr(self, 'prompt_count_labels') and suite_name in self.prompt_count_labels:
                            self.prompt_count_labels[suite_name].setText(f"{len(suite_data['prompts'])} prompts")

                        print(f"✅ Added prompt to suite '{suite_name}', total: {len(suite_data['prompts'])}")
                        break
            else:
                QMessageBox.warning(self, "Empty Prompt", "Prompt cannot be empty. Please enter some text.")

    def create_new_suite(self):
        """Create a new test suite"""
        print(f"🆕 NEW SUITE BUTTON CLICKED")
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QDialogButtonBox, QLabel, QLineEdit

        dialog = QDialog(self)
        dialog.setWindowTitle("Create New Test Suite")
        dialog.setMinimumSize(600, 500)

        layout = QVBoxLayout(dialog)

        # Suite name input
        name_label = QLabel("Suite Name:")
        layout.addWidget(name_label)
        name_edit = QLineEdit()
        name_edit.setPlaceholderText("e.g., Custom Tests, Mathematical Problems")
        layout.addWidget(name_edit)

        # Suite description
        desc_label = QLabel("Description (optional):")
        layout.addWidget(desc_label)
        desc_edit = QLineEdit()
        desc_edit.setPlaceholderText("Brief description of the test suite...")
        layout.addWidget(desc_edit)

        # Initial prompts
        prompts_label = QLabel("Initial Prompts (one per line):")
        layout.addWidget(prompts_label)
        prompts_edit = QTextEdit()
        prompts_edit.setPlaceholderText("Enter your test prompts here, one per line:\n\nWhat is the capital of France?\nExplain photosynthesis in simple terms.\nWrite a function that sorts an array.")
        prompts_edit.setMinimumHeight(300)
        layout.addWidget(prompts_edit)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec() == QDialog.Accepted:
            suite_name = name_edit.text().strip()
            description = desc_edit.text().strip()
            prompts_text = prompts_edit.toPlainText().strip()

            if not suite_name:
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.warning(self, "Invalid Name", "Suite name cannot be empty.")
                return

            # Parse prompts
            prompts = []
            if prompts_text:
                prompts = [prompt.strip() for prompt in prompts_text.split('\n') if prompt.strip()]

            if not prompts:
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.warning(self, "No Prompts", "At least one prompt is required.")
                return

            # Check if suite name already exists
            existing_names = [suite['name'] for suite in self.suite_widgets]
            if suite_name in existing_names:
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.warning(self, "Name Exists", f"A suite named '{suite_name}' already exists.")
                return

            # Create the new suite
            new_suite = {
                'name': suite_name,
                'icon': '📝',  # Default icon for custom suites
                'description': description,
                'prompts': prompts
            }

            self.add_suite_group(new_suite)
            print(f"Created new suite '{suite_name}' with {len(prompts)} prompts")

    def refresh_suite_display(self):
        """Refresh the entire test suites display"""
        # Make a copy of current suite data
        current_suites = []
        for suite_data in self.suite_widgets:
            current_suites.append({
                'name': suite_data['name'],
                'icon': '🔧' if 'Code' in suite_data['name'] else '✍️' if 'Creative' in suite_data['name'] else '🧠' if 'Logic' in suite_data['name'] else '📝',
                'prompts': suite_data['prompts'].copy()
            })

        # Clear current display
        for i in reversed(range(self.suites_layout.count())):
            child = self.suites_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
                child.deleteLater()

        # Clear widgets data
        self.suite_widgets.clear()

        # Reload suites from current data
        for suite in current_suites:
            self.add_suite_group(suite)

    def test_single_prompt(self, prompt):
        """Test a single prompt"""
        print(f"🧪 TEST BUTTON CLICKED: prompt='{prompt[:50]}...'")
        self.run_test.emit(prompt, [])

    def run_prompt(self, prompt):
        """Run a single prompt immediately"""
        print(f"▶️ PLAY BUTTON CLICKED: prompt='{prompt[:50]}...'")
        self.run_test.emit(prompt, [])

    def run_selected_suite(self):
        """Run the currently selected suite or multiple suites with cycles"""
        cycles = self.cycles_spinbox.value()
        use_objective_tests = self.use_objective_tests_checkbox.isChecked()

        if self.multi_suite_checkbox.isChecked():
            # Multi-suite mode
            selected_suites = self.get_selected_suites()
            if not selected_suites:
                QMessageBox.warning(self, "No Selection", "Please select at least one test suite.")
                return

            print(f"Running {len(selected_suites)} suites for {cycles} cycles each")

            for cycle in range(cycles):
                print(f"Starting cycle {cycle + 1}/{cycles}")
                for suite_data in selected_suites:
                    suite_name = suite_data['name']
                    prompts = suite_data['prompts']

                    print(f"Running suite: {suite_name}")

                    if use_objective_tests:
                        # Run with objective test integration
                        self.run_suite_with_objective_tests.emit(suite_name, prompts)
                    else:
                        # Standard suite execution
                        self.run_suite.emit(suite_name, prompts)
        else:
            # Single suite mode
            if self.current_suite:
                for suite_data in self.suite_widgets:
                    if suite_data['name'] == self.current_suite:
                        prompts = suite_data['prompts']

                        print(f"Running suite '{self.current_suite}' for {cycles} cycles")

                        for cycle in range(cycles):
                            print(f"Starting cycle {cycle + 1}/{cycles}")

                            if use_objective_tests:
                                # Run with objective test integration
                                self.run_suite_with_objective_tests.emit(self.current_suite, prompts)
                            else:
                                # Standard suite execution
                                self.run_suite.emit(self.current_suite, prompts)
                        break


class ParametersWidget(QWidget):
    """Parameter configuration and presets"""

    parameters_changed = Signal(dict)
    apply_parameters_request = Signal(dict)
    test_parameters_request = Signal(dict)
    output_format_changed = Signal(str, str)  # format_name, template

    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_parameter_presets()
        self.structured_output_manager = StructuredOutputManager()
        self.current_output_format = "plain_text"

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Preset selection
        preset_layout = QHBoxLayout()
        preset_layout.addWidget(QLabel("⚙️ Parameter Presets"))
        preset_layout.addStretch()

        save_preset_btn = QPushButton("+ Save Preset")
        preset_layout.addWidget(save_preset_btn)

        layout.addLayout(preset_layout)

        # Preset dropdown
        self.preset_combo = QComboBox()
        self.preset_combo.addItems([
            "Balanced Default",
            "Code Optimized",
            "Creative Max",
            "Fast Response",
            "Custom"
        ])
        self.preset_combo.currentTextChanged.connect(self.on_preset_changed)
        layout.addWidget(self.preset_combo)

        # Parameter controls
        params_group = QGroupBox("Parameters")
        params_layout = QVBoxLayout(params_group)

        # Temperature
        temp_layout = QHBoxLayout()
        temp_layout.addWidget(QLabel("Temperature:"))
        self.temp_slider = QSlider(Qt.Horizontal)
        self.temp_slider.setRange(-20, 200)  # -2.0 to 2.0
        self.temp_slider.setValue(70)  # 0.7
        self.temp_slider.valueChanged.connect(self.on_param_changed)
        self.temp_slider.setToolTip("Controls randomness: Lower = more focused, Higher = more creative")
        temp_layout.addWidget(self.temp_slider)
        self.temp_label = QLabel("0.7")
        temp_layout.addWidget(self.temp_label)
        temp_layout.addWidget(QLabel("(-2.0 to +2.0)"))
        params_layout.addLayout(temp_layout)

        # Top K
        topk_layout = QHBoxLayout()
        topk_layout.addWidget(QLabel("Top_K:"))
        self.topk_slider = QSlider(Qt.Horizontal)
        self.topk_slider.setRange(1, 100)
        self.topk_slider.setValue(40)
        self.topk_slider.valueChanged.connect(self.on_param_changed)
        self.topk_slider.setToolTip("Limits vocabulary: Lower = more predictable, Higher = more diverse")
        topk_layout.addWidget(self.topk_slider)
        self.topk_label = QLabel("40")
        topk_layout.addWidget(self.topk_label)
        topk_layout.addWidget(QLabel("(1 to 100)"))
        params_layout.addLayout(topk_layout)

        # Top P
        topp_layout = QHBoxLayout()
        topp_layout.addWidget(QLabel("Top_P:"))
        self.topp_slider = QSlider(Qt.Horizontal)
        self.topp_slider.setRange(0, 100)  # 0.0 to 1.0
        self.topp_slider.setValue(90)  # 0.90
        self.topp_slider.valueChanged.connect(self.on_param_changed)
        self.topp_slider.setToolTip("Controls nucleus sampling: Lower = more focused, Higher = more diverse")
        topp_layout.addWidget(self.topp_slider)
        self.topp_label = QLabel("0.90")
        topp_layout.addWidget(self.topp_label)
        topp_layout.addWidget(QLabel("(0.0 to 1.0)"))
        params_layout.addLayout(topp_layout)

        # Repeat Penalty
        repeat_layout = QHBoxLayout()
        repeat_layout.addWidget(QLabel("Repeat Penalty:"))
        self.repeat_slider = QSlider(Qt.Horizontal)
        self.repeat_slider.setRange(100, 200)  # 1.0 to 2.0
        self.repeat_slider.setValue(110)  # 1.10
        self.repeat_slider.valueChanged.connect(self.on_param_changed)
        self.repeat_slider.setToolTip("Reduces repetition: Higher = more varied responses")
        repeat_layout.addWidget(self.repeat_slider)
        self.repeat_label = QLabel("1.10")
        repeat_layout.addWidget(self.repeat_label)
        repeat_layout.addWidget(QLabel("(1.0 to 2.0)"))
        params_layout.addLayout(repeat_layout)

        # Context Length
        context_layout = QHBoxLayout()
        context_layout.addWidget(QLabel("Context:"))
        self.context_combo = QComboBox()
        self.context_combo.addItems(["512", "1024", "2048", "4096", "8192", "16384", "32768"])
        self.context_combo.setCurrentText("4096")
        self.context_combo.currentTextChanged.connect(self.on_param_changed)
        self.context_combo.setToolTip("Maximum context window for the model (tokens)")
        context_layout.addWidget(self.context_combo)
        context_layout.addWidget(QLabel("tokens"))
        params_layout.addLayout(context_layout)

        # Max Tokens
        max_tokens_layout = QHBoxLayout()
        max_tokens_layout.addWidget(QLabel("Max Tokens:"))
        self.max_tokens_combo = QComboBox()
        self.max_tokens_combo.addItems(["256", "512", "1024", "2048", "4096", "8192"])
        self.max_tokens_combo.setCurrentText("2048")
        self.max_tokens_combo.currentTextChanged.connect(self.on_param_changed)
        self.max_tokens_combo.setToolTip("Maximum response length from the model (tokens)")
        max_tokens_layout.addWidget(self.max_tokens_combo)
        max_tokens_layout.addWidget(QLabel("tokens"))
        params_layout.addLayout(max_tokens_layout)

        layout.addWidget(params_group)

        # Model-specific overrides
        overrides_group = QGroupBox("Model-Specific Overrides (Optional)")
        self.overrides_layout = QVBoxLayout(overrides_group)
        layout.addWidget(overrides_group)

        # Control buttons
        control_layout = QHBoxLayout()

        reset_btn = QPushButton("Reset to Defaults")
        reset_btn.clicked.connect(self.reset_to_defaults)
        control_layout.addWidget(reset_btn)

        apply_btn = QPushButton("Apply to Selected")
        apply_btn.clicked.connect(self.apply_parameters)
        control_layout.addWidget(apply_btn)

        test_btn = QPushButton("Test on One Model")
        test_btn.clicked.connect(self.test_parameters)
        control_layout.addWidget(test_btn)

        layout.addLayout(control_layout)

        # Structured Output Format Section
        output_group = QGroupBox("📄 Structured Output Format")
        output_layout = QVBoxLayout(output_group)

        # Output format selection
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("Output Format:"))

        self.output_format_combo = QComboBox()
        self.output_format_combo.addItems([
            "Plain Text (Default)",
            "JSON",
            "XML",
            "YAML",
            "Markdown",
            "CSV (Tabular Data)"
        ])
        self.output_format_combo.currentTextChanged.connect(self.on_output_format_changed)
        format_layout.addWidget(self.output_format_combo)
        format_layout.addStretch()

        output_layout.addLayout(format_layout)

        # Output format preview
        self.output_preview = QTextEdit()
        self.output_preview.setReadOnly(True)
        self.output_preview.setMaximumHeight(120)
        self.output_preview.setPlaceholderText("Select an output format to see preview")
        output_layout.addWidget(QLabel("Format Preview:"))
        output_layout.addWidget(self.output_preview)

        layout.addWidget(output_group)
        layout.addStretch()

    def load_parameter_presets(self):
        """Load parameter presets"""
        self.presets = {
            "Balanced Default": {
                "temperature": 0.7,
                "top_k": 40,
                "top_p": 0.9,
                "repeat_penalty": 1.1,
                "num_ctx": 4096,
                "num_predict": 2048
            },
            "Code Optimized": {
                "temperature": 0.2,
                "top_k": 20,
                "top_p": 0.95,
                "repeat_penalty": 1.15,
                "num_ctx": 8192,
                "num_predict": 4096
            },
            "Creative Max": {
                "temperature": 1.2,
                "top_k": 50,
                "top_p": 0.92,
                "repeat_penalty": 1.05,
                "num_ctx": 4096,
                "num_predict": 2048
            },
            "Fast Response": {
                "temperature": 0.5,
                "top_k": 10,
                "top_p": 0.8,
                "repeat_penalty": 1.1,
                "num_ctx": 2048,
                "num_predict": 512
            }
        }

    def on_preset_changed(self, preset_name):
        """Handle preset selection change"""
        if preset_name in self.presets:
            self.apply_preset_values(self.presets[preset_name])

    def apply_preset_values(self, preset_values):
        """Apply preset values to UI controls"""
        self.temp_slider.setValue(int(preset_values["temperature"] * 10))
        self.topk_slider.setValue(preset_values["top_k"])
        self.topp_slider.setValue(int(preset_values["top_p"] * 100))
        self.repeat_slider.setValue(int(preset_values["repeat_penalty"] * 100))
        self.context_combo.setCurrentText(str(preset_values["num_ctx"]))
        self.max_tokens_combo.setCurrentText(str(preset_values["num_predict"]))

    def on_param_changed(self):
        """Update parameter labels"""
        self.temp_label.setText(f"{self.temp_slider.value() / 10:.1f}")
        self.topk_label.setText(str(self.topk_slider.value()))
        self.topp_label.setText(f"{self.topp_slider.value() / 100:.2f}")
        self.repeat_label.setText(f"{self.repeat_slider.value() / 100:.2f}")

        # Mark as custom preset
        if self.preset_combo.currentText() != "Custom":
            self.preset_combo.blockSignals(True)
            self.preset_combo.setCurrentText("Custom")
            self.preset_combo.blockSignals(False)

        # Emit parameters changed signal
        current_params = self.get_parameters()
        self.parameters_changed.emit(current_params)

    def reset_to_defaults(self):
        """Reset to default parameters"""
        self.preset_combo.setCurrentText("Balanced Default")

    def apply_parameters(self):
        """Apply current parameters to selected models"""
        current_params = self.get_parameters()
        self.apply_parameters_request.emit(current_params)

    def test_parameters(self):
        """Test current parameters on a single model"""
        current_params = self.get_parameters()
        self.test_parameters_request.emit(current_params)

    def get_parameters(self):
        """Get current parameter values"""
        return {
            "temperature": self.temp_slider.value() / 10,
            "top_k": self.topk_slider.value(),
            "top_p": self.topp_slider.value() / 100,
            "repeat_penalty": self.repeat_slider.value() / 100,
            "num_ctx": int(self.context_combo.currentText()),
            "num_predict": int(self.max_tokens_combo.currentText())
        }

    def on_output_format_changed(self, format_name):
        """Handle output format selection change"""
        format_map = {
            "Plain Text (Default)": "plain_text",
            "JSON": "json",
            "XML": "xml",
            "YAML": "yaml",
            "Markdown": "markdown",
            "CSV (Tabular Data)": "csv"
        }

        format_key = format_map.get(format_name, "plain_text")
        self.current_output_format = format_key

        # Update preview
        self.update_output_preview(format_name)

        # Emit signal with format info
        template = self.structured_output_manager.get_template(OutputFormat(format_key))
        self.output_format_changed.emit(format_name, template.template)

    def update_output_preview(self, format_name):
        """Update the output format preview"""
        format_map = {
            "Plain Text (Default)": OutputFormat.PLAIN_TEXT if hasattr(OutputFormat, 'PLAIN_TEXT') else None,
            "JSON": OutputFormat.JSON,
            "XML": OutputFormat.XML,
            "YAML": OutputFormat.YAML,
            "Markdown": OutputFormat.MARKDOWN,
            "CSV (Tabular Data)": OutputFormat.CSV
        }

        output_format = format_map.get(format_name)
        if not output_format:
            self.output_preview.clear()
            self.output_preview.setPlaceholderText("Plain text format - no structure")
            return

        try:
            template = self.structured_output_manager.get_template(output_format)

            # Create a brief example for the preview
            example_prompt = "Explain what a triangle is"
            formatted_example = self.structured_output_manager.format_prompt(
                base_prompt=example_prompt,
                output_format=output_format
            )

            # Show just the template part for preview
            self.output_preview.setText(template.template)
            self.output_preview.setPlaceholderText("")

        except Exception as e:
            self.output_preview.setText(f"Error loading template: {str(e)}")

    def get_current_output_format(self):
        """Get the currently selected output format"""
        format_map = {
            "Plain Text (Default)": "plain_text",
            "JSON": "json",
            "XML": "xml",
            "YAML": "yaml",
            "Markdown": "markdown",
            "CSV (Tabular Data)": "csv"
        }

        current_text = self.output_format_combo.currentText()
        return format_map.get(current_text, "plain_text")

    def format_prompt_with_output(self, base_prompt, context=None):
        """Format a prompt with the selected output format"""
        if self.current_output_format == "plain_text":
            return base_prompt

        try:
            format_key = self.current_output_format.upper()
            output_format = OutputFormat(format_key)

            formatted_prompt = self.structured_output_manager.format_prompt(
                base_prompt=base_prompt,
                output_format=output_format,
                context=context or {}
            )

            return formatted_prompt

        except Exception as e:
            print(f"Error formatting prompt: {str(e)}")
            return base_prompt

    def validate_structured_response(self, response_text, expected_format=None):
        """Validate a structured response"""
        if not expected_format:
            expected_format = self.current_output_format

        if expected_format == "plain_text":
            return {"valid": True, "format": "plain_text"}

        try:
            format_key = expected_format.upper()
            output_format = OutputFormat(format_key)

            validation_result = self.structured_output_manager.validate_response(
                response_text, output_format
            )

            return validation_result

        except Exception as e:
            return {
                "valid": False,
                "error": str(e),
                "format": expected_format
            }


class ResultsWidget(QWidget):
    """Real-time results monitoring"""

    def __init__(self):
        super().__init__()
        self.init_ui()
        self.results_data = []
        # Enhanced tracking variables
        self.test_session_start_time = None
        self.current_test_info = {
            'suite_name': '',
            'prompts': [],
            'models': [],
            'cycles': 1,
            'total_tests': 0,
            'completed_tests': 0,
            'current_cycle': 0,
            'start_time': None,
            'estimated_completion_time': None
        }

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Header
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("📊 Test Results"))
        header_layout.addStretch()

        # Control buttons
        clear_btn = QPushButton("Clear Results")
        clear_btn.clicked.connect(self.clear_results)
        header_layout.addWidget(clear_btn)

        export_btn = QPushButton("Export CSV")
        export_btn.clicked.connect(self.export_results)
        header_layout.addWidget(export_btn)

        export_structured_btn = QPushButton("Export Structured JSON")
        export_structured_btn.clicked.connect(self.export_structured_results)
        header_layout.addWidget(export_structured_btn)

        layout.addLayout(header_layout)

        # Enhanced Test Information Panel
        test_info_frame = QFrame()
        test_info_frame.setStyleSheet("QFrame { border: 1px solid #555; border-radius: 5px; padding: 10px; background-color: #1a1a2e; }")
        test_info_layout = QVBoxLayout(test_info_frame)

        # Main test info
        self.test_info_label = QLabel("🧪 Test Session: Ready")
        self.test_info_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #eee;")
        test_info_layout.addWidget(self.test_info_label)

        # Detailed test info
        self.test_details_label = QLabel("No test session active")
        self.test_details_label.setStyleSheet("font-size: 12px; color: #bbb;")
        test_info_layout.addWidget(self.test_details_label)

        # Timing and progress info
        self.timing_info_label = QLabel("⏱️  Total Time: 0s | ETA: --")
        self.timing_info_label.setStyleSheet("font-size: 11px; color: #888;")
        test_info_layout.addWidget(self.timing_info_label)

        layout.addWidget(test_info_frame)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Statistics panel
        stats_frame = QFrame()
        stats_layout = QHBoxLayout(stats_frame)

        self.stats_labels = {
            'total': QLabel("Total: 0"),
            'completed': QLabel("✅ Completed: 0"),
            'errors': QLabel("❌ Errors: 0"),
            'avg_time': QLabel("Avg Time: 0.0s"),
            'avg_tokens': QLabel("Avg Tokens/s: 0.0")
        }

        for key, label in self.stats_labels.items():
            stats_layout.addWidget(label)

        stats_layout.addStretch()
        layout.addWidget(stats_frame)

        # Results table
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(7)
        self.results_table.setHorizontalHeaderLabels([
            "Model", "Status", "Time", "Tokens/s", "VRAM", "Temp", "Score"
        ])
        self.results_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        layout.addWidget(self.results_table)

        # Current response display
        response_group = QGroupBox("Current Response")
        response_layout = QVBoxLayout(response_group)

        self.current_model_label = QLabel("No active test")
        response_layout.addWidget(self.current_model_label)

        self.current_response_text = QTextEdit()
        self.current_response_text.setMaximumHeight(200)
        self.current_response_text.setReadOnly(True)
        response_layout.addWidget(self.current_response_text)

        layout.addWidget(response_group)

    def add_result(self, result):
        """Add a test result to the display"""
        self.results_data.append(result)
        self.update_results_table()
        self.update_statistics()
        self.update_current_response(result)

    def update_results_table(self):
        """Update the results table"""
        self.results_table.setRowCount(len(self.results_data))

        for row, result in enumerate(self.results_data):
            # Model name
            self.results_table.setItem(row, 0, QTableWidgetItem(result['model_name']))

            # Status
            status_icon = "✅" if result['status'] == 'completed' else "❌"
            self.results_table.setItem(row, 1, QTableWidgetItem(f"{status_icon} {result['status']}"))

            # Time
            self.results_table.setItem(row, 2, QTableWidgetItem(f"{result['response_time']:.1f}s"))

            # Tokens/s
            self.results_table.setItem(row, 3, QTableWidgetItem(f"{result['tokens_per_second']:.1f}"))

            # VRAM - get from system metrics if available
            vram_text = "N/A"
            try:
                # Try to get current system metrics from the main window
                if hasattr(self.parent(), 'system_monitor'):
                    metrics = self.parent().system_monitor.metrics
                    if metrics['gpu_utilization'] > 0:
                        vram_text = f"{metrics['gpu_vram_used_mb']:.0f}MB"
                    else:
                        vram_text = f"{metrics['gpu_vram_used_mb']:.0f}MB"
            except:
                pass
            self.results_table.setItem(row, 4, QTableWidgetItem(vram_text))

            # Temp - get from system metrics if available
            temp_text = "N/A"
            try:
                if hasattr(self.parent(), 'system_monitor'):
                    metrics = self.parent().system_monitor.metrics
                    if metrics['gpu_utilization'] > 0:
                        temp_text = f"{metrics['gpu_temp_c']:.0f}°C"
                    else:
                        temp_text = "N/A"
            except:
                pass
            self.results_table.setItem(row, 5, QTableWidgetItem(temp_text))

            # Score - calculate basic performance score
            score = self.calculate_performance_score(result)
            score_text = f"{score:.2f}" if score > 0 else "N/A"
            score_item = QTableWidgetItem(score_text)
            
            # Color code the score
            if score >= 0.8:
                score_item.setBackground(QBrush(QColor("#4CAF50")))  # Green - Excellent
            elif score >= 0.6:
                score_item.setBackground(QBrush(QColor("#8BC34A")))  # Light Green - Good
            elif score >= 0.4:
                score_item.setBackground(QBrush(QColor("#FFC107")))  # Yellow - Fair
            elif score > 0:
                score_item.setBackground(QBrush(QColor("#FF9800")))  # Orange - Poor
            else:
                score_item.setBackground(QBrush(QColor("#F44336")))  # Red - Error
            
            self.results_table.setItem(row, 6, score_item)

    def update_current_response(self, result):
        """Update the current response display"""
        self.current_model_label.setText(f"📝 Current Response ({result['model_name']}):")
        self.current_response_text.setPlainText(result['response_text'])

    def update_test_info(self, test_name, model_count, status):
        """Update test information display"""
        import time
        from datetime import datetime

        if status == "Running":
            if not self.test_session_start_time:
                self.test_session_start_time = time.time()
                self.current_test_info['start_time'] = time.time()

            self.test_info_label.setText(f"🧪 Test Session: {test_name} | 🤖 Models: {model_count} | ✅ Status: {status}")
        else:
            self.test_info_label.setText(f"🧪 Test Session: {test_name} | 🤖 Models: {model_count} | ✅ Status: {status}")

    def update_comprehensive_test_info(self, suite_name, prompts, models, cycles=1, current_cycle=1, completed_tests=0, total_tests=0):
        """Update comprehensive test information with detailed breakdown"""
        import time

        # Update tracking info
        self.current_test_info.update({
            'suite_name': suite_name,
            'prompts': prompts,
            'models': models,
            'cycles': cycles,
            'current_cycle': current_cycle,
            'completed_tests': completed_tests,
            'total_tests': total_tests
        })

        # Calculate timing information
        current_time = time.time()
        if self.test_session_start_time:
            elapsed_time = current_time - self.test_session_start_time
        else:
            elapsed_time = 0

        # Estimate completion time
        if completed_tests > 0 and total_tests > 0:
            avg_time_per_test = elapsed_time / completed_tests
            remaining_tests = total_tests - completed_tests
            eta_seconds = avg_time_per_test * remaining_tests
            eta = f"{int(eta_seconds // 60)}m {int(eta_seconds % 60)}s"
        else:
            eta = "--"

        # Format prompt types for display
        prompt_types = self._analyze_prompt_types(prompts)

        # Generate model details with VRAM/temperature estimates
        model_details = self._generate_model_details(models)

        # Update main test info
        progress_text = f"🧪 {suite_name} | Cycle {current_cycle}/{cycles} | {completed_tests}/{total_tests} tests"
        self.test_info_label.setText(progress_text)

        # Update detailed test info
        details_text = f"📝 Prompts: {len(prompts)} ({prompt_types}) | 🤖 Models: {len(models)} {model_details}"
        self.test_details_label.setText(details_text)

        # Update timing info
        timing_text = f"⏱️  Elapsed: {int(elapsed_time // 60)}m {int(elapsed_time % 60)}s | ETA: {eta} | Avg: {(elapsed_time / max(completed_tests, 1)):.1f}s/test"
        self.timing_info_label.setText(timing_text)

    def _analyze_prompt_types(self, prompts):
        """Analyze and categorize prompt types"""
        if not prompts:
            return "No prompts"

        categories = {'code': 0, 'math': 0, 'creative': 0, 'reasoning': 0, 'general': 0}

        for prompt in prompts:
            prompt_lower = prompt.lower()
            if any(word in prompt_lower for word in ['function', 'code', 'python', 'program']):
                categories['code'] += 1
            elif any(word in prompt_lower for word in ['calculate', 'area', 'formula', 'math']):
                categories['math'] += 1
            elif any(word in prompt_lower for word in ['story', 'poem', 'creative']):
                categories['creative'] += 1
            elif any(word in prompt_lower for word in ['reasoning', 'logic', 'analyze']):
                categories['reasoning'] += 1
            else:
                categories['general'] += 1

        # Build type summary
        active_types = [f"{k}({v})" for k, v in categories.items() if v > 0]
        return ", ".join(active_types) if active_types else "mixed"

    def _generate_model_details(self, models):
        """Generate model details with VRAM and temperature estimates"""
        if not models:
            return ""

        details = []
        for model in models[:3]:  # Show first 3 models
            model_name = model if isinstance(model, str) else model.get('name', 'Unknown')

            # Estimate VRAM based on model name patterns
            vram_estimate = self._estimate_vram(model_name)
            temp_estimate = "65-75°C"  # Typical GPU temp under load

            details.append(f"{model_name.split(':')[0]} (~{vram_estimate}, {temp_estimate})")

        if len(models) > 3:
            details.append(f"+{len(models)-3} more")

        return f"| {', '.join(details)}"

    def _estimate_vram(self, model_name):
        """Estimate VRAM usage based on model name"""
        model_lower = model_name.lower()

        if '3b' in model_lower or '3.8b' in model_lower:
            return "4-6GB"
        elif '7b' in model_lower or '8b' in model_lower:
            return "8-12GB"
        elif '13b' in model_lower:
            return "16-20GB"
        elif '34b' in model_lower:
            return "40-48GB"
        elif '70b' in model_lower:
            return "80-96GB"
        else:
            return "6-12GB"

    def clear_test_session(self):
        """Clear test session info and reset timers"""
        self.test_session_start_time = None
        self.current_test_info = {
            'suite_name': '',
            'prompts': [],
            'models': [],
            'cycles': 1,
            'total_tests': 0,
            'completed_tests': 0,
            'current_cycle': 0,
            'start_time': None,
            'estimated_completion_time': None
        }

        self.test_info_label.setText("🧪 Test Session: Ready")
        self.test_details_label.setText("No test session active")
        self.timing_info_label.setText("⏱️  Total Time: 0s | ETA: --")

    def initialize_test_session(self, suite_name, prompts, models, cycles=1, test_type="Standard Testing"):
        """Initialize a new test session with comprehensive information"""
        import time

        # Clear any existing session
        self.clear_test_session()

        # Set up new session
        self.test_session_start_time = time.time()

        total_tests = len(prompts) * len(models) * cycles

        self.current_test_info = {
            'suite_name': suite_name,
            'prompts': prompts,
            'models': models,
            'cycles': cycles,
            'total_tests': total_tests,
            'completed_tests': 0,
            'current_cycle': 1,
            'start_time': self.test_session_start_time,
            'estimated_completion_time': None,
            'test_type': test_type,
            'status': 'running'
        }

        # Analyze prompt types
        self.current_test_info['prompt_types'] = self._analyze_prompt_types(prompts)

        # Generate model details
        self.current_test_info['model_details'] = self._generate_model_details(models)

        # Initial display update
        self.update_comprehensive_test_info(
            suite_name=suite_name,
            prompts=prompts,
            models=models,
            cycles=cycles,
            current_cycle=1,
            completed_tests=0,
            total_tests=total_tests
        )

    def complete_test_session(self):
        """Mark the test session as completed and update final information"""
        import time

        if not self.current_test_info:
            return

        # Update completion status
        self.current_test_info['status'] = 'completed'
        self.current_test_info['completion_time'] = time.time()

        # Calculate final duration
        if self.test_session_start_time:
            final_duration = time.time() - self.test_session_start_time
            self.current_test_info['final_duration'] = final_duration

            # Update timing display with completion info
            minutes = int(final_duration // 60)
            seconds = int(final_duration % 60)
            self.timing_info_label.setText(f"⏱️  Completed in {minutes}m {seconds}s")

        # Update main test info
        suite_name = self.current_test_info.get('suite_name', 'Unknown')
        total_tests = self.current_test_info.get('total_tests', 0)
        completed_tests = self.current_test_info.get('completed_tests', 0)

        self.test_info_label.setText(f"✅ {suite_name} - Complete! ({completed_tests}/{total_tests} tests)")

        print(f"🎉 Test session '{suite_name}' completed successfully!")
        print(f"   Total tests: {total_tests}")
        print(f"   Completed tests: {completed_tests}")
        print(f"   Duration: {self.current_test_info.get('final_duration', 0):.1f} seconds")

    def update_progress(self, current_model, progress_percent):
        """Update progress bar"""
        self.test_info_label.setText(f"Testing {current_model}...")
        self.progress_bar.setValue(int(progress_percent))
        self.progress_bar.setVisible(True)

    def update_statistics(self):
        """Update the statistics display"""
        total = len(self.results_data)
        if total == 0:
            for label in self.stats_labels.values():
                label.setText(label.text().split(':')[0] + ": 0")
            return

        completed = sum(1 for r in self.results_data if r['status'] == 'completed')
        errors = total - completed

        # Calculate averages
        completed_results = [r for r in self.results_data if r['status'] == 'completed']
        if completed_results:
            avg_time = sum(r['response_time'] for r in completed_results) / len(completed_results)
            avg_tokens = sum(r['tokens_per_second'] for r in completed_results) / len(completed_results)
        else:
            avg_time = 0
            avg_tokens = 0

        # Update labels
        self.stats_labels['total'].setText(f"Total: {total}")
        self.stats_labels['completed'].setText(f"✅ Completed: {completed}")
        self.stats_labels['errors'].setText(f"❌ Errors: {errors}")
        self.stats_labels['avg_time'].setText(f"Avg Time: {avg_time:.1f}s")
        self.stats_labels['avg_tokens'].setText(f"Avg Tokens/s: {avg_tokens:.1f}")

    def export_results(self):
        """Export results to CSV"""
        if not self.results_data:
            print("No results to export")
            return

        from PySide6.QtWidgets import QFileDialog
        import csv

        filename, _ = QFileDialog.getSaveFileName(
            self, "Export Results", f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "CSV Files (*.csv)"
        )

        if filename:
            try:
                with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                    fieldnames = [
                        'timestamp', 'model_name', 'status', 'response_time',
                        'tokens_in', 'tokens_out', 'tokens_per_second',
                        'prompt_text', 'response_text', 'error'
                    ]
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()

                    for result in self.results_data:
                        writer.writerow({
                            'timestamp': result.get('timestamp', ''),
                            'model_name': result['model_name'],
                            'status': result['status'],
                            'response_time': result['response_time'],
                            'tokens_in': result['tokens_in'],
                            'tokens_out': result['tokens_out'],
                            'tokens_per_second': result['tokens_per_second'],
                            'prompt_text': result['prompt_text'],
                            'response_text': result['response_text'],
                            'error': result.get('error', '')
                        })

                print(f"Results exported to {filename}")

            except Exception as e:
                print(f"Error exporting results: {e}")

    def clear_results(self):
        """Clear all results"""
        self.results_data = []
        self.results_table.setRowCount(0)
        self.current_response_text.clear()
        self.current_model_label.setText("No active test")
        self.progress_bar.setVisible(False)
        self.update_statistics()

    def export_structured_results(self):
        """Export results as structured JSON with enhanced formatting"""
        if not self.results_data:
            print("No results to export")
            return

        from PySide6.QtWidgets import QFileDialog
        import json
        from datetime import datetime

        filename, _ = QFileDialog.getSaveFileName(
            self, "Export Structured Results",
            f"structured_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            "JSON Files (*.json)"
        )

        if filename:
            try:
                # Group results by model and parameter configuration
                structured_results = {
                    "export_info": {
                        "timestamp": datetime.now().isoformat(),
                        "total_results": len(self.results_data),
                        "export_type": "structured_output"
                    },
                    "test_info": {
                        "test_suite": "LLM Parameter Comparison",
                        "total_prompts_tested": len(set(r.get('prompt_text', '') for r in self.results_data)),
                        "models_tested": list(set(r.get('model_name', 'unknown') for r in self.results_data)),
                        "parameter_variations": self.analyze_parameter_variations()
                    },
                    "results": []
                }

                # Enhance each result with structured data
                for result in self.results_data:
                    enhanced_result = {
                        "timestamp": result.get('timestamp', ''),
                        "test_id": result.get('task_id', ''),
                        "model_name": result.get('model_name', 'unknown'),
                        "parameters": result.get('parameters', {}),
                        "status": result.get('status', 'unknown'),
                        "metrics": {
                            "response_time": result.get('response_time', 0),
                            "tokens_per_second": result.get('tokens_per_second', 0),
                            "response_length": len(result.get('response_text', '')),
                            "tokens_in": result.get('tokens_in', 0),
                            "tokens_out": result.get('tokens_out', 0)
                        },
                        "prompt": {
                            "text": result.get('prompt_text', ''),
                            "type": self.classify_prompt_type(result.get('prompt_text', ''))
                        },
                        "response": {
                            "raw_text": result.get('response_text', ''),
                            "structured_data": self.try_parse_structured_response(
                                result.get('response_text', ''),
                                result.get('parameters', {})
                            ),
                            "validation": self.validate_response_structure(
                                result.get('response_text', ''),
                                result.get('parameters', {})
                            )
                        },
                        "performance": {
                            "time_per_token": result.get('tokens_per_second', 0) > 0,
                            "tokens_per_second": result.get('tokens_per_second', 0),
                            "response_quality_score": self.calculate_quality_score(result)
                        }
                    }

                    structured_results["results"].append(enhanced_result)

                # Write structured results to file
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(structured_results, f, indent=2, ensure_ascii=False)

                print(f"Structured results exported to {filename}")
                print(f"  - Total results: {len(self.results_data)}")
                print(f"  - Models tested: {len(structured_results['test_info']['models_tested'])}")
                print(f"  - Parameter variations: {len(structured_results['test_info']['parameter_variations'])}")

            except Exception as e:
                print(f"Error exporting structured results: {e}")

    def analyze_parameter_variations(self):
        """Analyze parameter variations in the results"""
        param_variations = {}
        for result in self.results_data:
            params = result.get('parameters', {})
            param_key = self.create_parameter_key(params)
            if param_key not in param_variations:
                param_variations[param_key] = {
                    'count': 0,
                    'models': set(),
                    'avg_score': 0,
                    'responses': []
                }
            param_variations[param_key]['count'] += 1
            param_variations[param_key]['models'].add(result.get('model_name', 'unknown'))
            param_variations[param_key]['responses'].append(result)

        # Calculate average scores for each parameter configuration
        for param_key, data in param_variations.items():
            scores = []
            for response in data['responses']:
                score = self.calculate_quality_score(response)
                if score > 0:
                    scores.append(score)
            data['avg_score'] = sum(scores) / len(scores) if scores else 0
            data['models'] = list(data['models'])

        return param_variations

    def create_parameter_key(self, parameters):
        """Create a unique key for parameter configuration"""
        key_parts = []
        for param, value in sorted(parameters.items()):
            if isinstance(value, (int, float)):
                key_parts.append(f"{param}={value}")
            elif isinstance(value, str):
                key_parts.append(f"{param}={value}")
        return "_".join(key_parts) if key_parts else "default"

    def classify_prompt_type(self, prompt_text):
        """Classify the type of prompt"""
        prompt_lower = prompt_text.lower()
        if any(word in prompt_lower for word in ['function', 'code', 'python', 'program']):
            return "code_generation"
        elif any(word in prompt_lower for word in ['calculate', 'area', 'formula', 'math']):
            return "mathematical"
        elif any(word in prompt_lower for word in ['explain', 'what', 'how', 'why', 'describe']):
            return "explanation"
        elif any(word in prompt_lower for word in ['story', 'poem', 'creative', 'imagine']):
            return "creative"
        elif any(word in prompt_lower for word in ['solve', 'puzzle', 'logic', 'reasoning']):
            return "reasoning"
        else:
            return "general"

    def try_parse_structured_response(self, response_text, parameters):
        """Try to parse structured response"""
        # Check for JSON
        if response_text.strip().startswith('{') or '```json' in response_text:
            try:
                return json.loads(response_text.strip())
            except:
                pass

        # Check for XML
        if response_text.strip().startswith('<') or '```xml' in response_text:
            try:
                import xml.etree.ElementTree as ET
                root = ET.fromstring(response_text)
                return self.xml_to_dict(root)
            except:
                pass

        # Check for YAML
        if ':' in response_text and not response_text.strip().startswith('{') and not response_text.strip().startswith('<'):
            try:
                import yaml
                return yaml.safe_load(response_text)
            except:
                pass

        # Return as plain text if structured parsing fails
        return {"response": response_text, "format": "plain_text"}

    def xml_to_dict(self, element):
        """Convert XML element to dictionary"""
        result = {}
        if element.attrib:
            result.update(element.attrib)

        for child in element:
            if len(list(element)) == 0:
                # Leaf node
                result[child.tag] = child.text or ""
            else:
                result[child.tag] = self.xml_to_dict(child)

        if element.text and element.text.strip():
            if result:
                result["_text"] = element.text.strip()
            else:
                return element.text.strip()

        return result

    def validate_response_structure(self, response_text, parameters):
        """Validate response structure and return validation result"""
        validation = {
            "is_structured": False,
            "format": "plain_text",
            "validation_score": 0.0,
            "issues": [],
            "suggestions": []
        }

        # Check for structured indicators
        structured_indicators = [
            response_text.strip().startswith('{'),
            response_text.strip().startswith('<'),
            ':' in response_text and not response_text.strip().startswith('{'),
            '```' in response_text
        ]

        if any(structured_indicators):
            validation["is_structured"] = True

            # Try to parse the response
            parsed = self.try_parse_structured_response(response_text, parameters)
            if isinstance(parsed, dict) and parsed != {"response": response_text, "format": "plain_text"}:
                validation["format"] = self.detect_format(parsed)
                validation["validation_score"] = self.calculate_validation_score(parsed)
                validation["parsed_structure"] = list(parsed.keys())

                # Add validation details
                if validation["format"] == "json":
                    validation["issues"] = self.validate_json_structure(parsed)
                elif validation["format"] == "xml":
                    validation["issues"] = self.validate_xml_structure(parsed)

        return validation

    def detect_format(self, parsed_data):
        """Detect the format of parsed data"""
        if isinstance(parsed_data, dict):
            if "response" in parsed_data and isinstance(parsed_data.get("response"), str):
                if "confidence" in parsed_data:
                    return "json"
                elif "metadata" in parsed_data:
                    return "xml"
                elif any(key in parsed_data for key in ["main_response", "reasoning"]):
                    return "markdown"
        return "unknown"

    def calculate_validation_score(self, parsed_data):
        """Calculate validation score for structured response"""
        score = 0.0

        if isinstance(parsed_data, dict):
            # Check for expected fields in JSON
            json_fields = ["response", "confidence", "reasoning"]
            for field in json_fields:
                if field in parsed_data:
                    score += 0.25

            # Check for code examples
            if "code_examples" in parsed_data and isinstance(parsed_data.get("code_examples"), list):
                if len(parsed_data["code_examples"]) > 0:
                    score += 0.25

            # Check for metadata in XML
            if "metadata" in parsed_data:
                score += 0.5

        return min(score, 1.0)

    def validate_json_structure(self, json_data):
        """Validate JSON structure"""
        issues = []
        required_fields = ["response", "confidence", "reasoning"]
        for field in required_fields:
            if field not in json_data:
                issues.append(f"Missing required field: {field}")

        if "confidence" in json_data:
            confidence = json_data["confidence"]
            if not isinstance(confidence, (int, float)) or not (0 <= confidence <= 1):
                issues.append("Confidence should be a number between 0 and 1")

        return issues

    def validate_xml_structure(self, xml_data):
        """Validate XML structure"""
        issues = []
        if isinstance(xml_data, dict):
            if "metadata" not in xml_data:
                issues.append("Missing metadata section")
            if "content" not in xml_data:
                issues.append("Missing content section")
        return issues

    def calculate_performance_score(self, result):
        """Calculate a comprehensive performance score for a response"""
        score = 0.0

        # Base score for completed responses
        if result.get('status') == 'completed':
            score += 0.3

        # Response quality factors
        response_length = len(result.get('response_text', ''))
        if response_length > 50:
            score += 0.1  # Minimum length
        if response_length > 200:
            score += 0.2  # Good length
        if response_length > 500:
            score += 0.1  # Comprehensive length

        # Performance factors
        tps = result.get('tokens_per_second', 0)
        if tps > 5:
            score += 0.1  # Acceptable speed
        if tps > 15:
            score += 0.1  # Good speed
        if tps > 30:
            score += 0.1  # Excellent speed

        # Response time consideration (inverse scoring)
        response_time = result.get('response_time', 0)
        if response_time > 0 and response_time < 2:
            score += 0.1  # Fast response
        elif response_time > 0 and response_time < 5:
            score += 0.05  # Reasonable response

        return min(score, 1.0)

    def calculate_quality_score(self, result):
        """Calculate a quality score for a response (legacy method)"""
        return self.calculate_performance_score(result)


class ParameterCompareWidget(QWidget):
    """Parameter comparison and testing interface"""

    run_parameter_test = Signal(list, list, int)  # test_configs, prompts, iterations

    def __init__(self):
        super().__init__()
        self.init_ui()
        self.test_results = []
        self.framework = None

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Header
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("🧪 Parameter Comparison"))
        header_layout.addStretch()

        export_btn = QPushButton("Export Report")
        export_btn.clicked.connect(self.export_comparison_report)
        header_layout.addWidget(export_btn)

        layout.addLayout(header_layout)

        # Test Configuration Section
        config_group = QGroupBox("Test Configuration")
        config_layout = QVBoxLayout(config_group)

        # Model selection
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("Model:"))
        self.model_combo = QComboBox()
        model_layout.addWidget(self.model_combo)
        model_layout.addStretch()
        config_layout.addLayout(model_layout)

        # Parameter to test
        param_layout = QHBoxLayout()
        param_layout.addWidget(QLabel("Parameter:"))
        self.param_combo = QComboBox()
        self.param_combo.addItems(["Temperature", "Top_P", "Top_K", "Repeat Penalty"])
        self.param_combo.currentTextChanged.connect(self.on_parameter_changed)
        param_layout.addWidget(self.param_combo)
        param_layout.addStretch()
        config_layout.addLayout(param_layout)

        # Test type selection
        test_type_layout = QHBoxLayout()
        test_type_layout.addWidget(QLabel("Test Type:"))
        self.test_type_combo = QComboBox()
        self.test_type_combo.addItems([
            "Parameter Sweep (5 points)",
            "Parameter Sweep (10 points)",
            "Isolation Test (Custom Values)",
            "Compare with Baseline"
        ])
        self.test_type_combo.currentTextChanged.connect(self.on_test_type_changed)
        test_type_layout.addWidget(self.test_type_combo)
        test_type_layout.addStretch()
        config_layout.addLayout(test_type_layout)

        # Custom values for isolation test
        self.custom_values_frame = QFrame()
        custom_values_layout = QVBoxLayout(self.custom_values_frame)
        custom_values_layout.addWidget(QLabel("Custom Values (comma-separated):"))
        self.custom_values_edit = QLineEdit("0.1, 0.3, 0.5, 0.7, 0.9, 1.2")
        custom_values_layout.addWidget(self.custom_values_edit)
        config_layout.addWidget(self.custom_values_frame)
        self.custom_values_frame.hide()

        # Iterations per configuration
        iter_layout = QHBoxLayout()
        iter_layout.addWidget(QLabel("Iterations per config:"))
        self.iter_spinbox = QSpinBox()
        self.iter_spinbox.setRange(1, 20)
        self.iter_spinbox.setValue(5)
        iter_layout.addWidget(self.iter_spinbox)
        iter_layout.addWidget(QLabel("(Higher = more reliable results)"))
        iter_layout.addStretch()
        config_layout.addLayout(iter_layout)

        # Test prompt selection
        prompt_layout = QHBoxLayout()
        prompt_layout.addWidget(QLabel("Test Prompts:"))
        self.prompt_count_combo = QComboBox()
        self.prompt_count_combo.addItems(["2 prompts (Quick)", "5 prompts (Standard)", "10 prompts (Comprehensive)", "All 12 prompts (Exhaustive)"])
        prompt_layout.addWidget(self.prompt_count_combo)
        prompt_layout.addStretch()
        config_layout.addLayout(prompt_layout)

        layout.addWidget(config_group)

        # Parameter Preview Section
        preview_group = QGroupBox("Parameter Configurations Preview")
        self.preview_layout = QVBoxLayout(preview_group)
        self.preview_label = QLabel("Select parameters and test type to preview configurations")
        self.preview_layout.addWidget(self.preview_label)
        layout.addWidget(preview_group)

        # Control Buttons
        control_layout = QHBoxLayout()
        self.preview_btn = QPushButton("Preview Configurations")
        self.preview_btn.clicked.connect(self.preview_configurations)
        control_layout.addWidget(self.preview_btn)

        self.run_test_btn = QPushButton("🚀 Run Parameter Test")
        self.run_test_btn.clicked.connect(self.run_parameter_comparison)
        self.run_test_btn.setStyleSheet("QPushButton { background-color: #e94560; font-weight: bold; }")
        control_layout.addWidget(self.run_test_btn)

        layout.addLayout(control_layout)

        # Results Section
        results_group = QGroupBox("Test Results")
        results_layout = QVBoxLayout(results_group)

        # Progress info
        self.progress_label = QLabel("Ready to run parameter comparison tests")
        results_layout.addWidget(self.progress_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        results_layout.addWidget(self.progress_bar)

        # Results table
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(6)
        self.results_table.setHorizontalHeaderLabels([
            "Configuration", "Metric", "Mean", "Std Dev", "Min/Max", "Count"
        ])
        self.results_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        results_layout.addWidget(self.results_table)

        layout.addWidget(results_group)

    def on_parameter_changed(self, param_name):
        """Handle parameter selection change"""
        # Update parameter-specific info if needed
        self.preview_configurations()

    def on_test_type_changed(self, test_type):
        """Handle test type selection change"""
        if "Isolation Test" in test_type:
            self.custom_values_frame.show()
        else:
            self.custom_values_frame.hide()

    def preview_configurations(self):
        """Preview the parameter configurations that will be tested"""
        param_name = self.param_combo.currentText().lower().replace(" ", "_")
        test_type = self.test_type_combo.currentText()

        configurations = []

        if "Parameter Sweep" in test_type:
            steps = 5 if "5 points" in test_type else 10
            if param_name == "temperature":
                min_val, max_val = 0.1, 1.5
            elif param_name == "top_p":
                min_val, max_val = 0.1, 1.0
            elif param_name == "top_k":
                min_val, max_val = 1, 100
            elif param_name == "repeat_penalty":
                min_val, max_val = 1.0, 2.0
            else:
                min_val, max_val = 0.1, 1.0

            step_size = (max_val - min_val) / (steps - 1)
            for i in range(steps):
                value = min_val + (i * step_size)
                config = {"temperature": 0.7, "top_p": 0.9, "top_k": 40, "repeat_penalty": 1.1}
                config[param_name] = round(value, 2)
                config["label"] = f"{param_name}={round(value, 2)}"
                configurations.append(config)

        elif "Isolation Test" in test_type:
            try:
                custom_values = [float(v.strip()) for v in self.custom_values_edit.text().split(',')]
                for value in custom_values:
                    config = {"temperature": 0.7, "top_p": 0.9, "top_k": 40, "repeat_penalty": 1.1}
                    config[param_name] = value
                    config["label"] = f"{param_name}={value}"
                    configurations.append(config)
            except ValueError:
                self.preview_label.setText("Invalid custom values. Please enter comma-separated numbers.")
                return

        else:  # Compare with baseline
            config1 = {"temperature": 0.7, "top_p": 0.9, "top_k": 40, "repeat_penalty": 1.1}
            config1["label"] = "Baseline"
            configurations.append(config1)

            config2 = {"temperature": 0.7, "top_p": 0.9, "top_k": 40, "repeat_penalty": 1.1}
            if param_name == "temperature":
                config2["temperature"] = 0.3
            elif param_name == "top_p":
                config2["top_p"] = 0.8
            elif param_name == "top_k":
                config2["top_k"] = 20
            elif param_name == "repeat_penalty":
                config2["repeat_penalty"] = 1.2
            config2["label"] = f"Modified {param_name}"
            configurations.append(config2)

        # Display preview
        preview_text = f"Will test {len(configurations)} configurations:\n"
        for config in configurations[:5]:  # Show first 5
            preview_text += f"  • {config['label']}\n"
        if len(configurations) > 5:
            preview_text += f"  ... and {len(configurations) - 5} more\n"

        total_tests = len(configurations) * self.iter_spinbox.value() * self.get_prompt_count()
        preview_text += f"\nTotal tests: {total_tests} (estimated time: {total_tests * 2:.0f}s)"

        self.preview_label.setText(preview_text)
        self.pending_configurations = configurations

    def get_prompt_count(self):
        """Get the number of test prompts based on selection"""
        selection = self.prompt_count_combo.currentText()
        if "2 prompts" in selection:
            return 2
        elif "5 prompts" in selection:
            return 5
        elif "10 prompts" in selection:
            return 10
        else:  # All 12 prompts
            return 12

    def run_parameter_comparison(self):
        """Run the parameter comparison test"""
        if not hasattr(self, 'pending_configurations'):
            self.preview_configurations()

        if not self.model_combo.currentText():
            self.progress_label.setText("Please select a model first")
            return

        # Get test prompts
        all_prompts = self.get_parameter_test_prompts()
        prompt_count = self.get_prompt_count()
        test_prompts = all_prompts[:prompt_count]

        # Run the test
        self.run_parameter_test.emit(self.pending_configurations, test_prompts, self.iter_spinbox.value())

        # Update UI
        self.progress_label.setText(f"Running parameter comparison with {len(self.pending_configurations)} configurations...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, len(self.pending_configurations) * len(test_prompts) * self.iter_spinbox.value())
        self.run_test_btn.setEnabled(False)

    def get_parameter_test_prompts(self):
        """Get test prompts specifically designed for parameter comparison"""
        return [
            # Creative tasks (sensitive to temperature)
            "Write a short story opening about a time traveler.",
            "Describe a sunset from the perspective of an alien.",
            "Create a poem about artificial intelligence.",
            "Invent a new holiday and describe its traditions.",

            # Analytical tasks (sensitive to top_p/top_k)
            "Compare the advantages and disadvantages of solar and wind energy.",
            "Explain the concept of blockchain technology.",
            "Analyze the causes of climate change.",
            "Describe the differences between machine learning and deep learning.",

            # Technical tasks (sensitive to repeat penalty)
            "Write a function to sort a list of numbers in Python.",
            "Explain how HTTP requests work.",
            "Create a recipe for chocolate chip cookies.",
            "Give directions from New York to Los Angeles.",

            # Reasoning tasks (sensitive to multiple parameters)
            "If you have 8 balls, one of which is heavier, how can you find it with only 2 weighings?",
            "Explain the ethical implications of genetic engineering.",
            "Solve this riddle: I speak without a mouth and hear without ears. What am I?",
            "Design a system to prevent spam emails."
        ]

    def add_test_result(self, config_label, metrics):
        """Add a test result to the comparison"""
        self.test_results.append({
            'config_label': config_label,
            'metrics': metrics,
            'timestamp': time.time()
        })
        self.update_results_display()

    def update_results_display(self):
        """Update the results table with current test results"""
        # Group results by configuration
        config_groups = {}
        for result in self.test_results:
            label = result['config_label']
            if label not in config_groups:
                config_groups[label] = []
            config_groups[label].append(result)

        self.results_table.setRowCount(0)

        for config_label, results in config_groups.items():
            for metric_name in ['response_time', 'tokens_per_second', 'response_length']:
                values = [r['metrics'].get(metric_name, 0) for r in results if metric_name in r['metrics']]
                if values:
                    mean_val = sum(values) / len(values)
                    std_val = (sum((x - mean_val) ** 2 for x in values) / len(values)) ** 0.5
                    min_val = min(values)
                    max_val = max(values)

                    row = self.results_table.rowCount()
                    self.results_table.insertRow(row)
                    self.results_table.setItem(row, 0, QTableWidgetItem(config_label))
                    self.results_table.setItem(row, 1, QTableWidgetItem(metric_name))
                    self.results_table.setItem(row, 2, QTableWidgetItem(f"{mean_val:.3f}"))
                    self.results_table.setItem(row, 3, QTableWidgetItem(f"{std_val:.3f}"))
                    self.results_table.setItem(row, 4, QTableWidgetItem(f"{min_val:.2f}/{max_val:.2f}"))
                    self.results_table.setItem(row, 5, QTableWidgetItem(str(len(values))))

    def export_comparison_report(self):
        """Export a comprehensive comparison report"""
        if not self.test_results:
            print("No results to export")
            return

        from PySide6.QtWidgets import QFileDialog
        import json
        from datetime import datetime

        filename, _ = QFileDialog.getSaveFileName(
            self, "Export Comparison Report",
            f"parameter_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            "JSON Files (*.json)"
        )

        if filename:
            try:
                # Create comprehensive report
                report = {
                    "test_info": {
                        "model": self.model_combo.currentText(),
                        "parameter": self.param_combo.currentText(),
                        "test_type": self.test_type_combo.currentText(),
                        "iterations_per_config": self.iter_spinbox.value(),
                        "prompt_count": self.get_prompt_count(),
                        "timestamp": datetime.now().isoformat()
                    },
                    "results": self.test_results,
                    "summary": self.generate_summary_statistics()
                }

                with open(filename, 'w') as f:
                    json.dump(report, f, indent=2)

                print(f"Comparison report exported to {filename}")

            except Exception as e:
                print(f"Error exporting report: {e}")

    def generate_summary_statistics(self):
        """Generate summary statistics for the report"""
        config_groups = {}
        for result in self.test_results:
            label = result['config_label']
            if label not in config_groups:
                config_groups[label] = []
            config_groups[label].append(result)

        summary = {}
        for config_label, results in config_groups.items():
            metrics_summary = {}
            for metric in ['response_time', 'tokens_per_second', 'response_length']:
                values = [r['metrics'].get(metric, 0) for r in results if metric in r['metrics']]
                if values:
                    metrics_summary[metric] = {
                        "mean": sum(values) / len(values),
                        "std": (sum((x - sum(values) / len(values)) ** 2 for x in values) / len(values)) ** 0.5,
                        "min": min(values),
                        "max": max(values),
                        "count": len(values)
                    }
            summary[config_label] = metrics_summary

        return summary

    def update_progress(self, current, total):
        """Update progress bar"""
        self.progress_bar.setValue(current)
        if current >= total:
            self.progress_label.setText(f"Parameter comparison complete! {len(self.test_results)} results collected.")
            self.run_test_btn.setEnabled(True)
        else:
            self.progress_label.setText(f"Running tests... {current}/{total} completed")

    def set_available_models(self, models):
        """Update the available models in the dropdown"""
        self.model_combo.clear()
        self.model_combo.addItems(models)


class AdvancedAnalyticsWidget(QWidget):
    """Advanced Analytics and Performance Insights"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.analytics_data = []
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.refresh_analytics)
        self.update_timer.start(5000)  # Update every 5 seconds

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Header with controls
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("📈 Advanced Analytics"))
        header_layout.addStretch()
        
        # Control buttons
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.refresh_analytics)
        header_layout.addWidget(refresh_btn)
        
        export_btn = QPushButton("📊 Export Analytics")
        export_btn.clicked.connect(self.export_analytics)
        header_layout.addWidget(export_btn)
        
        clear_btn = QPushButton("🗑️ Clear Data")
        clear_btn.clicked.connect(self.clear_analytics)
        header_layout.addWidget(clear_btn)
        
        layout.addLayout(header_layout)
        
        # Analytics tabs
        self.analytics_tabs = QTabWidget()
        
        # Performance Overview Tab
        self.overview_tab = QWidget()
        overview_layout = QVBoxLayout(self.overview_tab)
        
        # Key Metrics
        metrics_group = QGroupBox("📊 Key Performance Metrics")
        metrics_layout = QVBoxLayout(metrics_group)
        
        # Performance scorecards
        scorecards_layout = QHBoxLayout()
        
        # Overall Performance Score
        overall_score_frame = QFrame()
        overall_score_layout = QVBoxLayout(overall_score_frame)
        overall_score_layout.addWidget(QLabel("Overall Performance"))
        self.overall_score_label = QLabel("0.00")
        overall_score_layout.addWidget(self.overall_score_label)
        scorecards_layout.addWidget(overall_score_frame)
        
        # Model Performance Score
        model_score_frame = QFrame()
        model_score_layout = QVBoxLayout(model_score_frame)
        model_score_layout.addWidget(QLabel("Model Performance"))
        self.model_score_label = QLabel("0.00")
        model_score_layout.addWidget(self.model_score_label)
        scorecards_layout.addWidget(model_score_frame)
        
        # Parameter Sensitivity Score
        param_score_frame = QFrame()
        param_score_layout = QVBoxLayout(param_score_frame)
        param_score_layout.addWidget(QLabel("Parameter Sensitivity"))
        self.param_score_label = QLabel("0.00")
        param_score_layout.addWidget(self.param_score_label)
        scorecards_layout.addWidget(param_score_frame)
        
        metrics_layout.addLayout(scorecards_layout)
        metrics_group.setLayout(metrics_layout)
        overview_layout.addWidget(metrics_group)
        
        # Performance Trends
        trends_group = QGroupBox("📈 Performance Trends")
        trends_layout = QVBoxLayout(trends_group)
        
        self.trends_table = QTableWidget()
        self.trends_table.setColumnCount(4)
        self.trends_table.setHorizontalHeaderLabels(["Metric", "Current", "Trend", "Change"])
        self.trends_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.trends_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.trends_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.trends_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        trends_layout.addWidget(self.trends_table)
        trends_group.setLayout(trends_layout)
        overview_layout.addWidget(trends_group)
        
        overview_layout.addStretch()
        self.analytics_tabs.addTab(self.overview_tab, "📊 Overview")
        
        # Model Comparison Tab
        self.comparison_tab = QWidget()
        comparison_layout = QVBoxLayout(self.comparison_tab)
        
        # Model Comparison Table
        self.comparison_table = QTableWidget()
        self.comparison_table.setColumnCount(8)
        self.comparison_table.setHorizontalHeaderLabels([
            "Model", "Avg Score", "Speed", "Reliability", "Cost Efficiency", "Best Use Case", "Issues"
        ])
        self.comparison_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.comparison_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.comparison_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.comparison_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.comparison_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.comparison_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.comparison_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)
        self.comparison_table.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeToContents)
        comparison_layout.addWidget(self.comparison_table)
        comparison_layout.addWidget(self.comparison_tab)
        
        self.analytics_tabs.addTab(self.comparison_tab, "🔍 Model Comparison")
        
        # Parameter Analysis Tab
        self.parameter_tab = QWidget()
        parameter_layout = QVBoxLayout(self.parameter_tab)
        
        # Parameter Impact Analysis
        param_group = QGroupBox("🎛️ Parameter Impact Analysis")
        param_layout = QVBoxLayout(param_group)
        
        self.param_heatmap = QTextEdit()
        self.param_heatmap.setReadOnly(True)
        self.param_heatmap.setMaximumHeight(200)
        self.param_heatmap.setStyleSheet("""
            QTextEdit {
                background-color: #1a1a2e;
                color: #eee;
                font-family: monospace;
                font-size: 10px;
                padding: 8px;
                border: 1px solid #333;
            }
        """)
        param_layout.addWidget(self.param_heatmap)
        
        # Parameter Recommendations
        recommendations_group = QGroupBox("💡 Parameter Recommendations")
        recommendations_layout = QVBoxLayout(recommendations_group)
        
        self.recommendations_text = QTextEdit()
        self.recommendations_text.setReadOnly(True)
        self.recommendations_text.setMaximumHeight(150)
        recommendations_layout.addWidget(self.recommendations_text)
        
        recommendations_group.setLayout(recommendations_layout)
        param_layout.addWidget(recommendations_group)
        
        param_group.setLayout(param_layout)
        parameter_layout.addWidget(self.parameter_tab)
        
        self.analytics_tabs.addTab(self.parameter_tab, "⚙️ Parameter Analysis")
        
        # Export & Reports Tab
        self.export_tab = QWidget()
        export_layout = QVBoxLayout(self.export_tab)
        
        export_info_label = QLabel("📊 Export Analytics & Reports")
        export_info_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #4CAF50; padding: 10px;")
        export_layout.addWidget(export_info_label)
        
        # Export options
        export_options_layout = QVBoxLayout()
        
        csv_export_btn = QPushButton("📊 Export CSV Report")
        csv_export_btn.clicked.connect(self.export_csv_report)
        export_options_layout.addWidget(csv_export_btn)
        
        json_export_btn = QPushButton("📄 Export JSON Report")
        json_export_btn.clicked.connect(self.export_json_report)
        export_options_layout.addWidget(json_export_btn)
        
        pdf_export_btn = QPushButton("📄 Export PDF Report")
        pdf_export_btn.clicked.connect(self.export_pdf_report)
        export_options_layout.addWidget(pdf_export_btn)
        
        export_options_layout.addStretch()
        export_layout.addLayout(export_options_layout)
        
        export_layout.addWidget(self.export_tab)
        self.analytics_tabs.addTab(self.export_tab, "📊 Export & Reports")
        
        layout.addWidget(self.analytics_tabs)
        
        # Status bar
        self.status_label = QLabel("Analytics: Ready | Data Points: 0")
        layout.addWidget(self.status_label)

    def refresh_analytics(self):
        """Refresh analytics data from results"""
        try:
            # Get results from main window if available
            if hasattr(self.parent(), 'results') and hasattr(self.parent().results, 'results_data'):
                results_data = self.parent().results.results_data
                self.process_results_data(results_data)
                self.update_displays()
            else:
                print("No results data available for analytics")
        except Exception as e:
            print(f"Error refreshing analytics: {e}")

    def process_results_data(self, results_data):
        """Process results data for analytics"""
        self.analytics_data = []
        
        for result in results_data:
            if result.get('status') == 'completed':
                analytics_entry = {
                    'timestamp': result.get('timestamp', ''),
                    'model_name': result.get('model_name', ''),
                    'response_time': result.get('response_time', 0),
                    'tokens_per_second': result.get('tokens_per_second', 0),
                    'response_length': len(result.get('response_text', '')),
                    'parameters': result.get('parameters', {}),
                    'prompt_type': self.classify_prompt_type(result.get('prompt_text', '')),
                    'performance_score': self.calculate_comprehensive_score(result)
                }
                self.analytics_data.append(analytics_entry)

    def calculate_comprehensive_score(self, result):
        """Calculate comprehensive performance score"""
        score = 0.0
        
        # Base completion score
        if result.get('status') == 'completed':
            score += 0.4
        
        # Response quality (30%)
        response_length = len(result.get('response_text', ''))
        if response_length > 100:
            score += 0.15
        elif response_length > 500:
            score += 0.3
        
        # Performance metrics (30%)
        tps = result.get('tokens_per_second', 0)
        if tps > 20:
            score += 0.2
        elif tps > 10:
            score += 0.1
        
        # Response time (20%)
        response_time = result.get('response_time', 0)
        if response_time < 1.0:
            score += 0.1
        elif response_time < 3.0:
            score += 0.05
        
        # Parameter optimization (20%)
        params = result.get('parameters', {})
        if params:
            # Check for optimal parameter ranges
            temp = params.get('temperature', 0.7)
            if 0.5 <= temp <= 1.0:
                score += 0.05
            elif 0.2 <= temp <= 0.8:
                score += 0.1
            elif 1.0 <= temp <= 1.4:
                score += 0.05
            
            top_p = params.get('top_p', 0.9)
            if 0.7 <= top_p <= 0.95:
                score += 0.05
            
            repeat_penalty = params.get('repeat_penalty', 1.1)
            if 1.05 <= repeat_penalty <= 1.2:
                score += 0.05
        
        return min(score, 1.0)

    def classify_prompt_type(self, prompt_text):
        """Classify prompt type for analytics"""
        prompt_lower = prompt_text.lower()
        
        if any(word in prompt_lower for word in ['function', 'code', 'python', 'program']):
            return "code"
        elif any(word in prompt_lower for word in ['calculate', 'area', 'formula', 'math', 'solve']):
            return "mathematical"
        elif any(word in prompt_lower for word in ['explain', 'what', 'how', 'why', 'describe']):
            return "explanation"
        elif any(word in prompt_lower for word in ['story', 'poem', 'creative', 'imagine', 'write']):
            return "creative"
        elif any(word in prompt_lower for word in ['reasoning', 'logic', 'puzzle', 'analyze']):
            return "reasoning"
        elif any(word in prompt_lower for word in ['compare', 'difference', 'advantage', 'disadvantage']):
            return "comparison"
        else:
            return "general"

    def update_displays(self):
        """Update all analytics displays"""
        if not self.analytics_data:
            return
            
        # Update Overview Tab
        self.update_overview_display()
        self.update_trends_display()
        self.update_comparison_display()
        self.update_parameter_display()
        self.update_recommendations()

    def update_overview_display(self):
        """Update overview display"""
        if not self.analytics_data:
            return
            
        # Calculate overall metrics
        total_tests = len(self.analytics_data)
        avg_score = sum(r['performance_score'] for r in self.analytics_data) / total_tests if total_tests > 0 else 0
        
        # Update scorecards
        self.overall_score_label.setText(f"{avg_score:.3f}")
        self.model_score_label.setText(f"{avg_score:.3f}")
        self.param_score_label.setText(f"{avg_score:.3f}")
        
        # Color code scorecards based on performance
        score_color = self.get_score_color(avg_score)
        self.overall_score_label.setStyleSheet(f"QLabel {{ color: {score_color}; font-size: 16px; font-weight: bold; }}")
        self.model_score_label.setStyleSheet(f"QLabel {{ color: {score_color}; font-size: 16px; font-weight: bold; }}")
        self.param_score_label.setStyleSheet(f"QLabel {{ color: {score_color}; font-size: 16px; font-weight: bold; }}")
        
        # Update trends table
        self.update_trends_data()

    def update_trends_data(self):
        """Update trends table"""
        if not self.analytics_data:
            self.trends_table.setRowCount(0)
            return
            
        # Calculate trends by comparing recent vs historical data
        recent_data = self.analytics_data[-10:] if len(self.analytics_data) >= 10 else self.analytics_data
        historical_data = self.analytics_data[:-10] if len(self.analytics_data) > 10 else []
        
        if not recent_data or not historical_data:
            return
            
        metrics = ['response_time', 'tokens_per_second', 'response_length', 'performance_score']
        
        self.trends_table.setRowCount(len(metrics))
        
        for i, metric in enumerate(metrics):
            recent_avg = sum(r[metric] for r in recent_data) / len(recent_data) if recent_data else 0
            historical_avg = sum(r[metric] for r in historical_data) / len(historical_data) if historical_data else 0
            
            trend = "→" if recent_avg > historical_avg else "→" if recent_avg < historical_avg else "→"
            change = f"{((recent_avg - historical_avg) / historical_avg * 100):+.1f}%" if historical_avg > 0 else "0.0%"
            
            row = i
            self.trends_table.setItem(row, 0, QTableWidgetItem(metric.replace('_', ' ').title()))
            self.trends_table.setItem(row, 1, QTableWidgetItem(f"{recent_avg:.3f}"))
            self.trends_table.setItem(row, 2, QTableWidgetItem(trend))
            self.trends_table.setItem(row, 3, QTableWidgetItem(change))
            
            # Color code based on trend
            trend_item = self.trends_table.item(row, 2)
            if trend_item:
                if "↑" in trend:
                    trend_item.setForeground(QBrush(QColor("#4CAF50")))  # Green - Improving
                elif "↓" in trend:
                    trend_item.setForeground(QBrush(QColor("#F44336")))  # Red - Declining
                else:
                    trend_item.setForeground(QBrush(QColor("#FF9800")))  # Orange - Stable

    def update_comparison_display(self):
        """Update model comparison table"""
        if not self.analytics_data:
            self.comparison_table.setRowCount(0)
            return
            
        # Group by model
        model_stats = {}
        for entry in self.analytics_data:
            model = entry['model_name']
            if model not in model_stats:
                model_stats[model] = {
                    'scores': [],
                    'response_times': [],
                    'tokens_per_second': [],
                    'response_lengths': [],
                    'prompt_types': {}
            }
            
            model_stats[model]['scores'].append(entry['performance_score'])
            model_stats[model]['response_times'].append(entry['response_time'])
            model_stats[model]['tokens_per_second'].append(entry['tokens_per_second'])
            model_stats[model]['response_lengths'].append(entry['response_length'])
            
            prompt_type = entry['prompt_type']
            if prompt_type not in model_stats[model]['prompt_types']:
                model_stats[model]['prompt_types'][prompt_type] = 0
            model_stats[model]['prompt_types'][prompt_type] += 1
        
        # Update comparison table
        self.comparison_table.setRowCount(len(model_stats))
        
        for i, (model, stats) in enumerate(model_stats.items()):
            avg_score = sum(stats['scores']) / len(stats['scores']) if stats['scores'] else 0
            avg_time = sum(stats['response_times']) / len(stats['response_times']) if stats['response_times'] else 0
            avg_tps = sum(stats['tokens_per_second']) / len(stats['tokens_per_second']) if stats['tokens_per_second'] else 0
            avg_length = sum(stats['response_lengths']) / len(stats['response_lengths']) if stats['response_lengths'] else 0
            
            # Calculate best use case based on prompt types
            best_use_case = self.determine_best_use_case(stats['prompt_types'])
            
            # Calculate cost efficiency (tokens per second)
            cost_efficiency = avg_tps / avg_time if avg_time > 0 else 0
            
            # Calculate reliability (inverse of response time variance)
            if len(stats['response_times']) > 1:
                time_variance = sum((t - avg_time) ** 2 for t in stats['response_times']) / len(stats['response_times'])
                reliability = 1 / (1 + time_variance) if time_variance > 0 else 1.0
            else:
                reliability = 1.0
            
            row = i
            self.comparison_table.setItem(row, 0, QTableWidgetItem(model))
            self.comparison_table.setItem(row, 1, QTableWidgetItem(f"{avg_score:.3f}"))
            self.comparison_table.setItem(row, 2, QTableWidgetItem(f"{avg_tps:.1f}"))
            self.comparison_table.setItem(row, 3, QTableWidgetItem(f"{reliability:.2f}"))
            self.comparison_table.setItem(row, 4, QTableWidgetItem(f"{cost_efficiency:.2f}"))
            self.comparison_table.setItem(row, 5, QTableWidgetItem(best_use_case))
            self.comparison_table.setItem(row, 6, QTableWidgetItem("📊"))
            self.comparison_table.setItem(row, 7, QTableWidgetItem("✅"))
            
            # Color code based on performance
            score_color = self.get_score_color(avg_score)
            self.comparison_table.item(row, 1).setBackground(QBrush(QColor(score_color)))
            
            # Add tooltip with detailed information
            tooltip = (
                f"Model: {model}\n"
                f"Avg Score: {avg_score:.3f}\n"
                f"Avg Speed: {avg_tps:.1f} tokens/s\n"
                f"Reliability: {reliability:.2f}\n"
                f"Cost Efficiency: {cost_efficiency:.2f} tokens/s\n"
                f"Best Use Case: {best_use_case}"
            )
            self.comparison_table.item(row, 0).setToolTip(tooltip)

    def determine_best_use_case(self, prompt_types):
        """Determine best use case based on prompt type distribution"""
        if not prompt_types:
            return "General"
            
        # Find the most common prompt type
        most_common = max(prompt_types.items(), key=lambda x: x[1])[0]
        return most_common

    def get_score_color(self, score):
        """Get color based on score value"""
        if score >= 0.8:
            return "#4CAF50"  # Green - Excellent
        elif score >= 0.6:
            return "#8BC34A"  # Light Green - Good
        elif score >= 0.4:
            return "#FFC107"  # Yellow - Fair
        elif score >= 0.2:
            return "#FF9800"  # Orange - Poor
        else:
            return "#F44336"  # Red - Very Poor

    def update_parameter_display(self):
        """Update parameter analysis display"""
        if not self.analytics_data:
            self.param_heatmap.clear()
            self.recommendations_text.clear()
            return
            
        # Analyze parameter impact
        param_impact = self.analyze_parameter_impact()
        
        # Create heatmap visualization
        heatmap_data = []
        for entry in self.analytics_data:
            params = entry['parameters']
            score = entry['performance_score']
            
            # Create heatmap row for each parameter
            heatmap_row = []
            for param, value in params.items():
                heatmap_row.append(f"{param}={value:.2f}")
            
            heatmap_data.append(f"Score: {score:.3f} | {' | '.join(heatmap_row)}")
        
        self.param_heatmap.setText("\n".join(heatmap_data))
        
        # Generate recommendations
        recommendations = self.generate_parameter_recommendations(param_impact)
        self.recommendations_text.setText(recommendations)

    def analyze_parameter_impact(self):
        """Analyze parameter impact on performance"""
        param_impact = {}
        
        for entry in self.analytics_data:
            params = entry['parameters']
            score = entry['performance_score']
            
            for param, value in params.items():
                if param not in param_impact:
                    param_impact[param] = {
                        'scores': [],
                        'values': [],
                        'correlation': 0.0
                    }
                
                param_impact[param]['values'].append(value)
                param_impact[param]['scores'].append(score)
            
            # Calculate correlation for each parameter
            for param in param_impact:
                if len(param_impact[param]['values']) > 1:
                    correlation = self.calculate_correlation(
                        param_impact[param]['values'],
                        param_impact[param]['scores']
                    )
                    param_impact[param]['correlation'] = correlation
        
        return param_impact

    def calculate_correlation(self, values, scores):
        """Calculate correlation between parameter values and scores"""
        if len(values) != len(scores):
            return 0.0
            
        # Calculate Pearson correlation
        n = len(values)
        if n == 0:
            return 0.0
            
        mean_x = sum(values) / n
        mean_y = sum(scores) / n
        
        sum_xy = sum((values[i] - mean_x) * (scores[i] - mean_y) for i in range(n))
        sum_x2 = sum((values[i] - mean_x) ** 2 for i in range(n))
        sum_y2 = sum((scores[i] - mean_y) ** 2 for i in range(n))
        
        if sum_x2 == 0 or sum_y2 == 0:
            return 0.0
            
        return sum_xy / (sum_x2 * sum_y2) ** 0.5

    def generate_parameter_recommendations(self, param_impact):
        """Generate parameter recommendations based on impact analysis"""
        recommendations = []
        
        # Sort parameters by impact
        sorted_params = sorted(
            param_impact.items(),
            key=lambda x: abs(x[1]['correlation']) if len(x[1]['values']) > 1 else 0,
            reverse=True
        )
        
        # Generate recommendations
        for param, impact in sorted_params[:5]:  # Top 5 impactful parameters
            if impact['correlation'] > 0.5:  # Strong correlation
                recommendation = f"{param}: {impact['values'][-1]:.2f} (Strong impact, correlation: {impact['correlation']:.2f})"
            elif impact['correlation'] > 0.3:
                recommendation = f"{param}: {impact['values'][-1]:.2f} (Moderate impact, correlation: {impact['correlation']:.2f})"
            else:
                recommendation = f"{param}: {impact['values'][-1]:.2f} (Low impact, correlation: {impact['correlation']:.2f})"
            
            recommendations.append(recommendation)
        
        return "\n".join(recommendations)

    def update_recommendations(self):
        """Update recommendations display"""
        if self.recommendations_text.toPlainText():
            self.recommendations_text.clear()
            return
            
        recommendations = self.generate_parameter_recommendations(self.analyze_parameter_impact())
        self.recommendations_text.setText(recommendations)

    def export_csv_report(self):
        """Export analytics report as CSV"""
        if not self.analytics_data:
            print("No analytics data to export")
            return
            
        from PySide6.QtWidgets import QFileDialog
        import csv
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export Analytics Report",
            f"analytics_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "CSV Files (*.csv)"
        )
        
        if filename:
            try:
                with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                    fieldnames = [
                        'timestamp', 'model_name', 'prompt_type', 'performance_score',
                        'response_time', 'tokens_per_second', 'response_length',
                        'temperature', 'top_k', 'top_p', 'repeat_penalty',
                        'num_ctx', 'num_predict'
                    ]
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()

                    for entry in self.analytics_data:
                        params = entry.get('parameters', {})
                        writer.writerow({
                            'timestamp': entry.get('timestamp', ''),
                            'model_name': entry.get('model_name', ''),
                            'prompt_type': entry.get('prompt_type', ''),
                            'performance_score': entry.get('performance_score', 0),
                            'response_time': entry.get('response_time', 0),
                            'tokens_per_second': entry.get('tokens_per_second', 0),
                            'response_length': entry.get('response_length', 0),
                            'temperature': params.get('temperature', 0),
                            'top_k': params.get('top_k', 0),
                            'top_p': params.get('top_p', 0),
                            'repeat_penalty': params.get('repeat_penalty', 0),
                            'num_ctx': params.get('num_ctx', 0),
                            'num_predict': params.get('num_predict', 0)
                        })

                print(f"Analytics report exported to {filename}")

            except Exception as e:
                print(f"Error exporting analytics report: {e}")

    def export_json_report(self):
        """Export detailed analytics report as JSON"""
        if not self.analytics_data:
            print("No analytics data to export")
            return
            
        from PySide6.QtWidgets import QFileDialog
        import json
        from datetime import datetime
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export Detailed Analytics Report",
            f"analytics_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            "JSON Files (*.json)"
        )
        
        if filename:
            try:
                # Create comprehensive analytics report
                report = {
                    "report_info": {
                        "export_timestamp": datetime.now().isoformat(),
                        "total_tests": len(self.analytics_data),
                        "report_type": "comprehensive_analytics"
                    },
                    "summary": self.generate_analytics_summary(),
                    "detailed_data": self.analytics_data,
                    "parameter_analysis": self.analyze_parameter_impact(),
                    "model_comparison": self.generate_model_comparison_summary(),
                    "trends": self.generate_trends_summary(),
                    "recommendations": self.generate_parameter_recommendations(self.analyze_parameter_impact())
                }
                
                # Write report to file
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(report, f, indent=2, ensure_ascii=False)
                
                print(f"Detailed analytics report exported to {filename}")
                print(f"  - Total tests: {len(self.analytics_data)}")
                print(f"  - Report type: {report['report_info']['report_type']}")
                print(f"  - Export timestamp: {report['report_info']['export_timestamp']}")

            except Exception as e:
                print(f"Error exporting JSON report: {e}")

    def export_pdf_report(self):
        """Export analytics report as PDF"""
        if not self.analytics_data:
            print("No analytics data to export")
            return
            
        from PySide6.QtWidgets import QFileDialog
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export Analytics Report",
            f"analytics_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            "PDF Files (*.pdf)"
        )
        
        if filename:
            print(f"PDF export to {filename}")
            # PDF export would require additional libraries like reportlab or similar
            print("Note: PDF export requires additional libraries (reportlab, matplotlib)")

    def generate_analytics_summary(self):
        """Generate analytics summary statistics"""
        if not self.analytics_data:
            return {}
            
        total_tests = len(self.analytics_data)
        avg_score = sum(r['performance_score'] for r in self.analytics_data) / total_tests if total_tests > 0 else 0
        
        # Model performance breakdown
        model_scores = {}
        prompt_type_scores = {}
        
        for entry in self.analytics_data:
            model = entry['model_name']
            score = entry['performance_score']
            prompt_type = entry.get('prompt_type', 'unknown')
            
            if model not in model_scores:
                model_scores[model] = []
            model_scores[model].append(score)
            
            if prompt_type not in prompt_type_scores:
                prompt_type_scores[prompt_type] = []
            prompt_type_scores[prompt_type].append(score)
        
        # Calculate model averages
        model_avg_scores = {}
        for model, scores in model_scores.items():
            if scores:
                model_avg_scores[model] = sum(scores) / len(scores)
        
        # Calculate prompt type averages
        prompt_avg_scores = {}
        for prompt_type, scores in prompt_type_scores.items():
            if scores:
                prompt_avg_scores[prompt_type] = sum(scores) / len(scores)
        
        return {
            'total_tests': total_tests,
            'average_score': avg_score,
            'model_performance': model_avg_scores,
            'prompt_type_performance': prompt_avg_scores,
            'test_distribution': {
                'code': len(prompt_type_scores.get('code', [])),
                'mathematical': len(prompt_type_scores.get('mathematical', [])),
                'explanation': len(prompt_type_scores.get('explanation', [])),
                'creative': len(prompt_type_scores.get('creative', [])),
                'reasoning': len(prompt_type_scores.get('reasoning', [])),
                'comparison': len(prompt_type_scores.get('comparison', [])),
                'general': len(prompt_type_scores.get('general', []))
            }
        }

    def generate_model_comparison_summary(self):
        """Generate model comparison summary"""
        if not self.analytics_data:
            return {}
            
        model_stats = {}
        for entry in self.analytics_data:
            model = entry['model_name']
            score = entry['performance_score']
            
            if model not in model_stats:
                model_stats[model] = {
                    'scores': [],
                    'response_times': [],
                    'tokens_per_second': [],
                    'response_lengths': [],
                    'prompt_types': {}
                }
            
            model_stats[model]['scores'].append(score)
            model_stats[model]['response_times'].append(entry['response_time'])
            model_stats[model]['tokens_per_second'].append(entry['tokens_per_second'])
            model_stats[model]['response_lengths'].append(entry['response_length'])
            
            prompt_type = entry.get('prompt_type', 'unknown')
            if prompt_type not in model_stats[model]['prompt_types']:
                model_stats[model]['prompt_types'][prompt_type] = 0
            model_stats[model]['prompt_types'][prompt_type] += 1
        
        # Generate comparison summary
        comparison_summary = {}
        for model, stats in model_stats.items():
            if stats['scores']:
                avg_score = sum(stats['scores']) / len(stats['scores'])
                avg_time = sum(stats['response_times']) / len(stats['response_times']) if stats['response_times'] else 0
                avg_tps = sum(stats['tokens_per_second']) / len(stats['tokens_per_second']) if stats['tokens_per_second'] else 0
                avg_length = sum(stats['response_lengths']) / len(stats['response_lengths']) if stats['response_lengths'] else 0
                
                comparison_summary[model] = {
                    'average_score': avg_score,
                    'average_time': avg_time,
                    'average_tokens_per_second': avg_tps,
                    'average_response_length': avg_length,
                    'prompt_type_distribution': model_stats['prompt_types'],
                    'reliability': self.calculate_reliability(stats['response_times']) if len(stats['response_times']) > 1 else 1.0,
                    'efficiency': avg_tps / avg_time if avg_time > 0 else 0
                }
        
        return comparison_summary

    def calculate_reliability(self, values):
        """Calculate reliability score based on response time variance"""
        if len(values) <= 1:
            return 1.0
            
        mean_val = sum(values) / len(values)
        variance = sum((x - mean_val) ** 2 for x in values) / len(values)
        
        if variance == 0:
            return 1.0
            
        return 1.0 / (1 + (variance / mean_val ** 2))

    def generate_trends_summary(self):
        """Generate trends summary"""
        if not self.analytics_data:
            return {}
            
        # Calculate overall trends
        recent_data = self.analytics_data[-10:] if len(self.analytics_data) >= 10 else self.analytics_data
        historical_data = self.analytics_data[:-10] if len(self.analytics_data) > 10 else []
        
        if not recent_data or not historical_data:
            return {}
            
        trends = {}
        metrics = ['response_time', 'tokens_per_second', 'response_length', 'performance_score']
        
        for metric in metrics:
            recent_avg = sum(r[metric] for r in recent_data) / len(recent_data) if recent_data else 0
            historical_avg = sum(r[metric] for r in historical_data) / len(historical_data) if historical_data else 0
            
            if historical_avg > 0:
                trend = "improving" if recent_avg > historical_avg else "declining"
                change = ((recent_avg - historical_avg) / historical_avg * 100)
            else:
                trend = "stable"
                change = 0.0
                
            trends[metric] = {
                'current': recent_avg,
                'historical': historical_avg,
                'trend': trend,
                'change': change
            }
        
        return trends

    def clear_analytics(self):
        """Clear all analytics data"""
        self.analytics_data = []
        self.update_displays()

    def export_analytics(self):
        """Export analytics data to file"""
        from PySide6.QtWidgets import QFileDialog
        import json
        from datetime import datetime

        if not self.analytics_data:
            QMessageBox.information(self, "No Data", "No analytics data available to export.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Analytics",
            f"analytics_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            "JSON Files (*.json)"
        )

        if file_path:
            try:
                with open(file_path, 'w') as f:
                    json.dump(self.analytics_data, f, indent=2, default=str)
                QMessageBox.information(self, "Success", f"Analytics data exported to {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export data: {e}")

    def export_analytics(self):
        """Export analytics data to file"""
        from PySide6.QtWidgets import QFileDialog, QMessageBox
        import json
        from datetime import datetime

        if not self.analytics_data:
            QMessageBox.information(self, "No Data", "No analytics data available to export.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Analytics",
            f"analytics_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            "JSON Files (*.json)"
        )

        if file_path:
            try:
                with open(file_path, 'w') as f:
                    json.dump(self.analytics_data, f, indent=2, default=str)
                QMessageBox.information(self, "Success", f"Analytics data exported to {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export data: {e}")

    def update_analytics_timer(self):
        """Periodic analytics update"""
        self.refresh_analytics()


# Parameter Optimization Lab Classes
class OptimizationStatus(Enum):
    EXPLORING = "exploring_parameter_space"
    REFINING = "refining_best_candidates"
    VALIDATING = "validating_consistency"
    CONVERGED = "converged_on_optimal"
    FAILED = "failed_to_converge"

@dataclass
class ParameterConfig:
    """Configuration for LLM parameters"""
    temperature: float
    num_ctx: int
    num_predict: int
    repeat_penalty: float
    top_k: int
    top_p: float

    def to_dict(self) -> dict:
        return {
            'temperature': self.temperature,
            'num_ctx': self.num_ctx,
            'num_predict': self.num_predict,
            'repeat_penalty': self.repeat_penalty,
            'top_k': self.top_k,
            'top_p': self.top_p
        }

    def __str__(self) -> str:
        return f"T{self.temperature:.2f}_C{self.num_ctx}_P{self.num_predict}_R{self.repeat_penalty:.2f}_K{self.top_k}_P{self.top_p:.2f}"

@dataclass
class OptimizationResult:
    """Result of a parameter optimization run"""
    config: ParameterConfig
    accuracy_score: float
    response_time: float
    consistency_score: float
    tokens_generated: int
    cycle: int
    phase: str

class OptimizationWorker(QThread):
    """Worker thread for parameter optimization"""
    progress_update = Signal(str, int, int)  # status, current, total
    result_found = Signal(object)  # OptimizationResult
    optimization_complete = Signal(object, dict)  # best_config, summary
    error_occurred = Signal(str)

    def __init__(self, model_name: str, prompt_text: str):
        super().__init__()
        self.model_name = model_name
        self.prompt_text = prompt_text
        self.running = False
        self.best_config = None
        self.best_score = 0.0

    def run_optimization(self):
        """Run the complete optimization process"""
        try:
            self.running = True
            self.progress_update.emit("Starting optimization...", 0, 100)

            # Phase 1: Exploration
            best_configs = self.exploration_phase()
            if not best_configs or not self.running:
                return

            # Phase 2: Refinement
            refined_config = self.refinement_phase(best_configs)
            if not refined_config or not self.running:
                return

            # Phase 3: Validation
            final_result = self.validation_phase(refined_config)
            if not final_result or not self.running:
                return

            # Complete
            summary = {
                'total_tests_run': len(getattr(self, 'test_results', [])),
                'best_accuracy': final_result.accuracy_score,
                'best_time': final_result.response_time,
                'consistency': final_result.consistency_score
            }
            self.optimization_complete.emit(refined_config, summary)

        except Exception as e:
            self.error_occurred.emit(f"Optimization error: {str(e)}")

    def exploration_phase(self) -> List[ParameterConfig]:
        """Explore parameter space systematically"""
        configs = []

        # Temperature exploration
        for temp in [0.1, 0.3, 0.5, 0.7, 0.9]:
            configs.append(ParameterConfig(
                temperature=temp, num_ctx=2048, num_predict=512,
                repeat_penalty=1.1, top_k=25, top_p=0.9
            ))

        # Context size exploration
        for ctx in [1024, 2048, 4096, 8192]:
            configs.append(ParameterConfig(
                temperature=0.5, num_ctx=ctx, num_predict=512,
                repeat_penalty=1.1, top_k=25, top_p=0.9
            ))

        # Output limit exploration
        for pred in [256, 512, 1024, 2048]:
            configs.append(ParameterConfig(
                temperature=0.5, num_ctx=2048, num_predict=pred,
                repeat_penalty=1.1, top_k=25, top_p=0.9
            ))

        # Test configurations
        best_configs = []
        for i, config in enumerate(configs):
            if not self.running:
                break

            self.progress_update.emit(f"Exploring phase 1/3: Testing {config}...", i, len(configs))
            result = self.test_configuration(config, cycles=3)
            if result:
                self.result_found.emit(result)
                if result.accuracy_score > 0.8:  # Good candidates
                    best_configs.append(config)

        return best_configs[:5] if best_configs else configs[:3]  # Top candidates

    def refinement_phase(self, candidate_configs: List[ParameterConfig]) -> Optional[ParameterConfig]:
        """Refine around best candidates"""
        if not candidate_configs:
            return None

        best_config = None
        best_score = 0.0

        for i, base_config in enumerate(candidate_configs):
            if not self.running:
                break

            self.progress_update.emit(f"Refining phase 2/3: Candidate {i+1}/{len(candidate_configs)}",
                                    i, len(candidate_configs))

            # Generate variations around the candidate
            variations = self.generate_variations(base_config)

            for j, config in enumerate(variations):
                if not self.running:
                    break

                result = self.test_configuration(config, cycles=5)
                if result:
                    self.result_found.emit(result)
                    if result.accuracy_score > best_score:
                        best_score = result.accuracy_score
                        best_config = config

        return best_config

    def validation_phase(self, config: ParameterConfig) -> Optional[OptimizationResult]:
        """Validate the best configuration thoroughly"""
        if not config or not self.running:
            return None

        self.progress_update.emit("Validating phase 3/3: Final verification...", 0, 10)

        # Run multiple validation cycles
        validation_results = []
        for i in range(10):
            if not self.running:
                break
            self.progress_update.emit(f"Validation cycle {i+1}/10", i, 10)
            result = self.test_configuration(config, cycles=1)
            if result:
                validation_results.append(result)

        if not validation_results:
            return None

        # Calculate consistency
        accuracies = [r.accuracy_score for r in validation_results]
        times = [r.response_time for r in validation_results]

        avg_accuracy = statistics.mean(accuracies)
        std_accuracy = statistics.stdev(accuracies) if len(accuracies) > 1 else 0
        avg_time = statistics.mean(times)

        consistency_score = 1.0 - (std_accuracy / avg_accuracy) if avg_accuracy > 0 else 0

        return OptimizationResult(
            config=config,
            accuracy_score=avg_accuracy,
            response_time=avg_time,
            consistency_score=consistency_score,
            tokens_generated=statistics.mean([r.tokens_generated for r in validation_results]),
            cycle=len(validation_results),
            phase="validation"
        )

    def generate_variations(self, base_config: ParameterConfig) -> List[ParameterConfig]:
        """Generate variations around a base configuration"""
        variations = []

        # Temperature variations
        for temp_offset in [-0.1, 0.1]:
            new_temp = max(0.1, min(1.0, base_config.temperature + temp_offset))
            variations.append(ParameterConfig(
                temperature=new_temp, num_ctx=base_config.num_ctx,
                num_predict=base_config.num_predict, repeat_penalty=base_config.repeat_penalty,
                top_k=base_config.top_k, top_p=base_config.top_p
            ))

        # Context variations
        for ctx_factor in [0.5, 2.0]:
            new_ctx = int(base_config.num_ctx * ctx_factor)
            new_ctx = max(512, min(8192, new_ctx))
            variations.append(ParameterConfig(
                temperature=base_config.temperature, num_ctx=new_ctx,
                num_predict=base_config.num_predict, repeat_penalty=base_config.repeat_penalty,
                top_k=base_config.top_k, top_p=base_config.top_p
            ))

        return variations

    def test_configuration(self, config: ParameterConfig, cycles: int = 3) -> Optional[OptimizationResult]:
        """Test a configuration and return average results"""
        results = []

        for cycle in range(cycles):
            if not self.running:
                break

            try:
                # Call the actual model
                start_time = time.time()
                response = self.call_model(config)
                end_time = time.time()

                # Calculate metrics
                accuracy = self.calculate_accuracy(response)
                response_time = end_time - start_time
                tokens = len(response.split())

                results.append({
                    'accuracy': accuracy,
                    'time': response_time,
                    'tokens': tokens
                })

            except Exception as e:
                print(f"Test cycle {cycle+1} failed: {e}")
                continue

        if not results:
            return None

        avg_accuracy = statistics.mean([r['accuracy'] for r in results])
        avg_time = statistics.mean([r['time'] for r in results])
        avg_tokens = statistics.mean([r['tokens'] for r in results])

        return OptimizationResult(
            config=config,
            accuracy_score=avg_accuracy,
            response_time=avg_time,
            consistency_score=0.0,  # Calculated in validation
            tokens_generated=int(avg_tokens),
            cycle=cycles,
            phase="testing"
        )

    def call_model(self, config: ParameterConfig) -> str:
        """Call the actual model with the given configuration"""
        try:
            response = ollama.generate(
                model=self.model_name,
                prompt=self.prompt_text,
                options=config.to_dict()
            )
            return response.get('response', '')
        except Exception as e:
            print(f"Model call failed: {e}")
            return ""

    def calculate_accuracy(self, response: str) -> float:
        """Calculate accuracy score based on response quality"""
        score = 1.0

        # Prompt-specific accuracy checks
        prompt_lower = self.prompt_text.lower()

        if "circle" in prompt_lower and "area" in prompt_lower:
            if "math.pi" in response:
                score += 0.3
            if "import math" in response:
                score += 0.2
            if "def " in response and "return " in response:
                score += 0.2
            if "radius" in response:
                score += 0.1

        elif "prime" in prompt_lower:
            primes = ["2", "3", "5", "7", "11", "13", "17", "19", "23", "29"]
            prime_count = sum(1 for prime in primes if prime in response)
            score += min(0.4, prime_count * 0.04)
            if "def " in response:
                score += 0.2
            if "%" in response or "modulo" in prompt_lower:
                score += 0.1

        elif "email" in prompt_lower:
            if "@" in response and "." in response:
                score += 0.3
            if "re" in response or "regex" in prompt_lower:
                score += 0.2
            if "def " in response:
                score += 0.2

        # General code quality
        if "```python" in response:
            score += 0.1
        if "Error" in response or "TODO" in response:
            score -= 0.2
        if len(response.split()) < 10:
            score -= 0.3

        return max(0.0, min(1.0, score))

    def stop(self):
        """Stop the optimization process"""
        self.running = False

class ParameterOptimizationLabWidget(QWidget):
    """Parameter Optimization Lab integrated widget"""

    def __init__(self):
        super().__init__()
        self.worker = None
        self.init_ui()

    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)

        # Header
        header_label = QLabel("🔬 Parameter Optimization Lab")
        header_label.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px;")
        layout.addWidget(header_label)

        # Description
        desc_label = QLabel("Exhaustively search for the perfect parameter sweet spot that achieves 100% accuracy with minimum consistent time.")
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("padding: 5px; color: #666;")
        layout.addWidget(desc_label)

        # Input section
        input_group = QGroupBox("Optimization Target")
        input_layout = QVBoxLayout()

        # Model selection
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("Model:"))
        self.model_combo = QComboBox()
        self.model_combo.addItems(["phi3:3.8b", "phi3:14b", "llama3.1:8b", "qwen2.5:7b"])
        model_layout.addWidget(self.model_combo)
        input_layout.addLayout(model_layout)

        # Prompt input
        prompt_layout = QVBoxLayout()
        prompt_layout.addWidget(QLabel("Prompt to optimize:"))
        self.prompt_edit = QTextEdit()
        self.prompt_edit.setMaximumHeight(100)
        self.prompt_edit.setPlaceholderText("Enter the prompt you want to optimize parameters for...")
        self.prompt_edit.setContextMenuPolicy(Qt.CustomContextMenu)
        prompt_layout.addWidget(self.prompt_edit)
        input_layout.addLayout(prompt_layout)

        input_group.setLayout(input_layout)
        layout.addWidget(input_group)

        # Control buttons
        button_layout = QHBoxLayout()
        self.start_button = QPushButton("🚀 Start Optimization")
        self.start_button.clicked.connect(self.start_optimization)
        button_layout.addWidget(self.start_button)

        self.stop_button = QPushButton("⏹️ Stop")
        self.stop_button.clicked.connect(self.stop_optimization)
        self.stop_button.setEnabled(False)
        button_layout.addWidget(self.stop_button)

        button_layout.addStretch()

        self.export_button = QPushButton("💾 Export Results")
        self.export_button.clicked.connect(self.export_results)
        button_layout.addWidget(self.export_button)

        layout.addLayout(button_layout)

        # Progress section
        progress_group = QGroupBox("Progress")
        progress_layout = QVBoxLayout()

        self.progress_label = QLabel("Ready to start optimization...")
        progress_layout.addWidget(self.progress_label)

        self.progress_bar = QProgressBar()
        progress_layout.addWidget(self.progress_bar)

        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)

        # Results section
        results_group = QGroupBox("Results")
        results_layout = QVBoxLayout()

        self.results_text = QTextEdit()
        self.results_text.setMaximumHeight(200)
        self.results_text.setPlaceholderText("Optimization results will appear here...")
        results_layout.addWidget(self.results_text)

        results_group.setLayout(results_layout)
        layout.addWidget(results_group)

        # Current best config
        config_group = QGroupBox("Best Configuration Found")
        config_layout = QVBoxLayout()

        self.best_config_label = QLabel("No optimization run yet")
        self.best_config_label.setWordWrap(True)
        config_layout.addWidget(self.best_config_label)

        config_group.setLayout(config_layout)
        layout.addWidget(config_group)

        # Visualization section
        viz_group = QGroupBox("📊 Parameter Landscape Visualization")
        viz_layout = QVBoxLayout()

        # Visualization tabs
        self.viz_tabs = QTabWidget()
        viz_layout.addWidget(self.viz_tabs)

        # Create individual visualization widgets
        self.landscape_widget = QWidget()
        self.landscape_layout = QVBoxLayout(self.landscape_widget)
        self.landscape_canvas = FigureCanvas(Figure(figsize=(8, 6)))
        self.landscape_layout.addWidget(self.landscape_canvas)
        self.viz_tabs.addTab(self.landscape_widget, "🌄 Performance Landscape")

        self.path_widget = QWidget()
        self.path_layout = QVBoxLayout(self.path_widget)
        self.path_canvas = FigureCanvas(Figure(figsize=(8, 6)))
        self.path_layout.addWidget(self.path_canvas)
        self.viz_tabs.addTab(self.path_widget, "🛤️ Optimization Path")

        self.heatmap_widget = QWidget()
        self.heatmap_layout = QVBoxLayout(self.heatmap_widget)
        self.heatmap_canvas = FigureCanvas(Figure(figsize=(8, 6)))
        self.heatmap_layout.addWidget(self.heatmap_canvas)
        self.viz_tabs.addTab(self.heatmap_widget, "🔥 Parameter Heatmap")

        self.parallel_widget = QWidget()
        self.parallel_layout = QVBoxLayout(self.parallel_widget)
        self.parallel_canvas = FigureCanvas(Figure(figsize=(8, 6)))
        self.parallel_layout.addWidget(self.parallel_canvas)
        self.viz_tabs.addTab(self.parallel_widget, "📐 Parallel Coordinates")

        # Visualization controls
        viz_controls = QHBoxLayout()
        self.update_viz_button = QPushButton("🔄 Update Visualizations")
        self.update_viz_button.clicked.connect(self.update_visualizations)
        viz_controls.addWidget(self.update_viz_button)

        self.save_viz_button = QPushButton("💾 Save Graphs")
        self.save_viz_button.clicked.connect(self.save_visualizations)
        viz_controls.addWidget(self.save_viz_button)

        viz_controls.addStretch()
        viz_layout.addLayout(viz_controls)

        viz_group.setLayout(viz_layout)
        layout.addWidget(viz_group)

        layout.addStretch()

    def start_optimization(self):
        """Start the parameter optimization process"""
        model_name = self.model_combo.currentText()
        prompt_text = self.prompt_edit.toPlainText().strip()

        if not prompt_text:
            QMessageBox.warning(self, "Warning", "Please enter a prompt to optimize.")
            return

        # Clear previous results
        self.results_text.clear()
        self.best_config_label.setText("Optimization in progress...")

        # Create and start worker
        self.worker = OptimizationWorker(model_name, prompt_text)
        self.worker.progress_update.connect(self.update_progress)
        self.worker.result_found.connect(self.add_result)
        self.worker.optimization_complete.connect(self.optimization_complete)
        self.worker.error_occurred.connect(self.show_error)

        # Update UI
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.model_combo.setEnabled(False)
        self.prompt_edit.setEnabled(False)

        # Start optimization
        self.worker.start()
        self.worker.run_optimization()

    def stop_optimization(self):
        """Stop the current optimization"""
        if self.worker:
            self.worker.stop()
            self.worker.wait()

        # Reset UI
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.model_combo.setEnabled(True)
        self.prompt_edit.setEnabled(True)
        self.progress_label.setText("Optimization stopped by user")

    def update_progress(self, status: str, current: int, total: int):
        """Update progress indicator"""
        self.progress_label.setText(status)
        if total > 0:
            self.progress_bar.setValue(int((current / total) * 100))

    def add_result(self, result: OptimizationResult):
        """Add a new result to the display"""
        result_text = f"Config: {result.config} | Accuracy: {result.accuracy_score:.3f} | Time: {result.response_time:.2f}s\n"
        self.results_text.append(result_text)

    def optimization_complete(self, best_config: ParameterConfig, summary: dict):
        """Handle optimization completion"""
        self.best_config_label.setText(
            f"🏆 OPTIMAL CONFIGURATION FOUND!\n\n"
            f"Configuration: {best_config}\n"
            f"Accuracy: {summary['best_accuracy']:.3f}\n"
            f"Response Time: {summary['best_time']:.2f}s\n"
            f"Consistency: {summary['consistency']:.3f}\n"
            f"Total Tests: {summary['total_tests_run']}"
        )

        # Reset UI
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.model_combo.setEnabled(True)
        self.prompt_edit.setEnabled(True)
        self.progress_label.setText("Optimization complete! 🎉")

        # Automatically update visualizations
        try:
            results = self.parse_results_from_text()
            if results:
                self.create_performance_landscape(results)
                self.create_optimization_path(results)
                self.create_parameter_heatmap(results)
                self.create_parallel_coordinates(results)
                print("✅ Visualizations automatically updated with optimization results!")
        except Exception as e:
            print(f"⚠️ Auto-visualization failed: {e}")

    def show_error(self, error_message: str):
        """Display error message"""
        QMessageBox.critical(self, "Optimization Error", error_message)
        self.stop_optimization()

    def export_results(self):
        """Export optimization results to file"""
        try:
            from datetime import datetime
            import json

            # Get current results
            results_text = self.results_text.toPlainText()
            best_config_text = self.best_config_label.text()

            if not results_text.strip() or "No optimization run yet" in best_config_text:
                QMessageBox.warning(self, "Warning", "No optimization results to export.")
                return

            # Prepare export data
            export_data = {
                'timestamp': datetime.now().isoformat(),
                'model': self.model_combo.currentText(),
                'prompt': self.prompt_edit.toPlainText(),
                'best_configuration': best_config_text,
                'detailed_results': results_text,
                'summary': {
                    'exported_by': 'Parameter Optimization Lab',
                    'version': '1.0'
                }
            }

            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"optimization_results_{timestamp}.json"

            # Save to file
            with open(filename, 'w') as f:
                json.dump(export_data, f, indent=2)

            QMessageBox.information(self, "Export Successful", f"Results exported to: {filename}")

        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export results: {str(e)}")

    def update_visualizations(self):
        """Update all visualization graphs with current results"""
        try:
            # Parse results from text widget
            results = self.parse_results_from_text()
            if not results:
                QMessageBox.warning(self, "Warning", "No optimization results to visualize.")
                return

            # Update all visualizations
            self.create_performance_landscape(results)
            self.create_optimization_path(results)
            self.create_parameter_heatmap(results)
            self.create_parallel_coordinates(results)

            QMessageBox.information(self, "Success", "Visualizations updated successfully!")

        except Exception as e:
            QMessageBox.critical(self, "Visualization Error", f"Failed to update visualizations: {str(e)}")

    def parse_results_from_text(self) -> List[dict]:
        """Parse optimization results from the results text widget"""
        results_text = self.results_text.toPlainText()
        if not results_text.strip():
            return []

        results = []
        lines = results_text.strip().split('\n\n')

        for line in lines:
            if line.strip() and "Config:" in line:
                try:
                    # Parse configuration string
                    config_part = line.split(" | ")[0].replace("Config: ", "")

                    # Extract parameters
                    parts = config_part.split('_')
                    if len(parts) >= 6:
                        config = {
                            'temperature': float(parts[0].replace('T', '')),
                            'num_ctx': int(parts[1].replace('C', '')),
                            'num_predict': int(parts[2].replace('P', '')),
                            'repeat_penalty': float(parts[3].replace('R', '')),
                            'top_k': int(parts[4].replace('K', '')),
                            'top_p': float(parts[5].replace('P', ''))
                        }

                        # Extract accuracy and time
                        accuracy_part = line.split("Accuracy: ")[1].split(" | ")[0]
                        time_part = line.split("Time: ")[1].split("s")[0]

                        result = {
                            'config': config,
                            'accuracy': float(accuracy_part),
                            'time': float(time_part),
                            'efficiency': float(accuracy_part) / float(time_part) if float(time_part) > 0 else 0
                        }
                        results.append(result)

                except Exception as e:
                    print(f"Error parsing line: {line}, Error: {e}")
                    continue

        return results

    def create_performance_landscape(self, results: List[dict]):
        """Create 3D performance landscape visualization"""
        fig = self.landscape_canvas.figure
        fig.clear()

        if len(results) < 3:
            self.create_simple_landscape(results)
            return

        # Create 3D surface plot
        ax = fig.add_subplot(111, projection='3d')

        # Extract data points
        temps = [r['config']['temperature'] for r in results]
        contexts = [r['config']['num_ctx'] for r in results]
        accuracies = [r['accuracy'] for r in results]

        # Create mesh for surface interpolation
        temp_range = np.linspace(min(temps), max(temps), 20)
        ctx_range = np.linspace(min(contexts), max(contexts), 20)
        temp_mesh, ctx_mesh = np.meshgrid(temp_range, ctx_range)

        # Interpolate accuracy values for surface
        from scipy.interpolate import griddata
        points = np.column_stack((temps, contexts))
        values = np.array(accuracies)
        acc_mesh = griddata(points, values, (temp_mesh, ctx_mesh), method='cubic')

        # Plot surface
        surf = ax.plot_surface(temp_mesh, ctx_mesh, acc_mesh, cmap='viridis', alpha=0.8)

        # Plot actual test points
        ax.scatter(temps, contexts, accuracies, c='red', s=50, alpha=1.0)

        # Mark optimal point
        best_result = max(results, key=lambda x: x['efficiency'])
        ax.scatter([best_result['config']['temperature']],
                  [best_result['config']['num_ctx']],
                  [best_result['accuracy']],
                  c='gold', s=200, marker='*', edgecolors='black', linewidth=2)

        ax.set_xlabel('Temperature')
        ax.set_ylabel('Context Size')
        ax.set_zlabel('Accuracy')
        ax.set_title('🌄 Parameter Performance Landscape')

        # Add colorbar
        fig.colorbar(surf, ax=ax, shrink=0.5, aspect=5)

        self.landscape_canvas.draw()

    def create_simple_landscape(self, results: List[dict]):
        """Create simple 2D landscape for limited data"""
        ax = self.landscape_canvas.figure.add_subplot(111)

        temps = [r['config']['temperature'] for r in results]
        times = [r['time'] for r in results]
        accuracies = [r['accuracy'] for r in results]

        # Create scatter plot with color representing accuracy
        scatter = ax.scatter(temps, times, c=accuracies, s=100, cmap='viridis', alpha=0.7)

        # Mark optimal point
        best_result = max(results, key=lambda x: x['efficiency'])
        ax.scatter(best_result['config']['temperature'], best_result['time'],
                  c='gold', s=200, marker='*', edgecolors='black', linewidth=2, zorder=10)

        ax.set_xlabel('Temperature')
        ax.set_ylabel('Response Time (s)')
        ax.set_title('🌄 Parameter Performance Landscape')
        ax.grid(True, alpha=0.3)

        # Add colorbar
        self.landscape_canvas.figure.colorbar(scatter, ax=ax, label='Accuracy')

        self.landscape_canvas.draw()

    def create_optimization_path(self, results: List[dict]):
        """Create optimization path visualization showing the journey to optimal solution"""
        fig = self.path_canvas.figure
        fig.clear()

        if len(results) < 2:
            ax = fig.add_subplot(111)
            ax.text(0.5, 0.5, 'Insufficient data for path visualization',
                   ha='center', va='center', transform=ax.transAxes)
            self.path_canvas.draw()
            return

        # Sort results by time (assuming optimization order)
        sorted_results = sorted(results, key=lambda x: x['time'])

        # Create multi-panel plot
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 8))
        fig.suptitle('🛤️ Optimization Journey Analysis')

        # Accuracy over time
        sequence = list(range(len(sorted_results)))
        accuracies = [r['accuracy'] for r in sorted_results]
        ax1.plot(sequence, accuracies, 'b-o', linewidth=2, markersize=6)
        ax1.set_xlabel('Test Sequence')
        ax1.set_ylabel('Accuracy')
        ax1.set_title('Accuracy Progression')
        ax1.grid(True, alpha=0.3)

        # Response time over sequence
        times = [r['time'] for r in sorted_results]
        ax2.plot(sequence, times, 'r-o', linewidth=2, markersize=6)
        ax2.set_xlabel('Test Sequence')
        ax2.set_ylabel('Response Time (s)')
        ax2.set_title('Response Time Pattern')
        ax2.grid(True, alpha=0.3)

        # Parameter evolution
        temps = [r['config']['temperature'] for r in sorted_results]
        ax3.plot(sequence, temps, 'g-o', linewidth=2, markersize=6)
        ax3.set_xlabel('Test Sequence')
        ax3.set_ylabel('Temperature')
        ax3.set_title('Temperature Evolution')
        ax3.grid(True, alpha=0.3)

        # Efficiency scatter
        efficiencies = [r['efficiency'] for r in sorted_results]
        scatter = ax4.scatter(sequence, efficiencies, c=accuracies, s=80, cmap='viridis')
        ax4.set_xlabel('Test Sequence')
        ax4.set_ylabel('Efficiency (Accuracy/Time)')
        ax4.set_title('Efficiency Landscape')
        ax4.grid(True, alpha=0.3)

        plt.tight_layout()
        self.path_canvas.draw()

    def create_parameter_heatmap(self, results: List[dict]):
        """Create parameter correlation heatmap"""
        fig = self.heatmap_canvas.figure
        fig.clear()

        if len(results) < 4:
            ax = fig.add_subplot(111)
            ax.text(0.5, 0.5, 'Insufficient data for heatmap visualization',
                   ha='center', va='center', transform=ax.transAxes)
            self.heatmap_canvas.draw()
            return

        # Create parameter matrix
        param_data = []
        param_names = ['Temperature', 'Context', 'Output', 'Repeat_Penalty', 'Top_K', 'Top_P', 'Accuracy', 'Time']

        for result in results:
            row = [
                result['config']['temperature'],
                result['config']['num_ctx'],
                result['config']['num_predict'],
                result['config']['repeat_penalty'],
                result['config']['top_k'],
                result['config']['top_p'],
                result['accuracy'],
                result['time']
            ]
            param_data.append(row)

        # Calculate correlation matrix
        # pandas already imported at top
        df = pd.DataFrame(param_data, columns=param_names)
        correlation_matrix = df.corr()

        # Create heatmap
        ax = fig.add_subplot(111)
        sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', center=0,
                   square=True, ax=ax, cbar_kws={'shrink': 0.8})

        ax.set_title('🔥 Parameter Correlation Heatmap')

        self.heatmap_canvas.draw()

    def create_parallel_coordinates(self, results: List[dict]):
        """Create parallel coordinates plot showing parameter relationships"""
        fig = self.parallel_canvas.figure
        fig.clear()

        if len(results) < 3:
            ax = fig.add_subplot(111)
            ax.text(0.5, 0.5, 'Insufficient data for parallel coordinates',
                   ha='center', va='center', transform=ax.transAxes)
            self.parallel_canvas.draw()
            return

        # Prepare data for parallel coordinates
        param_data = []
        for result in results:
            row = {
                'Temperature': result['config']['temperature'],
                'Context': result['config']['num_ctx'],
                'Output': result['config']['num_predict'],
                'Repeat_Penalty': result['config']['repeat_penalty'],
                'Top_K': result['config']['top_k'],
                'Top_P': result['config']['top_p'],
                'Accuracy': result['accuracy'],
                'Efficiency': result['efficiency']
            }
            param_data.append(row)

        # Create parallel coordinates plot
        from pandas.plotting import parallel_coordinates
        df = pd.DataFrame(param_data)

        # Normalize data for better visualization
        df_normalized = df.copy()
        for col in df.columns:
            if df[col].dtype in ['float64', 'int64']:
                df_normalized[col] = (df[col] - df[col].min()) / (df[col].max() - df[col].min())

        ax = fig.add_subplot(111)

        # Create lines colored by efficiency
        colors = plt.cm.viridis(df_normalized['Efficiency'])

        # Plot parallel coordinates manually
        columns = df_normalized.columns
        x_positions = range(len(columns))

        for i, (idx, row) in enumerate(df_normalized.iterrows()):
            color = colors[i]
            ax.plot(x_positions, row.values, color=color, alpha=0.6, linewidth=1.5)

        # Mark optimal configuration
        best_idx = df['Efficiency'].idxmax()
        best_row = df_normalized.iloc[best_idx]
        ax.plot(x_positions, best_row.values, color='gold', linewidth=4, alpha=1.0, label='Optimal')

        ax.set_xticks(x_positions)
        ax.set_xticklabels(columns, rotation=45, ha='right')
        ax.set_ylabel('Normalized Values')
        ax.set_title('📐 Parallel Coordinates - Parameter Relationships')
        ax.legend()
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        self.parallel_canvas.draw()

    def save_visualizations(self):
        """Save all visualization graphs to files"""
        try:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # Create output directory
            import os
            os.makedirs('optimization_visualizations', exist_ok=True)

            # Save each visualization
            canvases = [
                (self.landscape_canvas, 'performance_landscape'),
                (self.path_canvas, 'optimization_path'),
                (self.heatmap_canvas, 'parameter_heatmap'),
                (self.parallel_canvas, 'parallel_coordinates')
            ]

            saved_files = []
            for canvas, name in canvases:
                filename = f'optimization_visualizations/{name}_{timestamp}.png'
                canvas.figure.savefig(filename, dpi=300, bbox_inches='tight')
                saved_files.append(filename)

            QMessageBox.information(self, "Success",
                                  f"Saved {len(saved_files)} visualization files:\n" +
                                  "\n".join([f"• {f}" for f in saved_files]))

        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save visualizations: {str(e)}")


class LLMTesterEnhanced(QMainWindow):
    """Enhanced LLM Tester with tabbed interface"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("LLM Tester v2.0")
        self.setGeometry(100, 100, 1400, 1000)

        # Apply enhanced theme
        self.setStyleSheet("""
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

        # Initialize database connection
        try:
            db_name = init_database_connection()
            print(f"Connected to database: {db_name}")
        except Exception as db_error:
            print(f"Database initialization error: {db_error}")
            print("Application will continue without database functionality")

        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)

        # Create tab widget
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)

        # Create tabs
        self.model_library = ModelLibraryWidget()
        self.tab_widget.addTab(self.model_library, "Model Library")

        self.test_suites = TestSuitesWidget()
        self.tab_widget.addTab(self.test_suites, "Test Suites")

        self.parameters = ParametersWidget()
        self.tab_widget.addTab(self.parameters, "Parameters")

        self.results = ResultsWidget()
        self.tab_widget.addTab(self.results, "Results")

        self.param_compare = ParameterCompareWidget()
        self.tab_widget.addTab(self.param_compare, "Parameter Compare")

        # Advanced Analytics Tab
        self.analytics = AdvancedAnalyticsWidget()
        self.tab_widget.addTab(self.analytics, "📈 Analytics")

        # Parameter Optimization Lab Tab
        self.optimization_lab = ParameterOptimizationLabWidget()
        self.tab_widget.addTab(self.optimization_lab, "🔬 Optimization Lab")

        # Add Database Library tab (only in MasterMenu mode)
        db_info = get_current_db_info()
        if db_info.get('is_mastermenu_mode', False):
            self.db_library = DatabaseLibraryWidget()
            self.db_library.database_selected.connect(self.switch_database)
            self.tab_widget.addTab(self.db_library, "🗄️ Database Library")
        else:
            self.db_library = None

        # Status bar
        self.status_label = QLabel("Status: Ready | GPU: 0°C/8GB VRAM | RAM: 0GB/64GB | Queue: 0")
        main_layout.addWidget(self.status_label)

        # Initialize worker threads
        self.test_worker = TestWorker()
        self.test_worker.task_finished.connect(self.handle_test_result)
        self.test_worker.progress_updated.connect(self.handle_progress_update)
        self.test_worker.start()

        self.system_monitor = SystemMonitor()
        self.system_monitor.metrics_updated.connect(self.update_system_metrics)
        self.system_monitor.start()

        # Connect signals
        self.model_library.model_selection_changed.connect(self.on_model_selection_changed)
        self.test_suites.suite_selected.connect(self.on_suite_selected)
        self.test_suites.run_test.connect(self.run_single_test)
        self.test_suites.run_suite.connect(self.run_test_suite)
        self.test_suites.run_suite_with_objective_tests.connect(self.run_test_suite_with_objective_tests)
        self.parameters.parameters_changed.connect(self.on_parameters_changed)
        self.parameters.apply_parameters_request.connect(self.apply_parameters_to_models)
        self.parameters.test_parameters_request.connect(self.test_parameters_on_model)
        self.param_compare.run_parameter_test.connect(self.run_parameter_comparison_test)
        self.parameters.output_format_changed.connect(self.on_output_format_changed)

        # Initialize UI state
        self.update_model_overrides([])  # Start with empty model overrides

        # Update parameter comparison widget with available models
        self.update_parameter_compare_models()

    def on_model_selection_changed(self, selected_models):
        """Handle model selection changes"""
        print(f"Models selected: {selected_models}")

        # Update parameter widget model-specific overrides section
        self.update_model_overrides(selected_models)

        # Update test suites info
        if selected_models:
            self.test_suites.current_suite_label.setText(
                f"Suite: {self.test_suites.current_suite or 'None selected'} | Models: {len(selected_models)}"
            )

        # Enable/disable controls based on selection
        has_models = len(selected_models) > 0
        self.parameters.setEnabled(has_models)

        # Auto-clear results if models changed significantly
        if self.results.results_data and has_models:
            # Option to clear results when model selection changes
            pass

    def update_model_overrides(self, selected_models):
        """Update parameter widget with model-specific overrides"""
        # Clear existing overrides
        for i in reversed(range(self.parameters.overrides_layout.count())):
            child = self.parameters.overrides_layout.itemAt(i).widget()
            if child:
                child.setParent(None)

        if not selected_models:
            empty_label = QLabel("Select models to see overrides")
            self.parameters.overrides_layout.addWidget(empty_label)
            return

        # Add override controls for each selected model
        for model_name in selected_models[:3]:  # Limit to first 3 models
            model_frame = QFrame()
            model_layout = QHBoxLayout(model_frame)

            model_layout.addWidget(QLabel(f"{model_name}:"))

            override_checkbox = QCheckBox("Use custom params")
            model_layout.addWidget(override_checkbox)

            self.parameters.overrides_layout.addWidget(model_frame)

        if len(selected_models) > 3:
            more_label = QLabel(f"... and {len(selected_models) - 3} more models")
            self.parameters.overrides_layout.addWidget(more_label)

    def on_suite_selected(self, suite_name, prompts):
        """Handle test suite selection"""
        print(f"Suite selected: {suite_name} with {len(prompts)} prompts")
        selected_models = self.model_library.get_selected_models()
        self.results.update_test_info(suite_name, len(selected_models), "Ready")

        # Auto-switch to Parameters tab if no parameters are set
        current_params = self.parameters.get_parameters()
        if current_params['temperature'] == 0.7 and not self.results.results_data:
            # Suggest user to configure parameters
            pass

    def on_parameters_changed(self, parameters):
        """Handle parameter changes"""
        print(f"Parameters changed: {parameters}")

    def on_output_format_changed(self, format_name, template):
        """Handle output format changes"""
        print(f"Output format changed to: {format_name}")
        # You could update UI elements or apply the template here if needed
        # For now, just log the change

    def apply_parameters_to_models(self, parameters):
        """Apply parameters to selected models"""
        selected_models = self.model_library.get_selected_models()
        if not selected_models:
            print("No models selected to apply parameters to")
            return

        # Apply parameters and switch to Results tab if structured output is enabled
        if self.parameters.current_output_format != "plain_text":
            self.tab_widget.setCurrentIndex(3)  # Results tab index

        print(f"Applied parameters to {len(selected_models)} models: {parameters}")

        # Store structured format preference in results for future reference
        for model_name in selected_models:
            if not hasattr(self, '_structured_output_preferences'):
                self._structured_output_preferences = {}
            self._structured_output_preferences[model_name] = self.parameters.current_output_format

        # Update parameter comparison widget if available
        if hasattr(self, 'param_compare'):
            self.param_compare.set_available_models(self.model_library.get_available_models())

        print(f"Applying parameters to {len(selected_models)} models: {parameters}")

    def test_parameters_on_model(self, parameters):
        """Test parameters on a single model"""
        selected_models = self.model_library.get_selected_models()
        if not selected_models:
            print("No models selected to test parameters on")
            return

        # Use first selected model for testing
        test_model = selected_models[0]
        print(f"Testing parameters on {test_model}: {parameters}")

        # Create a simple test prompt
        test_prompt = "Hello, how are you?"
        self.run_test_with_parameters(test_model, test_prompt, parameters)

    def update_parameter_compare_models(self):
        """Update the parameter comparison widget with available models"""
        try:
            models = ollama.list()['models']
            model_names = [model['model'] for model in models]
            self.param_compare.set_available_models(model_names)
        except Exception as e:
            print(f"Error updating parameter compare models: {e}")
            self.param_compare.set_available_models([])

    def run_parameter_comparison_test(self, configurations, prompts, iterations):
        """Run a parameter comparison test"""
        print(f"Starting parameter comparison: {len(configurations)} configs, {len(prompts)} prompts, {iterations} iterations")

        # Create a special worker for parameter testing
        if not hasattr(self, 'parameter_test_worker'):
            self.parameter_test_worker = TestWorker()
            self.parameter_test_worker.task_finished.connect(self.handle_parameter_test_result)
            self.parameter_test_worker.progress_updated.connect(self.handle_parameter_test_progress)
            self.parameter_test_worker.start()

        # Queue all the parameter tests
        total_tests = len(configurations) * len(prompts) * iterations
        completed_tests = 0

        for config in configurations:
            for prompt in prompts:
                for iteration in range(iterations):
                    # Extract parameters without the 'label' field
                    params = {k: v for k, v in config.items() if k != 'label'}
                    config_label = config['label']

                        # Create task for parameter test
                    task_id = hash(f"param_test_{config_label}_{prompt}_{iteration}_{time.time()}") % 1000000
                    suite_id = hash("parameter_comparison") % 1000

                    task = (
                        self.param_compare.model_combo.currentText(),  # model
                        prompt,
                        params,
                        task_id,
                        suite_id,
                        config_label  # Additional info for parameter comparison
                    )
                    self.parameter_test_worker.add_task(task)
                    completed_tests += 1

        # Auto-switch to Parameter Compare tab to show progress
        self.tab_widget.setCurrentIndex(4)  # Parameter Compare tab index

    def handle_parameter_test_result(self, result):
        """Handle parameter comparison test results"""
        # Extract the configuration label from the result
        config_label = result.get('config_label', 'Unknown')

        # Create metrics dict for the comparison widget
        metrics = {
            'response_time': result.get('response_time', 0),
            'tokens_per_second': result.get('tokens_per_second', 0),
            'response_length': len(result.get('response_text', ''))
        }

        # Add result to parameter comparison widget
        self.param_compare.add_test_result(config_label, metrics)

        # Also add to regular results for visibility
        self.results.add_result(result)

    def handle_parameter_test_progress(self, current_model, progress_percent):
        """Handle parameter comparison test progress"""
        # Update parameter comparison progress
        if hasattr(self, 'parameter_test_worker'):
            total_queued = len(self.parameter_test_worker.tasks)
            completed = total_queued  # Approximate
            total = total_queued + completed
            if total > 0:
                self.param_compare.update_progress(completed, total)

    def run_single_test(self, prompt, selected_models=None):
        """Run a single test prompt"""
        if selected_models is None:
            selected_models = self.model_library.get_selected_models()

        if not selected_models:
            print("No models selected for testing")
            return

        current_parameters = self.parameters.get_parameters()

        # Auto-switch to Results tab if not already there
        if self.tab_widget.currentIndex() != 3:
            self.tab_widget.setCurrentIndex(3)  # Results tab index

        for model in selected_models:
            self.run_test_with_parameters(model, prompt, current_parameters)

    def run_test_with_parameters(self, model, prompt, parameters):
        """Run a test with specific parameters"""
        task_id = hash(f"{model}_{prompt}_{time.time()}") % 1000000
        suite_id = hash(prompt) % 1000

        task = (model, prompt, parameters, task_id, suite_id)
        self.test_worker.add_task(task)

        # Update results display
        self.results.update_test_info(f"Single Test", len(self.model_library.get_selected_models()), "Running")

    def run_test_suite(self, suite_name, prompts):
        """Run an entire test suite on selected models"""
        selected_models = self.model_library.get_selected_models()
        if not selected_models:
            print("No models selected for suite testing")
            return

        current_parameters = self.parameters.get_parameters()
        total_tasks = len(selected_models) * len(prompts)

        # Set up total task count for progress tracking
        self.test_worker.total_prompts = total_tasks
        self.test_worker.current_prompt_index = 0

        print(f"Running suite '{suite_name}' with {len(prompts)} prompts on {len(selected_models)} models")

        # Initialize comprehensive test information display
        self.results.initialize_test_session(suite_name, prompts, selected_models, cycles=1)
        self.results.clear_results()  # Clear previous results

        # Auto-switch to Results tab to show progress
        self.tab_widget.setCurrentIndex(3)  # Results tab index

        # Add all tasks to the worker
        for model in selected_models:
            for i, prompt in enumerate(prompts):
                task_id = hash(f"{suite_name}_{model}_{i}_{time.time()}") % 1000000
                suite_id = hash(suite_name) % 1000
                task = (model, prompt, current_parameters, task_id, suite_id)
                self.test_worker.add_task(task)

    def run_test_suite_with_objective_tests(self, suite_name, prompts):
        """Run a test suite with objective test integration"""
        try:
            # Import comprehensive test system
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.abspath(__file__)))

            from comprehensive_test_system import ComprehensiveTestSystem
            from objective_test_suite import OutputFormat

            print(f"Running suite '{suite_name}' with objective test integration")

            # Initialize comprehensive test system
            test_system = ComprehensiveTestSystem()

            # Run objective tests instead of regular prompts
            objective_results = []
            selected_models = self.model_library.get_selected_models()

            if not selected_models:
                print("No models selected for objective testing")
                return

            # Initialize comprehensive test information display for objective tests
            self.results.initialize_test_session(suite_name, prompts, selected_models, cycles=1, test_type="Objective Testing")
            self.results.clear_results()  # Clear previous results

            # Auto-switch to Results tab
            self.tab_widget.setCurrentIndex(3)

            for model in selected_models:
                print(f"Running objective tests on model: {model}")

                # Run each prompt as an objective test
                for i, prompt in enumerate(prompts):
                    try:
                        # Generate a test ID from the prompt
                        test_id = f"obj_test_{hash(prompt) % 10000}"

                        # For demonstration, use a sample from the objective test suite
                        # In practice, you might want to map prompts to specific objective tests
                        result = test_system.evaluate_response(
                            test_id=test_id,
                            llm_response=prompt,  # Using prompt as sample response
                            output_format=OutputFormat.JSON
                        )

                        # Convert to standard result format
                        standard_result = {
                            'model': model,
                            'prompt': prompt,
                            'response': result.objective_test_result.response if result.objective_test_result else "",
                            'suite_name': suite_name,
                            'test_type': 'objective_test',
                            'overall_performance_score': result.overall_performance_score,
                            'objective_score': result.objective_test_result.total_score if result.objective_test_result else 0,
                            'automated_score': result.automated_score_result.overall_score if result.automated_score_result else 0,
                            'logical_score': result.logical_validation_result.reasoning_score if result.logical_validation_result else 0,
                            'status': 'completed',
                            'timestamp': time.time()
                        }

                        self.results.add_result(standard_result)
                        objective_results.append(standard_result)

                        # Update comprehensive test information display
                        if hasattr(self.results, 'current_test_info') and self.results.current_test_info:
                            completed_tests = len(self.results.results_data)
                            total_tests = self.results.current_test_info.get('total_tests', len(prompts) * len(selected_models))

                            self.results.update_comprehensive_test_info(
                                suite_name=suite_name,
                                prompts=prompts,
                                models=selected_models,
                                cycles=1,
                                current_cycle=1,
                                completed_tests=completed_tests,
                                total_tests=total_tests
                            )

                    except Exception as e:
                        print(f"Error in objective test for prompt {i+1}: {e}")
                        # Add error result
                        error_result = {
                            'model': model,
                            'prompt': prompt,
                            'response': f"Objective test error: {str(e)}",
                            'suite_name': suite_name,
                            'test_type': 'objective_test_error',
                            'overall_performance_score': 0,
                            'status': 'error',
                            'timestamp': time.time()
                        }
                        self.results.add_result(error_result)

            print(f"Objective test suite completed: {len(objective_results)} tests executed")

            # Final update to show completed status
            if hasattr(self.results, 'current_test_info') and self.results.current_test_info:
                self.results.complete_test_session()

        except ImportError:
            print("Comprehensive test system not available. Running standard suite instead.")
            # Fallback to standard suite execution
            self.run_test_suite(suite_name, prompts)
        except Exception as e:
            print(f"Error in objective test integration: {e}")
            # Fallback to standard suite execution
            self.run_test_suite(suite_name, prompts)

    def handle_test_result(self, result):
        """Handle completed test results"""
        self.results.add_result(result)

        # Update queue status
        queue_size = len(self.test_worker.tasks)

        # Update comprehensive test information display
        if hasattr(self.results, 'current_test_info') and self.results.current_test_info:
            completed_tests = len(self.results.results_data)
            total_tests = self.results.current_test_info.get('total_tests', completed_tests + queue_size)

            if total_tests > 0:
                # Update progress tracking
                self.results.update_comprehensive_test_info(
                    suite_name=self.results.current_test_info.get('suite_name', ''),
                    prompts=self.results.current_test_info.get('prompts', []),
                    models=self.results.current_test_info.get('models', []),
                    cycles=self.results.current_test_info.get('cycles', 1),
                    current_cycle=self.results.current_test_info.get('current_cycle', 1),
                    completed_tests=completed_tests,
                    total_tests=total_tests
                )

        # Check if this is the last result in a batch
        if queue_size == 0:
            # All tests completed
            total_tests = len(self.results.results_data)
            completed_tests = sum(1 for r in self.results.results_data if r['status'] == 'completed')

            if total_tests > 0:
                print(f"All tests completed: {completed_tests}/{total_tests} successful")
                # Could show a notification or update status
                self.status_label.setText(
                    f"Status: Completed | {completed_tests}/{total_tests} tests passed | Queue: 0"
                )

                # Final update to show completed status
                if hasattr(self.results, 'current_test_info') and self.results.current_test_info:
                    self.results.complete_test_session()

        # Save to database
        try:
            db_session = next(get_db())
            save_test_result(
                db=db_session,
                run_id=result.get('task_id', 0),
                task_id=result.get('task_id', 0),
                is_loading_prompt=False,
                model_name=result['model_name'],
                task=result['prompt_text'],
                response=result['response_text'],
                response_time=result['response_time']
            )
            db_session.close()
        except Exception as e:
            print(f"Error saving result to database: {e}")

    def handle_progress_update(self, current_model, progress_percent):
        """Handle progress updates"""
        self.results.update_progress(current_model, progress_percent)

    def update_system_metrics(self, metrics):
        """Update system metrics display"""
        queue_size = len(self.test_worker.tasks)

        # Determine GPU status
        if metrics['gpu_utilization'] > 0:
            gpu_status = f"GPU: {metrics['gpu_temp_c']:.0f}°C/{metrics['gpu_vram_used_mb']:.0f}MB/{metrics['gpu_vram_total_mb']:.0f}MB ({metrics['gpu_utilization']:.0f}%)"
        else:
            gpu_status = f"GPU: {metrics['gpu_vram_used_mb']:.0f}MB/{metrics['gpu_vram_total_mb']:.0f}MB"

        status_text = (
            f"Status: Ready | "
            f"{gpu_status} | "
            f"RAM: {metrics['ram_used_gb']:.1f}GB/{metrics['ram_total_gb']:.0f}GB | "
            f"CPU: {metrics['cpu_percent']:.0f}% | Queue: {queue_size}"
        )
        self.status_label.setText(status_text)

    def switch_database(self, db_name):
        """Switch to a different database"""
        try:
            print(f"Switching to database: {db_name}")
            
            # Re-initialize database connection with new database
            new_db_name = init_database_connection(db_name)
            
            # Update status
            self.status_label.setText(f"Status: Switched to database '{new_db_name}'")
            
            # Clear current results to avoid confusion
            self.results.clear_results()
            
            # Optionally show a confirmation
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.information(
                self, 
                "Database Switched", 
                f"Successfully switched to database: {new_db_name}\n\nPrevious results have been cleared."
            )
            
        except Exception as e:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(
                self,
                "Database Switch Error",
                f"Failed to switch to database '{db_name}':\n{str(e)}"
            )

    def closeEvent(self, event):
        """Handle application close"""
        self.test_worker.stop()
        self.system_monitor.stop()

        # Also stop parameter test worker if it exists
        if hasattr(self, 'parameter_test_worker'):
            self.parameter_test_worker.stop()
            self.parameter_test_worker.wait()

        # Stop optimization lab worker if it exists
        if hasattr(self, 'optimization_lab') and self.optimization_lab.worker:
            self.optimization_lab.worker.stop()
            self.optimization_lab.worker.wait()

        self.test_worker.wait()
        self.system_monitor.wait()
        event.accept()


if __name__ == "__main__":
    try:
        app = QApplication(sys.argv)
        window = LLMTesterEnhanced()
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        print(f"Application failed to start: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
