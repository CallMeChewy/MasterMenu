from __future__ import annotations

import json
import os
import shlex
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from PySide6.QtCore import QPoint, Qt, QSize, Signal, QMimeData
from PySide6.QtGui import (
    QIcon,
    QPixmap,
    QFont,
    QDrag,
    QDragEnterEvent,
    QDragMoveEvent,
    QDropEvent,
    QKeySequence,
    QShortcut,
    QCursor,
)
from PySide6.QtWidgets import (
    QApplication,
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
    QDialog,
    QDialogButtonBox,
    QLineEdit,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
    QFrame,
    QAbstractItemView,
    QComboBox,
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


TOOL_MIME_TYPE = "application/x-mastermenu-tool"


class ToolListWidget(QListWidget):
    order_changed = Signal(list)
    move_to_category_requested = Signal(str, object, str, object)
    rebuild_requested = Signal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._category_id: Optional[str] = None
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDropIndicatorShown(False)
        self.setViewMode(QListView.IconMode)
        self.setFlow(QListView.LeftToRight)
        self.setWrapping(True)
        self.setResizeMode(QListWidget.Adjust)
        self.setMovement(QListView.Snap)
        self.setDragDropMode(QAbstractItemView.DragDrop)
        self.setDragDropOverwriteMode(False)
        self.setGridSize(QSize(240, 220))
        self.setDefaultDropAction(Qt.MoveAction)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:  # type: ignore[override]
        if event.mimeData().hasFormat(TOOL_MIME_TYPE):
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event: QDragMoveEvent) -> None:  # type: ignore[override]
        if event.mimeData().hasFormat(TOOL_MIME_TYPE):
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dragLeaveEvent(self, event) -> None:  # type: ignore[override]
        super().dragLeaveEvent(event)

    def startDrag(self, supported_actions) -> None:  # type: ignore[override]
        items = self.selectedItems()
        if not items:
            return

        item = items[0]
        widget = self.itemWidget(item)
        if widget:
            pixmap = widget.grab().scaled(160, 140, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        else:
            pixmap = QPixmap(self.gridSize())
            pixmap.fill(Qt.transparent)

        drag = QDrag(self)
        drag.setMimeData(self.mimeData(items))
        drag.setPixmap(pixmap)
        drag.setHotSpot(pixmap.rect().center())

        QApplication.setOverrideCursor(QCursor(Qt.PointingHandCursor))
        try:
            drag.exec(supported_actions, Qt.MoveAction)
        finally:
            QApplication.restoreOverrideCursor()

    def set_category(self, category_id: Optional[str]) -> None:
        self._category_id = category_id

    def mimeTypes(self) -> List[str]:
        return [TOOL_MIME_TYPE]

    def mimeData(self, items: List[QListWidgetItem]) -> QMimeData:  # type: ignore[override]
        mime = super().mimeData(items)
        if not items:
            return mime
        payload = {
            "tool_ids": [item.data(Qt.UserRole) for item in items],
            "source_category": self._category_id,
        }
        mime.setData(TOOL_MIME_TYPE, json.dumps(payload).encode("utf-8"))
        return mime

    def dropEvent(self, event: QDropEvent) -> None:  # type: ignore[override]
        if event.mimeData().hasFormat(TOOL_MIME_TYPE):
            payload = json.loads(bytes(event.mimeData().data(TOOL_MIME_TYPE)).decode("utf-8"))
            tool_ids = payload.get("tool_ids", [])
            source_category = payload.get("source_category")
            if source_category and self._category_id and source_category != self._category_id:
                target_row = self._target_row_from_event(event)
                if tool_ids:
                    self.move_to_category_requested.emit(
                        tool_ids[0],
                        source_category,
                        self._category_id,
                        target_row,
                    )
                event.acceptProposedAction()
                return

        if not event.mimeData().hasFormat(TOOL_MIME_TYPE):
            event.ignore()
            return

        payload = json.loads(bytes(event.mimeData().data(TOOL_MIME_TYPE)).decode("utf-8"))
        tool_ids = payload.get("tool_ids", [])
        source_category = payload.get("source_category")
        target_index = self._target_row_from_event(event)

        if not tool_ids:
            event.ignore()
            return

        if not self._category_id:
            event.ignore()
            return

        self.parentWidget()._pending_selection = tool_ids[0] if hasattr(self.parentWidget(), "_pending_selection") else None
        parent = self.parent()
        if isinstance(parent, LauncherTab):
            parent.queue_tool_selection(tool_ids[0])

        self.move_to_category_requested.emit(
            tool_ids[0],
            source_category,
            self._category_id,
            target_index,
        )
        event.acceptProposedAction()
        self.rebuild_requested.emit()

    def _target_row_from_event(self, event: QDropEvent) -> Optional[int]:
        pos = event.position().toPoint()
        target_item = self.itemAt(pos)
        if target_item:
            return self.row(target_item)
        return self.count()


class CategoryListWidget(QListWidget):
    tool_drop_requested = Signal(str, object, str)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setAcceptDrops(True)
        self._hover_item: Optional[QListWidgetItem] = None
        self._previous_selection_row: Optional[int] = None

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:  # type: ignore[override]
        if event.mimeData().hasFormat(TOOL_MIME_TYPE):
            event.acceptProposedAction()
            self._previous_selection_row = self.currentRow()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event: QDragMoveEvent) -> None:  # type: ignore[override]
        if event.mimeData().hasFormat(TOOL_MIME_TYPE):
            event.acceptProposedAction()
            item = self.itemAt(event.position().toPoint())
            if item is not self._hover_item:
                if self._hover_item:
                    self._hover_item.setSelected(False)
                self._hover_item = item
                if item:
                    item.setSelected(True)
        else:
            super().dragMoveEvent(event)

    def dragLeaveEvent(self, event) -> None:  # type: ignore[override]
        if self._hover_item:
            self._hover_item.setSelected(False)
            self._hover_item = None
        if self._previous_selection_row is not None and self._previous_selection_row >= 0:
            self.setCurrentRow(self._previous_selection_row)
        self._previous_selection_row = None
        super().dragLeaveEvent(event)

    def dropEvent(self, event: QDropEvent) -> None:  # type: ignore[override]
        if self._hover_item:
            self._hover_item.setSelected(False)
            self._hover_item = None
        if self._previous_selection_row is not None and self._previous_selection_row >= 0:
            self.setCurrentRow(self._previous_selection_row)
        self._previous_selection_row = None
        if not event.mimeData().hasFormat(TOOL_MIME_TYPE):
            super().dropEvent(event)
            return

        item = self.itemAt(event.position().toPoint())
        if not item:
            event.ignore()
            return

        category_id = item.data(Qt.UserRole)
        payload = json.loads(bytes(event.mimeData().data(TOOL_MIME_TYPE)).decode("utf-8"))
        tool_ids = payload.get("tool_ids", [])
        source_category = payload.get("source_category")
        if tool_ids and category_id:
            self.tool_drop_requested.emit(tool_ids[0], source_category, category_id)
            event.acceptProposedAction()
        else:
            event.ignore()

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

    def __init__(self, menu_config: MenuConfig, tool_registry: Dict[str, ToolManifest], parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("launcherTab")
        self.menu_config = menu_config
        self.tool_registry = tool_registry
        self._current_tab_config = self._resolve_launcher_tab(menu_config)
        self._active_category_id: Optional[str] = None
        self._pending_selection: Optional[str] = None

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(16)

        self.category_list = CategoryListWidget()
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
        self.category_list.tool_drop_requested.connect(self._handle_category_drop)
        layout.addWidget(self.category_list, 1)

        self.item_list = ToolListWidget()
        self.item_list.setViewMode(QListView.IconMode)
        self.item_list.setFlow(QListView.LeftToRight)
        self.item_list.setWrapping(True)
        self.item_list.setResizeMode(QListWidget.Adjust)
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
        self.item_list.itemActivated.connect(self._on_item_activated)
        self.item_list.currentItemChanged.connect(self._on_item_changed)
        self.item_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.item_list.customContextMenuRequested.connect(self._show_context_menu)
        self.item_list.order_changed.connect(self._commit_order_change)
        self.item_list.move_to_category_requested.connect(self._handle_tool_move_request)
        self.item_list.rebuild_requested.connect(self._rebuild_active_category_view)
        layout.addWidget(self.item_list, 3)

        self._populate_categories(self._active_category_id)

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

    def _populate_categories(self, selected_category: Optional[str] = None) -> None:
        self.category_list.clear()
        if not self._current_tab_config:
            return

        target_row = 0
        for index, category in enumerate(self._current_tab_config.categories):
            item = QListWidgetItem(category.name)
            item.setData(Qt.UserRole, category.id)
            self.category_list.addItem(item)
            if selected_category and category.id == selected_category:
                target_row = index

        if self.category_list.count() > 0:
            self.category_list.setCurrentRow(target_row)
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

    def _populate_items(self, category_config, selected_tool_id: Optional[str] = None) -> None:
        self.item_list.clear()
        self.item_list.set_category(category_config.id if category_config else None)
        if not category_config:
            return

        target_row = 0
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

            current_row = self.item_list.row(item)
            if selected_tool_id and tool.id == selected_tool_id:
                target_row = current_row

        if self.item_list.count() > 0:
            self.item_list.setCurrentRow(target_row)

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
            self.request_launch.emit(tool)

    def _on_item_changed(self, current: Optional[QListWidgetItem], _previous: Optional[QListWidgetItem]) -> None:
        if not current:
            self.tool_selected.emit(None)
            return
        tool_id = current.data(Qt.UserRole)
        tool = self.tool_registry.get(tool_id)
        if tool:
            self.tool_selected.emit(tool)

    def _commit_order_change(self, ordered_ids: List[str]) -> None:
        if not self._active_category_id:
            return
        category = self._find_category(self._active_category_id)
        if not category:
            return
        if len(ordered_ids) != len(category.item_ids):
            return
        if ordered_ids == category.item_ids:
            return
        category.item_ids = list(ordered_ids)
        payload = {
            "category_id": self._active_category_id,
            "ordered_ids": ordered_ids,
        }
        self.maintenance_action_requested.emit("reorder_category_items", payload)

    def _handle_tool_move_request(
        self,
        tool_id: str,
        source_category: Optional[str],
        target_category: str,
        target_index: Optional[int],
    ) -> None:
        if not tool_id or not target_category:
            return
        payload = {
            "tool_id": tool_id,
            "destination_category": target_category,
        }
        if source_category:
            payload["source_category"] = source_category
        if target_index is not None:
            payload["target_index"] = target_index
        self.maintenance_action_requested.emit("move_item_to_category", payload)

    def _handle_category_drop(
        self,
        tool_id: str,
        source_category: Optional[str],
        target_category: str,
    ) -> None:
        self._handle_tool_move_request(tool_id, source_category, target_category, None)

    def queue_tool_selection(self, tool_id: str) -> None:
        self._pending_selection = tool_id

    def _rebuild_active_category_view(self) -> None:
        if not self._active_category_id:
            return
        category_config = self._find_category(self._active_category_id)
        selected_tool_id = None
        current_item = self.item_list.currentItem()
        if current_item:
            selected_tool_id = current_item.data(Qt.UserRole)
        selection = selected_tool_id or self._pending_selection
        self._populate_items(category_config, selection)
        self._pending_selection = None

    def _show_context_menu(self, position: QPoint) -> None:
        item = self.item_list.itemAt(position)
        menu = QMenu(self)

        if not item:
            add_tool_action = None
            if self._active_category_id:
                add_tool_action = menu.addAction("Add Tool…")
            add_category_action = menu.addAction("Add Category…")

            selected_action = menu.exec(self.item_list.mapToGlobal(position))
            if selected_action == add_tool_action and self._active_category_id:
                self.add_tool_requested.emit(self._active_category_id)
            elif selected_action == add_category_action:
                self.category_action_requested.emit("add_category", {})
            return

        tool = self.tool_registry.get(item.data(Qt.UserRole))
        if not tool:
            return

        open_folder_action = menu.addAction("Open Tool Folder")
        readme_action = None
        if tool.readme_path.exists():
            readme_action = menu.addAction("Open README")
        menu.addSeparator()
        edit_action = menu.addAction("Edit Tool…")
        change_icon_action = menu.addAction("Change Icon…")

        selected_action = menu.exec(self.item_list.mapToGlobal(position))

        if selected_action == open_folder_action:
            self._open_tool_folder(tool)
        elif selected_action == readme_action:
            self._open_tool_readme(tool)
        elif selected_action == edit_action:
            self.maintenance_action_requested.emit("edit_item", {"tool_id": tool.id})
        elif selected_action == change_icon_action:
            self.maintenance_action_requested.emit("change_icon", {"tool_id": tool.id})

    def _open_tool_folder(self, tool: ToolManifest) -> None:
        folder = tool.app_dir
        if not _open_with_system_handler(folder):
            QMessageBox.information(self, "Tool Folder", str(folder))

    def _open_tool_readme(self, tool: ToolManifest) -> None:
        readme = tool.readme_path
        if not readme.exists():
            QMessageBox.information(self, "README", "No README found for this tool.")
            return
        if not _open_with_system_handler(readme):
            QMessageBox.information(self, "README", str(readme))

    def _show_category_context_menu(self, position: QPoint) -> None:
        item = self.category_list.itemAt(position)
        menu = QMenu(self)

        add_category_action = menu.addAction("Add Category…")
        selected_category_id: Optional[str] = None

        add_item_action = None
        rename_action = None
        delete_action = None

        if item:
            selected_category_id = item.data(Qt.UserRole)
            menu.addSeparator()
            add_item_action = menu.addAction("Add Tool to Category…")
            rename_action = menu.addAction("Rename Category…")
            delete_action = menu.addAction("Delete Category")

        selected = menu.exec(self.category_list.mapToGlobal(position))

        if selected == add_category_action:
            self.category_action_requested.emit("add_category", {})
        elif selected == add_item_action and selected_category_id:
            self.add_tool_requested.emit(selected_category_id)
        elif selected == rename_action and selected_category_id:
            self.category_action_requested.emit("rename_category", {"category_id": selected_category_id})
        elif selected == delete_action and selected_category_id:
            self.category_action_requested.emit("delete_category", {"category_id": selected_category_id})

    def refresh(self, menu_config: MenuConfig, tool_registry: Dict[str, ToolManifest]) -> None:
        self.menu_config = menu_config
        self.tool_registry = tool_registry
        self._current_tab_config = self._resolve_launcher_tab(menu_config)
        self._populate_categories(self._active_category_id)


class MaintenanceTab(QWidget):
    add_tool_requested = Signal(str)
    delete_tool_requested = Signal(str)
    add_category_requested = Signal()
    rename_category_requested = Signal(str)
    delete_category_requested = Signal(str)
    reload_requested = Signal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._menu_config: Optional[MenuConfig] = None
        self._tool_registry: Dict[str, ToolManifest] = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(18)

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
            QComboBox {
                background: rgba(12, 30, 60, 0.9);
                border-radius: 10px;
                padding: 6px 10px;
                color: #f0f6ff;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #1a3d73,
                    stop:1 #1b5aa6);
                border-radius: 12px;
                padding: 9px 18px;
                color: #f3f8ff;
            }
            QPushButton:disabled {
                background: rgba(40, 70, 110, 0.5);
                color: rgba(235, 245, 255, 0.4);
            }
            QPushButton:hover:!disabled {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #22508d,
                    stop:1 #2470d0);
            }
            """
        )

        category_row = QHBoxLayout()
        category_row.addWidget(QLabel("Category:"))
        self.category_combo = QComboBox()
        self.category_combo.currentIndexChanged.connect(self._populate_tool_combo)
        category_row.addWidget(self.category_combo, 1)
        layout.addLayout(category_row)

        category_buttons = QHBoxLayout()
        self.add_category_button = QPushButton("Add Category…")
        self.add_category_button.clicked.connect(self.add_category_requested)
        category_buttons.addWidget(self.add_category_button)

        self.rename_category_button = QPushButton("Rename Category…")
        self.rename_category_button.clicked.connect(self._emit_rename_category)
        category_buttons.addWidget(self.rename_category_button)

        self.delete_category_button = QPushButton("Delete Category…")
        self.delete_category_button.clicked.connect(self._emit_delete_category)
        category_buttons.addWidget(self.delete_category_button)
        category_buttons.addStretch(1)
        layout.addLayout(category_buttons)

        tool_row = QHBoxLayout()
        tool_row.addWidget(QLabel("Tool:"))
        self.tool_combo = QComboBox()
        tool_row.addWidget(self.tool_combo, 1)
        layout.addLayout(tool_row)

        tool_buttons = QHBoxLayout()
        self.add_tool_button = QPushButton("Add Tool to Category…")
        self.add_tool_button.clicked.connect(self._emit_add_tool)
        tool_buttons.addWidget(self.add_tool_button)

        self.delete_tool_button = QPushButton("Remove Tool…")
        self.delete_tool_button.clicked.connect(self._emit_delete_tool)
        tool_buttons.addWidget(self.delete_tool_button)
        tool_buttons.addStretch(1)
        layout.addLayout(tool_buttons)

        layout.addStretch(1)

        self.reload_button = QPushButton("Reload Configuration")
        self.reload_button.clicked.connect(self.reload_requested)
        layout.addWidget(self.reload_button, 0, Qt.AlignRight)

        self.refresh(None, {})

    def refresh(self, menu_config: Optional[MenuConfig], tool_registry: Dict[str, ToolManifest]) -> None:
        self._menu_config = menu_config
        self._tool_registry = tool_registry
        self.category_combo.blockSignals(True)
        self.category_combo.clear()
        self.category_combo.addItem("Select category…", None)

        launcher_tab = None
        if menu_config:
            for tab in menu_config.tabs:
                if tab.id == "launcher":
                    launcher_tab = tab
                    break
            if not launcher_tab and menu_config.tabs:
                launcher_tab = menu_config.tabs[0]

        if launcher_tab:
            for category in launcher_tab.categories:
                self.category_combo.addItem(category.name, category.id)

        self.category_combo.blockSignals(False)
        self._populate_tool_combo()
        self._update_button_states()

    def _populate_tool_combo(self) -> None:
        self.tool_combo.clear()
        self.tool_combo.addItem("Select tool…", None)
        if not self._menu_config:
            self._update_button_states()
            return

        launcher_tab = None
        for tab in self._menu_config.tabs:
            if tab.id == "launcher":
                launcher_tab = tab
                break
        if not launcher_tab and self._menu_config.tabs:
            launcher_tab = self._menu_config.tabs[0]

        selected_category = self._current_category_id()
        if not launcher_tab:
            self._update_button_states()
            return

        for category in launcher_tab.categories:
            if selected_category and category.id != selected_category:
                continue
            for tool_id in category.item_ids:
                tool = self._tool_registry.get(tool_id)
                if not tool:
                    continue
                label = tool.name
                if not selected_category:
                    label = f"{tool.name} ({category.name})"
                self.tool_combo.addItem(label, tool.id)

        self._update_button_states()

    def _current_category_id(self) -> Optional[str]:
        return self.category_combo.currentData()

    def _current_tool_id(self) -> Optional[str]:
        return self.tool_combo.currentData()

    def _emit_add_tool(self) -> None:
        category_id = self._current_category_id()
        if not category_id:
            QMessageBox.information(self, "Add Tool", "Select a category first.")
            return
        self.add_tool_requested.emit(category_id)

    def _emit_delete_tool(self) -> None:
        tool_id = self._current_tool_id()
        if not tool_id:
            QMessageBox.information(self, "Remove Tool", "Select a tool to remove.")
            return
        self.delete_tool_requested.emit(tool_id)

    def _emit_rename_category(self) -> None:
        category_id = self._current_category_id()
        if not category_id:
            QMessageBox.information(self, "Rename Category", "Select a category first.")
            return
        self.rename_category_requested.emit(category_id)

    def _emit_delete_category(self) -> None:
        category_id = self._current_category_id()
        if not category_id:
            QMessageBox.information(self, "Delete Category", "Select a category first.")
            return
        self.delete_category_requested.emit(category_id)

    def _update_button_states(self) -> None:
        has_category = self._current_category_id() is not None
        has_tool = self._current_tool_id() is not None
        self.add_tool_button.setEnabled(has_category)
        self.rename_category_button.setEnabled(has_category)
        self.delete_category_button.setEnabled(has_category)
        self.delete_tool_button.setEnabled(has_tool)
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
        self.maintenance_tab = MaintenanceTab()

        self.tabs.addTab(self.launcher_tab, "Launcher")
        self.tabs.addTab(self.maintenance_tab, "Maintenance")

        self.launcher_tab.tool_selected.connect(self._update_status_with_tool)
        self.launcher_tab.request_launch.connect(self.launch_tool)
        self.launcher_tab.maintenance_action_requested.connect(self.handle_maintenance_action)
        self.launcher_tab.add_tool_requested.connect(self.handle_add_tool)
        self.launcher_tab.category_action_requested.connect(self.handle_category_action)

        self.maintenance_tab.refresh(self.menu_config, self.tool_registry)
        self.maintenance_tab.add_tool_requested.connect(self.handle_add_tool)
        self.maintenance_tab.delete_tool_requested.connect(self._delete_tool_from_maintenance)
        self.maintenance_tab.add_category_requested.connect(lambda: self.handle_category_action("add_category", {}))
        self.maintenance_tab.rename_category_requested.connect(
            lambda category_id: self.handle_category_action("rename_category", {"category_id": category_id})
        )
        self.maintenance_tab.delete_category_requested.connect(
            lambda category_id: self.handle_category_action("delete_category", {"category_id": category_id})
        )
        self.maintenance_tab.reload_requested.connect(self.reload_configuration)

        self.reload_shortcut = QShortcut(QKeySequence("Ctrl+R"), self)
        self.reload_shortcut.activated.connect(self.reload_configuration)

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

    def _update_status_with_tool(self, tool: Optional[ToolManifest]) -> None:
        if not tool:
            self.statusBar().clearMessage()
            return
        synopsis = tool.synopsis or tool.notes or ""
        message = tool.name if not synopsis else f"{tool.name} – {synopsis}"
        self.statusBar().showMessage(message, 5000)

    def _delete_tool_from_maintenance(self, tool_id: str) -> None:
        tool = self.tool_registry.get(tool_id)
        if not tool:
            QMessageBox.warning(self, "Remove Tool", "Tool not found.")
            return
        self._delete_item(tool)

    def reload_configuration(self) -> None:
        try:
            self.menu_config = load_menu_config()
            self.tool_registry = build_tool_registry(self.menu_config)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Reload Failed", str(exc))
            return

        self.launcher_tab.refresh(self.menu_config, self.tool_registry)
        self.maintenance_tab.refresh(self.menu_config, self.tool_registry)
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
        actions_requiring_tool = {
            "edit_item",
            "change_icon",
            "move_item",
            "move_item_up",
            "move_item_down",
            "delete_item",
            "move_item_to_category",
        }

        if action in actions_requiring_tool and not tool:
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
        elif action == "move_item_to_category" and tool:
            destination = payload.get("destination_category")
            index = payload.get("target_index")
            self._move_tool_to_category(tool, destination, index)
        elif action == "reorder_category_items":
            category_id = payload.get("category_id")
            ordered_ids = payload.get("ordered_ids", [])
            self._reorder_category_items(category_id, ordered_ids)

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

    def _move_tool_to_category(
        self,
        tool: ToolManifest,
        destination_id: Optional[str],
        target_index: Optional[int],
    ) -> None:
        if not destination_id:
            return

        destination = self._find_category(destination_id)
        if not destination:
            QMessageBox.warning(self, "Move Tool", f"Category '{destination_id}' not found.")
            return

        location = self._find_tool_location(tool.id)
        if not location:
            QMessageBox.warning(self, "Move Tool", "Tool location could not be determined.")
            return

        source_category, source_index = location

        if destination.id == source_category.id:
            item_ids = source_category.item_ids
            item_ids.pop(source_index)
            insert_at = target_index if target_index is not None else len(item_ids)
            insert_at = max(0, min(insert_at, len(item_ids)))
            item_ids.insert(insert_at, tool.id)
        else:
            source_category.item_ids = [tid for tid in source_category.item_ids if tid != tool.id]
            insert_at = target_index if target_index is not None else len(destination.item_ids)
            insert_at = max(0, min(insert_at, len(destination.item_ids)))
            destination.item_ids.insert(insert_at, tool.id)

        try:
            save_menu_config(self.menu_config)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Move Tool", f"Failed to update menu config: {exc}")
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

    def _reorder_category_items(self, category_id: Optional[str], ordered_ids: List[str]) -> None:
        if not category_id:
            return
        category = self._find_category(category_id)
        if not category:
            QMessageBox.warning(self, "Reorder", f"Category '{category_id}' not found.")
            return
        if set(ordered_ids) != set(category.item_ids):
            QMessageBox.warning(self, "Reorder", "Mismatch between tool lists; aborting reorder.")
            return

        category.item_ids = ordered_ids

        try:
            save_menu_config(self.menu_config)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Reorder", f"Failed to update menu config: {exc}")
            return

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
