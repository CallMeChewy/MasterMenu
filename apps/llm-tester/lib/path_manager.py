#!/usr/bin/env python3
# File: path_manager.py
# Path: /home/herb/Desktop/MasterMenu/apps/llm-tester/lib/path_manager.py
# Standard: AIDEV-PascalCase-2.1
# Created: 2025-10-04
# Last Modified: 2025-10-04 6:45PM

"""
Path Manager for LLM-Tester
Handles relocatable paths, symlinks, and persistent data management
"""

import os
import sys
import yaml
import json
from pathlib import Path
from typing import Dict, Optional, List
import logging

class PathManager:
    """
    Manages all paths for the LLM-Tester application with support for:
    - Device relocation through symlinks
    - Persistent data storage
    - Configuration management
    - Library loading
    """

    def __init__(self, config_file: str = "config/config.yaml"):
        """Initialize the path manager with configuration"""
        self.app_root = self._find_app_root()
        self.config_file = config_file
        self.config = self._load_config()
        self.paths = self._resolve_all_paths()
        self._ensure_directories()

        # Setup logging
        self._setup_logging()

    def _find_app_root(self) -> Path:
        """Find the application root directory by looking for app.yaml"""
        current = Path(__file__).parent

        # Look for app.yaml in parent directories
        for parent in [current] + list(current.parents):
            if (parent / "app.yaml").exists():
                return parent

        # Fallback to script directory
        return current.parent

    def _load_config(self) -> Dict:
        """Load configuration from YAML file"""
        config_path = self.app_root / self.config_file

        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    return yaml.safe_load(f)
            except Exception as e:
                logging.warning(f"Failed to load config from {config_path}: {e}")

        # Return default configuration
        return self._get_default_config()

    def _get_default_config(self) -> Dict:
        """Get default configuration when config file is not available"""
        return {
            "paths": {
                "data_dir": "data",
                "db_dir": "db",
                "results_dir": "results",
                "logs_dir": "logs",
                "src_dir": "src",
                "lib_dir": "lib",
                "tools_dir": "tools"
            },
            "database": {
                "default": "db/llm_tester.db"
            }
        }

    def _resolve_all_paths(self) -> Dict[str, Path]:
        """Resolve all application paths with proper handling of symlinks"""
        paths = {}
        config_paths = self.config.get("paths", {})

        # Core paths
        for path_name, path_rel in config_paths.items():
            abs_path = self.app_root / path_rel
            resolved_path = abs_path.resolve()

            # Create if it doesn't exist
            if not resolved_path.exists():
                resolved_path.mkdir(parents=True, exist_ok=True)

            paths[path_name] = resolved_path

        # Additional computed paths
        paths["app_root"] = self.app_root
        paths["config_file"] = self.app_root / self.config_file
        paths["main_db"] = paths["db_dir"] / "llm_tester.db"

        # Results subdirectories
        results_dir = paths["results_dir"]
        paths["optimization_results"] = results_dir / "optimization"
        paths["test_results"] = results_dir / "testing"
        paths["visualizations"] = results_dir / "visualizations"
        paths["exports"] = results_dir / "exports"

        # External data paths (can be symlinked)
        paths["external_data"] = paths["data_dir"] / "external"
        paths["models"] = paths["data_dir"] / "models"

        return paths

    def _ensure_directories(self):
        """Ensure all necessary directories exist"""
        for path_name, path_obj in self.paths.items():
            if path_name.endswith("_dir") or path_name in ["optimization_results", "test_results", "visualizations", "exports", "external_data", "models"]:
                try:
                    path_obj.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    logging.error(f"Failed to create directory {path_name}: {e}")

    def _setup_logging(self):
        """Setup logging configuration"""
        log_dir = self.paths.get("logs_dir", self.app_root / "logs")
        log_file = log_dir / "app.log"

        # Ensure log directory exists
        log_dir.mkdir(parents=True, exist_ok=True)

        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )

        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Path manager initialized with root: {self.app_root}")

    def get_path(self, path_name: str) -> Optional[Path]:
        """Get a specific path by name"""
        return self.paths.get(path_name)

    def get_relative_path(self, path_name: str) -> Optional[str]:
        """Get a path relative to the application root"""
        path = self.get_path(path_name)
        if path:
            return str(path.relative_to(self.app_root))
        return None

    def ensure_external_link(self, link_name: str, target_path: str) -> bool:
        """
        Create or update an external symlink for data that may be on different devices

        Args:
            link_name: Name of the link (e.g., "large_datasets")
            target_path: Target path to link to

        Returns:
            True if successful, False otherwise
        """
        try:
            external_dir = self.paths["external_data"]
            link_path = external_dir / link_name

            # Remove existing link if it exists
            if link_path.exists():
                if link_path.is_symlink():
                    link_path.unlink()
                else:
                    self.logger.warning(f"Existing non-symlink found at {link_path}")
                    return False

            # Create new symlink
            link_path.symlink_to(Path(target_path))
            self.logger.info(f"Created external symlink: {link_path} -> {target_path}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to create external symlink {link_name}: {e}")
            return False

    def backup_data(self, backup_name: Optional[str] = None) -> str:
        """
        Create a backup of all application data

        Args:
            backup_name: Optional name for backup (defaults to timestamp)

        Returns:
            Path to backup directory
        """
        import shutil
        from datetime import datetime

        if backup_name is None:
            backup_name = datetime.now().strftime("%Y%m%d_%H%M%S")

        backup_dir = self.app_root / "backups" / backup_name

        try:
            # Create backup directory
            backup_dir.mkdir(parents=True, exist_ok=True)

            # Backup key directories
            backup_items = [
                ("db", self.paths["db_dir"]),
                ("results", self.paths["results_dir"]),
                ("config", self.paths["config_dir"]),
                ("logs", self.paths["logs_dir"])
            ]

            for name, source in backup_items:
                if source.exists():
                    dest = backup_dir / name
                    shutil.copytree(source, dest, dirs_exist_ok=True)
                    self.logger.info(f"Backed up {name} to {dest}")

            self.logger.info(f"Backup completed: {backup_dir}")
            return str(backup_dir)

        except Exception as e:
            self.logger.error(f"Backup failed: {e}")
            raise

    def restore_data(self, backup_path: str) -> bool:
        """
        Restore data from a backup

        Args:
            backup_path: Path to backup directory

        Returns:
            True if successful, False otherwise
        """
        import shutil

        try:
            backup_dir = Path(backup_path)
            if not backup_dir.exists():
                self.logger.error(f"Backup directory does not exist: {backup_path}")
                return False

            # Restore key directories
            restore_items = [
                ("db", self.paths["db_dir"]),
                ("results", self.paths["results_dir"]),
                ("config", self.paths["config_dir"]),
                ("logs", self.paths["logs_dir"])
            ]

            for name, dest in restore_items:
                source = backup_dir / name
                if source.exists():
                    if dest.exists():
                        shutil.rmtree(dest)
                    shutil.copytree(source, dest)
                    self.logger.info(f"Restored {name} from {source}")

            self.logger.info(f"Restore completed from: {backup_path}")
            return True

        except Exception as e:
            self.logger.error(f"Restore failed: {e}")
            return False

    def get_storage_info(self) -> Dict:
        """Get information about storage usage"""
        import shutil

        info = {
            "app_root": str(self.app_root),
            "paths": {},
            "storage_usage": {}
        }

        # Path information
        for name, path in self.paths.items():
            info["paths"][name] = {
                "path": str(path),
                "exists": path.exists(),
                "is_symlink": path.is_symlink(),
                "target": str(path.resolve()) if path.is_symlink() else None
            }

        # Storage usage
        for path_name in ["db_dir", "results_dir", "logs_dir", "data_dir"]:
            path = self.paths.get(path_name)
            if path and path.exists():
                usage = shutil.disk_usage(path)
                info["storage_usage"][path_name] = {
                    "total": usage.total,
                    "used": usage.used,
                    "free": usage.free,
                    "path": str(path)
                }

        return info

    def validate_installation(self) -> List[str]:
        """
        Validate the installation and return any issues

        Returns:
            List of validation issues (empty if all OK)
        """
        issues = []

        # Check essential directories
        essential_paths = ["app_root", "db_dir", "results_dir", "config_dir"]
        for path_name in essential_paths:
            path = self.paths.get(path_name)
            if not path or not path.exists():
                issues.append(f"Missing essential directory: {path_name}")

        # Check configuration file
        config_file = self.paths.get("config_file")
        if not config_file or not config_file.exists():
            issues.append("Missing configuration file")

        # Check write permissions
        test_file = self.paths["data_dir"] / ".write_test"
        try:
            test_file.touch()
            test_file.unlink()
        except Exception as e:
            issues.append(f"No write permission in data directory: {e}")

        # Check external symlinks
        external_dir = self.paths.get("external_data")
        if external_dir and external_dir.exists():
            for item in external_dir.iterdir():
                if item.is_symlink() and not item.exists():
                    issues.append(f"Broken external symlink: {item}")

        return issues

# Global instance
_path_manager = None

def get_path_manager() -> PathManager:
    """Get the global path manager instance"""
    global _path_manager
    if _path_manager is None:
        _path_manager = PathManager()
    return _path_manager

def get_path(path_name: str) -> Optional[Path]:
    """Convenience function to get a path"""
    return get_path_manager().get_path(path_name)

if __name__ == "__main__":
    # Test the path manager
    pm = get_path_manager()

    print("LLM-Tester Path Manager")
    print("=" * 40)
    print(f"App Root: {pm.app_root}")
    print(f"Configuration: {pm.config_file}")
    print("\nResolved Paths:")
    for name, path in pm.paths.items():
        print(f"  {name}: {path}")

    print("\nValidation:")
    issues = pm.validate_installation()
    if issues:
        print("Issues found:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("✅ Installation is valid")