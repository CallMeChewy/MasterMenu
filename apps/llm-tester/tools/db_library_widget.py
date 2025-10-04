import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, 
    QPushButton, QLabel, QDialog, QDialogButtonBox, QLineEdit, QTextEdit,
    QMessageBox, QHeaderView, QComboBox
)
from PySide6.QtCore import Signal, Qt
from db_library import (
    list_databases, add_database, copy_database, delete_database, 
    get_database_info, ensure_db_dir
)

class NewDatabaseDialog(QDialog):
    """Dialog for creating a new database"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create New Database")
        self.setMinimumSize(400, 200)
        
        layout = QVBoxLayout(self)
        
        # Name input
        layout.addWidget(QLabel("Database Name:"))
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g., creative_writing_tests")
        layout.addWidget(self.name_edit)
        
        # Description input
        layout.addWidget(QLabel("Description:"))
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("Describe the purpose of this database...")
        self.description_edit.setMaximumHeight(80)
        layout.addWidget(self.description_edit)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def get_values(self):
        return self.name_edit.text().strip(), self.description_edit.toPlainText().strip()

class CopyDatabaseDialog(QDialog):
    """Dialog for copying an existing database"""
    def __init__(self, source_databases, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Copy Database")
        self.setMinimumSize(400, 250)
        
        layout = QVBoxLayout(self)
        
        # Source database selection
        layout.addWidget(QLabel("Source Database:"))
        self.source_combo = QComboBox()
        self.source_combo.addItems(source_databases)
        layout.addWidget(self.source_combo)
        
        # New name input
        layout.addWidget(QLabel("New Database Name:"))
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g., creative_writing_tests_copy")
        layout.addWidget(self.name_edit)
        
        # New description input
        layout.addWidget(QLabel("New Description:"))
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("Describe the purpose of this copied database...")
        self.description_edit.setMaximumHeight(80)
        layout.addWidget(self.description_edit)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def get_values(self):
        return (
            self.source_combo.currentText(),
            self.name_edit.text().strip(),
            self.description_edit.toPlainText().strip()
        )

class DatabaseLibraryWidget(QWidget):
    """Widget for managing the database library"""
    
    database_selected = Signal(str)  # Emitted when a database is selected
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.refresh_database_list()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("🗄️ Database Library"))
        header_layout.addStretch()
        
        # New database button
        new_btn = QPushButton("➕ New Database")
        new_btn.clicked.connect(self.create_new_database)
        header_layout.addWidget(new_btn)
        
        # Copy database button
        copy_btn = QPushButton("📋 Copy Database")
        copy_btn.clicked.connect(self.copy_database)
        header_layout.addWidget(copy_btn)
        
        # Delete database button
        delete_btn = QPushButton("🗑️ Delete")
        delete_btn.clicked.connect(self.delete_selected_database)
        header_layout.addWidget(delete_btn)
        
        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.refresh_database_list)
        header_layout.addWidget(refresh_btn)
        
        layout.addLayout(header_layout)
        
        # Database table
        self.db_table = QTableWidget()
        self.db_table.setColumnCount(5)
        self.db_table.setHorizontalHeaderLabels([
            "Name", "Description", "Created", "Last Updated", "Size (MB)"
        ])
        
        # Configure table
        header = self.db_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        
        self.db_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.db_table.itemSelectionChanged.connect(self.on_selection_changed)
        layout.addWidget(self.db_table)
        
        # Status label
        self.status_label = QLabel("Select a database to use for testing")
        self.status_label.setStyleSheet("color: #888; font-style: italic;")
        layout.addWidget(self.status_label)
        
        # Select button
        select_layout = QHBoxLayout()
        select_layout.addStretch()
        
        self.select_btn = QPushButton("📂 Use Selected Database")
        self.select_btn.clicked.connect(self.select_database)
        self.select_btn.setEnabled(False)
        select_layout.addWidget(self.select_btn)
        
        layout.addLayout(select_layout)
    
    def refresh_database_list(self):
        """Refresh the list of databases in the table"""
        databases = list_databases()
        
        self.db_table.setRowCount(len(databases))
        
        for row, db_info in enumerate(databases):
            # Name
            self.db_table.setItem(row, 0, QTableWidgetItem(db_info["name"]))
            
            # Description
            self.db_table.setItem(row, 1, QTableWidgetItem(db_info["description"]))
            
            # Created date
            created_date = db_info["created_at"][:10] if db_info["created_at"] else "N/A"
            self.db_table.setItem(row, 2, QTableWidgetItem(created_date))
            
            # Last updated date
            updated_date = db_info["last_updated"][:10] if db_info["last_updated"] else "N/A"
            self.db_table.setItem(row, 3, QTableWidgetItem(updated_date))
            
            # Size
            size_str = f"{db_info['size_mb']:.2f}" if db_info["size_mb"] > 0 else "0.00"
            self.db_table.setItem(row, 4, QTableWidgetItem(size_str))
        
        # Update status
        if databases:
            self.status_label.setText(f"Found {len(databases)} database(s)")
        else:
            self.status_label.setText("No databases found. Create a new one to get started.")
    
    def on_selection_changed(self):
        """Handle table selection change"""
        selected_items = self.db_table.selectedItems()
        has_selection = len(selected_items) > 0
        self.select_btn.setEnabled(has_selection)
        
        if has_selection:
            row = selected_items[0].row()
            db_name = self.db_table.item(row, 0).text()
            self.status_label.setText(f"Selected: {db_name}")
    
    def create_new_database(self):
        """Create a new database"""
        dialog = NewDatabaseDialog(self)
        if dialog.exec() == QDialog.Accepted:
            name, description = dialog.get_values()
            
            if not name:
                QMessageBox.warning(self, "Invalid Name", "Database name cannot be empty.")
                return
            
            # Check if name already exists
            existing_dbs = [db["name"] for db in list_databases()]
            if name in existing_dbs:
                QMessageBox.warning(self, "Name Exists", f"A database named '{name}' already exists.")
                return
            
            # Create the database
            from db_library import DB_DIR
            ensure_db_dir()
            db_path = DB_DIR / f"{name}.db"
            
            # Add to library (this will create the empty database file)
            add_database(name, description, db_path)
            
            # Refresh the list
            self.refresh_database_list()
            
            QMessageBox.information(self, "Success", f"Database '{name}' created successfully.")
    
    def copy_database(self):
        """Copy an existing database"""
        databases = list_databases()
        if not databases:
            QMessageBox.information(self, "No Databases", "No databases available to copy.")
            return
        
        dialog = CopyDatabaseDialog([db["name"] for db in databases], self)
        if dialog.exec() == QDialog.Accepted:
            source_name, new_name, new_description = dialog.get_values()
            
            if not new_name:
                QMessageBox.warning(self, "Invalid Name", "New database name cannot be empty.")
                return
            
            # Check if name already exists
            existing_dbs = [db["name"] for db in list_databases()]
            if new_name in existing_dbs:
                QMessageBox.warning(self, "Name Exists", f"A database named '{new_name}' already exists.")
                return
            
            # Copy the database
            success, message = copy_database(source_name, new_name, new_description)
            
            if success:
                self.refresh_database_list()
                QMessageBox.information(self, "Success", message)
            else:
                QMessageBox.warning(self, "Error", message)
    
    def delete_selected_database(self):
        """Delete the selected database"""
        selected_items = self.db_table.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "No Selection", "Please select a database to delete.")
            return
        
        row = selected_items[0].row()
        db_name = self.db_table.item(row, 0).text()
        
        # Confirm deletion
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete the database '{db_name}'?\n\nThis action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            success = delete_database(db_name)
            if success:
                self.refresh_database_list()
                QMessageBox.information(self, "Success", f"Database '{db_name}' deleted successfully.")
            else:
                QMessageBox.warning(self, "Error", f"Failed to delete database '{db_name}'.")
    
    def select_database(self):
        """Select the currently highlighted database"""
        selected_items = self.db_table.selectedItems()
        if not selected_items:
            return
        
        row = selected_items[0].row()
        db_name = self.db_table.item(row, 0).text()
        
        # Emit signal to parent
        self.database_selected.emit(db_name)
        
        # Update status
        self.status_label.setText(f"✅ Using database: {db_name}")
