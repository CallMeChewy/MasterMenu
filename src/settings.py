from pathlib import Path

# Base directory for the MasterMenu application (one level above src).
PROJECT_ROOT = Path(__file__).resolve().parent.parent

ASSETS_DIR = PROJECT_ROOT / "assets"
APPS_DIR = PROJECT_ROOT / "apps"
MENU_CONFIG_PATH = PROJECT_ROOT / "menu_config.yaml"

BACKUP_DIR = PROJECT_ROOT / "backups"
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

WORKDIR_ROOT = Path.home() / ".local/share/mastermenu"
WORKDIR_ROOT.mkdir(parents=True, exist_ok=True)
