#!/usr/bin/env python3
"""Generate PATH wrappers for CLI-friendly MasterMenu tools.

Tools opt-in by including the tag "cli" in their app.yaml file. Wrappers live in
bin/<tool-id> and simply delegate to the tool's run.sh script.
"""
from __future__ import annotations

import os
import stat
import sys
from pathlib import Path
from typing import Iterable

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    sys.exit(f"PyYAML is required to generate wrappers: {exc}")

WRAPPER_TEMPLATE = """#!/usr/bin/env bash
set -euo pipefail
APP_DIR=\"{app_dir}\"
exec \"${{APP_DIR}}/run.sh\" \"$@\"
"""


def find_cli_tools(apps_dir: Path) -> Iterable[tuple[str, Path]]:
    for entry in sorted(apps_dir.iterdir()):
        if not entry.is_dir() or entry.name.startswith("."):
            continue
        app_yaml = entry / "app.yaml"
        if not app_yaml.exists():
            continue
        try:
            data = yaml.safe_load(app_yaml.read_text()) or {}
        except yaml.YAMLError as exc:
            print(f"Skipping {entry.name}: failed to parse app.yaml ({exc})", file=sys.stderr)
            continue
        tags = data.get("tags") or []
        expose_cli = data.get("expose_cli")
        if isinstance(tags, dict):  # tolerate incorrect type
            tags = list(tags.values())
        normalized_tags = {str(tag).lower() for tag in tags}
        if expose_cli or "cli" in normalized_tags:
            tool_id = str(data.get("id") or entry.name)
            yield tool_id, entry


def write_wrapper(wrapper_dir: Path, tool_id: str, app_dir: Path) -> None:
    wrapper_path = wrapper_dir / tool_id
    wrapper_path.write_text(WRAPPER_TEMPLATE.format(app_dir=app_dir.as_posix()))
    wrapper_path.chmod(wrapper_path.stat().st_mode | stat.S_IEXEC)


def remove_stale_wrappers(wrapper_dir: Path, valid_ids: set[str]) -> None:
    for wrapper in wrapper_dir.iterdir():
        if wrapper.is_file() and os.access(wrapper, os.X_OK) and wrapper.name not in valid_ids:
            wrapper.unlink()


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: update_wrappers.py <apps-dir> <wrapper-dir>", file=sys.stderr)
        return 1

    apps_dir = Path(sys.argv[1]).resolve()
    wrapper_dir = Path(sys.argv[2]).resolve()
    wrapper_dir.mkdir(parents=True, exist_ok=True)

    valid_ids: set[str] = set()

    for tool_id, app_dir in find_cli_tools(apps_dir):
        valid_ids.add(tool_id)
        write_wrapper(wrapper_dir, tool_id, app_dir)
        print(f"Generated wrapper bin/{tool_id}")

    remove_stale_wrappers(wrapper_dir, valid_ids)
    return 0


if __name__ == "__main__":
    sys.exit(main())
