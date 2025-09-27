# MasterMenu

MasterMenu consolidates local helper scripts and mini-apps into a PySide6 desktop launcher with maintenance tooling.

## Quick Start

1. **Install dependencies**
   
   ```bash
   cd MasterMenu
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. **Run the menu**
   
   ```bash
   python src/main.py
   ```
3. Launch tools from the **Launcher** tab. Select an item to preview details or hit **Maintenance Mode** in the toolbar to add/edit/reorder entries directly.

## Features

- YAML-powered configuration (`menu_config.yaml` + `apps/<tool>/app.yaml`) for predictable category/order management.
- In-app maintenance: create new tools from the template scaffold, edit metadata, move tools between categories, tweak launch commands, or change icons (placeholder art ships by default).
- Tool directories live under `apps/`, each with its own README, launcher script, and optional `.venv/` for isolation.
- Automatic backups of manifests/configs whenever maintenance actions save changes (see `backups/`).

## Structure

```
MasterMenu/
├── apps/               # Individual tool folders + template scaffold
├── assets/             # Shared icons and placeholders
├── menu_config.yaml    # Tab/category definitions for the launcher UI
├── requirements.txt    # PySide6 + PyYAML dependencies
└── src/                # PySide6 application code
```

## Maintenance Notes

- Use Maintenance Mode (toolbar toggle) for live edits. A reload button keeps the UI in sync with manual YAML edits if you prefer working in a text editor.
- When adding icons later, drop art in the tool directory or use the “Change Icon…” action, which copies the selected file and updates the manifest.

## Next Steps

- Migrate remaining scripts into `apps/` following the existing pattern.
- Swap placeholder icons for bespoke art once available.
- Extend maintenance tooling (drag-and-drop ordering, validation, etc.) as needs evolve.
