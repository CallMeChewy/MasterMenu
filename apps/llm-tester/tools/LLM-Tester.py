import sys
import ollama
import time
import json
from PySide6.QtCore import QThread, Signal, Qt
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTreeWidget, QTreeWidgetItem, QTextEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QLabel, QSpinBox, QSplitter, QScrollArea
)
from database import init_db, get_db, save_test_result
import queue

class Worker(QThread):
    task_finished = Signal(object)

    def __init__(self):
        super().__init__()
        self.tasks = []
        self.running = True

    def run(self):
        while self.running:
            if self.tasks:
                model_name, task, is_loading_prompt, task_id, run_id = self.tasks.pop(0)
                try:
                    start_time = time.time()
                    response = ollama.generate(model=model_name, prompt=task)
                    end_time = time.time()
                    response_time = end_time - start_time

                    if response_time > 600: # 10 minutes timeout
                        self.task_finished.emit(("Timeout", 999, model_name, task, is_loading_prompt, task_id, run_id))
                        continue

                    self.task_finished.emit((response, response_time, model_name, task, is_loading_prompt, task_id, run_id))
                except Exception as e:
                    self.task_finished.emit((e, 0, model_name, task, is_loading_prompt, task_id, run_id))
                finally:
                    time.sleep(1) # Add a 1-second delay
            else:
                self.msleep(100) # Sleep if no tasks

    def add_task(self, task):
        self.tasks.append(task)

    def stop(self):
        self.running = False

class DatabaseWorker(QThread):
    def __init__(self):
        super().__init__()
        self.queue = queue.Queue()
        self.running = True

    def run(self):
        while self.running:
            try:
                data = self.queue.get(timeout=1) # Timeout to allow checking self.running
                db_session = next(get_db())
                save_test_result(
                    db=db_session,
                    run_id=data['run_id'],
                    task_id=data['task_id'],
                    is_loading_prompt=data['is_loading_prompt'],
                    model_name=data['model_name'],
                    task=data['task'],
                    response=data['response'],
                    response_time=data['response_time']
                )
                db_session.close()
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Database worker error: {e}")

    def save_result(self, data):
        self.queue.put(data)

    def stop(self):
        self.running = False

class LLMTester(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LLM Tester")
        self.setGeometry(100, 100, 1600, 900)
        self.model_times = {}

        # Apply a gradient blue theme
        self.setStyleSheet("""
            QMainWindow {
                background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                                  stop: 0 #2c3e50, stop: 1 #3498db);
            }
            QWidget {
                font-size: 14pt;
            }
            QSplitter::handle {
                background-color: #3498db;
            }
            QSplitter::handle:vertical {
                height: 5px;
            }
        """)

        # Init DB
        init_db()

        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)

        # --- Top Layout: Model Selection & Tasks --- #
        top_splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(top_splitter)

        # Model Selection (Left Side)
        model_widget = QWidget()
        model_layout = QVBoxLayout(model_widget)
        model_layout.addWidget(QLabel("Select Models:"))
        self.model_tree = QTreeWidget()
        self.model_tree.setColumnCount(4)
        self.model_tree.setHeaderLabels(["Model", "Size (GB)", "Fastest", "Slowest"])
        self.populate_models()
        model_layout.addWidget(self.model_tree)

        model_selection_buttons_layout = QHBoxLayout()
        model_layout.addLayout(model_selection_buttons_layout)
        select_all_button = QPushButton("Select All")
        select_all_button.clicked.connect(self.select_all_models)
        model_selection_buttons_layout.addWidget(select_all_button)
        deselect_all_button = QPushButton("Deselect All")
        deselect_all_button.clicked.connect(self.deselect_all_models)
        model_selection_buttons_layout.addWidget(deselect_all_button)

        left_scroll_area = QScrollArea()
        left_scroll_area.setWidgetResizable(True)
        left_scroll_area.setWidget(model_widget)
        top_splitter.addWidget(left_scroll_area)

        # Task Inputs (Right Side)
        tasks_widget = QWidget()
        tasks_layout = QVBoxLayout(tasks_widget)
        tasks_layout.addWidget(QLabel("Coding Tasks:"))
        self.tasks_splitter = QSplitter(Qt.Vertical)
        tasks_layout.addWidget(self.tasks_splitter)
        self.task_inputs = []
        for i in range(10):
            task_input = QTextEdit()
            self.tasks_splitter.addWidget(task_input)
            self.task_inputs.append(task_input)

        right_scroll_area = QScrollArea()
        right_scroll_area.setWidgetResizable(True)
        right_scroll_area.setWidget(tasks_widget)
        top_splitter.addWidget(right_scroll_area)

        top_splitter.setSizes([self.width() // 2, self.width() // 2])


        # --- Controls --- #
        control_layout = QHBoxLayout()
        main_layout.addLayout(control_layout)
        
        control_layout.addWidget(QLabel("Cycles:"))
        self.cycles_spinbox = QSpinBox()
        self.cycles_spinbox.setMinimum(1)
        self.cycles_spinbox.setValue(1)
        control_layout.addWidget(self.cycles_spinbox)

        self.run_button = QPushButton("Run Tests")
        self.run_button.clicked.connect(self.run_tests)
        control_layout.addWidget(self.run_button)

        self.save_selections_button = QPushButton("Save Selections")
        self.save_selections_button.clicked.connect(self.save_selections)
        control_layout.addWidget(self.save_selections_button)

        # --- Results Table --- #
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(3)
        self.results_table.setHorizontalHeaderLabels(["Model", "Response", "Response Time (s)"])
        self.results_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.results_table.setColumnWidth(0, 200)
        main_layout.addWidget(self.results_table)

        self.load_selections()

        # --- Worker Threads --- #
        self.worker_thread = Worker()
        self.worker_thread.task_finished.connect(self.handle_test_result)
        self.worker_thread.start()

        self.db_worker = DatabaseWorker()
        self.db_worker.start()

    def populate_models(self):
        try:
            models = ollama.list()['models']
            for model in models:
                item = QTreeWidgetItem(self.model_tree)
                item.setText(0, model['model'])
                size_gb = model['size'] / (1024**3)
                item.setText(1, f"{size_gb:.2f}")
                item.setText(2, "N/A")
                item.setText(3, "N/A")
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                item.setCheckState(0, Qt.Unchecked)
                self.model_times[model['model']] = {'fastest': float('inf'), 'slowest': 0}
        except Exception as e:
            print(f"Error getting models: {e}")

    def select_all_models(self):
        for i in range(self.model_tree.topLevelItemCount()):
            item = self.model_tree.topLevelItem(i)
            item.setCheckState(0, Qt.Checked)

    def deselect_all_models(self):
        for i in range(self.model_tree.topLevelItemCount()):
            item = self.model_tree.topLevelItem(i)
            item.setCheckState(0, Qt.Unchecked)

    def run_tests(self):
        tasks = [task_input.toPlainText() for task_input in self.task_inputs]
        num_cycles = self.cycles_spinbox.value()

        selected_models = []
        for i in range(self.model_tree.topLevelItemCount()):
            item = self.model_tree.topLevelItem(i)
            if item.checkState(0) == Qt.Checked:
                selected_models.append(item.text(0))

        if not selected_models or not any(tasks):
            return

        self.run_button.setEnabled(False)
        
        run_id = int(time.time())
        loading_prompt = "Print the word 'Ready'. perform no action."

        for _ in range(num_cycles):
            for model_name in selected_models:
                # Add loading prompt
                self.worker_thread.add_task((model_name, loading_prompt, True, 0, run_id))
                # Add other tasks
                for i, task in enumerate(tasks):
                    if task:
                        self.worker_thread.add_task((model_name, task, False, i + 1, run_id))

    def handle_test_result(self, result):
        response, response_time, model_name, task, is_loading_prompt, task_id, run_id = result

        if response == "Timeout":
            self.model_times[model_name]['fastest'] = 999
            self.model_times[model_name]['slowest'] = 999
        elif isinstance(response, Exception):
            print(f"Error running test: {response}")
        else:
            response_text = response['response']

            row_position = self.results_table.rowCount()
            self.results_table.insertRow(row_position)

            self.results_table.setItem(row_position, 0, QTableWidgetItem(model_name))
            self.results_table.setItem(row_position, 1, QTableWidgetItem(response_text))
            self.results_table.setItem(row_position, 2, QTableWidgetItem(f"{response_time:.4f}"))

            # Update fast/slow times
            if not is_loading_prompt:
                if response_time < self.model_times[model_name]['fastest']:
                    self.model_times[model_name]['fastest'] = response_time
                if response_time > self.model_times[model_name]['slowest']:
                    self.model_times[model_name]['slowest'] = response_time

            # Auto-save result
            self.db_worker.save_result({
                'run_id': run_id,
                'task_id': task_id,
                'is_loading_prompt': is_loading_prompt,
                'model_name': model_name,
                'task': task,
                'response': response_text,
                'response_time': response_time
            })
        
        # Update UI
        for i in range(self.model_tree.topLevelItemCount()):
            item = self.model_tree.topLevelItem(i)
            if item.text(0) == model_name:
                item.setText(2, f"{self.model_times[model_name]['fastest']:.4f}" if self.model_times[model_name]['fastest'] != float('inf') else "N/A")
                item.setText(3, f"{self.model_times[model_name]['slowest']:.4f}" if self.model_times[model_name]['slowest'] != 0 else "N/A")

        if not self.worker_thread.tasks:
            self.run_button.setEnabled(True)

    def save_selections(self):
        selected_models = []
        for i in range(self.model_tree.topLevelItemCount()):
            item = self.model_tree.topLevelItem(i)
            if item.checkState(0) == Qt.Checked:
                selected_models.append(item.text(0))
        
        tasks = [task_input.toPlainText() for task_input in self.task_inputs]
        
        data = {
            "selected_models": selected_models,
            "tasks": tasks
        }
        
        with open("defaults.json", "w") as f:
            json.dump(data, f)

    def load_selections(self):
        try:
            with open("defaults.json", "r") as f:
                data = json.load(f)

            if isinstance(data, list):
                # Old format, just a list of models
                selected_models = data
                tasks = []
            else:
                # New format, a dictionary
                selected_models = data.get("selected_models", [])
                tasks = data.get("tasks", [])

            for i in range(self.model_tree.topLevelItemCount()):
                item = self.model_tree.topLevelItem(i)
                if item.text(0) in selected_models:
                    item.setCheckState(0, Qt.Checked)
            
            for i, task in enumerate(tasks):
                if i < len(self.task_inputs):
                    self.task_inputs[i].setPlainText(task)

        except FileNotFoundError:
            pass # No defaults saved yet

    def closeEvent(self, event):
        self.worker_thread.stop()
        self.worker_thread.wait()
        self.db_worker.stop()
        self.db_worker.wait()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LLMTester()
    window.show()
    sys.exit(app.exec())