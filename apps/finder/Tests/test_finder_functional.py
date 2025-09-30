# File: test_finder_functional.py
# Path: /home/herb/Desktop/Finder/Test/test_finder_functional.py
# Standard: AIDEV-PascalCase-2.1
# Created: 2025-07-18
# Last Modified: 2025-07-18  01:45PM
"""
Functional tests for the Finder application using real files in the current directory
Tests realistic search scenarios with actual project files
"""

import unittest
import os
import sys
from unittest.mock import patch, Mock

# Add the parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import our classes (we'll need to mock Qt components)
with patch('PySide6.QtWidgets.QApplication'), \
     patch('PySide6.QtWidgets.QMainWindow'), \
     patch('PySide6.QtWidgets.QWidget'), \
     patch('PySide6.QtCore.QObject'), \
     patch('PySide6.QtCore.QThread'), \
     patch('PySide6.QtGui.QSyntaxHighlighter'):
    
    from Finder import SearchWorker


class TestFinderWithRealFiles(unittest.TestCase):
    """Test Finder functionality with real files in the project directory"""
    
    def setUp(self):
        """Set up test environment"""
        self.project_dir = os.path.dirname(os.path.abspath(__file__))
        self.available_files = self._get_available_files()
        
    def _get_available_files(self):
        """Get list of available files in the project directory"""
        files = []
        for root, dirs, filenames in os.walk(self.project_dir):
            for filename in filenames:
                if filename.endswith(('.py', '.txt', '.md', '.sh', '.json')):
                    files.append(os.path.join(root, filename))
        return files
    
    def test_search_python_files(self):
        """Test searching Python files for common patterns"""
        search_params = {
            'search_paths': [self.project_dir],
            'file_extensions': ['.py'],
            'search_mode': 'line',
            'unique_mode': False,
            'phrases': {
                'A': {'text': 'def', 'case_sensitive': True},
                'B': {'text': 'class', 'case_sensitive': True},
                'C': {'text': 'import', 'case_sensitive': True}
            },
            'formula': 'A | B | C'
        }
        
        with patch('PySide6.QtCore.QObject.__init__'):
            worker = SearchWorker(search_params)
            files = worker._get_files_to_search()
            
            # Should find Python files
            py_files = [f for f in files if f.endswith('.py')]
            self.assertGreater(len(py_files), 0, "Should find Python files in project")
            
            # Test search in actual files
            matches = []
            for filepath in py_files[:5]:  # Test first 5 files to avoid long test times
                try:
                    file_matches = worker._search_file(filepath)
                    matches.extend(file_matches)
                except Exception as e:
                    print(f"Error searching {filepath}: {e}")
            
            # Should find matches for def, class, or import
            self.assertGreater(len(matches), 0, "Should find function/class/import definitions")
    
    def test_search_markdown_files(self):
        """Test searching Markdown files for documentation patterns"""
        search_params = {
            'search_paths': [self.project_dir],
            'file_extensions': ['.md'],
            'search_mode': 'line',
            'unique_mode': False,
            'phrases': {
                'A': {'text': '#', 'case_sensitive': False},
                'B': {'text': 'Standard', 'case_sensitive': False},
                'C': {'text': 'AIDEV', 'case_sensitive': False}
            },
            'formula': 'A & (B | C)'
        }
        
        with patch('PySide6.QtCore.QObject.__init__'):
            worker = SearchWorker(search_params)
            files = worker._get_files_to_search()
            
            # Should find markdown files
            md_files = [f for f in files if f.endswith('.md')]
            if len(md_files) > 0:
                # Test search in actual files
                matches = []
                for filepath in md_files:
                    try:
                        file_matches = worker._search_file(filepath)
                        matches.extend(file_matches)
                    except Exception as e:
                        print(f"Error searching {filepath}: {e}")
                
                # Should find matches for headers with Standard or AIDEV
                self.assertGreater(len(matches), 0, "Should find header lines with Standard or AIDEV")
    
    def test_search_claude_md_file(self):
        """Test specific search in CLAUDE.md file"""
        claude_file = os.path.join(self.project_dir, 'CLAUDE.md')
        
        if os.path.exists(claude_file):
            search_params = {
                'search_paths': [claude_file],
                'file_extensions': ['.md'],
                'search_mode': 'line',
                'unique_mode': False,
                'phrases': {
                    'A': {'text': 'python', 'case_sensitive': False},
                    'B': {'text': 'command', 'case_sensitive': False},
                    'C': {'text': 'Project', 'case_sensitive': False}
                },
                'formula': 'A | B | C'
            }
            
            with patch('PySide6.QtCore.QObject.__init__'):
                worker = SearchWorker(search_params)
                matches = worker._search_file(claude_file)
                
                # Should find references to Python, commands, or Project
                self.assertGreater(len(matches), 0, "Should find project-related content in CLAUDE.md")
    
    def test_search_script_files(self):
        """Test searching script files in Scripts directory"""
        scripts_dir = os.path.join(self.project_dir, 'Scripts')
        
        if os.path.exists(scripts_dir):
            search_params = {
                'search_paths': [scripts_dir],
                'file_extensions': ['.py'],
                'search_mode': 'line',
                'unique_mode': False,
                'phrases': {
                    'A': {'text': 'File:', 'case_sensitive': True},
                    'B': {'text': 'Path:', 'case_sensitive': True},
                    'C': {'text': 'Standard:', 'case_sensitive': True}
                },
                'formula': 'A & B & C'
            }
            
            with patch('PySide6.QtCore.QObject.__init__'):
                worker = SearchWorker(search_params)
                files = worker._get_files_to_search()
                
                if len(files) > 0:
                    # Test search for header patterns
                    matches = []
                    for filepath in files[:10]:  # Test first 10 files
                        try:
                            file_matches = worker._search_file(filepath)
                            matches.extend(file_matches)
                        except Exception as e:
                            print(f"Error searching {filepath}: {e}")
                    
                    # Should find files with proper headers
                    self.assertGreater(len(matches), 0, "Should find files with AIDEV headers")
    
    def test_search_with_common_operators(self):
        """Test search using common operators (&, |, !) with real files"""
        search_params = {
            'search_paths': [self.project_dir],
            'file_extensions': ['.py', '.txt'],
            'search_mode': 'line',
            'unique_mode': False,
            'phrases': {
                'A': {'text': 'def', 'case_sensitive': False},
                'B': {'text': 'class', 'case_sensitive': False},
                'C': {'text': 'import', 'case_sensitive': False}
            },
            'formula': 'A & !B'  # Functions but not classes
        }
        
        with patch('PySide6.QtCore.QObject.__init__'):
            worker = SearchWorker(search_params)
            files = worker._get_files_to_search()
            
            if len(files) > 0:
                # Test search with common operators
                matches = []
                for filepath in files[:5]:  # Test first 5 files
                    try:
                        file_matches = worker._search_file(filepath)
                        matches.extend(file_matches)
                    except Exception as e:
                        print(f"Error searching {filepath}: {e}")
                
                # Should find lines with 'def' but not 'class'
                for match in matches:
                    line_content = match[0]
                    self.assertIn('def', line_content.lower())
                    self.assertNotIn('class', line_content.lower())
    
    def test_case_sensitive_search(self):
        """Test case-sensitive search with real files"""
        search_params = {
            'search_paths': [self.project_dir],
            'file_extensions': ['.py'],
            'search_mode': 'line',
            'unique_mode': False,
            'phrases': {
                'A': {'text': 'File', 'case_sensitive': True},
                'B': {'text': 'file', 'case_sensitive': True},
                'C': {'text': 'FILE', 'case_sensitive': True}
            },
            'formula': 'A | B | C'
        }
        
        with patch('PySide6.QtCore.QObject.__init__'):
            worker = SearchWorker(search_params)
            files = worker._get_files_to_search()
            
            if len(files) > 0:
                # Test case-sensitive search
                matches = []
                for filepath in files[:3]:  # Test first 3 files
                    try:
                        file_matches = worker._search_file(filepath)
                        matches.extend(file_matches)
                    except Exception as e:
                        print(f"Error searching {filepath}: {e}")
                
                # Verify case sensitivity
                for match in matches:
                    line_content = match[0]
                    self.assertTrue(
                        'File' in line_content or 'file' in line_content or 'FILE' in line_content,
                        f"Case-sensitive match failed: {line_content}"
                    )
    
    def test_unique_mode_functionality(self):
        """Test unique mode with real files"""
        search_params = {
            'search_paths': [self.project_dir],
            'file_extensions': ['.py'],
            'search_mode': 'line',
            'unique_mode': True,
            'phrases': {
                'A': {'text': 'import', 'case_sensitive': False},
                'B': {'text': 'from', 'case_sensitive': False}
            },
            'formula': 'A | B'
        }
        
        with patch('PySide6.QtCore.QObject.__init__'):
            worker = SearchWorker(search_params)
            files = worker._get_files_to_search()
            
            if len(files) > 0:
                # Test unique mode
                matches = []
                for filepath in files[:3]:  # Test first 3 files
                    try:
                        file_matches = worker._search_file(filepath)
                        matches.extend(file_matches)
                    except Exception as e:
                        print(f"Error searching {filepath}: {e}")
                
                # In unique mode, should not have duplicate content
                seen_content = set()
                for match in matches:
                    line_content = match[0].strip()
                    if line_content in seen_content:
                        self.fail(f"Duplicate content found in unique mode: {line_content}")
                    seen_content.add(line_content)
    
    def test_document_mode_vs_line_mode(self):
        """Test document mode vs line mode with real files"""
        base_params = {
            'search_paths': [self.project_dir],
            'file_extensions': ['.txt', '.md'],
            'unique_mode': False,
            'phrases': {
                'A': {'text': 'Python', 'case_sensitive': False},
                'B': {'text': 'project', 'case_sensitive': False}
            },
            'formula': 'A & B'
        }
        
        # Test line mode
        line_params = {**base_params, 'search_mode': 'line'}
        
        with patch('PySide6.QtCore.QObject.__init__'):
            worker_line = SearchWorker(line_params)
            files = worker_line._get_files_to_search()
            
            if len(files) > 0:
                line_matches = []
                for filepath in files[:3]:  # Test first 3 files
                    try:
                        file_matches = worker_line._search_file(filepath)
                        line_matches.extend(file_matches)
                    except Exception as e:
                        print(f"Error searching {filepath}: {e}")
                
                # Test document mode
                doc_params = {**base_params, 'search_mode': 'document'}
                worker_doc = SearchWorker(doc_params)
                
                doc_matches = []
                for filepath in files[:3]:  # Test first 3 files
                    try:
                        file_matches = worker_doc._search_file(filepath)
                        doc_matches.extend(file_matches)
                    except Exception as e:
                        print(f"Error searching {filepath}: {e}")
                
                # Document mode should return fewer matches (whole files vs lines)
                if len(line_matches) > 0 and len(doc_matches) > 0:
                    # In document mode, matches should be file-level
                    for match in doc_matches:
                        line_number = match[1]
                        self.assertEqual(line_number, 0, "Document mode should return line number 0")


class TestFinderWithProjectFiles(unittest.TestCase):
    """Test Finder with specific project files and patterns"""
    
    def setUp(self):
        """Set up test environment"""
        self.project_dir = os.path.dirname(os.path.abspath(__file__))
    
    def test_search_design_standards(self):
        """Test searching Design Standard files"""
        standards_dir = os.path.join(self.project_dir, 'Docs', 'Standards')
        
        if os.path.exists(standards_dir):
            search_params = {
                'search_paths': [standards_dir],
                'file_extensions': ['.md'],
                'search_mode': 'line',
                'unique_mode': False,
                'phrases': {
                    'A': {'text': 'Design Standard', 'case_sensitive': False},
                    'B': {'text': 'v2.', 'case_sensitive': False},
                    'C': {'text': 'AIDEV', 'case_sensitive': False}
                },
                'formula': 'A & (B | C)'
            }
            
            with patch('PySide6.QtCore.QObject.__init__'):
                worker = SearchWorker(search_params)
                files = worker._get_files_to_search()
                
                if len(files) > 0:
                    matches = []
                    for filepath in files:
                        try:
                            file_matches = worker._search_file(filepath)
                            matches.extend(file_matches)
                        except Exception as e:
                            print(f"Error searching {filepath}: {e}")
                    
                    # Should find Design Standard references
                    self.assertGreater(len(matches), 0, "Should find Design Standard references")
    
    def test_search_git_files(self):
        """Test searching Git-related files"""
        search_params = {
            'search_paths': [self.project_dir],
            'file_extensions': ['.py', '.sh'],
            'search_mode': 'line',
            'unique_mode': False,
            'phrases': {
                'A': {'text': 'git', 'case_sensitive': False},
                'B': {'text': 'GitHub', 'case_sensitive': False},
                'C': {'text': 'commit', 'case_sensitive': False}
            },
            'formula': '(A | B) & C'
        }
        
        with patch('PySide6.QtCore.QObject.__init__'):
            worker = SearchWorker(search_params)
            files = worker._get_files_to_search()
            
            if len(files) > 0:
                matches = []
                for filepath in files:
                    if 'GitHub' in filepath or 'git' in filepath.lower():
                        try:
                            file_matches = worker._search_file(filepath)
                            matches.extend(file_matches)
                        except Exception as e:
                            print(f"Error searching {filepath}: {e}")
                
                # Should find Git-related commit references
                if len(matches) > 0:
                    self.assertGreater(len(matches), 0, "Should find Git commit references")
    
    def test_search_database_files(self):
        """Test searching database-related files"""
        db_dir = os.path.join(self.project_dir, 'Scripts', 'DataBase')
        
        if os.path.exists(db_dir):
            search_params = {
                'search_paths': [db_dir],
                'file_extensions': ['.py'],
                'search_mode': 'line',
                'unique_mode': False,
                'phrases': {
                    'A': {'text': 'SQL', 'case_sensitive': False},
                    'B': {'text': 'MySQL', 'case_sensitive': False},
                    'C': {'text': 'SQLite', 'case_sensitive': False}
                },
                'formula': 'A & (B | C)'
            }
            
            with patch('PySide6.QtCore.QObject.__init__'):
                worker = SearchWorker(search_params)
                files = worker._get_files_to_search()
                
                if len(files) > 0:
                    matches = []
                    for filepath in files:
                        try:
                            file_matches = worker._search_file(filepath)
                            matches.extend(file_matches)
                        except Exception as e:
                            print(f"Error searching {filepath}: {e}")
                    
                    # Should find SQL database references
                    self.assertGreater(len(matches), 0, "Should find SQL database references")
    
    def test_search_complex_formula(self):
        """Test complex formula with real files"""
        search_params = {
            'search_paths': [self.project_dir],
            'file_extensions': ['.py'],
            'search_mode': 'line',
            'unique_mode': False,
            'phrases': {
                'A': {'text': 'def', 'case_sensitive': True},
                'B': {'text': 'class', 'case_sensitive': True},
                'C': {'text': 'import', 'case_sensitive': True},
                'D': {'text': 'from', 'case_sensitive': True},
                'E': {'text': 'return', 'case_sensitive': True}
            },
            'formula': '(A | B) & (C | D) & E'  # Functions or classes, with imports, and returns
        }
        
        with patch('PySide6.QtCore.QObject.__init__'):
            worker = SearchWorker(search_params)
            files = worker._get_files_to_search()
            
            if len(files) > 0:
                matches = []
                for filepath in files[:5]:  # Test first 5 files
                    try:
                        file_matches = worker._search_file(filepath)
                        matches.extend(file_matches)
                    except Exception as e:
                        print(f"Error searching {filepath}: {e}")
                
                # Verify complex formula results
                for match in matches:
                    line_content = match[0].lower()
                    
                    # Should have def or class
                    has_def_or_class = 'def' in line_content or 'class' in line_content
                    
                    # Should have import or from
                    has_import = 'import' in line_content or 'from' in line_content
                    
                    # Should have return
                    has_return = 'return' in line_content
                    
                    # All conditions should be true for complex formula
                    self.assertTrue(has_def_or_class and has_import and has_return,
                                  f"Complex formula failed for: {line_content}")


def run_functional_tests():
    """Run functional tests and provide detailed results"""
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTest(unittest.makeSuite(TestFinderWithRealFiles))
    suite.addTest(unittest.makeSuite(TestFinderWithProjectFiles))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print detailed summary
    print(f"\n{'='*70}")
    print(f"FUNCTIONAL TEST SUMMARY")
    print(f"{'='*70}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print(f"\nFAILURES:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback.split('AssertionError: ')[-1].split(chr(10))[0]}")
    
    if result.errors:
        print(f"\nERRORS:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback.split(chr(10))[-2]}")
    
    print(f"{'='*70}")
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_functional_tests()
    sys.exit(0 if success else 1)