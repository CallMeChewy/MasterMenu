# File: Finder.py
# Path: apps/finder/Finder.py
# Standard: AIDEV-PascalCase-2.1
# Created: 2025-07-18
# Last Modified: 2025-07-28  08:10PM
"""
Finder - Advanced Document Search Application
A comprehensive PySide6-based search tool with logical formula construction,
phrase-based searching, and advanced result display with color coding.
"""

import sys
import os
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Set, Tuple, Optional

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGroupBox, QCheckBox, QRadioButton, QLineEdit, QPushButton,
    QTextEdit, QPlainTextEdit, QFileDialog, QButtonGroup, QLabel,
    QScrollArea, QGridLayout, QFrame, QSplitter, QComboBox, QMessageBox,
    QListView, QTreeView, QAbstractItemView
)
from PySide6.QtCore import QThread, QObject, Signal, Qt, QTimer
from PySide6.QtGui import (
    QFont,
    QTextCharFormat,
    QColor,
    QSyntaxHighlighter,
    QTextDocument,
    QCursor,
)

# MasterMenu-inspired color palette used throughout the Finder UI
MASTER_THEME = {
    'background_top': '#1a335d',
    'background_mid': '#204272',
    'background_bottom': '#152a4b',
    'panel_bg': '#1e3964',
    'panel_border': 'rgba(150, 220, 255, 0.45)',
    'panel_title': '#c7e6ff',
    'text_primary': '#e9f3ff',
    'text_muted': '#b4cae6',
    'input_bg': '#162f54',
    'input_border': 'rgba(150, 220, 255, 0.45)',
    'hover_border': 'rgba(150, 220, 255, 0.65)',
    'primary_btn_start': 'rgba(60, 120, 210, 0.95)',
    'primary_btn_end': 'rgba(50, 150, 240, 0.95)',
    'accent_btn_start': 'rgba(220, 160, 60, 0.95)',
    'accent_btn_end': 'rgba(240, 190, 90, 0.95)',
    'neutral_btn_start': 'rgba(55, 90, 140, 0.92)',
    'neutral_btn_end': 'rgba(40, 70, 120, 0.92)',
    'warn_btn_start': 'rgba(200, 90, 40, 0.95)',
    'warn_btn_end': 'rgba(230, 130, 60, 0.95)',
    'info_btn_start': 'rgba(70, 140, 210, 0.95)',
    'info_btn_end': 'rgba(90, 170, 240, 0.95)',
    'success_border': 'rgba(110, 220, 150, 0.85)',
    'warning_border': 'rgba(230, 190, 80, 0.85)',
    'error_border': 'rgba(240, 110, 110, 0.9)'
}


class FormulaHighlighter(QSyntaxHighlighter):
    """Syntax highlighter for formula input with parentheses/bracket matching and error highlighting"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_formats()
        self.finder_app = None  # Will be set by parent
        
    def setup_formats(self):
        """Setup text formats for different elements"""
        self.formats = {}
        
        # Parentheses colors (cycling through colors for nesting)
        self.paren_colors = [
            QColor(255, 100, 100),  # Red
            QColor(100, 255, 100),  # Green
            QColor(100, 100, 255),  # Blue
            QColor(255, 255, 100),  # Yellow
            QColor(255, 100, 255),  # Magenta
            QColor(100, 255, 255),  # Cyan
        ]
        
        # Operators
        self.operator_format = QTextCharFormat()
        self.operator_format.setForeground(QColor(200, 100, 50))
        self.operator_format.setFontWeight(QFont.Weight.Bold)
        
        # Phrase references (A-D) - case insensitive (default)
        self.phrase_format_insensitive = QTextCharFormat()
        self.phrase_format_insensitive.setForeground(QColor(50, 150, 200))
        self.phrase_format_insensitive.setFontWeight(QFont.Weight.Bold)
        
        # Phrase references - case sensitive (same color but underlined)
        self.phrase_format_sensitive = QTextCharFormat()
        self.phrase_format_sensitive.setForeground(QColor(50, 150, 200))  # Same blue color
        self.phrase_format_sensitive.setFontWeight(QFont.Weight.Bold)
        self.phrase_format_sensitive.setUnderlineStyle(QTextCharFormat.UnderlineStyle.SingleUnderline)
        
        # Error highlighting
        self.error_format = QTextCharFormat()
        self.error_format.setForeground(QColor(255, 255, 255))
        self.error_format.setBackground(QColor(255, 100, 100))
        self.error_format.setFontWeight(QFont.Weight.Bold)
        
        # Invalid characters
        self.invalid_format = QTextCharFormat()
        self.invalid_format.setForeground(QColor(255, 0, 0))
        self.invalid_format.setBackground(QColor(255, 255, 100))
        self.invalid_format.setFontWeight(QFont.Weight.Bold)
        
    def highlightBlock(self, text):
        """Highlight the current text block with error detection"""
        # First, check for invalid characters (now including common operators)
        valid_chars = set('ABCD()[]{}ANDORNOTXRandornotxr \t&|!~^')
        for i, char in enumerate(text):
            if char not in valid_chars:
                self.setFormat(i, 1, self.invalid_format)
        
        # Highlight word-based operators
        word_operators = r'\b(AND|OR|NOT|NOR|XOR|XNOR)\b'
        for match in re.finditer(word_operators, text, re.IGNORECASE):
            self.setFormat(match.start(), match.end() - match.start(), self.operator_format)
            
        # Highlight symbol-based operators
        symbol_operators = r'[&|!~^]+'
        for match in re.finditer(symbol_operators, text):
            self.setFormat(match.start(), match.end() - match.start(), self.operator_format)
        
        # Highlight phrase references with case sensitivity indication
        self._highlight_phrase_references(text)
            
        # Highlight parentheses with color matching and error detection
        paren_stack = []
        for i, char in enumerate(text):
            if char in '([{':
                level = len(paren_stack) % len(self.paren_colors)
                color = self.paren_colors[level]
                format = QTextCharFormat()
                format.setForeground(color)
                format.setFontWeight(QFont.Weight.Bold)
                self.setFormat(i, 1, format)
                paren_stack.append((char, level))
            elif char in ')]}':
                if paren_stack:
                    open_char, level = paren_stack.pop()
                    if self._is_matching_paren(open_char, char):
                        color = self.paren_colors[level]
                        format = QTextCharFormat()
                        format.setForeground(color)
                        format.setFontWeight(QFont.Weight.Bold)
                        self.setFormat(i, 1, format)
                    else:
                        # Mismatched parenthesis - highlight as error
                        self.setFormat(i, 1, self.error_format)
                else:
                    # Unmatched closing parenthesis - highlight as error
                    self.setFormat(i, 1, self.error_format)
        
        # Highlight any remaining unmatched opening parentheses
        for open_char, level in paren_stack:
            # Find the position of unmatched opening parenthesis
            for i, char in enumerate(text):
                if char == open_char:
                    # Check if this is actually unmatched (simple check)
                    self.setFormat(i, 1, self.error_format)
                    break
                    
    def _is_matching_paren(self, open_char, close_char):
        """Check if parentheses match"""
        pairs = {'(': ')', '[': ']', '{': '}'}
        return pairs.get(open_char) == close_char
    
    def _highlight_phrase_references(self, text):
        """Highlight phrase references with case sensitivity visual indicators"""
        phrases = r'\b[A-D]\b'
        for match in re.finditer(phrases, text):
            letter = match.group()
            
            # Check if we have access to the finder app for case sensitivity info
            if self.finder_app:
                case_sensitive = self.finder_app.case_sensitive_checkboxes[letter].isChecked()
                phrase_text = self.finder_app.phrase_inputs[letter].text().strip()
                
                # Choose format: underlined if case sensitive, normal if not
                if case_sensitive and phrase_text:
                    format_to_use = self.phrase_format_sensitive  # Underlined
                else:
                    format_to_use = self.phrase_format_insensitive  # Normal
                        
                # Apply the formatting
                self.setFormat(match.start(), match.end() - match.start(), format_to_use)
                
                # Update tooltip with simple information
                self.finder_app.formula_input.setToolTip(self._build_formula_tooltip())
            else:
                # Fallback to insensitive format if no finder app reference
                self.setFormat(match.start(), match.end() - match.start(), self.phrase_format_insensitive)
    
    def _build_formula_tooltip(self):
        """Build simple tooltip showing variable information"""
        tooltip_lines = ["Formula Variables:"]
        
        for letter in 'ABCD':
            if self.finder_app:
                case_sensitive = self.finder_app.case_sensitive_checkboxes[letter].isChecked()
                phrase_text = self.finder_app.phrase_inputs[letter].text().strip()
                
                if phrase_text:
                    case_info = "Match Case" if case_sensitive else "Any Case"
                    underline_indicator = f"{letter}̲" if case_sensitive else letter
                    tooltip_lines.append(f"{underline_indicator}: '{phrase_text}' ({case_info})")
                    
        if len(tooltip_lines) == 1:
            tooltip_lines.append("(No variables defined)")
            
        tooltip_lines.append("")
        tooltip_lines.append("Visual Indicator:")
        tooltip_lines.append("Underlined = Match Case (case sensitive)")
        tooltip_lines.append("Normal = Any Case (case insensitive)")
        
        return "\n".join(tooltip_lines)
    
    def refresh_highlighting(self):
        """Refresh highlighting when case sensitivity settings change"""
        if self.document():
            self.rehighlight()


class SearchWorker(QObject):
    """Worker thread for performing document search operations"""
    
    result_found = Signal(str, str, int, bool)  # file_path, content, line_number, is_unique
    search_finished = Signal(str)
    progress_update = Signal(int, int)  # current, total
    error = Signal(str)  # Add error signal for better error handling
    
    def __init__(self, search_params):
        super().__init__()
        self.search_params = search_params
        self.is_cancelled = False
        self.unique_matches = {}  # Track unique matches per file
        
    def run_search(self):
        """Execute the search operation"""
        try:
            files_to_search = self._get_files_to_search()
            total_files = len(files_to_search)
            
            if total_files == 0:
                self.search_finished.emit("No files found matching the criteria.")
                return
                
            match_count = 0
            
            for i, file_path in enumerate(files_to_search):
                if self.is_cancelled:
                    break
                    
                self.progress_update.emit(i + 1, total_files)
                
                try:
                    matches = self._search_file(file_path)
                    for match in matches:
                        if self.is_cancelled:
                            break
                        match_count += 1
                        line_content, line_number, is_unique = match
                        self.result_found.emit(file_path, line_content, line_number, is_unique)
                        
                except Exception as e:
                    self.result_found.emit(file_path, f"ERROR: Cannot read file: {e}", 0, False)
                    
            self.search_finished.emit(f"Search complete. Found {match_count} matches in {total_files} files.")
            
        except Exception as e:
            self.search_finished.emit(f"Search error: {e}")
            
    def _get_files_to_search(self):
        """Get list of files to search based on parameters"""
        files = []
        search_paths = self.search_params['search_paths']
        file_extensions = self.search_params['file_extensions']
        
        for search_path in search_paths:
            if os.path.isfile(search_path):
                if self._is_valid_extension(search_path, file_extensions):
                    files.append(search_path)
            elif os.path.isdir(search_path):
                for root, _, filenames in os.walk(search_path):
                    for filename in filenames:
                        if self._is_valid_extension(filename, file_extensions):
                            files.append(os.path.join(root, filename))
                            
        return files
        
    def _is_valid_extension(self, filename, extensions):
        """Check if file extension matches search criteria"""
        if not extensions:
            return True
        return any(filename.lower().endswith(ext.lower()) for ext in extensions)
        
    def _search_file(self, file_path):
        """Search a single file for matches"""
        matches = []
        phrases = self.search_params['phrases']
        search_mode = self.search_params['search_mode']
        formula = self.search_params['formula']
        unique_mode = self.search_params['unique_mode']
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                if search_mode == 'document':
                    # Search entire document
                    content = f.read()
                    if self._evaluate_formula(content, phrases, formula):
                        is_unique = file_path not in self.unique_matches
                        if is_unique:
                            self.unique_matches[file_path] = True
                        if not unique_mode or is_unique:
                            matches.append((content[:200] + "...", 0, is_unique))
                else:
                    # Search line by line
                    for line_num, line in enumerate(f, 1):
                        if self._evaluate_formula(line, phrases, formula):
                            # Check if this is a unique match for this line content
                            match_key = f"{file_path}:{line.strip()}"
                            is_unique = match_key not in self.unique_matches
                            if is_unique:
                                self.unique_matches[match_key] = True
                            if not unique_mode or is_unique:
                                matches.append((line.strip(), line_num, is_unique))
                                
        except Exception as e:
            matches.append((f"Error reading file: {e}", 0, False))
            
        return matches
        
    def _evaluate_formula(self, content, phrases, formula):
        """Evaluate the logical formula against the content"""
        if not formula.strip():
            return False
            
        # Normalize operators first
        normalized_formula = self._normalize_operators(formula)
            
        # Create a mapping of phrase variables to their presence in content
        phrase_values = {}
        for letter, phrase_data in phrases.items():
            phrase_text = phrase_data.get('text', '')
            case_sensitive = phrase_data.get('case_sensitive', False)
            
            if phrase_text.strip():
                if case_sensitive:
                    # Case-sensitive search
                    phrase_values[letter] = phrase_text in content
                else:
                    # Case-insensitive search
                    phrase_values[letter] = phrase_text.lower() in content.lower()
            else:
                phrase_values[letter] = False
                
        # Replace phrase variables in formula with their boolean values
        # Use word boundaries to avoid replacing letters within operators
        import re
        eval_formula = normalized_formula.upper()
        for letter in 'ABCD':
            # Use regex with word boundaries to only replace standalone variables
            pattern = r'\b' + letter + r'\b'
            replacement = str(phrase_values.get(letter, False))
            eval_formula = re.sub(pattern, replacement, eval_formula)
            
        # Replace logical operators with Python equivalents
        eval_formula = eval_formula.replace('AND', ' and ')
        eval_formula = eval_formula.replace('OR', ' or ')
        eval_formula = eval_formula.replace('NOT', ' not ')
        eval_formula = eval_formula.replace('NOR', ' not (') # Will need special handling
        eval_formula = eval_formula.replace('XOR', ' != ')
        eval_formula = eval_formula.replace('XNOR', ' == ')
        
        # Handle NOR specially - convert "A NOR B" to "not (A or B)"
        eval_formula = re.sub(r'not \(([^)]+)\)', r'not (\1)', eval_formula)
        
        try:
            return eval(eval_formula)
        except:
            return False
            
    def cancel(self):
        """Cancel the search operation"""
        self.is_cancelled = True
        
    def _normalize_operators(self, formula):
        """Convert common logical operators to standard form"""
        import re
        # Order matters - longer operators first to avoid partial replacements
        operator_replacements = [
            ('&&', ' AND '),
            ('||', ' OR '),
            ('&', ' AND '),
            ('|', ' OR '),
            ('!', ' NOT '),
            ('~', ' NOT '),
            ('^', ' XOR ')
        ]
        
        # Apply replacements in order
        normalized = formula
        for symbol, replacement in operator_replacements:
            normalized = normalized.replace(symbol, replacement)
            
        # Clean up multiple spaces
        normalized = re.sub(r'\s+', ' ', normalized).strip()
            
        return normalized


class Finder(QMainWindow):
    """Main Finder application window"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Finder - Advanced Document Search")
        self.setGeometry(100, 100, 1400, 900)  # Increased size to ensure all content is visible
        self.setObjectName("FinderWindow")
        
        # Initialize search thread components
        self.search_thread = None
        self.search_worker = None
        
        # Initialize auto-formula tracking
        self._last_auto_formula = ""
        self._has_search_results = False
        self._launched_from_mastermenu = bool(os.environ.get("MASTERMENU_WORKDIR"))

        # Setup UI
        self._setup_ui()
        self._setup_defaults()
        self._setup_tab_order()
        self._apply_mastermenu_theme()

        self._pulse_timer = QTimer(self)
        self._pulse_timer.setInterval(420)
        self._pulse_timer.timeout.connect(self._pulse_search_indicator)
        self._pulse_state_on = False
        
    def _setup_ui(self):
        """Setup the user interface"""
        central_widget = QWidget()
        central_widget.setObjectName("FinderCentral")
        self.setCentralWidget(central_widget)
        
        # Main layout using splitter
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left panel for controls with scroll area
        left_panel_content = QWidget()
        left_panel_content.setObjectName("FinderLeftPanel")
        left_layout = QVBoxLayout(left_panel_content)
        left_layout.setContentsMargins(10, 10, 10, 10)
        left_layout.setSpacing(10)

        # Create control sections
        self._create_phrase_section(left_layout)
        self._create_search_mode_section(left_layout)
        self._create_file_types_section(left_layout)
        self._create_path_section(left_layout)
        self._create_formula_section(left_layout)
        
        # Add stretch to push everything to top
        left_layout.addStretch()
        
        # Wrap in scroll area
        left_scroll = QScrollArea()
        left_scroll.setWidget(left_panel_content)
        left_scroll.setWidgetResizable(True)
        left_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        left_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        left_scroll.setFrameShape(QFrame.NoFrame)
        left_scroll.setObjectName("FinderLeftScroll")

        # Right panel for results
        right_panel = QWidget()
        right_panel.setObjectName("FinderRightPanel")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(10, 10, 10, 10)
        right_layout.setSpacing(10)
        self._create_results_section(right_layout)
        
        # Add panels to splitter
        splitter.addWidget(left_scroll)  # Use scroll area instead of direct panel
        splitter.addWidget(right_panel)
        splitter.setSizes([450, 950])  # Adjusted sizes for new window dimensions
        
        main_layout.addWidget(splitter)
        
    def _create_phrase_section(self, parent_layout):
        """Create the phrase input section (A-D)"""
        group_box = QGroupBox("Search Phrases (A-D)")
        layout = QGridLayout()
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setHorizontalSpacing(6)
        layout.setVerticalSpacing(6)

        self.phrase_inputs = {}
        self.case_sensitive_checkboxes = {}

        for letter in 'ABCD':
            label = QLabel(f"{letter}:")
            label.setMinimumWidth(20)
            label.setMaximumWidth(20)
            
            line_edit = QLineEdit()
            line_edit.setPlaceholderText(f"Enter phrase {letter}")
            line_edit.setMinimumWidth(180)
            
            case_checkbox = QCheckBox("Match Case")
            case_checkbox.setToolTip("Check to make this phrase case-sensitive")
            case_checkbox.setChecked(False)  # Default to case-insensitive

            self.phrase_inputs[letter] = line_edit
            self.case_sensitive_checkboxes[letter] = case_checkbox

            # Connect to auto-formula construction (no real-time validation)
            line_edit.textChanged.connect(self._update_auto_formula)
            line_edit.textChanged.connect(self._refresh_formula_highlighting)  # Also refresh highlighting
            line_edit.textChanged.connect(self._invalidate_cached_results)

            # Connect case sensitivity checkbox to refresh formula highlighting
            case_checkbox.stateChanged.connect(self._refresh_formula_highlighting)
            case_checkbox.stateChanged.connect(self._invalidate_cached_results)

            row = ord(letter) - ord('A')
            layout.addWidget(label, row, 0)
            layout.addWidget(line_edit, row, 1)
            layout.addWidget(case_checkbox, row, 2)

        group_box.setLayout(layout)
        parent_layout.addWidget(group_box)

    def _style_button(self, button: QPushButton, role: str = "neutral"):
        """Apply MasterMenu-inspired styling to buttons via dynamic properties"""
        button.setProperty("buttonRole", role)
        button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        button.setMinimumHeight(30)
        button.setMaximumHeight(34)
        button.setContentsMargins(0, 0, 0, 0)

        # Refresh style so property-based selectors take effect immediately
        button.style().unpolish(button)
        button.style().polish(button)

    def _apply_mastermenu_theme(self):
        """Apply the MasterMenu visual theme to the Finder window"""
        palette = MASTER_THEME
        theme_qss = f"""
        QMainWindow#FinderWindow {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {palette['background_top']},
                stop:0.45 {palette['background_mid']},
                stop:1 {palette['background_bottom']});
            color: {palette['text_primary']};
        }}

        QWidget#FinderCentral {{
            background: transparent;
        }}

        QWidget#FinderLeftPanel,
        QWidget#FinderRightPanel,
        QScrollArea#FinderLeftScroll {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 rgba(16, 42, 79, 0.88),
                stop:1 rgba(11, 28, 52, 0.94));
        }}

        QGroupBox {{
            background: {palette['panel_bg']};
            border: 1px solid {palette['panel_border']};
            border-radius: 14px;
            color: {palette['text_primary']};
            margin-top: 12px;
        }}

        QGroupBox::title {{
            color: {palette['panel_title']};
            font-weight: 600;
            padding: 0 8px;
            margin-top: 4px;
        }}

        QLabel {{
            color: {palette['text_primary']};
        }}

        QLineEdit,
        QTextEdit,
        QPlainTextEdit {{
            background: {palette['input_bg']};
            border: 1px solid {palette['input_border']};
            border-radius: 10px;
            padding: 6px 8px;
            color: {palette['text_primary']};
            selection-background-color: rgba(120, 200, 255, 0.55);
        }}

        QLineEdit:focus,
        QTextEdit:focus,
        QPlainTextEdit:focus {{
            border-color: {palette['hover_border']};
        }}

        QTextEdit#FinderResultsDisplay {{
            background: #102b4d;
            border: 1px solid rgba(170, 230, 255, 0.45);
        }}

        QLineEdit[validationState="valid"],
        QTextEdit[validationState="valid"],
        QPlainTextEdit[validationState="valid"] {{
            border: 2px solid {palette['success_border']};
        }}

        QLineEdit[validationState="warning"],
        QTextEdit[validationState="warning"],
        QPlainTextEdit[validationState="warning"] {{
            border: 2px solid {palette['warning_border']};
            background: rgba(60, 44, 8, 0.65);
        }}

        QLineEdit[validationState="error"],
        QTextEdit[validationState="error"],
        QPlainTextEdit[validationState="error"] {{
            border: 2px solid {palette['error_border']};
            background: rgba(68, 20, 20, 0.55);
        }}

        QCheckBox,
        QRadioButton {{
            color: {palette['text_primary']};
            spacing: 6px;
        }}

        QCheckBox::indicator,
        QRadioButton::indicator {{
            width: 18px;
            height: 18px;
        }}

        QCheckBox::indicator {{
            border-radius: 4px;
            border: 1px solid {palette['input_border']};
            background: {palette['input_bg']};
        }}

        QCheckBox::indicator:checked {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 rgba(88, 180, 255, 0.85),
                stop:1 rgba(120, 210, 255, 0.95));
            border: 1px solid {palette['hover_border']};
        }}

        QRadioButton::indicator {{
            border-radius: 9px;
            border: 1px solid {palette['input_border']};
            background: {palette['input_bg']};
        }}

        QRadioButton::indicator:checked {{
            background: qradialgradient(cx:0.5, cy:0.5, radius:0.7,
                stop:0 rgba(88, 180, 255, 0.9),
                stop:1 transparent);
            border: 1px solid {palette['hover_border']};
        }}

        QPushButton {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 {palette['neutral_btn_start']},
                stop:1 {palette['neutral_btn_end']});
            border-radius: 12px;
            border: 1px solid rgba(120, 200, 255, 0.35);
            color: {palette['text_primary']};
            font-weight: 600;
            padding: 6px 14px;
        }}

        QPushButton:hover {{
            border-color: {palette['hover_border']};
        }}

        QPushButton:disabled {{
            color: rgba(220, 230, 245, 0.5);
            border-color: rgba(120, 200, 255, 0.12);
            background: rgba(12, 22, 40, 0.6);
        }}

        QPushButton[buttonRole="primary"] {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 {palette['primary_btn_start']},
                stop:1 {palette['primary_btn_end']});
            border: 1px solid {palette['hover_border']};
        }}

        QPushButton[buttonRole="accent"] {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 {palette['accent_btn_start']},
                stop:1 {palette['accent_btn_end']});
            border: 1px solid rgba(230, 190, 90, 0.8);
        }}

        QPushButton[buttonRole="info"] {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 {palette['info_btn_start']},
                stop:1 {palette['info_btn_end']});
            border: 1px solid rgba(120, 200, 255, 0.7);
        }}

        QPushButton[buttonRole="neutral"] {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 {palette['neutral_btn_start']},
                stop:1 {palette['neutral_btn_end']});
        }}

        QLabel#SyntaxStatusLabel {{
            font-weight: 600;
            color: {palette['text_primary']};
        }}

        QLabel#SyntaxStatusLabel[statusRole="idle"] {{
            color: {palette['text_muted']};
        }}

        QLabel#SyntaxStatusLabel[statusRole="valid"] {{
            color: {palette['success_border']};
        }}

        QLabel#SyntaxStatusLabel[statusRole="warning"] {{
            color: {palette['warning_border']};
        }}

        QLabel#SyntaxStatusLabel[statusRole="error"] {{
            color: {palette['error_border']};
        }}

        QLabel#SearchStatusIndicator {{
            padding-left: 4px;
            font-style: italic;
            color: {palette['text_muted']};
        }}

        QLabel#SearchStatusIndicator[pulseState="on"] {{
            color: {palette['success_border']};
        }}

        QLabel#SearchStatusIndicator[pulseState="off"] {{
            color: rgba(200, 220, 255, 0.7);
        }}
        """

        self.setStyleSheet(theme_qss)

    def _invalidate_cached_results(self):
        """Clear displayed results when input parameters change"""
        if self._has_search_results:
            self.results_display.clear()
            self._has_search_results = False

    def _set_formula_validation_state(self, state: str, message: str):
        """Update visual feedback for the formula editor"""
        if state not in {"idle", "valid", "warning", "error"}:
            state = "idle"

        self.formula_input.setProperty("validationState", state)
        self.formula_input.style().unpolish(self.formula_input)
        self.formula_input.style().polish(self.formula_input)

        self.syntax_label.setText(message)
        self.syntax_label.setProperty("statusRole", state)
        self.syntax_label.style().unpolish(self.syntax_label)
        self.syntax_label.style().polish(self.syntax_label)

        # Enable search when valid or pending edits so validation can run
        self.btn_search.setEnabled(state in {"valid", "idle"})

    def _mark_formula_dirty(self):
        """Reset validation state once the user edits the formula"""
        self._set_formula_validation_state("idle", "Syntax: Pending edits")

    def _determine_warning_state(self, warnings: List[str]) -> str:
        """Classify warnings to decide whether search should be blocked"""
        lowered = [w.lower() for w in warnings]
        blocking_terms = ["always be false", "logical paradox", "cannot be satisfied"]
        if any(term in message for message in lowered for term in blocking_terms):
            return "warning"
        return "valid"

    def _render_validation_feedback(self, formula: str, validation_result: Dict[str, List[str]]):
        """Display validation outcome and suggestions in the results panel"""
        self.results_display.clear()
        self.results_display.setTextColor(QColor(180, 220, 255))
        self.results_display.append("🧪 Formula Validation Report")
        self.results_display.append("=" * 40)

        formatted_formula = formula if formula else "<empty>"
        self.results_display.setTextColor(QColor(200, 220, 255))
        self.results_display.append(f"Formula: {formatted_formula}")

        if validation_result['is_valid'] and not validation_result['warnings']:
            self.results_display.setTextColor(QColor(150, 255, 170))
            self.results_display.append("\n✅ No issues detected. Ready to search.")
        else:
            if validation_result['errors']:
                self.results_display.setTextColor(QColor(255, 180, 180))
                self.results_display.append("\n❌ Errors:")
                for error in validation_result['errors']:
                    self.results_display.append(f"  • {error}")

            if validation_result['warnings']:
                self.results_display.setTextColor(QColor(255, 220, 150))
                self.results_display.append("\n⚠️ Warnings:")
                for warning in validation_result['warnings']:
                    self.results_display.append(f"  • {warning}")

            suggestions = self._suggestions_from_messages(
                validation_result['errors'] + validation_result['warnings']
            )
            if suggestions:
                self.results_display.setTextColor(QColor(180, 230, 255))
                self.results_display.append("\n💡 Suggested Changes:")
                for suggestion in suggestions:
                    self.results_display.append(f"  • {suggestion}")

        self._has_search_results = True

    def _suggestions_from_messages(self, messages: List[str]) -> List[str]:
        """Generate user-friendly suggestions based on validation messages"""
        seen: Set[str] = set()
        suggestions: List[str] = []

        for message in messages:
            lower_msg = message.lower()
            suggestion = ""

            if "logical paradox" in lower_msg or "always be false" in lower_msg:
                suggestion = "Remove contradictory terms like 'A AND NOT A', or split them into separate conditions."
            elif "always be true" in lower_msg or "tautology" in lower_msg:
                suggestion = "Simplify tautologies such as 'A OR NOT A' to reduce unnecessary matches."
            elif "no corresponding phrases" in lower_msg:
                suggestion = "Fill in phrases for the listed variables or remove those letters from the formula."
            elif "invalid characters" in lower_msg:
                suggestion = "Replace unsupported characters with AND/OR/NOT operators or parentheses."
            elif "invalid sequence" in lower_msg:
                suggestion = "Ensure each variable is separated by an operator, e.g. 'A AND B'."
            elif "unmatched closing" in lower_msg or "unclosed" in lower_msg or "parentheses" in lower_msg:
                suggestion = "Balance parentheses/brackets so every opening symbol has a matching close."
            elif "missing valid" in lower_msg or "needs operand" in lower_msg:
                suggestion = "Provide values on both sides of each operator, such as 'A OR (B AND C)'."
            elif "empty parentheses" in lower_msg:
                suggestion = "Add content inside the empty parentheses or remove them entirely."
            elif "variables" in lower_msg and "used in formula" in lower_msg:
                suggestion = "Either supply phrases for the named variables or remove them from the expression."
            else:
                suggestion = f"Review: {message}"

            suggestion_key = suggestion.lower()
            if suggestion_key not in seen:
                seen.add(suggestion_key)
                suggestions.append(suggestion)

        return suggestions

    def _pulse_search_indicator(self):
        """Animate the search status indicator while work is in progress"""
        if not hasattr(self, 'search_status_indicator'):
            return
        if not self.search_status_indicator.isVisible():
            return

        self._pulse_state_on = not self._pulse_state_on
        next_state = "on" if self._pulse_state_on else "off"
        self.search_status_indicator.setProperty("pulseState", next_state)
        self.search_status_indicator.setText("🟢 Searching…" if self._pulse_state_on else "⚪ Searching…")
        self.search_status_indicator.style().unpolish(self.search_status_indicator)
        self.search_status_indicator.style().polish(self.search_status_indicator)

    def _enforce_formula_case(self):
        """Force alphabetic logical operators to uppercase"""
        text = self.formula_input.toPlainText()
        if not text:
            return

        def _upper(match):
            return match.group(0).upper()

        import re
        transformed = re.sub(r'\b(and|or|not|nor|xor|xnor)\b', _upper, text, flags=re.IGNORECASE)
        if transformed != text:
            cursor = self.formula_input.textCursor()
            position = cursor.position()
            self.formula_input.blockSignals(True)
            self.formula_input.setPlainText(transformed)
            new_cursor = self.formula_input.textCursor()
            new_cursor.setPosition(min(position, len(transformed)))
            self.formula_input.setTextCursor(new_cursor)
            self.formula_input.blockSignals(False)
            # Ensure highlighting stays current after case enforcement
            self._refresh_formula_highlighting()

    def _create_search_mode_section(self, parent_layout):
        """Create search mode selection (Document/Line)"""
        group_box = QGroupBox("Search Mode")
        layout = QHBoxLayout()
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(10)

        self.search_mode_group = QButtonGroup()

        self.rb_document = QRadioButton("Document")
        self.rb_document.setToolTip("Search entire document as one unit")
        self.rb_document.toggled.connect(self._invalidate_cached_results)

        self.rb_line = QRadioButton("Line") 
        self.rb_line.setToolTip("Search line by line")
        self.rb_line.setChecked(True)
        self.rb_line.toggled.connect(self._invalidate_cached_results)
        
        self.search_mode_group.addButton(self.rb_document)
        self.search_mode_group.addButton(self.rb_line)
        
        layout.addWidget(self.rb_document)
        layout.addWidget(self.rb_line)
        layout.addStretch()
        
        group_box.setLayout(layout)
        parent_layout.addWidget(group_box)
        
    def _create_file_types_section(self, parent_layout):
        """Create file type selection checkboxes"""
        group_box = QGroupBox("File Types")
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)

        # Standard file types
        types_layout = QGridLayout()
        types_layout.setHorizontalSpacing(10)
        types_layout.setVerticalSpacing(6)

        self.file_type_checkboxes = {}
        file_types = ['txt', 'md', 'html', 'css', 'json', 'js', 'py', 'xml', 'log', 'csv']

        for i, file_type in enumerate(file_types):
            cb = QCheckBox(f".{file_type}")
            if file_type in ['txt', 'md']:  # Default selections
                cb.setChecked(True)
            cb.stateChanged.connect(self._invalidate_cached_results)
            self.file_type_checkboxes[file_type] = cb
            types_layout.addWidget(cb, i // 4, i % 4)

        layout.addLayout(types_layout)

        # Custom extensions
        custom_layout = QHBoxLayout()
        custom_layout.addWidget(QLabel("Custom:"))

        self.custom_extensions = QLineEdit()
        self.custom_extensions.setPlaceholderText("e.g., aaa,bbb,ccc")
        self.custom_extensions.textChanged.connect(self._invalidate_cached_results)
        custom_layout.addWidget(self.custom_extensions)
        
        layout.addLayout(custom_layout)
        
        group_box.setLayout(layout)
        parent_layout.addWidget(group_box)
        
    def _create_path_section(self, parent_layout):
        """Create path selection section"""
        group_box = QGroupBox("Search Path")
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)

        # Current path display
        self.path_display = QLineEdit()
        self.path_display.setReadOnly(True)
        self.path_display.setPlaceholderText("No path selected")
        layout.addWidget(self.path_display)
        
        # Path selection buttons
        button_layout = QHBoxLayout()
        
        self.btn_select_folder = QPushButton("Select Folders")
        self.btn_select_folder.clicked.connect(self._select_folders)

        self.btn_select_files = QPushButton("Select Files")
        self.btn_select_files.clicked.connect(self._select_files)

        self.btn_current_folder = QPushButton("Current Folder")
        self.btn_current_folder.clicked.connect(self._use_current_folder)
        
        button_layout.addWidget(self.btn_select_folder)
        button_layout.addWidget(self.btn_select_files)
        button_layout.addWidget(self.btn_current_folder)
        
        layout.addLayout(button_layout)
        
        # Store selected paths
        self.selected_paths = []
        
        group_box.setLayout(layout)
        parent_layout.addWidget(group_box)
        
    def _create_formula_section(self, parent_layout):
        """Create formula construction section"""
        group_box = QGroupBox("Search Formula")
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)

        # Formula input with syntax highlighting
        self.formula_input = QPlainTextEdit()
        self.formula_input.setFixedHeight(36)
        self.formula_input.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.formula_input.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.formula_input.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.formula_input.setMaximumBlockCount(1)
        self.formula_input.setPlaceholderText("Enter formula using A-D, AND/&, OR/|, NOT/!, NOR, XOR/^, XNOR, (, ), [, ], {, } or leave empty for auto-construction")
        self.formula_input.textChanged.connect(self._invalidate_cached_results)
        self.formula_input.textChanged.connect(self._enforce_formula_case)
        self.formula_input.textChanged.connect(self._mark_formula_dirty)
        self.formula_input.setProperty("validationState", "idle")

        # Setup syntax highlighter
        self.highlighter = FormulaHighlighter(self.formula_input.document())
        self.highlighter.finder_app = self

        layout.addWidget(self.formula_input)
        
        # Unique mode checkbox
        self.cb_unique = QCheckBox("Unique (show only first occurrence)")
        self.cb_unique.stateChanged.connect(self._invalidate_cached_results)
        layout.addWidget(self.cb_unique)

        # Syntax validation label
        self.syntax_label = QLabel("Syntax: OK")
        self.syntax_label.setObjectName("SyntaxStatusLabel")
        self.syntax_label.setProperty("statusRole", "idle")
        layout.addWidget(self.syntax_label)
        
        # Connect formula input to validation
        # Remove real-time validation - only validate on button press
        # self.formula_input.textChanged.connect(self._validate_formula)
        
        # Add search and validate buttons directly below formula
        button_row = QHBoxLayout()
        button_row.setSpacing(8)

        self.btn_search = QPushButton("Search")
        self.btn_search.clicked.connect(self._start_search)
        self.btn_search.setToolTip("Start searching with current parameters")

        self.btn_validate = QPushButton("Validate")
        self.btn_validate.clicked.connect(self._validate_formula_on_demand)
        self.btn_validate.setToolTip("Check formula for errors and warnings")

        self.btn_reset = QPushButton("Reset")
        self.btn_reset.clicked.connect(self._reset_form)
        self.btn_reset.setToolTip("Clear all fields and reset to defaults")

        self.btn_test_suite = QPushButton("Examples")
        self.btn_test_suite.clicked.connect(self._run_test_suite)
        self.btn_test_suite.setToolTip("Run educational test suite with 5 example formulas")

        self._style_button(self.btn_search, role="primary")
        self._style_button(self.btn_validate, role="accent")
        self._style_button(self.btn_reset, role="neutral")
        self._style_button(self.btn_test_suite, role="info")

        button_row.addWidget(self.btn_search)
        button_row.addWidget(self.btn_validate)
        button_row.addWidget(self.btn_reset)
        button_row.addWidget(self.btn_test_suite)
        layout.addLayout(button_row)

        self.search_status_indicator = QLabel("")
        self.search_status_indicator.setObjectName("SearchStatusIndicator")
        self.search_status_indicator.setProperty("pulseState", "off")
        self.search_status_indicator.hide()
        layout.addWidget(self.search_status_indicator)

        group_box.setLayout(layout)
        parent_layout.addWidget(group_box)
        
    def _create_results_section(self, parent_layout):
        """Create results display section"""
        group_box = QGroupBox("Search Results")
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)

        # Results display
        self.results_display = QTextEdit()
        self.results_display.setReadOnly(True)
        self.results_display.setFont(QFont("Courier", 10))
        self.results_display.setObjectName("FinderResultsDisplay")

        layout.addWidget(self.results_display)

        group_box.setLayout(layout)
        parent_layout.addWidget(group_box)
        
    def _setup_defaults(self):
        """Setup default values"""
        self.rb_line.setChecked(True)
        self.file_type_checkboxes['txt'].setChecked(True)
        self.file_type_checkboxes['md'].setChecked(True)
        self.cb_unique.setChecked(False)

        self._set_default_search_root()

        if self._launched_from_mastermenu:
            self.btn_current_folder.setVisible(False)

        self._set_formula_validation_state("idle", "Syntax: Awaiting formula")
        
    def _setup_tab_order(self):
        """Setup tab order for better navigation"""
        # Create tab order list
        tab_widgets = []
        
        # Add phrase inputs and case checkboxes
        for letter in 'ABCD':
            tab_widgets.append(self.phrase_inputs[letter])
            tab_widgets.append(self.case_sensitive_checkboxes[letter])
            
        # Add search mode radio buttons
        tab_widgets.extend([self.rb_document, self.rb_line])
        
        # Add file type checkboxes
        for cb in self.file_type_checkboxes.values():
            tab_widgets.append(cb)
        tab_widgets.append(self.custom_extensions)
        
        # Add path selection buttons
        tab_widgets.extend([self.btn_select_folder, self.btn_select_files, self.btn_current_folder])
        
        # Add formula input and unique checkbox
        tab_widgets.extend([self.formula_input, self.cb_unique])
        
        # Add control buttons
        tab_widgets.extend([self.btn_search, self.btn_validate, self.btn_reset, self.btn_test_suite])
        
        # Set tab order
        for i in range(len(tab_widgets) - 1):
            self.setTabOrder(tab_widgets[i], tab_widgets[i + 1])
            
    def _select_folders(self):
        """Select one or more folders for searching"""
        dialog = QFileDialog(self, "Select Folders")
        dialog.setFileMode(QFileDialog.FileMode.Directory)
        dialog.setOption(QFileDialog.Option.ShowDirsOnly, True)
        dialog.setOption(QFileDialog.Option.DontUseNativeDialog, True)

        list_view = dialog.findChild(QListView, "listView")
        if list_view:
            list_view.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        tree_view = dialog.findChild(QTreeView)
        if tree_view:
            tree_view.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)

        if dialog.exec():
            folders = [os.path.abspath(path) for path in dialog.selectedFiles()]
            if folders:
                self.selected_paths = folders
                if len(folders) == 1:
                    self.path_display.setText(folders[0])
                else:
                    self.path_display.setText(f"{len(folders)} folders selected")
                self._invalidate_cached_results()

    def _select_files(self):
        """Select multiple files for searching"""
        files, _ = QFileDialog.getOpenFileNames(self, "Select Files")
        if files:
            self.selected_paths = files
            if len(files) == 1:
                self.path_display.setText(files[0])
            else:
                self.path_display.setText(f"{len(files)} files selected")
            self._invalidate_cached_results()

    def _use_current_folder(self):
        """Use current working directory"""
        current_dir = os.getcwd()
        self.selected_paths = [current_dir]
        self.path_display.setText(current_dir)
        self._invalidate_cached_results()

    def _set_default_search_root(self):
        """Apply the default search root (Desktop if available)"""
        default_root = Path.home() / 'Desktop'
        if not default_root.exists():
            default_root = Path.cwd()
        default_root = default_root.resolve()
        self.selected_paths = [str(default_root)]
        self.path_display.setText(str(default_root))
        
    def _validate_formula(self):
        """Validate the formula syntax with detailed error reporting"""
        formula = self.formula_input.toPlainText().strip()

        if not formula:
            self._set_formula_validation_state("warning", "Syntax: Provide a formula before searching")
            return False

        # Comprehensive validation with detailed error reporting
        validation_result = self._comprehensive_formula_validation(formula)

        if validation_result['is_valid']:
            if validation_result['warnings']:
                state = self._determine_warning_state(validation_result['warnings'])
                self._set_formula_validation_state(state, "Logic: Review warnings")
                if state == "warning":
                    self._show_validation_dialog("Formula Warnings", validation_result['warnings'], is_error=False)
                return state == "valid"
            self._set_formula_validation_state("valid", "Syntax: OK")
            return True
        else:
            self._set_formula_validation_state("error", "Syntax: Errors detected")
            self._show_validation_dialog("Formula Errors", validation_result['errors'], is_error=True)
            return False
        
    def _validate_formula_on_demand(self):
        """Validate formula only when button is pressed - no real-time validation"""
        formula = self.formula_input.toPlainText().strip()

        if not formula:
            self._set_formula_validation_state("warning", "Syntax: Provide a formula before searching")
            feedback = {
                'is_valid': False,
                'errors': ["The formula is empty. Add phrases (A-D) or enter a custom expression."],
                'warnings': []
            }
            self._render_validation_feedback(formula, feedback)
            return

        # Run comprehensive validation
        validation_result = self._comprehensive_formula_validation(formula)

        if validation_result['is_valid']:
            warning_state = self._determine_warning_state(validation_result['warnings']) if validation_result['warnings'] else 'valid'
            status_message = "Logic: Review warnings" if warning_state != 'valid' else "Syntax: OK"
            self._set_formula_validation_state(warning_state, status_message)
        else:
            self._set_formula_validation_state("error", "Syntax: Errors detected")

        self._render_validation_feedback(formula, validation_result)
        
    def _comprehensive_formula_validation(self, formula):
        """Comprehensive formula validation with detailed error reporting"""
        errors = []
        warnings = []
        
        # Check for balanced parentheses with detailed reporting
        paren_result = self._check_balanced_parentheses_detailed(formula)
        if paren_result['errors']:
            errors.extend(paren_result['errors'])
            
        # Check for valid tokens with detailed reporting
        token_result = self._check_valid_tokens_detailed(formula)
        if token_result['errors']:
            errors.extend(token_result['errors'])
            
        # Check for logical structure issues
        structure_result = self._check_logical_structure(formula)
        if structure_result['errors']:
            errors.extend(structure_result['errors'])
        if structure_result['warnings']:
            warnings.extend(structure_result['warnings'])
            
        # Check for logical paradoxes with detailed reporting
        paradox_result = self._check_paradoxes_detailed(formula)
        if paradox_result['warnings']:
            warnings.extend(paradox_result['warnings'])
            
        # Check for impossible conditions
        impossible_result = self._check_impossible_conditions(formula)
        if impossible_result['errors']:
            errors.extend(impossible_result['errors'])
        if impossible_result['warnings']:
            warnings.extend(impossible_result['warnings'])
            
        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
        
    def _check_balanced_parentheses_detailed(self, formula):
        """Check parentheses balance with detailed error reporting"""
        errors = []
        stack = []
        pairs = {'(': ')', '[': ']', '{': '}'}
        
        for i, char in enumerate(formula):
            if char in pairs:
                stack.append((char, i))
            elif char in pairs.values():
                if not stack:
                    errors.append(f"Unmatched closing '{char}' at position {i+1}")
                else:
                    open_char, open_pos = stack.pop()
                    if pairs[open_char] != char:
                        errors.append(f"Mismatched parentheses: '{open_char}' at position {open_pos+1} closed by '{char}' at position {i+1}")
                        
        # Check for unclosed parentheses
        for open_char, pos in stack:
            errors.append(f"Unclosed '{open_char}' at position {pos+1}")
            
        return {'errors': errors}
        
    def _check_balanced_parentheses(self, formula):
        """Check if parentheses are balanced (legacy method)"""
        result = self._check_balanced_parentheses_detailed(formula)
        return len(result['errors']) == 0
        
    def _check_valid_tokens_detailed(self, formula):
        """Check tokens with detailed error reporting"""
        errors = []
        
        # Normalize formula by converting common operators to standard form
        normalized_formula = self._normalize_operators(formula)
        
        # Remove spaces and convert to upper case for analysis
        clean_formula = normalized_formula.upper().replace(' ', '')
        
        # Check for invalid characters (now including common operators)
        valid_chars = set('ABCD()[]{}ANDORNOTXR&|!~^')
        invalid_chars = set(clean_formula) - valid_chars
        if invalid_chars:
            errors.append(f"Invalid characters found: {', '.join(sorted(invalid_chars))}")
            
        # Extract tokens (including symbol operators)
        tokens = re.findall(r'AND|OR|NOT|NOR|XOR|XNOR|&&?|\|\|?|!|~|\^|[A-D]|[()[\]{}]', clean_formula)
        
        if not tokens:
            errors.append("No valid tokens found in formula")
            return {'errors': errors}
            
        # Check for invalid token sequences
        for i in range(len(tokens) - 1):
            current = tokens[i]
            next_token = tokens[i + 1]
            
            # Two variables in a row
            if current in 'ABCD' and next_token in 'ABCD':
                errors.append(f"Invalid sequence: '{current} {next_token}' - missing operator between variables")
                
            # Two binary operators in a row
            if current in ['AND', 'OR', 'NOR', 'XOR', 'XNOR'] and next_token in ['AND', 'OR', 'NOR', 'XOR', 'XNOR']:
                errors.append(f"Invalid sequence: '{current} {next_token}' - consecutive operators")
                
        return {'errors': errors}
        
    def _check_logical_structure(self, formula):
        """Check logical structure of the formula"""
        errors = []
        warnings = []
        
        # Normalize operators first
        normalized_formula = self._normalize_operators(formula)
        tokens = re.findall(r'AND|OR|NOT|NOR|XOR|XNOR|[A-D]|[()[\]{}]', normalized_formula.upper())
        
        if not tokens:
            return {'errors': errors, 'warnings': warnings}
            
        # Check for operators without operands
        binary_ops = ['AND', 'OR', 'NOR', 'XOR', 'XNOR']
        
        for i, token in enumerate(tokens):
            if token in binary_ops:
                # Check if there's a valid operand before and after
                if i == 0:
                    errors.append(f"'{token}' operator at start of formula needs left operand")
                elif i == len(tokens) - 1:
                    errors.append(f"'{token}' operator at end of formula needs right operand")
                else:
                    # Check left operand
                    left_token = tokens[i-1]
                    if left_token in binary_ops or left_token == 'NOT':
                        errors.append(f"'{token}' operator missing valid left operand")
                    
                    # Check right operand
                    right_token = tokens[i+1]
                    if right_token in binary_ops:
                        errors.append(f"'{token}' operator missing valid right operand")
                        
            elif token == 'NOT':
                # Check if NOT has a valid operand
                if i == len(tokens) - 1:
                    errors.append("'NOT' operator at end of formula needs operand")
                else:
                    next_token = tokens[i+1]
                    if next_token in binary_ops:
                        errors.append("'NOT' operator missing valid operand")
                        
        return {'errors': errors, 'warnings': warnings}
        
    def _check_paradoxes_detailed(self, formula):
        """Check for logical paradoxes with detailed reporting"""
        warnings = []
        
        # Check for obvious contradictions like "A AND NOT A"
        for letter in 'ABCD':
            # Pattern: A AND NOT A
            pattern1 = f'{letter} AND NOT {letter}'
            pattern2 = f'NOT {letter} AND {letter}'
            
            if pattern1 in formula.upper() or pattern2 in formula.upper():
                warnings.append(f"Logical paradox detected: '{letter} AND NOT {letter}' - this will always be false")
                
        # Check for tautologies like "A OR NOT A"
        for letter in 'ABCD':
            pattern1 = f'{letter} OR NOT {letter}'
            pattern2 = f'NOT {letter} OR {letter}'
            
            if pattern1 in formula.upper() or pattern2 in formula.upper():
                warnings.append(f"Tautology detected: '{letter} OR NOT {letter}' - this will always be true")
                
        return {'warnings': warnings}
        
    def _check_impossible_conditions(self, formula):
        """Check for impossible logical conditions"""
        errors = []
        warnings = []
        
        # Check for empty parentheses
        if '()' in formula or '[]' in formula or '{}' in formula:
            errors.append("Empty parentheses/brackets found - they must contain expressions")
            
        # Check for variables that don't have corresponding phrases
        used_vars = set(re.findall(r'[A-D]', formula.upper()))
        empty_vars = []
        
        for var in used_vars:
            if var in self.phrase_inputs:
                if not self.phrase_inputs[var].text().strip():
                    empty_vars.append(var)
                    
        if empty_vars:
            warnings.append(f"Variables {', '.join(empty_vars)} are used in formula but have no corresponding phrases")
            
        return {'errors': errors, 'warnings': warnings}
        
    def _normalize_operators(self, formula):
        """Convert common logical operators to standard form"""
        import re
        # Order matters - longer operators first to avoid partial replacements
        operator_replacements = [
            ('&&', ' AND '),
            ('||', ' OR '),
            ('&', ' AND '),
            ('|', ' OR '),
            ('!', ' NOT '),
            ('~', ' NOT '),
            ('^', ' XOR ')
        ]
        
        # Apply replacements in order
        normalized = formula
        for symbol, replacement in operator_replacements:
            normalized = normalized.replace(symbol, replacement)
            
        # Clean up multiple spaces
        normalized = re.sub(r'\s+', ' ', normalized).strip()
            
        return normalized
        
    def _auto_construct_formula(self):
        """Automatically construct formula from non-empty variables"""
        active_vars = []
        
        # Find all variables with non-empty phrases
        for letter in 'ABCD':
            if self.phrase_inputs[letter].text().strip():
                active_vars.append(letter)
                
        if not active_vars:
            return ""
        elif len(active_vars) == 1:
            return active_vars[0]
        else:
            # Join with AND operator
            return " AND ".join(active_vars)
            
    def _update_auto_formula(self):
        """Update formula automatically if user hasn't entered one"""
        current_formula = self.formula_input.toPlainText().strip()
        
        # Only auto-construct if formula is empty or was previously auto-constructed
        if not current_formula or hasattr(self, '_last_auto_formula') and current_formula == self._last_auto_formula:
            auto_formula = self._auto_construct_formula()
            if auto_formula:
                self.formula_input.setPlainText(auto_formula)
                self._last_auto_formula = auto_formula
            elif current_formula:
                self.formula_input.clear()
                self._last_auto_formula = ""
    
    def _refresh_formula_highlighting(self):
        """Refresh formula highlighting when case sensitivity settings change"""
        if hasattr(self, 'highlighter'):
            self.highlighter.refresh_highlighting()
        
    def _show_validation_dialog(self, title, messages, is_error=True):
        """Show validation dialog with detailed error/warning information"""
        dialog = QMessageBox()
        dialog.setWindowTitle(title)
        
        if is_error:
            dialog.setIcon(QMessageBox.Icon.Critical)
        else:
            dialog.setIcon(QMessageBox.Icon.Warning)
            
        # Format messages for display
        formatted_messages = []
        for i, msg in enumerate(messages, 1):
            formatted_messages.append(f"{i}. {msg}")
            
        dialog.setText("\n".join(formatted_messages))
        dialog.setDetailedText("Formula validation found the following issues:\n\n" + "\n".join(formatted_messages))
        
        if is_error:
            dialog.setStandardButtons(QMessageBox.StandardButton.Ok)
        else:
            dialog.setStandardButtons(QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Ignore)
            
        dialog.exec()
        
    def _check_valid_tokens(self, formula):
        """Check if all tokens in formula are valid (legacy method)"""
        result = self._check_valid_tokens_detailed(formula)
        return len(result['errors']) == 0
        
    def _check_paradoxes(self, formula):
        """Basic check for logical paradoxes (legacy method)"""
        result = self._check_paradoxes_detailed(formula)
        return len(result['warnings']) > 0
        
    def _start_search(self):
        """Start the search operation"""
        if not self._validate_search_parameters():
            return
            
        # Stop any existing search
        if self.search_thread and self.search_thread.isRunning():
            self.search_worker.cancel()
            self.search_thread.quit()
            self.search_thread.wait()
            
        # Clear results
        self.results_display.clear()
        self._has_search_results = False

        # Prepare search parameters
        search_params = self._prepare_search_parameters()
        
        # Start search
        self.search_thread = QThread()
        self.search_worker = SearchWorker(search_params)
        self.search_worker.moveToThread(self.search_thread)
        
        # Connect signals
        self.search_thread.started.connect(self.search_worker.run_search)
        self.search_worker.result_found.connect(self._display_result)
        self.search_worker.search_finished.connect(self._search_finished)
        self.search_worker.progress_update.connect(self._update_progress)
        
        # Update UI
        self.btn_search.setText("Searching...")
        self.btn_search.setEnabled(False)

        if hasattr(self, 'search_status_indicator'):
            self._pulse_state_on = True
            self.search_status_indicator.setProperty("pulseState", "on")
            self.search_status_indicator.setText("🟢 Searching…")
            self.search_status_indicator.show()
            self.search_status_indicator.style().unpolish(self.search_status_indicator)
            self.search_status_indicator.style().polish(self.search_status_indicator)
            self._pulse_timer.start()

        # Start the thread
        self.search_thread.start()
        
    def _validate_search_parameters(self):
        """Validate search parameters before starting"""
        # Check if formula is valid (show error dialog during search)
        formula = self.formula_input.toPlainText().strip()
        if formula:  # Only validate if there's a formula
            validation_result = self._comprehensive_formula_validation(formula)
            if not validation_result['is_valid']:
                self._set_formula_validation_state("error", "Syntax: Errors detected")
                self._render_validation_feedback(formula, validation_result)
                errors_text = "\n".join([f"• {e}" for e in validation_result['errors']])
                QMessageBox.critical(
                    self,
                    "Search Error - Invalid Formula",
                    f"❌ Cannot search with invalid formula:\n\n{errors_text}\n\nUse 'Validate Formula' to review suggestions."
                )
                return False
            warning_state = self._determine_warning_state(validation_result['warnings']) if validation_result['warnings'] else 'valid'
            status_message = "Logic: Review warnings" if warning_state != 'valid' else "Syntax: OK"
            self._set_formula_validation_state(warning_state, status_message)
            if warning_state != 'valid':
                self._render_validation_feedback(formula, validation_result)
                warnings_text = "\n".join([f"• {w}" for w in validation_result['warnings']])
                QMessageBox.warning(
                    self,
                    "Search Blocked - Logical Issue",
                    f"⚠️ Formula cannot be executed until the logical conflicts are resolved:\n\n{warnings_text}"
                )
                return False
        
        # Check if any phrases are entered
        has_phrases = any(self.phrase_inputs[letter].text().strip() for letter in 'ABCD')
        if not has_phrases:
            QMessageBox.warning(self, "No Phrases", "Please enter at least one search phrase.")
            return False
            
        # Check if any file types are selected
        has_file_types = any(cb.isChecked() for cb in self.file_type_checkboxes.values())
        has_custom = self.custom_extensions.text().strip()
        
        if not has_file_types and not has_custom:
            QMessageBox.warning(self, "No File Types", "Please select at least one file type.")
            return False
            
        # Check if search path is selected
        if not self.selected_paths:
            QMessageBox.warning(self, "No Search Path", "Please select a search path.")
            return False
            
        return True
        
    def _prepare_search_parameters(self):
        """Prepare search parameters for the worker"""
        # Get phrases with case sensitivity settings
        phrases = {}
        for letter in 'ABCD':
            phrases[letter] = {
                'text': self.phrase_inputs[letter].text().strip(),
                'case_sensitive': self.case_sensitive_checkboxes[letter].isChecked()
            }
            
        # Get file extensions
        extensions = []
        for file_type, cb in self.file_type_checkboxes.items():
            if cb.isChecked():
                extensions.append(f".{file_type}")
                
        # Add custom extensions
        custom_ext = self.custom_extensions.text().strip()
        if custom_ext:
            for ext in custom_ext.split(','):
                ext = ext.strip()
                if ext and not ext.startswith('.'):
                    ext = '.' + ext
                if ext:
                    extensions.append(ext)
                    
        return {
            'phrases': phrases,
            'search_mode': 'document' if self.rb_document.isChecked() else 'line',
            'file_extensions': extensions,
            'search_paths': self.selected_paths,
            'formula': self.formula_input.toPlainText().strip(),
            'unique_mode': self.cb_unique.isChecked()
        }
        
    def _truncate_result_text(self, text: str, limit: int = 1024) -> str:
        """Clamp result text so the UI stays readable."""
        if len(text) <= limit:
            return text
        return text[: max(0, limit - 3)].rstrip() + "..."

    def _display_result(self, file_path, content, line_number, is_unique):
        """Display a search result"""
        # Convert absolute path to relative if possible
        try:
            rel_path = os.path.relpath(file_path)
            if len(rel_path) < len(file_path):
                display_path = rel_path
            else:
                display_path = file_path
        except:
            display_path = file_path
            
        # File path in light blue
        self.results_display.setTextColor(QColor(210, 238, 255))  # Brighter blue
        self.results_display.append(display_path)
        
        # Content with line number
        if line_number > 0:
            # Line number in red if unique, white if not
            line_color = QColor(255, 100, 100) if is_unique else QColor(255, 255, 255)
            content_color = QColor(255, 255, 255)  # White
            
            self.results_display.setTextColor(line_color)
            self.results_display.insertPlainText(f"{line_number}: ")
            
            truncated = self._truncate_result_text(content)
            self.results_display.setTextColor(content_color)
            self.results_display.insertPlainText(truncated)
            self.results_display.append("")  # New line
        else:
            # Document match
            self.results_display.setTextColor(QColor(255, 255, 255))
            self.results_display.append(self._truncate_result_text(content))
            
        self.results_display.append("")  # Extra line for spacing
        self._has_search_results = True

    def _search_finished(self, message):
        """Handle search completion"""
        self.results_display.setTextColor(QColor(100, 255, 100))  # Light green
        self.results_display.append(f"\n{message}")
        self._has_search_results = True

        # Reset button state
        self.btn_search.setText("Search")
        self.btn_search.setEnabled(True)

        if hasattr(self, 'search_status_indicator'):
            self._pulse_timer.stop()
            self.search_status_indicator.setProperty("pulseState", "off")
            self.search_status_indicator.style().unpolish(self.search_status_indicator)
            self.search_status_indicator.style().polish(self.search_status_indicator)
            self.search_status_indicator.hide()

        # Clean up thread
        if self.search_thread:
            self.search_thread.quit()
            self.search_thread.wait()
            
    def _update_progress(self, current, total):
        """Update search progress"""
        self.btn_search.setText(f"Searching... ({current}/{total})")
        
    def _reset_form(self):
        """Reset/clear the form"""
        # Clear phrases and reset case sensitivity
        for line_edit in self.phrase_inputs.values():
            line_edit.clear()
        for checkbox in self.case_sensitive_checkboxes.values():
            checkbox.setChecked(False)
            
        # Reset search mode
        self.rb_line.setChecked(True)
        
        # Reset file types to defaults
        for cb in self.file_type_checkboxes.values():
            cb.setChecked(False)
        self.file_type_checkboxes['txt'].setChecked(True)
        self.file_type_checkboxes['md'].setChecked(True)
        
        # Clear custom extensions
        self.custom_extensions.clear()

        # Reset path to default root
        self._set_default_search_root()

        # Clear formula and auto-formula tracking
        self.formula_input.clear()
        self._last_auto_formula = ""
        
        # Reset unique mode
        self.cb_unique.setChecked(False)

        # Clear results
        self.results_display.clear()
        self._has_search_results = False
        
    def _run_test_suite(self):
        """Run the educational test suite"""
        # Show a dialog to choose test suite type
        dialog = QMessageBox()
        dialog.setWindowTitle("Educational Test Suite")
        dialog.setIcon(QMessageBox.Icon.Information)
        dialog.setText("Choose Test Suite Type")
        dialog.setInformativeText(
            "Choose between basic learning examples or comprehensive edge case testing:\n\n"
            "📚 BASIC EXAMPLES:\n"
            "• 5 progressive difficulty levels (simple to expert)\n"
            "• Different formulas each run\n"
            "• Great for learning formula construction\n\n"
            "🎓 COMPREHENSIVE TESTING:\n"
            "• Advanced edge case scenarios\n"
            "• Case sensitivity + logic combinations\n"
            "• Document vs Line search modes\n"
            "• Expert-level pattern testing\n\n"
            "Results will be displayed in this window."
        )
        
        # Add custom buttons
        basic_button = dialog.addButton("📚 Basic Examples", QMessageBox.ButtonRole.AcceptRole)
        advanced_button = dialog.addButton("🎓 Comprehensive Testing", QMessageBox.ButtonRole.AcceptRole)
        cancel_button = dialog.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)
        
        result = dialog.exec()
        clicked_button = dialog.clickedButton()
        
        if clicked_button == basic_button:
            self._execute_basic_test_suite()
        elif clicked_button == advanced_button:
            self._execute_comprehensive_test_suite()
    
    def _execute_basic_test_suite(self):
        """Execute the basic educational test suite"""
        try:
            # Run the basic test suite internally
            self._run_basic_test_suite_internal()
        except Exception as e:
            self.results_display.clear()
            self.results_display.setTextColor(QColor(255, 100, 100))
            self.results_display.append(f"❌ Error running basic test suite: {e}")
    
    def _execute_comprehensive_test_suite(self):
        """Execute the comprehensive advanced test suite"""
        try:
            # Run the comprehensive test suite internally
            self._run_comprehensive_test_suite_internal()
        except Exception as e:
            self.results_display.clear()
            self.results_display.setTextColor(QColor(255, 100, 100))
            self.results_display.append(f"❌ Error running comprehensive test suite: {e}")
    
    def _run_basic_test_suite_internal(self):
        """Run test suite internally and display results"""
        try:
            # Import and run the test suite generator
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Tests'))
            from test_suite_generator import TestSuiteRunner
            
            # Clear results display
            self.results_display.clear()
            self.results_display.setTextColor(QColor(100, 200, 255))
            self.results_display.append("🎓 Running Educational Test Suite...")
            self.results_display.append("=" * 50)
            
            # Run the test suite
            runner = TestSuiteRunner()
            scenarios = runner.generator.generate_test_suite()
            
            # Display each scenario
            for i, scenario in enumerate(scenarios, 1):
                self.results_display.setTextColor(QColor(255, 200, 100))
                self.results_display.append(f"\n📊 Level {scenario['complexity']}: {scenario['name']}")
                self.results_display.append("=" * 40)
                
                # Show variables with simple case sensitivity indicators
                self.results_display.setTextColor(QColor(150, 255, 150))
                self.results_display.append("Variables:")
                for letter, phrase_data in scenario['phrases'].items():
                    if phrase_data['text']:
                        if phrase_data['case_sensitive']:
                            case_info = "Match Case"
                            # Show underlined letter for case sensitive
                            letter_display = f"{letter}̲"
                        else:
                            case_info = "Any Case"
                            # Show normal letter for case insensitive
                            letter_display = letter
                        self.results_display.append(f"  {letter_display} = '{phrase_data['text']}' ({case_info})")
                
                # Show formula
                self.results_display.setTextColor(QColor(255, 255, 100))
                self.results_display.append(f"Formula: {scenario['formula']}")
                
                # Show educational note
                self.results_display.setTextColor(QColor(200, 200, 255))
                self.results_display.append(f"💡 {scenario['educational_note']}")
                
                # Offer to try this formula
                self.results_display.setTextColor(QColor(100, 255, 100))
                self.results_display.append("← You can copy this formula to try it yourself!")
            
            # Final message
            self.results_display.setTextColor(QColor(255, 200, 100))
            self.results_display.append("\n" + "=" * 50)
            self.results_display.append("🎓 Educational Examples Complete!")
            self.results_display.append("💡 Try copying any formula above to test it yourself")
            self.results_display.append("🔄 Click 'Run Examples' again for different formulas")
            
            # Add visual indicator explanation
            self.results_display.setTextColor(QColor(200, 200, 255))
            self.results_display.append("\n📋 Visual Indicators:")
            self.results_display.append("Normal letter (A) = Any Case (case insensitive)")
            self.results_display.append("Underlined letter (A̲) = Match Case (case sensitive)")
            self.results_display.append("Formula variables show underlines when Match Case is checked")
            
        except Exception as e:
            self.results_display.setTextColor(QColor(255, 100, 100))
            self.results_display.append(f"Error running basic test suite: {e}")
    
    def _run_comprehensive_test_suite_internal(self):
        """Run comprehensive advanced test suite internally and display results"""
        try:
            # Import and run the advanced test suite
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Tests'))
            from test_suite_advanced_scenarios import AdvancedTestSuiteRunner
            
            # Clear results display
            self.results_display.clear()
            self.results_display.setTextColor(QColor(200, 100, 255))
            self.results_display.append("🎓 Running Comprehensive Advanced Test Suite...")
            self.results_display.append("=" * 60)
            self.results_display.append("Testing complex interactions: Logic + Case Sensitivity + Search Modes")
            self.results_display.append("=" * 60)
            
            # Run the comprehensive test suite
            runner = AdvancedTestSuiteRunner()
            scenarios = runner.generator.generate_comprehensive_test_suite()
            
            # Group scenarios by category for organized display
            categories = {}
            for scenario in scenarios:
                category = scenario['category']
                if category not in categories:
                    categories[category] = []
                categories[category].append(scenario)
            
            # Display scenarios by category
            for category_name, category_scenarios in categories.items():
                self.results_display.setTextColor(QColor(255, 150, 50))
                self.results_display.append(f"\n📋 CATEGORY: {category_name}")
                self.results_display.append("=" * 50)
                
                for i, scenario in enumerate(category_scenarios, 1):
                    self.results_display.setTextColor(QColor(100, 255, 200))
                    self.results_display.append(f"\n🔬 Test {i}: {scenario['name']}")
                    self.results_display.append("-" * 40)
                    
                    # Description and educational note
                    self.results_display.setTextColor(QColor(200, 200, 255))
                    self.results_display.append(f"📝 {scenario['description']}")
                    self.results_display.setTextColor(QColor(255, 255, 150))
                    self.results_display.append(f"🎓 {scenario['educational_note']}")
                    
                    # Show configuration
                    self.results_display.setTextColor(QColor(150, 255, 150))
                    self.results_display.append(f"Formula: {scenario['formula']}")
                    self.results_display.append(f"Search Mode: {scenario['search_mode']}")
                    
                    # Show variables with simple case sensitivity indicators
                    self.results_display.append("Variables:")
                    for letter, phrase_data in scenario['phrases'].items():
                        if phrase_data['text']:
                            if phrase_data['case_sensitive']:
                                case_info = "Match Case"
                                # Show underlined letter for case sensitive
                                letter_display = f"{letter}̲"
                            else:
                                case_info = "Any Case"
                                # Show normal letter for case insensitive
                                letter_display = letter
                            self.results_display.append(f"  {letter_display} = '{phrase_data['text']}' ({case_info})")
                    
                    # Show expected behavior
                    self.results_display.setTextColor(QColor(255, 200, 100))
                    self.results_display.append(f"Expected: {scenario['expected_behavior']}")
                    
                    # Show test cases if available
                    if 'test_cases' in scenario and scenario['test_cases']:
                        self.results_display.setTextColor(QColor(255, 255, 255))
                        self.results_display.append("Test Cases:")
                        for test_input, expected in scenario['test_cases']:
                            self.results_display.append(f"  '{test_input}' → {expected}")
            
            # Summary and learning points
            self.results_display.setTextColor(QColor(255, 200, 100))
            self.results_display.append("\n" + "=" * 60)
            self.results_display.append("🎓 COMPREHENSIVE TEST SUITE COMPLETE!")
            self.results_display.append("=" * 60)
            
            self.results_display.setTextColor(QColor(150, 255, 150))
            self.results_display.append("\n🔑 KEY LEARNING POINTS:")
            self.results_display.append("• Case sensitivity works independently for each variable (A-D)")
            self.results_display.append("• Logical operators (&, |, !) respect individual case settings")
            self.results_display.append("• Document mode evaluates entire files; Line mode evaluates each line")
            self.results_display.append("• Parentheses control operator precedence in complex formulas")
            self.results_display.append("• Empty phrases are treated as always false")
            self.results_display.append("• Special characters are treated as literal text, not regex")
            
            self.results_display.setTextColor(QColor(100, 200, 255))
            self.results_display.append("\n🚀 NEXT STEPS:")
            self.results_display.append("• Try these scenarios in actual searches")
            self.results_display.append("• Experiment with your own combinations")
            self.results_display.append("• Use 'Match Case' checkboxes for case sensitivity control")
            self.results_display.append("• Switch between Document and Line search modes")
            
            self.results_display.setTextColor(QColor(200, 200, 255))
            self.results_display.append("\n📋 Visual Indicators:")
            self.results_display.append("Normal letter (A) = Any Case (case insensitive)")
            self.results_display.append("Underlined letter (A̲) = Match Case (case sensitive)")
            self.results_display.append("Formula variables show underlines when Match Case is checked")
            
        except Exception as e:
            self.results_display.setTextColor(QColor(255, 100, 100))
            self.results_display.append(f"Error running comprehensive test suite: {e}")
            import traceback
            self.results_display.append(traceback.format_exc())
        
    def closeEvent(self, event):
        """Handle application close event"""
        # Clean up search thread
        if self.search_thread and self.search_thread.isRunning():
            self.search_worker.cancel()
            self.search_thread.quit()
            self.search_thread.wait()
        event.accept()


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Finder")
    app.setApplicationVersion("1.0")
    app.setOrganizationName("Project Himalaya")
    
    # Create and show the main window
    window = Finder()
    window.show()
    
    # Run the application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
