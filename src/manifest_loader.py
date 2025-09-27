from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import yaml

from settings import APPS_DIR, MENU_CONFIG_PATH, BACKUP_DIR


class ManifestError(RuntimeError):
    """Raised when an application manifest cannot be loaded."""


@dataclass
class ToolManifest:
    id: str
    name: str
    synopsis: str
    command: List[str]
    cwd: Path
    env: Dict[str, str]
    icon_path: Path
    notes: str
    tags: List[str]
    manifest_path: Path
    venv_path: Optional[Path] = None
    auto_create_venv: bool = False
    raw: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        data = dict(self.raw)
        data["id"] = self.id
        data["name"] = self.name
        data["synopsis"] = self.synopsis
        data["command"] = list(self.command)

        if "cwd" in self.raw:
            data["cwd"] = self.raw.get("cwd", ".")
        else:
            try:
                rel_cwd = self.cwd.relative_to(self.app_dir)
                data["cwd"] = str(rel_cwd)
            except ValueError:
                data["cwd"] = str(self.cwd)

        data["env"] = dict(self.env)

        if "icon" in self.raw and self.raw.get("icon"):
            data["icon"] = self.raw["icon"]
        else:
            if self.icon_path.parent == self.app_dir:
                data["icon"] = self.icon_path.name
            else:
                data["icon"] = str(self.icon_path)

        data["notes"] = self.notes
        data["tags"] = list(self.tags)

        if self.venv_path:
            try:
                rel_path = self.venv_path.relative_to(self.app_dir)
                venv_path = str(rel_path)
            except ValueError:
                venv_path = str(self.venv_path)
            data["venv"] = {
                "path": venv_path,
                "auto_create": self.auto_create_venv,
            }
        elif "venv" in data:
            data.pop("venv", None)

        return data

    @property
    def app_dir(self) -> Path:
        return self.manifest_path.parent

    @property
    def readme_path(self) -> Path:
        return self.app_dir / "README.md"


@dataclass
class CategoryConfig:
    id: str
    name: str
    item_ids: List[str]

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "items": list(self.item_ids),
        }


@dataclass
class TabConfig:
    id: str
    name: str
    categories: List[CategoryConfig]
    layout: Dict
    locked: bool = False
    template: Optional[str] = None

    def to_dict(self) -> Dict:
        data: Dict[str, object] = {
            "id": self.id,
            "name": self.name,
            "categories": [category.to_dict() for category in self.categories],
        }
        if self.layout:
            data["layout"] = self.layout
        if self.locked:
            data["locked"] = self.locked
        if self.template:
            data["template"] = self.template
        return data


@dataclass
class MenuConfig:
    tabs: List[TabConfig]
    metadata: Dict

    def to_dict(self) -> Dict:
        data: Dict[str, object] = {
            "tabs": [tab.to_dict() for tab in self.tabs],
        }
        if self.metadata:
            data["metadata"] = self.metadata
        return data


def _coerce_command(raw_cmd) -> List[str]:
    if isinstance(raw_cmd, str):
        return [raw_cmd]
    if isinstance(raw_cmd, (list, tuple)):
        return [str(part) for part in raw_cmd]
    raise ManifestError(f"Command must be a string or list, got {type(raw_cmd)!r}")


def load_tool_manifest(tool_id: str) -> ToolManifest:
    manifest_path = APPS_DIR / tool_id / "app.yaml"
    if not manifest_path.exists():
        raise ManifestError(f"Manifest not found for tool '{tool_id}' at {manifest_path}")

    data = yaml.safe_load(manifest_path.read_text()) or {}

    command = _coerce_command(data.get("command", []))
    if not command:
        raise ManifestError(f"Tool '{tool_id}' missing command in manifest")

    cwd_field = data.get("cwd", ".")
    cwd_path = (manifest_path.parent / cwd_field).resolve()

    env = {str(k): str(v) for k, v in (data.get("env") or {}).items()}

    icon_name = data.get("icon", "icon.png")
    icon_path = (manifest_path.parent / icon_name).resolve()

    notes = str(data.get("notes", "")).strip()
    tags = [str(tag) for tag in data.get("tags", [])]

    venv_cfg = data.get("venv") or {}
    venv_path = None
    auto_create = False
    if "path" in venv_cfg:
        venv_path = (manifest_path.parent / venv_cfg["path"]).resolve()
        auto_create = bool(venv_cfg.get("auto_create", False))

    return ToolManifest(
        id=tool_id,
        name=str(data.get("name", tool_id)).strip() or tool_id,
        synopsis=str(data.get("synopsis", "")).strip(),
        command=command,
        cwd=cwd_path,
        env=env,
        icon_path=icon_path,
        notes=notes,
        tags=tags,
        manifest_path=manifest_path,
        venv_path=venv_path,
        auto_create_venv=auto_create,
        raw=data,
    )


def load_menu_config() -> MenuConfig:
    if not MENU_CONFIG_PATH.exists():
        raise ManifestError(f"Menu configuration not found at {MENU_CONFIG_PATH}")

    data = yaml.safe_load(MENU_CONFIG_PATH.read_text()) or {}

    tabs: List[TabConfig] = []
    for tab_data in data.get("tabs", []):
        categories: List[CategoryConfig] = []
        for cat_data in tab_data.get("categories", []) or []:
            category = CategoryConfig(
                id=str(cat_data.get("id")),
                name=str(cat_data.get("name", cat_data.get("id", "Unnamed"))),
                item_ids=[str(item) for item in (cat_data.get("items") or [])],
            )
            categories.append(category)

        tab = TabConfig(
            id=str(tab_data.get("id")),
            name=str(tab_data.get("name", tab_data.get("id", "Tab"))),
            categories=categories,
            layout=tab_data.get("layout") or {},
            locked=bool(tab_data.get("locked", False)),
            template=tab_data.get("template"),
        )
        tabs.append(tab)

    metadata = data.get("metadata", {})

    return MenuConfig(tabs=tabs, metadata=metadata)


def build_tool_registry(menu_config: MenuConfig) -> Dict[str, ToolManifest]:
    tool_ids = set()
    for tab in menu_config.tabs:
        for category in tab.categories:
            tool_ids.update(category.item_ids)

    registry: Dict[str, ToolManifest] = {}
    for tool_id in sorted(tool_ids):
        try:
            registry[tool_id] = load_tool_manifest(tool_id)
        except ManifestError as exc:
            # Skip missing manifests but log in metadata for UI
            registry[tool_id] = ToolManifest(
                id=tool_id,
                name=f"{tool_id} (missing)",
                synopsis=str(exc),
                command=["echo", str(exc)],
                cwd=APPS_DIR,
                env={},
                icon_path=APPS_DIR / tool_id / "icon.png",
                notes=str(exc),
                tags=["invalid"],
                manifest_path=APPS_DIR / tool_id / "app.yaml",
                raw={},
            )
    return registry


def _ensure_backup_dir(name: str) -> Path:
    target = BACKUP_DIR / name
    target.mkdir(parents=True, exist_ok=True)
    return target


def _write_with_backup(target_path: Path, data: str, backup_subdir: str) -> None:
    if target_path.exists():
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = _ensure_backup_dir(backup_subdir)
        backup_path = backup_dir / f"{target_path.stem}_{timestamp}{target_path.suffix}"
        backup_path.write_text(target_path.read_text())
    target_path.write_text(data)


def save_menu_config(menu_config: MenuConfig) -> None:
    payload = menu_config.to_dict()
    yaml_str = yaml.safe_dump(payload, sort_keys=False, allow_unicode=True)
    _write_with_backup(MENU_CONFIG_PATH, yaml_str, "menu_config")


def save_tool_manifest(manifest: ToolManifest) -> None:
    data = manifest.to_dict()
    yaml_str = yaml.safe_dump(data, sort_keys=False, allow_unicode=True)
    _write_with_backup(manifest.manifest_path, yaml_str, f"manifests/{manifest.id}")
