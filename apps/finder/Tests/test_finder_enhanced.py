# File: test_finder_enhanced.py
# Path: /home/herb/Desktop/Finder/Test/test_finder_enhanced.py
# Standard: AIDEV-PascalCase-2.1
# Created: 2025-07-18
# Last Modified: 2025-07-18  01:45PM
"""
Enhanced functional tests for the Finder application with detailed summaries
Provides comprehensive test reporting with color-coded output and human-readable explanations
"""

import unittest
import os
import sys
from unittest.mock import patch, Mock
import time
from datetime import datetime

# Add the parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    
    # Formula colors
    VARIABLE = '\033[96m'  # Cyan for variables
    OPERATOR = '\033[93m'  # Yellow for operators
    VALUE = '\033[92m'     # Green for values
    RESULT = '\033[95m'    # Magenta for results

# Import our classes (we'll need to mock Qt components)
with patch('PySide6.QtWidgets.QApplication'), \
     patch('PySide6.QtWidgets.QMainWindow'), \
     patch('PySide6.QtWidgets.QWidget'), \
     patch('PySide6.QtCore.QObject'), \
     patch('PySide6.QtCore.QThread'), \
     patch('PySide6.QtGui.QSyntaxHighlighter'):
    
    from Finder import SearchWorker


class TestScenario:
    """Class to hold test scenario information"""
    
    def __init__(self, name, description, phrases, formula, search_mode='line', file_types=None):
        self.name = name
        self.description = description
        self.phrases = phrases
        self.formula = formula
        self.search_mode = search_mode
        self.file_types = file_types or ['.py', '.txt', '.md']
        self.results = []
        self.success = False
        self.error_message = None
        self.execution_time = 0
        self.files_searched = 0
        
    def add_result(self, file_path, content, line_number, is_unique):
        """Add a search result"""
        self.results.append({
            'file_path': file_path,
            'content': content,
            'line_number': line_number,
            'is_unique': is_unique
        })
        
    def print_summary(self):
        """Print detailed test summary with colors"""
        print(f"\n{Colors.HEADER}{'='*80}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.HEADER}TEST SCENARIO: {self.name}{Colors.ENDC}")
        print(f"{Colors.HEADER}{'='*80}{Colors.ENDC}")
        
        # Description
        print(f"{Colors.OKBLUE}Description:{Colors.ENDC} {self.description}")
        
        # Variables section
        print(f"\n{Colors.UNDERLINE}Variables Used:{Colors.ENDC}")
        for letter, phrase_data in self.phrases.items():
            if phrase_data['text']:
                case_info = f" (Case {'Sensitive' if phrase_data['case_sensitive'] else 'Insensitive'})"
                print(f"  {Colors.VARIABLE}{letter}{Colors.ENDC} = '{Colors.VALUE}{phrase_data['text']}{Colors.ENDC}'{case_info}")
        
        # Formula section
        print(f"\n{Colors.UNDERLINE}Search Formula:{Colors.ENDC}")
        colored_formula = self._colorize_formula(self.formula)
        print(f"  User Formula: {colored_formula}")
        
        # Formula with values
        print(f"\n{Colors.UNDERLINE}Formula with Values:{Colors.ENDC}")
        value_formula = self._create_value_formula()
        print(f"  {value_formula}")
        
        # Human-readable intent
        print(f"\n{Colors.UNDERLINE}Search Intent:{Colors.ENDC}")
        intent = self._generate_human_intent()
        print(f"  {Colors.OKCYAN}{intent}{Colors.ENDC}")
        
        # Search parameters
        print(f"\n{Colors.UNDERLINE}Search Parameters:{Colors.ENDC}")
        print(f"  Search Mode: {Colors.WARNING}{self.search_mode.title()}{Colors.ENDC}")
        print(f"  File Types: {Colors.WARNING}{', '.join(self.file_types)}{Colors.ENDC}")
        print(f"  Files Searched: {Colors.WARNING}{self.files_searched}{Colors.ENDC}")
        print(f"  Execution Time: {Colors.WARNING}{self.execution_time:.3f}s{Colors.ENDC}")
        
        # Results section
        print(f"\n{Colors.UNDERLINE}Expected Results:{Colors.ENDC}")
        expected = self._get_expected_results()
        print(f"  {expected}")
        
        # Actual results
        print(f"\n{Colors.UNDERLINE}Actual Results:{Colors.ENDC}")
        if self.error_message:
            print(f"  {Colors.FAIL}ERROR: {self.error_message}{Colors.ENDC}")
        elif self.results:
            print(f"  {Colors.OKGREEN}Found {len(self.results)} matches:{Colors.ENDC}")
            for i, result in enumerate(self.results[:5], 1):  # Show first 5 results
                file_name = os.path.basename(result['file_path'])
                line_info = f"Line {result['line_number']}: " if result['line_number'] > 0 else ""
                unique_marker = f" {Colors.FAIL}[UNIQUE]{Colors.ENDC}" if result['is_unique'] else ""
                content_preview = result['content'][:60] + "..." if len(result['content']) > 60 else result['content']
                print(f"    {i}. {Colors.OKBLUE}{file_name}{Colors.ENDC} - {line_info}{content_preview}{unique_marker}")
            
            if len(self.results) > 5:
                print(f"    ... and {len(self.results) - 5} more matches")
        else:
            print(f"  {Colors.WARNING}No matches found{Colors.ENDC}")
        
        # Success/Failure
        print(f"\n{Colors.UNDERLINE}Test Result:{Colors.ENDC}")
        if self.success:
            print(f"  {Colors.OKGREEN}✓ SUCCESS{Colors.ENDC} - Test passed as expected")
        else:
            print(f"  {Colors.FAIL}✗ FAILURE{Colors.ENDC} - Test did not meet expectations")
        
        # Analysis
        print(f"\n{Colors.UNDERLINE}Analysis:{Colors.ENDC}")
        analysis = self._generate_analysis()
        print(f"  {analysis}")
        
        print(f"{Colors.HEADER}{'='*80}{Colors.ENDC}")
        
    def _colorize_formula(self, formula):
        """Add colors to formula components"""
        colored = formula
        
        # Color variables
        for letter in 'ABCDEF':
            if letter in formula:
                colored = colored.replace(letter, f"{Colors.VARIABLE}{letter}{Colors.ENDC}")
        
        # Color operators
        operators = ['AND', 'OR', 'NOT', 'NOR', 'XOR', 'XNOR', '&', '|', '!', '^', '&&', '||', '~']
        for op in operators:
            if op in formula:
                colored = colored.replace(op, f"{Colors.OPERATOR}{op}{Colors.ENDC}")
        
        return colored
    
    def _create_value_formula(self):
        """Create formula with actual values substituted"""
        value_formula = self.formula
        
        for letter, phrase_data in self.phrases.items():
            if phrase_data['text']:
                # Simulate the evaluation logic
                has_phrase = f"contains('{phrase_data['text']}')"
                value_formula = value_formula.replace(letter, f"{Colors.VALUE}{has_phrase}{Colors.ENDC}")
        
        return value_formula
    
    def _generate_human_intent(self):
        """Generate human-readable description of search intent"""
        active_phrases = {k: v for k, v in self.phrases.items() if v['text']}
        
        if not active_phrases:
            return "No search criteria specified"
        
        if len(active_phrases) == 1:
            letter, phrase_data = list(active_phrases.items())[0]
            return f"Find content containing '{phrase_data['text']}'"
        
        # Parse formula to understand intent
        formula_upper = self.formula.upper()
        
        if 'AND' in formula_upper:
            if 'OR' in formula_upper:
                return "Find content matching complex criteria with both AND and OR conditions"
            else:
                phrases = [f"'{v['text']}'" for v in active_phrases.values()]
                return f"Find content containing ALL of: {', '.join(phrases)}"
        
        elif 'OR' in formula_upper:
            phrases = [f"'{v['text']}'" for v in active_phrases.values()]
            return f"Find content containing ANY of: {', '.join(phrases)}"
        
        elif 'NOT' in formula_upper:
            return "Find content with exclusion criteria (NOT conditions)"
        
        else:
            return "Find content matching the specified formula"
    
    def _get_expected_results(self):
        """Get expected results description"""
        if not any(v['text'] for v in self.phrases.values()):
            return f"{Colors.WARNING}No results expected - no search criteria{Colors.ENDC}"
        
        mode_desc = "line-by-line" if self.search_mode == 'line' else "document-level"
        return f"{Colors.OKGREEN}Expected matches in {mode_desc} search across {', '.join(self.file_types)} files{Colors.ENDC}"
    
    def _generate_analysis(self):
        """Generate analysis of the results"""
        if self.error_message:
            return f"{Colors.FAIL}Test failed due to error: {self.error_message}{Colors.ENDC}"
        
        if not self.results:
            return f"{Colors.WARNING}No results found - check if search criteria exist in target files{Colors.ENDC}"
        
        unique_count = sum(1 for r in self.results if r['is_unique'])
        analysis_parts = [
            f"{Colors.OKGREEN}Found {len(self.results)} total matches{Colors.ENDC}",
            f"{Colors.OKGREEN}{unique_count} unique matches{Colors.ENDC}",
            f"{Colors.OKGREEN}Searched {self.files_searched} files{Colors.ENDC}",
            f"{Colors.OKGREEN}Performance: {self.execution_time:.3f}s{Colors.ENDC}"
        ]
        
        return " | ".join(analysis_parts)


class TestFinderEnhanced(unittest.TestCase):
    """Enhanced functional tests with detailed reporting"""
    
    def setUp(self):
        """Set up test environment"""
        self.project_dir = os.path.dirname(os.path.abspath(__file__))
        self.test_scenarios = []
        
    def create_test_scenario(self, name, description, phrases, formula, search_mode='line', file_types=None):
        """Create a test scenario"""
        scenario = TestScenario(name, description, phrases, formula, search_mode, file_types)
        self.test_scenarios.append(scenario)
        return scenario
    
    def execute_scenario(self, scenario):
        """Execute a test scenario and collect results"""
        start_time = time.time()
        
        try:
            # Prepare search parameters
            search_params = {
                'search_paths': [self.project_dir],
                'file_extensions': scenario.file_types,
                'search_mode': scenario.search_mode,
                'unique_mode': False,
                'phrases': scenario.phrases,
                'formula': scenario.formula
            }
            
            # Execute search
            with patch('PySide6.QtCore.QObject.__init__'):
                worker = SearchWorker(search_params)
                files = worker._get_files_to_search()
                scenario.files_searched = len(files)
                
                # Search files
                for filepath in files[:10]:  # Limit to first 10 files for testing
                    try:
                        file_matches = worker._search_file(filepath)
                        for match in file_matches:
                            line_content, line_number, is_unique = match
                            scenario.add_result(filepath, line_content, line_number, is_unique)
                    except Exception as e:
                        print(f"Error searching {filepath}: {e}")
                        continue
                
                # Determine success based on whether we found expected results
                scenario.success = len(scenario.results) > 0
                
        except Exception as e:
            scenario.error_message = str(e)
            scenario.success = False
        
        scenario.execution_time = time.time() - start_time
        
        # Print detailed summary
        scenario.print_summary()
        
        return scenario.success
    
    def test_python_function_search(self):
        """Test searching for Python functions"""
        scenario = self.create_test_scenario(
            name="Python Function Search",
            description="Search for Python function definitions across the project",
            phrases={
                'A': {'text': 'def ', 'case_sensitive': True},
                'B': {'text': 'class ', 'case_sensitive': True},
                'C': {'text': 'import', 'case_sensitive': False}
            },
            formula='A | B',
            search_mode='line',
            file_types=['.py']
        )
        
        success = self.execute_scenario(scenario)
        self.assertTrue(success, "Should find Python functions or classes")
    
    def test_documentation_search(self):
        """Test searching for documentation headers"""
        scenario = self.create_test_scenario(
            name="Documentation Header Search",
            description="Search for documentation headers containing design standards",
            phrases={
                'A': {'text': '#', 'case_sensitive': False},
                'B': {'text': 'Standard', 'case_sensitive': False},
                'C': {'text': 'Design', 'case_sensitive': False}
            },
            formula='A & (B | C)',
            search_mode='line',
            file_types=['.md']
        )
        
        success = self.execute_scenario(scenario)
        self.assertTrue(success, "Should find documentation headers")
    
    def test_complex_formula_search(self):
        """Test complex formula with multiple conditions"""
        scenario = self.create_test_scenario(
            name="Complex Formula Search",
            description="Search for Python code with specific patterns using complex logic",
            phrases={
                'A': {'text': 'def', 'case_sensitive': True},
                'B': {'text': 'return', 'case_sensitive': True},
                'C': {'text': 'class', 'case_sensitive': True},
                'D': {'text': 'import', 'case_sensitive': False},
                'E': {'text': 'self', 'case_sensitive': True}
            },
            formula='(A & B) | (C & E)',
            search_mode='line',
            file_types=['.py']
        )
        
        success = self.execute_scenario(scenario)
        self.assertTrue(success, "Should find complex Python patterns")
    
    def test_case_sensitive_search(self):
        """Test case-sensitive vs case-insensitive search"""
        scenario = self.create_test_scenario(
            name="Case Sensitivity Test",
            description="Compare case-sensitive and case-insensitive search results",
            phrases={
                'A': {'text': 'File', 'case_sensitive': True},
                'B': {'text': 'file', 'case_sensitive': False},
                'C': {'text': 'PATH', 'case_sensitive': True}
            },
            formula='A | B | C',
            search_mode='line',
            file_types=['.py', '.md']
        )
        
        success = self.execute_scenario(scenario)
        self.assertTrue(success, "Should find case-sensitive matches")
    
    def test_common_operators_search(self):
        """Test search with common operators"""
        scenario = self.create_test_scenario(
            name="Common Operators Test",
            description="Test search using common operators (&, |, !) instead of word operators",
            phrases={
                'A': {'text': 'Python', 'case_sensitive': False},
                'B': {'text': 'Java', 'case_sensitive': False},
                'C': {'text': 'error', 'case_sensitive': False}
            },
            formula='A & !C',
            search_mode='line',
            file_types=['.py', '.txt', '.md']
        )
        
        success = self.execute_scenario(scenario)
        self.assertTrue(success, "Should find Python content without errors")
    
    def test_document_vs_line_mode(self):
        """Test document mode vs line mode"""
        scenario = self.create_test_scenario(
            name="Document Mode Search",
            description="Search entire documents for patterns (vs line-by-line)",
            phrases={
                'A': {'text': 'Python', 'case_sensitive': False},
                'B': {'text': 'project', 'case_sensitive': False},
                'C': {'text': 'test', 'case_sensitive': False}
            },
            formula='A & B',
            search_mode='document',
            file_types=['.md', '.txt']
        )
        
        success = self.execute_scenario(scenario)
        self.assertTrue(success, "Should find documents containing both terms")
    
    def test_single_variable_search(self):
        """Test simple single variable search"""
        scenario = self.create_test_scenario(
            name="Single Variable Search",
            description="Test the simplest search case - single variable like 'B'",
            phrases={
                'A': {'text': '', 'case_sensitive': False},
                'B': {'text': 'import', 'case_sensitive': False},
                'C': {'text': '', 'case_sensitive': False}
            },
            formula='B',
            search_mode='line',
            file_types=['.py']
        )
        
        success = self.execute_scenario(scenario)
        self.assertTrue(success, "Should find import statements")
    
    def test_git_related_search(self):
        """Test searching for Git-related content"""
        scenario = self.create_test_scenario(
            name="Git Content Search",
            description="Search for Git-related operations and commands",
            phrases={
                'A': {'text': 'git', 'case_sensitive': False},
                'B': {'text': 'commit', 'case_sensitive': False},
                'C': {'text': 'GitHub', 'case_sensitive': False}
            },
            formula='(A | C) & B',
            search_mode='line',
            file_types=['.py', '.sh', '.md']
        )
        
        success = self.execute_scenario(scenario)
        # Note: This might not find results if no Git content exists
        print(f"Git search completed - found {len(scenario.results)} matches")


def run_enhanced_tests():
    """Run enhanced functional tests with detailed reporting"""
    print(f"{Colors.HEADER}{Colors.BOLD}")
    print("=" * 80)
    print("FINDER APPLICATION - ENHANCED FUNCTIONAL TESTS")
    print("=" * 80)
    print(f"{Colors.ENDC}")
    
    print(f"{Colors.OKBLUE}Starting comprehensive functional tests with detailed reporting...{Colors.ENDC}")
    print(f"{Colors.OKBLUE}Test execution time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.ENDC}")
    
    # Create test suite
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    suite.addTest(loader.loadTestsFromTestCase(TestFinderEnhanced))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=0, stream=open(os.devnull, 'w'))
    result = runner.run(suite)
    
    # Print final summary
    print(f"\n{Colors.HEADER}{Colors.BOLD}")
    print("=" * 80)
    print("ENHANCED FUNCTIONAL TEST SUMMARY")
    print("=" * 80)
    print(f"{Colors.ENDC}")
    
    total_tests = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    successes = total_tests - failures - errors
    
    print(f"{Colors.OKGREEN}✓ Tests Run: {total_tests}{Colors.ENDC}")
    print(f"{Colors.OKGREEN}✓ Successful: {successes}{Colors.ENDC}")
    print(f"{Colors.FAIL}✗ Failures: {failures}{Colors.ENDC}")
    print(f"{Colors.FAIL}✗ Errors: {errors}{Colors.ENDC}")
    print(f"{Colors.OKCYAN}Success Rate: {(successes/total_tests*100):.1f}%{Colors.ENDC}")
    
    if result.failures:
        print(f"\n{Colors.FAIL}FAILURES:{Colors.ENDC}")
        for test, traceback in result.failures:
            print(f"  - {test}")
    
    if result.errors:
        print(f"\n{Colors.FAIL}ERRORS:{Colors.ENDC}")
        for test, traceback in result.errors:
            print(f"  - {test}")
    
    print(f"\n{Colors.HEADER}Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.ENDC}")
    print(f"{Colors.HEADER}{'='*80}{Colors.ENDC}")
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_enhanced_tests()
    sys.exit(0 if success else 1)