from __future__ import annotations

import os
import shlex
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from PySide6.QtCore import QPoint, Qt, QSize, Signal
from PySide6.QtGui import QIcon, QPixmap, QFont
from PySide6.QtWidgets import (
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListView,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QTextBrowser,
    QDialog,
    QDialogButtonBox,
    QLineEdit,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
    QFrame,
    QAbstractItemView,
)

from manifest_loader import (
    MenuConfig,
    CategoryConfig,
    TabConfig,
    ToolManifest,
    build_tool_registry,
    load_tool_manifest,
    load_menu_config,
    save_menu_config,
    save_tool_manifest,
)
from settings import APPS_DIR, ASSETS_DIR, WORKDIR_ROOT


def _open_with_system_handler(path: Path) -> bool:
    """Open a file or directory with the default OS handler."""

    if sys.platform.startswith("linux"):
        opener = shutil.which("xdg-open")
        if opener:
            subprocess.Popen([opener, str(path)])
            return True
    elif sys.platform == "darwin":
        opener = shutil.which("open")
        if opener:
            subprocess.Popen([opener, str(path)])
            return True
    elif os.name == "nt":
        try:
            os.startfile(str(path))  # type: ignore[attr-defined]
            return True
        except OSError:
            return False
    return False


def _shlex_join(parts: List[str]) -> str:
    if not parts:
        return ""
    join = getattr(shlex, "join", None)
    if join:
        return join(parts)
    return " ".join(shlex.quote(part) for part in parts)


class ToolCardWidget(QFrame):
    """Visual card representing a tool inside the launcher grid."""

    def __init__(self, tool: ToolManifest, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.tool = tool
        self.setObjectName("toolCard")
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Plain)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        self.icon_label = QLabel()
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setMinimumHeight(96)
        layout.addWidget(self.icon_label)

        self.name_label = QLabel(tool.name)
        name_font = QFont()
        name_font.setBold(True)
        name_font.setPointSize(name_font.pointSize() + 1)
        self.name_label.setFont(name_font)
        self.name_label.setAlignment(Qt.AlignCenter)
        self.name_label.setWordWrap(True)
        layout.addWidget(self.name_label)

        self.synopsis_label = QLabel(tool.synopsis or "")
        self.synopsis_label.setWordWrap(True)
        self.synopsis_label.setAlignment(Qt.AlignTop)
        syn_font = QFont()
        syn_font.setPointSize(max(8, syn_font.pointSize() - 1))
        self.synopsis_label.setFont(syn_font)
        layout.addWidget(self.synopsis_label)

        layout.addStretch(1)

        self._apply_pixmap()
        self._apply_style()

    def _apply_pixmap(self) -> None:
        pixmap = QPixmap(str(self.tool.icon_path))
        if pixmap.isNull():
            pixmap = QPixmap(str(ASSETS_DIR / "icons" / "placeholder.png"))
        if pixmap.isNull():
            pixmap = QPixmap(96, 96)
            pixmap.fill(Qt.gray)
        self.icon_label.setPixmap(
            pixmap.scaled(96, 96, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        )

    def _apply_style(self) -> None:
        self.setStyleSheet(
            """
            QFrame#toolCard {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(20, 44, 86, 0.92),
                    stop:1 rgba(29, 74, 142, 0.92));
                border-radius: 18px;
                border: 1px solid rgba(120, 200, 255, 0.18);
                color: #f4f8ff;
            }
            QFrame#toolCard:hover {
                border-color: rgba(150, 220, 255, 0.9);
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(26, 58, 110, 0.98),
                    stop:1 rgba(38, 92, 170, 0.98));
            }
            QFrame#toolCard QLabel {
                color: #f1f6ff;
            }
            """
        )

    def update_tool(self, tool: ToolManifest) -> None:
        self.tool = tool
        self.name_label.setText(tool.name)
        self.synopsis_label.setText(tool.synopsis or "")
        self._apply_pixmap()

class ToolMetadataDialog(QDialog):
    def __init__(
        self,
        *,
        title: str,
        tool_id: str,
        name: str,
        synopsis: str,
        command: str,
        notes: str,
        allow_id_edit: bool,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(420)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.id_edit = QLineEdit(tool_id)
        self.id_edit.setReadOnly(not allow_id_edit)
        form.addRow("Tool ID", self.id_edit)

        self.name_edit = QLineEdit(name)
        form.addRow("Name", self.name_edit)

        self.synopsis_edit = QLineEdit(synopsis)
        form.addRow("Synopsis", self.synopsis_edit)

        self.command_edit = QLineEdit(command)
        form.addRow("Command", self.command_edit)

        self.notes_edit = QPlainTextEdit(notes)
        self.notes_edit.setPlaceholderText("Optional notes shown in the Details tab.")
        form.addRow("Notes", self.notes_edit)

        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_values(self) -> Dict[str, str]:
        return {
            "tool_id": self.id_edit.text().strip(),
            "name": self.name_edit.text().strip(),
            "synopsis": self.synopsis_edit.text().strip(),
            "command": self.command_edit.text().strip(),
            "notes": self.notes_edit.toPlainText().strip(),
        }

    def accept(self) -> None:  # type: ignore[override]
        values = self.get_values()
        if not values["tool_id"]:
            QMessageBox.warning(self, "Validation", "Tool ID cannot be empty.")
            return
        if not values["name"]:
            QMessageBox.warning(self, "Validation", "Tool name cannot be empty.")
            return
        if not values["command"]:
            QMessageBox.warning(self, "Validation", "Command cannot be empty.")
            return
        super().accept()

class LauncherTab(QWidget):
    tool_selected = Signal(object)
    request_launch = Signal(object)
    maintenance_action_requested = Signal(str, dict)
    add_tool_requested = Signal(str)
    category_action_requested = Signal(str, dict)
    maintenance_mode_changed = Signal(bool)
    reload_requested = Signal()

    def __init__(self, menu_config: MenuConfig, tool_registry: Dict[str, ToolManifest], parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("launcherTab")
        self.menu_config = menu_config
        self.tool_registry = tool_registry
        self._current_tab_config = self._resolve_launcher_tab(menu_config)
        self._active_category_id: Optional[str] = None
        self.maintenance_mode = False

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(16)

        self.category_list = QListWidget()
        self.category_list.setSelectionMode(QListWidget.SingleSelection)
        self.category_list.currentRowChanged.connect(self._on_category_changed)
        self.category_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.category_list.customContextMenuRequested.connect(self._show_category_context_menu)
        self.category_list.setFixedWidth(230)
        self.category_list.setStyleSheet(
            """
            QListWidget {
                background: rgba(10, 25, 48, 0.92);
                border: 1px solid rgba(255, 255, 255, 0.04);
                border-radius: 14px;
                color: #e8f1ff;
                padding: 6px;
            }
            QListWidget::item {
                border-radius: 12px;
                padding: 10px;
                margin: 4px 2px;
            }
            QListWidget::item:selected {
                background: rgba(88, 180, 255, 0.30);
                border: 1px solid rgba(120, 200, 255, 0.8);
                color: #ffffff;
            }
            """
        )
        layout.addWidget(self.category_list, 1)

        self.item_list = QListWidget()
        self.item_list.setViewMode(QListView.IconMode)
        self.item_list.setFlow(QListView.LeftToRight)
        self.item_list.setWrapping(True)
        self.item_list.setResizeMode(QListWidget.Adjust)
        self.item_list.setMovement(QListWidget.Static)
        self.item_list.setSpacing(18)
        self.item_list.setSelectionMode(QListWidget.SingleSelection)
        self.item_list.setSelectionRectVisible(False)
        self.item_list.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.item_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.item_list.setStyleSheet(
            """
            QListWidget {
                background: rgba(7, 17, 33, 0.2);
                border: none;
            }
            QListWidget::item {
                margin: 12px;
            }
            QListWidget::item:selected {
                outline: none;
            }
            """
        )
        self.item_list.setSelectionMode(QListWidget.SingleSelection)
        self.item_list.itemActivated.connect(self._on_item_activated)
        self.item_list.itemClicked.connect(self._on_item_clicked)
        self.item_list.currentItemChanged.connect(self._on_item_changed)
        self.item_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.item_list.customContextMenuRequested.connect(self._show_context_menu)
        layout.addWidget(self.item_list, 3)

        self._populate_categories()

        self.setStyleSheet(
            """
            QWidget#launcherTab {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #0f1f3a,
                    stop:0.5 #143764,
                    stop:1 #0a1a33);
            }
            """
        )

    def _resolve_launcher_tab(self, menu_config: MenuConfig) -> Optional[TabConfig]:
        for tab in menu_config.tabs:
            if tab.id == "launcher":
                return tab
        return menu_config.tabs[0] if menu_config.tabs else None

    def _populate_categories(self) -> None:
        self.category_list.clear()
        if not self._current_tab_config:
            return

        for category in self._current_tab_config.categories:
            item = QListWidgetItem(category.name)
            item.setData(Qt.UserRole, category.id)
            self.category_list.addItem(item)

        if self.category_list.count() > 0:
            self.category_list.setCurrentRow(0)
        else:
            self._active_category_id = None

    def _on_category_changed(self, row: int) -> None:
        if row < 0:
            self.item_list.clear()
            self._active_category_id = None
            return

        item = self.category_list.item(row)
        if not item:
            return

        category_id = item.data(Qt.UserRole)
        self._active_category_id = category_id
        category_config = self._find_category(category_id)
        self._populate_items(category_config)

    def _find_category(self, category_id: str):
        if not self._current_tab_config:
            return None
        for category in self._current_tab_config.categories:
            if category.id == category_id:
                return category
        return None

    def _populate_items(self, category_config) -> None:
        self.item_list.clear()
        if not category_config:
            return

        for tool_id in category_config.item_ids:
            tool = self.tool_registry.get(tool_id)
            if not tool:
                continue

            item = QListWidgetItem()
            item.setData(Qt.UserRole, tool.id)
            item.setToolTip(tool.synopsis or tool.name)
            item.setSizeHint(QSize(240, 220))
            self.item_list.addItem(item)

            card = ToolCardWidget(tool)
            self.item_list.setItemWidget(item, card)

        if self.item_list.count() > 0:
            self.item_list.setCurrentRow(0)

    def _current_tool(self) -> Optional[ToolManifest]:
        current = self.item_list.currentItem()
        if not current:
            return None
        tool_id = current.data(Qt.UserRole)
        return self.tool_registry.get(tool_id)

    def _on_item_activated(self, list_item: QListWidgetItem) -> None:
        tool_id = list_item.data(Qt.UserRole)
        tool = self.tool_registry.get(tool_id)
        if tool:
            if self.maintenance_mode:
                self.tool_selected.emit(tool)
            else:
                self.request_launch.emit(tool)

    def _on_item_clicked(self, list_item: QListWidgetItem) -> None:
        tool_id = list_item.data(Qt.UserRole)
        tool = self.tool_registry.get(tool_id)
        if tool:
            if self.maintenance_mode:
                self.tool_selected.emit(tool)
            else:
                self.request_launch.emit(tool)

    def _on_item_changed(self, current: Optional[QListWidgetItem], _previous: Optional[QListWidgetItem]) -> None:
        if not current:
            self.tool_selected.emit(None)
            return
        tool_id = current.data(Qt.UserRole)
        tool = self.tool_registry.get(tool_id)
        if tool:
            self.tool_selected.emit(tool)

    def _show_context_menu(self, position: QPoint) -> None:
        item = self.item_list.itemAt(position)
        menu = QMenu(self)
        reload_action = menu.addAction("Reload Configuration")
        if self.maintenance_mode:
            toggle_action = menu.addAction("Exit Maintenance Mode")
        else:
            toggle_action = menu.addAction("Enter Maintenance Mode")

        menu.addSeparator()
        if not item:
            if self.maintenance_mode and self._active_category_id:
                add_action = menu.addAction("Add Item…")
            else:
                add_action = None
            menu.addSeparator()
            if self.maintenance_mode:
                add_category_action = menu.addAction("Add Category…")
            else:
                add_category_action = None
            selected_action = menu.exec(self.item_list.mapToGlobal(position))
            if selected_action == reload_action:
                self.reload_requested.emit()
                return
            if selected_action == toggle_action:
                self.set_maintenance_mode(not self.maintenance_mode)
                self.maintenance_mode_changed.emit(self.maintenance_mode)
                return
            if selected_action and selected_action == add_action and self._active_category_id:
                self.add_tool_requested.emit(self._active_category_id)
            elif selected_action and selected_action == add_category_action:
                self.category_action_requested.emit("add_category", {})
            return

        tool = self.tool_registry.get(item.data(Qt.UserRole))
        if not tool:
            return

        launch_action = menu.addAction("Launch")
        details_action = menu.addAction("Show Details")
        open_folder_action = menu.addAction("Open Tool Folder")
        menu.addSeparator()
        edit_action = None
        change_icon_action = None
        move_action = None
        move_up_action = None
        move_down_action = None
        delete_action = None
        if self.maintenance_mode:
            menu.addSeparator()
            edit_action = menu.addAction("Edit Item…")
            change_icon_action = menu.addAction("Change Icon…")
            move_action = menu.addAction("Move to Category…")
            move_up_action = menu.addAction("Move Up")
            move_down_action = menu.addAction("Move Down")
            menu.addSeparator()
            delete_action = menu.addAction("Delete Item")

        selected_action = menu.exec(self.item_list.mapToGlobal(position))

        if selected_action == reload_action:
            self.reload_requested.emit()
            return
        if selected_action == toggle_action:
            self.set_maintenance_mode(not self.maintenance_mode)
            self.maintenance_mode_changed.emit(self.maintenance_mode)
            return

        if selected_action == launch_action:
            self.request_launch.emit(tool)
        elif selected_action == details_action:
            self.tool_selected.emit(tool)
        elif selected_action == open_folder_action:
            self._open_tool_folder(tool)
        elif selected_action == edit_action:
            self.maintenance_action_requested.emit("edit_item", {"tool_id": tool.id})
        elif selected_action == change_icon_action:
            self.maintenance_action_requested.emit("change_icon", {"tool_id": tool.id})
        elif selected_action == move_action:
            self.maintenance_action_requested.emit("move_item", {"tool_id": tool.id})
        elif selected_action == move_up_action:
            self.maintenance_action_requested.emit("move_item_up", {"tool_id": tool.id})
        elif selected_action == move_down_action:
            self.maintenance_action_requested.emit("move_item_down", {"tool_id": tool.id})
        elif selected_action == delete_action:
            self.maintenance_action_requested.emit("delete_item", {"tool_id": tool.id})

    def _open_tool_folder(self, tool: ToolManifest) -> None:
        folder = tool.app_dir
        if not _open_with_system_handler(folder):
            QMessageBox.information(self, "Tool Folder", str(folder))

    def _show_category_context_menu(self, position: QPoint) -> None:
        if not self.maintenance_mode:
            toggle_menu = QMenu(self)
            toggle_action = toggle_menu.addAction("Enter Maintenance Mode")
            selected = toggle_menu.exec(self.category_list.mapToGlobal(position))
            if selected == toggle_action:
                self.set_maintenance_mode(True)
                self.maintenance_mode_changed.emit(True)
            return

        item = self.category_list.itemAt(position)
        menu = QMenu(self)

        toggle_action = menu.addAction("Exit Maintenance Mode")
        menu.addSeparator()

        add_category_action = menu.addAction("Add Category…")
        selected_category_id: Optional[str] = None

        rename_action = None
        delete_action = None
        add_item_action = None

        if item:
            selected_category_id = item.data(Qt.UserRole)
            menu.addSeparator()
            add_item_action = menu.addAction("Add Item to Category…")
            rename_action = menu.addAction("Rename Category…")
            delete_action = menu.addAction("Delete Category")

        selected = menu.exec(self.category_list.mapToGlobal(position))

        if selected == toggle_action:
            self.set_maintenance_mode(False)
            self.maintenance_mode_changed.emit(False)
        elif selected == add_category_action:
            self.category_action_requested.emit("add_category", {})
        elif selected == add_item_action and selected_category_id:
            self.add_tool_requested.emit(selected_category_id)
        elif selected == rename_action and selected_category_id:
            self.category_action_requested.emit("rename_category", {"category_id": selected_category_id})
        elif selected == delete_action and selected_category_id:
            self.category_action_requested.emit("delete_category", {"category_id": selected_category_id})

    def set_maintenance_mode(self, enabled: bool) -> None:
        self.maintenance_mode = enabled

    def refresh(self, menu_config: MenuConfig, tool_registry: Dict[str, ToolManifest]) -> None:
        self.menu_config = menu_config
        self.tool_registry = tool_registry
        self._current_tab_config = self._resolve_launcher_tab(menu_config)
        self._populate_categories()


class DetailsTab(QWidget):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        self.setStyleSheet(
            """
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #08162b,
                    stop:1 #0c1f3f);
                color: #e6f1ff;
            }
            QLabel {
                color: #eaf3ff;
            }
            QTextBrowser {
                background: rgba(19, 40, 74, 0.92);
                border-radius: 16px;
                border: 1px solid rgba(130, 200, 255, 0.18);
                padding: 14px;
                color: #e4efff;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #1a3d73,
                    stop:1 #1b5aa6);
                border-radius: 12px;
                padding: 9px 18px;
                color: #f3f8ff;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #22508d,
                    stop:1 #2470d0);
            }
            """
        )

        self.name_label = QLabel("Select a tool to view details")
        self.name_label.setProperty("class", "heading")
        self.name_label.setWordWrap(True)

        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignRight)

        self.synopsis_label = QLabel("–")
        self.synopsis_label.setWordWrap(True)
        form_layout.addRow("Synopsis", self.synopsis_label)

        self.command_label = QLabel("–")
        self.command_label.setWordWrap(True)
        form_layout.addRow("Command", self.command_label)

        self.cwd_label = QLabel("–")
        self.cwd_label.setWordWrap(True)
        form_layout.addRow("Working Dir", self.cwd_label)

        self.tags_label = QLabel("–")
        self.tags_label.setWordWrap(True)
        form_layout.addRow("Tags", self.tags_label)

        self.icon_label = QLabel("–")
        self.icon_label.setWordWrap(True)
        form_layout.addRow("Icon", self.icon_label)

        self.notes_view = QTextBrowser()
        self.notes_view.setPlaceholderText("Notes will appear here when available.")

        layout.addWidget(self.name_label)
        layout.addLayout(form_layout)
        layout.addWidget(QLabel("Notes"))
        layout.addWidget(self.notes_view, 1)

        button_row = QHBoxLayout()
        self.open_readme_button = QPushButton("Open README")
        self.open_readme_button.setEnabled(False)
        self.open_readme_button.clicked.connect(self._emit_open_readme)
        button_row.addWidget(self.open_readme_button)

        self.open_folder_button = QPushButton("Open Folder")
        self.open_folder_button.setEnabled(False)
        self.open_folder_button.clicked.connect(self._emit_open_folder)
        button_row.addWidget(self.open_folder_button)

        button_row.addStretch(1)
        layout.addLayout(button_row)

        self._current_tool: Optional[ToolManifest] = None

    open_readme_requested = Signal(object)
    open_folder_requested = Signal(object)

    def display_tool(self, tool: Optional[ToolManifest]) -> None:
        self._current_tool = tool
        if not tool:
            self.name_label.setText("Select a tool to view details")
            self.synopsis_label.setText("–")
            self.command_label.setText("–")
            self.cwd_label.setText("–")
            self.tags_label.setText("–")
            self.icon_label.setText("–")
            self.notes_view.clear()
            self.open_readme_button.setEnabled(False)
            self.open_folder_button.setEnabled(False)
            return

        self.name_label.setText(tool.name)
        self.synopsis_label.setText(tool.synopsis or "–")
        self.command_label.setText(" ".join(tool.command))
        self.cwd_label.setText(str(tool.cwd))
        self.tags_label.setText(", ".join(tool.tags) if tool.tags else "–")
        self.icon_label.setText(str(tool.icon_path))
        self.notes_view.setPlainText(tool.notes or "No notes provided.")
        self.open_folder_button.setEnabled(True)
        self.open_readme_button.setEnabled(tool.readme_path.exists())

    def _emit_open_readme(self) -> None:
        if self._current_tool:
            self.open_readme_requested.emit(self._current_tool)

    def _emit_open_folder(self) -> None:
        if self._current_tool:
            self.open_folder_requested.emit(self._current_tool)
class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("MasterMenu")
        self.resize(1280, 800)

        try:
            self.menu_config = load_menu_config()
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Configuration Error", str(exc))
            raise

        self.tool_registry = build_tool_registry(self.menu_config)

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.setStyleSheet(
            """
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #061225,
                    stop:1 #0b1f3f);
            }
            QTabWidget::pane {
                border: none;
                background: transparent;
            }
            QTabBar::tab {
                background: transparent;
                color: #9aa7bd;
                padding: 10px 18px;
                margin: 0 6px;
            }
            QTabBar::tab:selected {
                color: #f0f4fb;
                border-bottom: 2px solid #4aa3ff;
            }
            """
        )

        self.launcher_tab = LauncherTab(self.menu_config, self.tool_registry)
        self.details_tab = DetailsTab()

        self.tabs.addTab(self.launcher_tab, "Launcher")
        self.tabs.addTab(self.details_tab, "Details")

        self.launcher_tab.tool_selected.connect(self.details_tab.display_tool)
        self.launcher_tab.request_launch.connect(self.launch_tool)
        self.details_tab.open_folder_requested.connect(self.open_tool_folder)
        self.details_tab.open_readme_requested.connect(self.open_tool_readme)
        self.launcher_tab.maintenance_action_requested.connect(self.handle_maintenance_action)
        self.launcher_tab.add_tool_requested.connect(self.handle_add_tool)
        self.launcher_tab.category_action_requested.connect(self.handle_category_action)
        self.launcher_tab.maintenance_mode_changed.connect(self.set_maintenance_mode)
        self.launcher_tab.reload_requested.connect(self.reload_configuration)

    def launch_tool(self, tool: ToolManifest) -> None:
        env = os.environ.copy()
        env.update({k: str(v) for k, v in tool.env.items()})

        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        run_root = WORKDIR_ROOT / tool.id
        run_dir = run_root / timestamp
        tmp_dir = run_dir / "tmp"
        tmp_dir.mkdir(parents=True, exist_ok=True)

        env.setdefault("MASTERMENU_WORKDIR", str(run_dir))
        env.setdefault("OUTPUT_ROOT", str(run_dir))
        env.setdefault("TMP_ROOT", str(tmp_dir))

        cwd = str(tool.cwd)
        command = [str(part) for part in tool.command]

        try:
            subprocess.Popen(
                command,
                cwd=cwd,
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except FileNotFoundError as exc:
            QMessageBox.critical(self, "Launch Error", f"Command not found: {exc}")
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Launch Error", str(exc))

    def open_tool_folder(self, tool: ToolManifest) -> None:
        if not _open_with_system_handler(tool.app_dir):
            QMessageBox.information(self, "Tool Folder", str(tool.app_dir))

    def open_tool_readme(self, tool: ToolManifest) -> None:
        readme = tool.readme_path
        if not readme.exists():
            QMessageBox.information(self, "README", "No README found for this tool.")
            return
        if not _open_with_system_handler(readme):
            QMessageBox.information(self, "README", str(readme))

    def set_maintenance_mode(self, enabled: bool) -> None:
        self.launcher_tab.set_maintenance_mode(enabled)
        status = "Maintenance mode enabled" if enabled else "Maintenance mode disabled"
        self.statusBar().showMessage(status, 3000)

    def reload_configuration(self) -> None:
        current_mode = self.launcher_tab.maintenance_mode
        try:
            self.menu_config = load_menu_config()
            self.tool_registry = build_tool_registry(self.menu_config)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Reload Failed", str(exc))
            return

        self.launcher_tab.refresh(self.menu_config, self.tool_registry)
        self.details_tab.display_tool(None)
        self.launcher_tab.set_maintenance_mode(current_mode)
        self.statusBar().showMessage("Configuration reloaded", 3000)

    def handle_add_tool(self, category_id: str) -> None:
        dialog = ToolMetadataDialog(
            title="Add Tool",
            tool_id="",
            name="",
            synopsis="",
            command="bash ./run.sh",
            notes="",
            allow_id_edit=True,
            parent=self,
        )
        if dialog.exec() != QDialog.Accepted:
            return

        values = dialog.get_values()
        tool_id = values["tool_id"]
        if not tool_id:
            return
        if any(ch in tool_id for ch in " /\\"):
            QMessageBox.warning(self, "Add Tool", "Tool ID cannot contain spaces or slashes.")
            return
        if tool_id in self.tool_registry or (APPS_DIR / tool_id).exists():
            QMessageBox.warning(self, "Add Tool", f"Tool ID '{tool_id}' already exists.")
            return

        template_dir = APPS_DIR / "_template"
        destination = APPS_DIR / tool_id
        try:
            shutil.copytree(template_dir, destination)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Add Tool", f"Failed to create tool folder: {exc}")
            return

        try:
            manifest = load_tool_manifest(tool_id)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Add Tool", f"Failed to load manifest: {exc}")
            return

        command_list = self._parse_command_string(values["command"])
        if command_list is None:
            return

        manifest.id = tool_id
        manifest.name = values["name"]
        manifest.synopsis = values["synopsis"]
        manifest.command = command_list
        manifest.notes = values["notes"]
        manifest.raw["category"] = category_id
        manifest.raw["id"] = tool_id
        manifest.raw["name"] = values["name"]
        manifest.raw["synopsis"] = values["synopsis"]
        manifest.raw["command"] = command_list
        manifest.raw["notes"] = values["notes"]
        manifest.raw.setdefault("icon", "icon.png")

        try:
            save_tool_manifest(manifest)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Add Tool", f"Failed to save manifest: {exc}")
            return

        category = self._find_category(category_id)
        if not category:
            QMessageBox.warning(self, "Add Tool", f"Category '{category_id}' not found.")
            shutil.rmtree(destination, ignore_errors=True)
            return
        if tool_id not in category.item_ids:
            category.item_ids.append(tool_id)

        try:
            save_menu_config(self.menu_config)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Add Tool", f"Failed to update menu config: {exc}")
            return

        self.reload_configuration()

    def handle_maintenance_action(self, action: str, payload: Dict) -> None:
        tool_id = payload.get("tool_id")
        tool = self.tool_registry.get(tool_id) if tool_id else None
        if action != "add_category" and not tool:
            QMessageBox.warning(self, "Maintenance", "Tool not found for action.")
            return

        if action == "edit_item" and tool:
            self._edit_tool(tool)
        elif action == "change_icon" and tool:
            self._change_icon(tool)
        elif action == "move_item" and tool:
            self._move_item(tool)
        elif action == "move_item_up" and tool:
            self._reorder_item(tool, -1)
        elif action == "move_item_down" and tool:
            self._reorder_item(tool, 1)
        elif action == "delete_item" and tool:
            self._delete_item(tool)

    def handle_category_action(self, action: str, payload: Dict) -> None:
        if action == "add_category":
            self._add_category()
            return

        category_id = payload.get("category_id")
        category = self._find_category(category_id) if category_id else None
        if not category:
            QMessageBox.warning(self, "Maintenance", "Category not found.")
            return

        if action == "rename_category":
            self._rename_category(category)
        elif action == "delete_category":
            self._delete_category(category)

    def _launcher_tab_config(self) -> Optional[TabConfig]:
        for tab in self.menu_config.tabs:
            if tab.id == "launcher":
                return tab
        return self.menu_config.tabs[0] if self.menu_config.tabs else None

    def _find_category(self, category_id: Optional[str]) -> Optional[CategoryConfig]:
        launcher_tab = self._launcher_tab_config()
        if not launcher_tab or category_id is None:
            return None
        for category in launcher_tab.categories:
            if category.id == category_id:
                return category
        return None

    def _find_tool_location(self, tool_id: str) -> Optional[Tuple[CategoryConfig, int]]:
        launcher_tab = self._launcher_tab_config()
        if not launcher_tab:
            return None
        for category in launcher_tab.categories:
            if tool_id in category.item_ids:
                return category, category.item_ids.index(tool_id)
        return None

    def _parse_command_string(self, command: str) -> Optional[List[str]]:
        try:
            return shlex.split(command)
        except ValueError as exc:
            QMessageBox.warning(self, "Command", f"Invalid command: {exc}")
            return None

    def _edit_tool(self, tool: ToolManifest) -> None:
        dialog = ToolMetadataDialog(
            title="Edit Tool",
            tool_id=tool.id,
            name=tool.name,
            synopsis=tool.synopsis,
            command=_shlex_join(tool.command),
            notes=tool.notes,
            allow_id_edit=False,
            parent=self,
        )
        if dialog.exec() != QDialog.Accepted:
            return

        values = dialog.get_values()
        command_list = self._parse_command_string(values["command"])
        if command_list is None:
            return

        tool.name = values["name"]
        tool.synopsis = values["synopsis"]
        tool.command = command_list
        tool.notes = values["notes"]
        tool.raw["name"] = tool.name
        tool.raw["synopsis"] = tool.synopsis
        tool.raw["command"] = command_list
        tool.raw["notes"] = tool.notes

        try:
            save_tool_manifest(tool)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Edit Tool", f"Failed to save manifest: {exc}")
            return

        self.reload_configuration()

    def _change_icon(self, tool: ToolManifest) -> None:
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Select Icon",
            str(tool.app_dir),
            "Images (*.png *.jpg *.jpeg *.svg *.webp);;All files (*.*)",
        )
        if not file_name:
            return

        source = Path(file_name)
        dest_name = source.name
        dest = tool.app_dir / dest_name

        counter = 1
        while dest.exists() and dest != tool.icon_path:
            dest_name = f"{source.stem}_{counter}{source.suffix.lower()}"
            dest = tool.app_dir / dest_name
            counter += 1

        try:
            shutil.copy2(source, dest)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Change Icon", f"Failed to copy icon: {exc}")
            return

        tool.icon_path = dest
        tool.raw["icon"] = dest_name

        try:
            save_tool_manifest(tool)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Change Icon", f"Failed to save manifest: {exc}")
            return

        self.reload_configuration()

    def _move_item(self, tool: ToolManifest) -> None:
        launcher_tab = self._launcher_tab_config()
        if not launcher_tab:
            return

        current_location = self._find_tool_location(tool.id)
        categories = launcher_tab.categories
        names = [category.name for category in categories]
        selected_name, ok = QInputDialog.getItem(
            self,
            "Move Tool",
            "Select destination category:",
            names,
            editable=False,
        )
        if not ok or not selected_name:
            return

        destination = next((c for c in categories if c.name == selected_name), None)
        if not destination:
            return

        if current_location and current_location[0].id == destination.id:
            return

        if current_location:
            current_category, _ = current_location
            current_category.item_ids = [tid for tid in current_category.item_ids if tid != tool.id]

        if tool.id not in destination.item_ids:
            destination.item_ids.append(tool.id)

        try:
            save_menu_config(self.menu_config)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Move Tool", f"Failed to update menu config: {exc}")
            return

        self.reload_configuration()

    def _reorder_item(self, tool: ToolManifest, delta: int) -> None:
        location = self._find_tool_location(tool.id)
        if not location:
            return

        category, index = location
        new_index = index + delta
        if new_index < 0 or new_index >= len(category.item_ids):
            return

        category.item_ids[index], category.item_ids[new_index] = (
            category.item_ids[new_index],
            category.item_ids[index],
        )

        try:
            save_menu_config(self.menu_config)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Reorder Tool", f"Failed to update menu config: {exc}")
            return

        self.reload_configuration()

    def _delete_item(self, tool: ToolManifest) -> None:
        response = QMessageBox.question(
            self,
            "Remove Tool",
            f"Remove '{tool.name}' from the menu? The tool files remain on disk.",
            QMessageBox.Yes | QMessageBox.No,
        )
        if response != QMessageBox.Yes:
            return

        location = self._find_tool_location(tool.id)
        if location:
            category, _ = location
            category.item_ids = [tid for tid in category.item_ids if tid != tool.id]

        try:
            save_menu_config(self.menu_config)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Remove Tool", f"Failed to update menu config: {exc}")
            return

        delete_files = QMessageBox.question(
            self,
            "Delete Files",
            "Delete the tool directory from disk as well?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if delete_files == QMessageBox.Yes:
            try:
                shutil.rmtree(tool.app_dir)
            except Exception as exc:  # noqa: BLE001
                QMessageBox.warning(self, "Delete Files", f"Failed to delete directory: {exc}")

        self.reload_configuration()

    def _add_category(self) -> None:
        tab = self._launcher_tab_config()
        if not tab:
            return

        category_id, ok = QInputDialog.getText(self, "Add Category", "Category ID:")
        if not ok or not category_id:
            return
        category_id = category_id.strip()
        if self._find_category(category_id):
            QMessageBox.warning(self, "Add Category", "Category ID already exists.")
            return

        name, ok = QInputDialog.getText(self, "Add Category", "Display Name:")
        if not ok or not name:
            return

        tab.categories.append(CategoryConfig(id=category_id, name=name.strip(), item_ids=[]))

        try:
            save_menu_config(self.menu_config)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Add Category", f"Failed to update menu config: {exc}")
            return

        self.reload_configuration()

    def _rename_category(self, category: CategoryConfig) -> None:
        new_name, ok = QInputDialog.getText(
            self,
            "Rename Category",
            "Display Name:",
            text=category.name,
        )
        if not ok or not new_name:
            return

        category.name = new_name.strip()

        try:
            save_menu_config(self.menu_config)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Rename Category", f"Failed to update menu config: {exc}")
            return

        self.reload_configuration()

    def _delete_category(self, category: CategoryConfig) -> None:
        if category.item_ids:
            response = QMessageBox.question(
                self,
                "Delete Category",
                "Category contains tools. Remove the category and unlink its tools?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if response != QMessageBox.Yes:
                return

        launcher_tab = self._launcher_tab_config()
        if not launcher_tab:
            return

        launcher_tab.categories = [c for c in launcher_tab.categories if c.id != category.id]

        try:
            save_menu_config(self.menu_config)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Delete Category", f"Failed to update menu config: {exc}")
            return

        self.reload_configuration()
