#!/usr/bin/env python3
"""
Simple PySide6 Backup Explorer - Basic version that should work reliably
"""

import sys
import os
import json
import re
import subprocess
import shutil
import tempfile
from datetime import datetime
from pathlib import Path

REPO_ENV_VAR = "PIKAPEEK_REPO_PATH"
DEFAULT_REPO_PATH = os.environ.get("PIKAPEEK_DEFAULT_REPO", "")
REPO_SEARCH_ROOT = os.environ.get("PIKAPEEK_REPO_ROOT", "/media")
DATE_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}$")
BORG_LIST_TIMEOUT = int(os.environ.get("PIKAPEEK_LIST_TIMEOUT", "0"))
BORG_EXTRACT_TIMEOUT = int(os.environ.get("PIKAPEEK_EXTRACT_TIMEOUT", "0"))


def resolve_repo_path():
    """Return the repository path to use for Borg operations."""
    env_path = os.environ.get(REPO_ENV_VAR)
    if env_path:
        resolved = os.path.abspath(os.path.expanduser(env_path))
        if os.path.isdir(resolved):
            return resolved
        print(f"Warning: {REPO_ENV_VAR} points to missing path: {resolved}", file=sys.stderr)
    discovered = discover_repositories()
    if discovered:
        return discovered[0]
    fallback = os.path.abspath(os.path.expanduser(DEFAULT_REPO_PATH)) if DEFAULT_REPO_PATH else DEFAULT_REPO_PATH
    return fallback


def format_timestamp(value: str) -> str:
    """Format ISO timestamps into a concise display string."""
    if not value:
        return "Unknown"
    try:
        return datetime.fromisoformat(value).strftime("%Y-%m-%d %H:%M")
    except ValueError:
        return value


def format_size(size: int) -> str:
    """Return a human readable size string."""
    try:
        size = int(size)
    except (TypeError, ValueError):
        return "Unknown"

    if size < 1024:
        return f"{size} B"
    if size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    if size < 1024 * 1024 * 1024:
        return f"{size / (1024 * 1024):.1f} MB"
    return f"{size / (1024 * 1024 * 1024):.1f} GB"


def discover_repositories() -> list[str]:
    """Find backup repositories under the media root."""
    candidates = set()

    if not os.path.isdir(REPO_SEARCH_ROOT):
        return []

    for current_root, dirnames, _ in os.walk(REPO_SEARCH_ROOT):
        depth = os.path.relpath(current_root, REPO_SEARCH_ROOT).count(os.sep)
        if depth > 4:
            dirnames[:] = []
            continue

        for dirname in list(dirnames):
            full_path = os.path.join(current_root, dirname)
            if "pika" not in full_path.lower():
                continue
            if DATE_PATTERN.search(dirname) and os.path.isdir(full_path):
                candidates.add(os.path.normpath(full_path))

    return sorted(candidates)

try:
    from PySide6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QListWidget, QListWidgetItem, QTableWidget, QTableWidgetItem, QLabel, QPushButton,
        QComboBox, QMessageBox, QSplitter, QAbstractItemView, QGroupBox, QLineEdit,
        QPlainTextEdit, QCheckBox, QFileDialog
    )
    from PySide6.QtCore import Qt, QThread, Signal, QTimer
except ImportError:
    print("PySide6 not available. Please install with: pip install PySide6")
    sys.exit(1)

class SimpleBackupWorker(QThread):
    """Simple worker for basic operations"""
    result_ready = Signal(str, object, object)  # operation, result, context
    
    def __init__(self, operation, repo_path, *args, **kwargs):
        super().__init__()
        self.operation = operation
        self.repo_path = repo_path
        self.args = args
        self.kwargs = kwargs
    
    def run(self):
        try:
            if self.operation == "list_archives":
                result = self.list_archives()
                self.result_ready.emit("list_archives", result, None)
            elif self.operation == "list_directory":
                archive, path = self.args
                result = self.list_directory(archive, path)
                self.result_ready.emit("list_directory", result, {"archive": archive, "path": path})
            elif self.operation == "summarize_subtree":
                archive, path = self.args
                result = self.summarize_subtree(archive, path)
                self.result_ready.emit("summarize_subtree", result, {"archive": archive, "path": path})
            elif self.operation == "extract_items":
                payload = self.kwargs
                result = self.extract_items(**payload)
                self.result_ready.emit("extract_items", result, payload)
        except Exception as e:
            self.result_ready.emit(self.operation, f"Error: {e}", None)
    
    def list_archives(self):
        """Get backup archives"""
        try:
            result = subprocess.run(
                ['bash', '-c', f'echo "y" | borg list "{self.repo_path}"'],
                capture_output=True,
                text=True,
                check=False,
                timeout=(BORG_LIST_TIMEOUT or None)
            )
            
            if result.returncode != 0:
                return f"Error: {result.stderr}"
            
            archives = []
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 4:
                        archives.append({
                            'name': parts[0],
                            'date': f"{parts[2]} {parts[3]}"
                        })
            
            return list(reversed(archives))  # Most recent first
            
        except Exception as e:
            return f"Error: {e}"
    
    def list_directory(self, archive: str, path: str):
        """List the immediate contents of a path in a Borg archive."""
        archive_ref = f"{self.repo_path}::{archive}"
        target_path = path.strip('/')
        cmd = ['borg', 'list', '--json-lines', archive_ref]
        if target_path:
            cmd.append(target_path)

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
            timeout=(BORG_LIST_TIMEOUT or None)
        )

        if result.returncode != 0:
            stderr = result.stderr.strip() or "Unknown borg list error"
            return f"Error: {stderr}"

        items = []
        seen = set()
        prefix = target_path
        for line in result.stdout.splitlines():
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue

            entry_path = data.get('path', '')
            if not entry_path:
                continue

            if prefix:
                if not entry_path.startswith(prefix):
                    continue
                relative = entry_path[len(prefix):].lstrip('/')
            else:
                relative = entry_path

            if not relative:
                continue

            name = relative.split('/', 1)[0]
            if name in seen:
                continue
            seen.add(name)

            if name.startswith('.'):
                continue

            entry_type = data.get('type', '')
            is_dir = entry_type == 'd'
            size = 'Folder' if is_dir else format_size(data.get('size', 0))
            date = format_timestamp(data.get('mtime'))

            items.append({
                'name': name,
                'is_dir': is_dir,
                'size': size,
                'date': date,
                'archive_path': '/'.join(filter(None, [target_path, name]))
            })

        items.sort(key=lambda entry: (not entry['is_dir'], entry['name'].lower()))
        return items

    def summarize_subtree(self, archive: str, path: str):
        """Return counts and approximate size for a subtree."""
        archive_ref = f"{self.repo_path}::{archive}"
        target_path = path.strip('/')
        cmd = ['borg', 'list', '--json-lines', archive_ref]
        if target_path:
            cmd.append(target_path)

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
            timeout=(BORG_LIST_TIMEOUT or None)
        )

        if result.returncode != 0:
            stderr = result.stderr.strip() or "Unknown borg list error"
            return f"Error: {stderr}"

        files = 0
        dirs = 0
        size_bytes = 0
        for line in result.stdout.splitlines():
            if not line:
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue

            entry_type = data.get('type')
            if entry_type == 'd':
                dirs += 1
            else:
                files += 1
            size_bytes += int(data.get('size', 0))

        return {
            'files': files,
            'directories': dirs,
            'size_bytes': size_bytes,
        }

    def extract_items(self, archive: str, paths, destination: str):
        """Extract selected paths from an archive into a destination directory."""
        archive_ref = f"{self.repo_path}::{archive}"
        extracted = []
        errors = []

        for path in paths:
            relative = path.strip('/')
            if not relative:
                errors.append("Cannot extract the archive root")
                continue

            parts = relative.split('/')
            strip_components = max(0, len(parts) - 1)
            base_name = parts[-1]

            with tempfile.TemporaryDirectory() as temp_dir:
                cmd = ['borg', 'extract']
                if strip_components:
                    cmd.extend(['--strip-components', str(strip_components)])
                cmd.append(archive_ref)
                cmd.append(relative)

                result = subprocess.run(
                    cmd,
                    cwd=temp_dir,
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=(BORG_EXTRACT_TIMEOUT or None)
                )

                if result.returncode != 0:
                    stderr = result.stderr.strip() or f"Failed to extract {relative}"
                    errors.append(stderr)
                    continue

                extracted_path = os.path.join(temp_dir, base_name)
                if not os.path.exists(extracted_path):
                    errors.append(f"Extracted item not found: {base_name}")
                    continue

                dest_path = self._unique_destination(destination, base_name)
                try:
                    shutil.move(extracted_path, dest_path)
                    extracted.append(dest_path)
                except Exception as err:
                    errors.append(f"Copy failed for {base_name}: {err}")

        return {'extracted': extracted, 'errors': errors}

    @staticmethod
    def _unique_destination(destination: str, base_name: str) -> str:
        """Return a destination path that does not clobber existing files."""
        target = os.path.join(destination, base_name)
        if not os.path.exists(target):
            return target

        name, ext = os.path.splitext(base_name)
        counter = 1
        while True:
            candidate = os.path.join(destination, f"{name}_{counter}{ext}")
            if not os.path.exists(candidate):
                return candidate
            counter += 1


class SubtreeRestoreWorker(QThread):
    """Restore an entire archive subtree to a destination."""

    progress = Signal(str)
    finished = Signal(bool, str, dict)

    def __init__(self, repo_path: str, archive: str, source_path: str, destination_root: str, allow_overwrite: bool):
        super().__init__()
        self.repo_path = repo_path
        self.archive = archive
        self.source_path = source_path.strip('/')
        self.destination_root = destination_root
        self.allow_overwrite = allow_overwrite

    def run(self):
        try:
            if not self.source_path:
                self.finished.emit(False, "A source path must be provided", {})
                return

            archive_ref = f"{self.repo_path}::{self.archive}"
            parts = self.source_path.split('/')
            base_name = parts[-1]
            strip_components = max(0, len(parts) - 1)

            destination_root = os.path.abspath(os.path.expanduser(self.destination_root))
            if not os.path.isdir(destination_root):
                self.finished.emit(False, f"Destination not found: {destination_root}", {})
                return

            dest_path = os.path.join(destination_root, base_name)
            if os.path.exists(dest_path):
                if self.allow_overwrite:
                    try:
                        if os.path.isdir(dest_path):
                            shutil.rmtree(dest_path)
                        else:
                            os.remove(dest_path)
                    except Exception as err:
                        self.finished.emit(False, f"Failed to remove existing destination: {err}", {})
                        return
                else:
                    dest_path = SimpleBackupWorker._unique_destination(destination_root, base_name)

            file_count = 0
            with tempfile.TemporaryDirectory() as temp_dir:
                cmd = ['borg', 'extract', '--list']
                if strip_components:
                    cmd.extend(['--strip-components', str(strip_components)])
                cmd.append(archive_ref)
                cmd.append(self.source_path)

                process = subprocess.Popen(
                    cmd,
                    cwd=temp_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1
                )

                for line in process.stdout or []:
                    line = line.rstrip()
                    if line:
                        file_count += 1
                        self.progress.emit(line)

                process.wait()

                if process.returncode != 0:
                    message = f"Restore failed with exit code {process.returncode}"
                    self.finished.emit(False, message, {'files': file_count})
                    return

                extracted_path = os.path.join(temp_dir, base_name)
                if not os.path.exists(extracted_path):
                    self.finished.emit(False, f"Restored content not found: {base_name}", {'files': file_count})
                    return

                try:
                    shutil.move(extracted_path, dest_path)
                except Exception as err:
                    self.finished.emit(False, f"Failed to move restored data: {err}", {'files': file_count})
                    return

            self.finished.emit(True, f"Restored to {dest_path}", {'files': file_count, 'destination': dest_path})

        except Exception as err:
            self.finished.emit(False, f"Restore error: {err}", {})


class SimplePikaExplorer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.repo_path = resolve_repo_path()
        if not os.path.isdir(self.repo_path):
            QMessageBox.critical(self, "Repository Missing", f"Backup repository not found:\n{self.repo_path}")
            raise SystemExit(1)
        self.available_repos = discover_repositories()
        if self.repo_path not in self.available_repos:
            self.available_repos.insert(0, self.repo_path)
        if not self.available_repos:
            self.available_repos.append(self.repo_path)
        default_recovery = os.environ.get("OUTPUT_ROOT")
        if not default_recovery:
            default_recovery = Path.home() / "Desktop" / "RecoveredFiles"
        self.recovery_path = os.environ.get("PIKAPEEK_RECOVERY_PATH", str(default_recovery))

        default_temp = os.environ.get("TMP_ROOT")
        if not default_temp:
            default_temp = Path.home() / "Desktop" / "TempPreview"
        self.temp_path = os.environ.get("PIKAPEEK_TEMP_PATH", str(default_temp))
        self.current_archive = None
        self.current_path = None
        default_home_prefix = Path.home().as_posix().lstrip('/')
        self.home_prefix = os.environ.get("PIKAPEEK_HOME_PREFIX", default_home_prefix)
        self.is_extracting = False
        self.active_workers: list[SimpleBackupWorker] = []
        self.restore_worker: SubtreeRestoreWorker | None = None
        
        # Create directories
        os.makedirs(self.recovery_path, exist_ok=True)
        os.makedirs(self.temp_path, exist_ok=True)
        
        self.init_ui()
        self.load_archives()

    def init_ui(self):
        """Initialize simple UI"""
        self.setWindowTitle("🐭 Simple Pika Backup Explorer")
        self.setGeometry(100, 100, 1000, 700)
        
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2E3440;
            }
            QLabel, QSplitter {
                color: #ECEFF4;
                background-color: transparent;
            }
            QComboBox, QPushButton {
                color: #ECEFF4;
                background-color: #3B4252;
                border: 1px solid #4C566A;
            }
            QPushButton:hover {
                background-color: #4C566A;
            }
            QPushButton:pressed {
                background-color: #5E81AC;
            }
            QListWidget, QTableWidget {
                color: #ECEFF4;
                background-color: #3B4252;
                border: 1px solid #4C566A;
            }
            QHeaderView::section {
                color: #ECEFF4;
                background-color: #5E81AC;
                padding: 4px;
                border: 1px solid #4C566A;
            }
            QTableWidget::item:selected {
                background-color: #88C0D0;
                color: #2E3440;
            }
        """)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Top controls
        controls_layout = QHBoxLayout()
        
        controls_layout.addWidget(QLabel("📅 Select Backup:"))
        
        self.archive_combo = QComboBox()
        self.archive_combo.setMinimumWidth(400)
        self.archive_combo.currentTextChanged.connect(self.on_archive_selected)
        controls_layout.addWidget(self.archive_combo)
        
        self.mount_btn = QPushButton("🔍 Open")
        self.mount_btn.clicked.connect(self.open_selected_archive)
        self.mount_btn.setEnabled(False)
        controls_layout.addWidget(self.mount_btn)
        
        self.unmount_btn = QPushButton("🔒 Close")
        self.unmount_btn.clicked.connect(self.close_archive)
        self.unmount_btn.setEnabled(False)
        controls_layout.addWidget(self.unmount_btn)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        
        # Status
        repo_layout = QHBoxLayout()
        repo_layout.addWidget(QLabel("📦 Repository:"))
        self.repo_combo = QComboBox()
        for repo in self.available_repos:
            self.repo_combo.addItem(repo, repo)
        index = self.repo_combo.findData(self.repo_path)
        if index >= 0:
            self.repo_combo.setCurrentIndex(index)
        self.repo_combo.currentIndexChanged.connect(self.on_repository_selected)
        repo_layout.addWidget(self.repo_combo)
        repo_layout.addStretch()
        layout.addLayout(repo_layout)

        self.status_label = QLabel(f"Loading backup archives from {self.repo_path}...")
        layout.addWidget(self.status_label)
        
        # Main content - splitter
        splitter = QSplitter(Qt.Horizontal)
        
        # Left - Simple folder list
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.addWidget(QLabel("📁 Quick Access:"))
        
        self.folder_list = QListWidget()
        self.folder_list.itemClicked.connect(self.on_folder_selected)
        left_layout.addWidget(self.folder_list)
        
        splitter.addWidget(left_widget)
        
        # Right - File table
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        self.path_label = QLabel("No archive mounted")
        right_layout.addWidget(self.path_label)
        
        self.file_table = QTableWidget()
        self.file_table.setColumnCount(3)
        self.file_table.setHorizontalHeaderLabels(["Name", "Date", "Size"])
        self.file_table.itemDoubleClicked.connect(self.on_file_double_clicked)
        self.file_table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        right_layout.addWidget(self.file_table)
        
        # File actions
        actions_layout = QHBoxLayout()
        
        self.temp_copy_btn = QPushButton("📋 Copy to Temp")
        self.temp_copy_btn.clicked.connect(self.temp_copy_selected)
        self.temp_copy_btn.setEnabled(False)
        actions_layout.addWidget(self.temp_copy_btn)
        
        self.copy_btn = QPushButton("💾 Copy Permanent")
        self.copy_btn.clicked.connect(self.copy_selected)
        self.copy_btn.setEnabled(False)
        actions_layout.addWidget(self.copy_btn)
        
        self.open_temp_btn = QPushButton("📂 Open Temp Folder")
        self.open_temp_btn.clicked.connect(lambda: subprocess.run(['nautilus', self.temp_path], check=False))
        actions_layout.addWidget(self.open_temp_btn)
        
        self.open_recovery_btn = QPushButton("📂 Open Recovery Folder")
        self.open_recovery_btn.clicked.connect(lambda: subprocess.run(['nautilus', self.recovery_path], check=False))
        actions_layout.addWidget(self.open_recovery_btn)
        
        right_layout.addLayout(actions_layout)
        
        splitter.addWidget(right_widget)
        splitter.setSizes([250, 750])
        
        layout.addWidget(splitter)
        
        # Selection handler
        self.file_table.itemSelectionChanged.connect(self.on_selection_changed)

        # Restore panel
        restore_group = QGroupBox("Full Restore")
        restore_layout = QVBoxLayout(restore_group)

        path_row = QHBoxLayout()
        path_row.addWidget(QLabel("Source path:"))
        self.restore_path_edit = QLineEdit(f"/{self.home_prefix}")
        path_row.addWidget(self.restore_path_edit)
        self.use_current_btn = QPushButton("Use current")
        self.use_current_btn.clicked.connect(self.on_use_current_path)
        path_row.addWidget(self.use_current_btn)
        self.use_selection_btn = QPushButton("Use selection")
        self.use_selection_btn.clicked.connect(self.on_use_selection_path)
        path_row.addWidget(self.use_selection_btn)
        restore_layout.addLayout(path_row)

        dest_row = QHBoxLayout()
        dest_row.addWidget(QLabel("Destination:"))
        self.restore_destination_edit = QLineEdit(self.recovery_path)
        dest_row.addWidget(self.restore_destination_edit)
        self.destination_browse_btn = QPushButton("Browse…")
        self.destination_browse_btn.clicked.connect(self.on_browse_destination)
        dest_row.addWidget(self.destination_browse_btn)
        restore_layout.addLayout(dest_row)

        options_row = QHBoxLayout()
        self.overwrite_checkbox = QCheckBox("Allow overwrite of destination")
        options_row.addWidget(self.overwrite_checkbox)
        options_row.addStretch()
        restore_layout.addLayout(options_row)

        action_row = QHBoxLayout()
        self.restore_button = QPushButton("Restore subtree")
        self.restore_button.clicked.connect(self.on_restore_clicked)
        action_row.addWidget(self.restore_button)
        self.restore_preview_btn = QPushButton("Preview count")
        self.restore_preview_btn.clicked.connect(self.on_preview_clicked)
        action_row.addWidget(self.restore_preview_btn)
        action_row.addStretch()
        restore_layout.addLayout(action_row)

        self.restore_log = QPlainTextEdit()
        self.restore_log.setReadOnly(True)
        self.restore_log.setPlaceholderText("Restore progress will appear here…")
        self.restore_log.setMaximumBlockCount(5000)
        restore_layout.addWidget(self.restore_log)

        layout.addWidget(restore_group)

    def _start_worker(self, worker: SimpleBackupWorker, slot, message: str | None = None):
        """Wire up signals, track worker lifetime, and start it."""
        self.active_workers.append(worker)
        timer_ref = {'timer': None}

        if message:
            self.status_label.setText(message)

            timer = QTimer(self)
            timer.setInterval(1500)
            dot_ref = {'count': 0}

            def pulse():
                dot_ref['count'] = (dot_ref['count'] + 1) % 4
                self.status_label.setText(f"{message}{'.' * dot_ref['count']}")

            timer.timeout.connect(pulse)
            timer.start()
            timer_ref['timer'] = timer

        def stop_timer():
            timer = timer_ref.get('timer')
            if timer:
                timer.stop()
                timer.deleteLater()
                timer_ref['timer'] = None

        def handle_result(operation, result, context):
            stop_timer()
            if message:
                self.status_label.setText(message)
            slot(operation, result, context)

        worker.result_ready.connect(handle_result)
        worker.finished.connect(lambda w=worker: self._cleanup_worker(w, stop_timer))
        worker.start()

    def _cleanup_worker(self, worker: SimpleBackupWorker, stop_timer=None):
        if stop_timer:
            stop_timer()
        if worker in self.active_workers:
            self.active_workers.remove(worker)
        worker.deleteLater()

    def load_archives(self):
        """Load backup archives"""
        self.archive_combo.clear()
        self.archive_combo.addItem("Loading backups...", None)
        self.mount_btn.setEnabled(False)
        self.unmount_btn.setEnabled(False)
        message = f"Listing archives in {self.repo_path}"
        self.status_label.setText(message)
        worker = SimpleBackupWorker("list_archives", self.repo_path)
        self._start_worker(worker, self.on_archives_loaded, message)

    def on_archives_loaded(self, operation, result, _context):
        """Handle loaded archives"""
        if isinstance(result, str) and result.startswith("Error"):
            QMessageBox.critical(self, "Error", result)
            self.status_label.setText("Failed to load archives")
            return

        self.archive_combo.clear()
        self.archive_combo.addItem("Select backup date...", None)

        for archive in result:
            display_text = f"{archive['date']} - {archive['name']}"
            self.archive_combo.addItem(display_text, archive)

        self.status_label.setText(f"Loaded {len(result)} backup archives")

    def on_archive_selected(self):
        """Handle archive selection"""
        self.mount_btn.setEnabled(self.archive_combo.currentData() is not None)

    def on_repository_selected(self, _index):
        """Switch to a different backup repository."""
        path = self.repo_combo.currentData()
        if not path or path == self.repo_path:
            return

        if self.is_extracting:
            QMessageBox.warning(self, "Busy", "Wait for the current extraction to finish before switching repositories.")
            previous_index = self.repo_combo.findData(self.repo_path)
            if previous_index >= 0:
                self.repo_combo.blockSignals(True)
                self.repo_combo.setCurrentIndex(previous_index)
                self.repo_combo.blockSignals(False)
            return

        if not os.path.isdir(path):
            QMessageBox.warning(self, "Missing Repository", f"Repository not found:\n{path}")
            previous_index = self.repo_combo.findData(self.repo_path)
            if previous_index >= 0:
                self.repo_combo.blockSignals(True)
                self.repo_combo.setCurrentIndex(previous_index)
                self.repo_combo.blockSignals(False)
            return

        self.repo_path = path
        self.close_archive()
        self.mount_btn.setEnabled(False)
        self.status_label.setText(f"Loading backup archives from {self.repo_path}...")
        self.load_archives()
    
    def open_selected_archive(self):
        """Prepare the selected archive for browsing."""
        archive_data = self.archive_combo.currentData()
        if not archive_data:
            return

        archive_name = archive_data['name']
        self.current_archive = archive_name
        self.unmount_btn.setEnabled(True)
        self.mount_btn.setEnabled(False)

        self.setup_folder_list()
        self.load_files(self.home_prefix)
        self.status_label.setText(f"Opened archive: {archive_name}")
    
    def setup_folder_list(self):
        """Setup quick access folder list"""
        self.folder_list.clear()
        quick_paths = [
            (self.home_prefix, "🏠 Home"),
            (f"{self.home_prefix}/Desktop", "📁 Desktop"),
            (f"{self.home_prefix}/Documents", "📁 Documents"),
            (f"{self.home_prefix}/Projects", "📁 Projects"),
            (f"{self.home_prefix}/Downloads", "📁 Downloads"),
            (f"{self.home_prefix}/Pictures", "📁 Pictures"),
            (f"{self.home_prefix}/Scripts", "📁 Scripts"),
        ]

        for path, label in quick_paths:
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, path)
            self.folder_list.addItem(item)
    
    def on_folder_selected(self, item):
        """Handle folder selection"""
        folder_path = item.data(Qt.UserRole)
        if folder_path:
            self.load_files(folder_path)
    
    def load_files(self, path: str):
        """Load files from the given archive path."""
        if not self.current_archive:
            return

        normalized = path.strip('/') if path else ''
        display_path = f"/{normalized}" if normalized else "/"
        self.current_path = normalized

        self.path_label.setText(f"📁 {display_path}")
        message = f"Listing {display_path}"
        self.status_label.setText(message)

        worker = SimpleBackupWorker(
            "list_directory",
            self.repo_path,
            self.current_archive,
            normalized,
        )
        self._start_worker(worker, self.on_files_loaded, message)

    def on_files_loaded(self, operation, result, context):
        """Handle loaded files"""
        if context and context.get('path') != self.current_path:
            return

        if isinstance(result, str):
            QMessageBox.warning(self, "Warning", result)
            self.status_label.setText("Failed to load directory")
            return
        
        # Clear and populate table
        self.file_table.setRowCount(0)
        
        for file_info in result:
            row = self.file_table.rowCount()
            self.file_table.insertRow(row)
            
            # Name with icon
            icon = "📁" if file_info['is_dir'] else "📄"
            name_item = QTableWidgetItem(f"{icon} {file_info['name']}")
            name_item.setData(Qt.UserRole, file_info)
            self.file_table.setItem(row, 0, name_item)
            
            # Date
            self.file_table.setItem(row, 1, QTableWidgetItem(file_info['date']))
            
            # Size
            self.file_table.setItem(row, 2, QTableWidgetItem(file_info['size']))
        
        self.file_table.resizeColumnsToContents()
        self.status_label.setText(f"Loaded {len(result)} items")

        # Prefill restore path with current directory for convenience
        if self.current_path is not None:
            self.restore_path_edit.setText(self._format_display_path(self.current_path or self.home_prefix))
    
    def on_file_double_clicked(self, item):
        """Handle file double-click"""
        if item.column() != 0:
            return
        
        file_info = item.data(Qt.UserRole)
        if file_info['is_dir']:
            # Navigate to directory
            self.load_files(file_info['archive_path'])

    def on_selection_changed(self):
        """Handle selection change"""
        if self.is_extracting:
            self.temp_copy_btn.setEnabled(False)
            self.copy_btn.setEnabled(False)
            return

        selected = self.file_table.selectedItems()
        has_selection = len(selected) > 0
        
        self.temp_copy_btn.setEnabled(has_selection)
        self.copy_btn.setEnabled(has_selection)

    def on_use_current_path(self):
        """Populate restore path with the currently viewed directory."""
        if self.current_path is None:
            target = self.home_prefix
        else:
            target = self.current_path or self.home_prefix
        self.restore_path_edit.setText(self._format_display_path(target))

    def on_use_selection_path(self):
        """Populate restore path from the first selected entry."""
        items = self.get_selected_items()
        if items:
            target = items[0].get('archive_path') or self.current_path or self.home_prefix
        else:
            target = self.current_path or self.home_prefix
        self.restore_path_edit.setText(self._format_display_path(target))

    def on_browse_destination(self):
        """Choose a destination directory for restores."""
        directory = QFileDialog.getExistingDirectory(self, "Select destination", self.restore_destination_edit.text() or os.path.expanduser("~"))
        if directory:
            self.restore_destination_edit.setText(directory)

    def on_preview_clicked(self):
        """Run a quick summary of the subtree before restore."""
        if not self.current_archive:
            QMessageBox.warning(self, "No Archive", "Select an archive to summarize first.")
            return

        relative = self._normalize_input_path(self.restore_path_edit.text())
        if not relative:
            QMessageBox.warning(self, "Missing Path", "Enter a source path to summarize.")
            return

        message = f"Scanning /{relative}"
        self.restore_log.appendPlainText(f"Starting summary: {message}")
        worker = SimpleBackupWorker("summarize_subtree", self.repo_path, self.current_archive, relative)
        self._start_worker(worker, self.on_preview_result, message)

    def on_preview_result(self, operation, result, context):
        """Display summary results."""
        if operation != "summarize_subtree":
            return

        if isinstance(result, str):
            QMessageBox.warning(self, "Summary Error", result)
            self.restore_log.appendPlainText(result)
            return

        files = result.get('files', 0)
        dirs = result.get('directories', 0)
        size_bytes = result.get('size_bytes', 0)
        size_str = format_size(size_bytes)
        summary = f"Summary: {files} files, {dirs} folders, approx {size_str}"
        self.restore_log.appendPlainText(summary)
        self.status_label.setText(summary)

    def get_selected_items(self):
        """Get selected file info"""
        selected_items = []
        selected_rows = set()
        for item in self.file_table.selectedItems():
            selected_rows.add(item.row())

        for row in sorted(list(selected_rows)):
            item = self.file_table.item(row, 0)
            if item:
                selected_items.append(item.data(Qt.UserRole))
        return selected_items

    def temp_copy_selected(self):
        """Copy selected items to temp"""
        items = self.get_selected_items()
        if items:
            self.start_extraction(items, self.temp_path, "Temp")

    def copy_selected(self):
        """Copy selected items permanently"""
        items = self.get_selected_items()
        if items:
            self.start_extraction(items, self.recovery_path, "Recovery")

    def start_extraction(self, items, destination, label):
        """Kick off extraction of selected archive paths."""
        if not self.current_archive:
            return

        paths = [item.get('archive_path') for item in items if item]
        if not paths:
            return

        self.is_extracting = True
        self.temp_copy_btn.setEnabled(False)
        self.copy_btn.setEnabled(False)
        message = f"Extracting {len(paths)} item(s) to {label}"
        self.status_label.setText(message)

        worker = SimpleBackupWorker(
            "extract_items",
            self.repo_path,
            archive=self.current_archive,
            paths=paths,
            destination=destination,
        )
        self._start_worker(
            worker,
            lambda op, result, ctx, lbl=label: self.on_items_extracted(op, result, ctx, lbl),
            message,
        )

    def on_items_extracted(self, operation, result, context, label):
        """Handle completion of extraction jobs."""
        if operation != "extract_items":
            return

        self.is_extracting = False
        self.on_selection_changed()

        if isinstance(result, str):
            QMessageBox.warning(self, "Warning", result)
            self.status_label.setText("Extraction failed")
            return

        extracted = result.get('extracted', [])
        errors = result.get('errors', [])

        if extracted:
            QMessageBox.information(self, "Success", f"Copied {len(extracted)} item(s) to {label} folder.")
            self.status_label.setText(f"Copied {len(extracted)} item(s) to {label} folder")
        else:
            self.status_label.setText("No items extracted")

        if errors:
            QMessageBox.warning(self, "Warnings", "\n".join(errors))

    def close_archive(self):
        """Clear the current archive selection."""
        self.current_archive = None
        self.current_path = None
        self.unmount_btn.setEnabled(False)
        self.mount_btn.setEnabled(True)

        self.folder_list.clear()
        self.file_table.setRowCount(0)
        self.path_label.setText("No archive selected")
        self.status_label.setText("Archive closed")

    def on_restore_clicked(self):
        """Begin restoring a subtree to the chosen destination."""
        if not self.current_archive:
            QMessageBox.warning(self, "No Archive", "Open an archive before restoring.")
            return

        relative = self._normalize_input_path(self.restore_path_edit.text())
        if not relative:
            QMessageBox.warning(self, "Missing Path", "Enter a source path to restore.")
            return

        destination_root = self.restore_destination_edit.text().strip()
        if not destination_root:
            QMessageBox.warning(self, "Missing Destination", "Choose where the restore should go.")
            return

        self.restore_log.clear()
        self.restore_log.appendPlainText(f"Restoring /{relative} from {self.current_archive}")
        self._set_restore_controls_enabled(False)

        self.restore_worker = SubtreeRestoreWorker(
            self.repo_path,
            self.current_archive,
            relative,
            destination_root,
            self.overwrite_checkbox.isChecked(),
        )
        self.restore_worker.progress.connect(self.on_restore_progress)
        self.restore_worker.finished.connect(self.on_restore_finished)
        self.restore_worker.start()

    def on_restore_progress(self, line: str):
        """Append progress lines to the restore log."""
        self.restore_log.appendPlainText(line)
        self.restore_log.verticalScrollBar().setValue(self.restore_log.verticalScrollBar().maximum())

    def on_restore_finished(self, success: bool, message: str, stats: dict):
        """Handle completion of restore."""
        self.restore_worker = None
        self._set_restore_controls_enabled(True)
        summary_line = message
        if stats:
            files = stats.get('files')
            dest = stats.get('destination')
            if files is not None:
                summary_line += f" (entries processed: {files})"
            if dest:
                summary_line += f" → {dest}"
        self.restore_log.appendPlainText(summary_line)
        if success:
            QMessageBox.information(self, "Restore complete", summary_line)
            self.status_label.setText(summary_line)
        else:
            QMessageBox.warning(self, "Restore failed", summary_line)
            self.status_label.setText("Restore failed")

    def _set_restore_controls_enabled(self, enabled: bool):
        self.restore_button.setEnabled(enabled)
        self.restore_preview_btn.setEnabled(enabled)
        self.use_current_btn.setEnabled(enabled)
        self.use_selection_btn.setEnabled(enabled)
        self.destination_browse_btn.setEnabled(enabled)
        self.overwrite_checkbox.setEnabled(enabled)

    def _normalize_input_path(self, text: str) -> str:
        value = (text or '').strip()
        if not value:
            return ''
        value = value.lstrip('/')
        return value

    def _format_display_path(self, path: str) -> str:
        if not path:
            return '/'
        return f"/{path}"

def main():
    app = QApplication(sys.argv)
    
    # Check if display is available
    if not app.primaryScreen():
        print("No display available. Make sure you're running in a graphical environment.")
        return 1
    
    window = SimplePikaExplorer()
    window.show()
    
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())
