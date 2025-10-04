import datetime
import os
from sqlalchemy import create_engine, Column, Integer, String, Text, Float, DateTime, Boolean
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from pathlib import Path

# Import our new library functions
from db_library import get_default_db_path, load_library, add_database, update_database_timestamp

Base = declarative_base()

# Global variables for database connection
engine = None
SessionLocal = None
current_db_path = None
current_db_name = None
is_mastermenu_mode = os.environ.get('MASTERMENU_WORKDIR') is not None

def init_database_connection(db_name=None):
    """Initialize database connection based on mode and selected database"""
    global engine, SessionLocal, current_db_path, current_db_name
    
    if is_mastermenu_mode:
        # MasterMenu mode: use library system
        library = load_library()
        if not db_name and library:
            # If no db specified, use the first one in the library
            db_name = list(library.keys())[0]
        
        if db_name and db_name in library:
            current_db_path = Path(library[db_name]["path"])
            current_db_name = db_name
        else:
            # Fallback to creating a new default database
            from db_library import DB_DIR
            DB_DIR.mkdir(exist_ok=True)
            current_db_path = DB_DIR / "mastermenu_default.db"
            current_db_name = "mastermenu_default"
            if not current_db_path.exists():
                add_database("mastermenu_default", "Default database for MasterMenu", current_db_path)
    else:
        # Standalone mode: use default database
        current_db_path = get_default_db_path()
        current_db_name = "default"
        
        # Add to library if not already there
        library = load_library()
        if "default" not in library:
            add_database("default", "Default standalone database", current_db_path)
    
    # Create engine and session
    DATABASE_URL = f"sqlite:///{current_db_path}"
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    print(f"Database initialized: {current_db_name} at {current_db_path}")
    return current_db_name

def get_current_db_info():
    """Get information about the current database"""
    global current_db_name, current_db_path
    return {
        "name": current_db_name,
        "path": str(current_db_path) if current_db_path else None,
        "is_mastermenu_mode": is_mastermenu_mode
    }

class TestResult(Base):
    __tablename__ = "test_results"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, index=True)
    task_id = Column(Integer)
    is_loading_prompt = Column(Boolean, default=False)
    model_name = Column(String, index=True)
    task = Column(Text)
    response = Column(Text)
    response_time = Column(Float)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def save_test_result(db, run_id, task_id, is_loading_prompt, model_name, task, response, response_time):
    print(f"Saving test result for model: {model_name}")
    try:
        db_result = TestResult(
            run_id=run_id,
            task_id=task_id,
            is_loading_prompt=is_loading_prompt,
            model_name=model_name,
            task=task,
            response=response,
            response_time=response_time
        )
        db.add(db_result)
        db.commit()
        db.refresh(db_result)
        print(f"Successfully saved test result for model: {model_name}")
        return db_result
    except Exception as e:
        print(f"Error saving test result: {e}")
        db.rollback()
        return None
