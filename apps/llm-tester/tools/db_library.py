import os
import json
import shutil
from datetime import datetime
from pathlib import Path

# Directory for all database files
DB_DIR = Path("DB_Results")
LIBRARY_FILE = DB_DIR / "library.json"

def ensure_db_dir():
    """Ensure the database directory exists"""
    DB_DIR.mkdir(exist_ok=True)

def get_library_path():
    """Get the path to the library file"""
    return LIBRARY_FILE

def load_library():
    """Load the library of databases"""
    ensure_db_dir()
    if not LIBRARY_FILE.exists():
        return {}
    try:
        with open(LIBRARY_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}

def save_library(library_data):
    """Save the library of databases"""
    ensure_db_dir()
    with open(LIBRARY_FILE, 'w') as f:
        json.dump(library_data, f, indent=2)

def add_database(name, description, db_path):
    """Add a new database to the library"""
    library = load_library()
    library[name] = {
        "description": description,
        "path": str(db_path),
        "created_at": datetime.now().isoformat(),
        "last_updated": datetime.now().isoformat()
    }
    save_library(library)

def update_database_timestamp(name):
    """Update the last updated timestamp for a database"""
    library = load_library()
    if name in library:
        library[name]["last_updated"] = datetime.now().isoformat()
        save_library(library)

def get_database_info(name):
    """Get information about a specific database"""
    library = load_library()
    if name in library:
        info = library[name].copy()
        # Add file size
        db_path = Path(info["path"])
        if db_path.exists():
            info["size_mb"] = round(db_path.stat().st_size / (1024 * 1024), 2)
        else:
            info["size_mb"] = 0
        return info
    return None

def list_databases():
    """List all databases in the library"""
    library = load_library()
    db_list = []
    for name, info in library.items():
        db_info = get_database_info(name)
        if db_info:
            db_list.append({
                "name": name,
                "description": db_info["description"],
                "created_at": db_info["created_at"],
                "last_updated": db_info["last_updated"],
                "size_mb": db_info["size_mb"]
            })
    return db_list

def delete_database(name):
    """Delete a database from the library and remove its file"""
    library = load_library()
    if name in library:
        db_path = Path(library[name]["path"])
        if db_path.exists():
            os.remove(db_path)
        del library[name]
        save_library(library)
        return True
    return False

def copy_database(source_name, new_name, new_description):
    """Copy an existing database to a new one"""
    library = load_library()
    if source_name not in library:
        return False, "Source database not found"
    
    source_path = Path(library[source_name]["path"])
    if not source_path.exists():
        return False, "Source database file not found"
    
    # Create new database path
    new_db_path = DB_DIR / f"{new_name}.db"
    if new_db_path.exists():
        return False, "Database with this name already exists"
    
    # Copy the file
    shutil.copy2(source_path, new_db_path)
    
    # Add to library
    add_database(new_name, new_description, new_db_path)
    
    return True, "Database copied successfully"

def get_default_db_path():
    """Get the default database path (for standalone mode)"""
    ensure_db_dir()
    return DB_DIR / "default.db"
