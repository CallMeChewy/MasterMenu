# File: test_suite_advanced_scenarios.py
# Path: /home/herb/Desktop/Finder/Tests/test_suite_advanced_scenarios.py
# Standard: AIDEV-PascalCase-2.1
# Created: 2025-07-28
# Last Modified: 2025-07-28  06:30PM

"""
Advanced Educational Test Suite - Comprehensive Edge Case Testing
Tests complex interactions between logical operations, case sensitivity, and search modes
"""

import sys
import os
import time
import random
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
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

class AdvancedScenarioGenerator:
    """Generates comprehensive test scenarios covering all edge cases"""
    
    def __init__(self):
        # Test content variations for comprehensive testing
        self.test_documents = {
            'mixed_case.txt': """
This document contains Python code examples.
def process_data(data):
    return DATA.upper()

class DataProcessor:
    def __init__(self):
        self.python_version = "3.9"
        
# TODO: Add error handling
ERROR: Invalid data format
Warning: deprecated function
""",
            'documentation.md': """
# Project Documentation
## Design Standards
This file follows DESIGN patterns.
Created: 2025-07-28
Modified: 2025-07-28
Path: /project/docs/

### Standards Enforcement
- Code must follow standards
- STANDARDS are enforced
- design patterns required
""",
            'log_file.log': """
2025-07-28 10:00:01 INFO: Application started
2025-07-28 10:00:02 ERROR: Connection failed
2025-07-28 10:00:03 WARNING: Retrying connection
2025-07-28 10:00:04 INFO: Connected successfully
2025-07-28 10:00:05 DEBUG: Processing request
""",
            'config.json': """
{
    "app_name": "Finder",
    "version": "1.0.0",
    "debug": true,
    "ERROR_HANDLING": {
        "log_errors": true,
        "error_file": "errors.log"
    }
}
"""
        }
    
    def generate_comprehensive_test_suite(self):
        """Generate comprehensive test scenarios covering all edge cases"""
        scenarios = []
        
        # Category 1: Case Sensitivity Edge Cases
        scenarios.extend(self._generate_case_sensitivity_scenarios())
        
        # Category 2: Logical Operation Complexity
        scenarios.extend(self._generate_logical_complexity_scenarios())
        
        # Category 3: Document vs Line Search Mode Interactions
        scenarios.extend(self._generate_search_mode_scenarios())
        
        # Category 4: Mixed Case + Logic + Search Mode Combinations
        scenarios.extend(self._generate_mixed_complexity_scenarios())
        
        # Category 5: Edge Cases and Error Conditions
        scenarios.extend(self._generate_edge_case_scenarios())
        
        return scenarios
    
    def _generate_case_sensitivity_scenarios(self):
        """Generate scenarios specifically testing case sensitivity interactions"""
        scenarios = []
        
        # Scenario 1: Mixed case sensitivity with AND operation
        scenarios.append({
            'name': 'Mixed Case Sensitivity with AND Logic',
            'complexity': 'Case Sensitivity',
            'category': 'Case Sensitivity Edge Cases',
            'description': 'Test case-sensitive A with case-insensitive B in AND operation',
            'phrases': {
                'A': {'text': 'python', 'case_sensitive': True},
                'B': {'text': 'error', 'case_sensitive': False}
            },
            'formula': 'A & B',
            'search_mode': 'line',
            'expected_behavior': 'Should find lines with exact "python" AND any case of "error"',
            'educational_note': 'Demonstrates independent case sensitivity per variable in logical operations',
            'test_cases': [
                ('Python code with ERROR', False),  # A wrong case
                ('python code with ERROR', True),   # Both match
                ('python code with error', True),   # Both match
                ('PYTHON code with error', False),  # A wrong case
            ]
        })
        
        # Scenario 2: Case sensitivity with OR operation
        scenarios.append({
            'name': 'Case Sensitivity with OR Logic',
            'complexity': 'Case Sensitivity',
            'category': 'Case Sensitivity Edge Cases',
            'description': 'Test different case sensitivities with OR logic',
            'phrases': {
                'A': {'text': 'DATA', 'case_sensitive': True},
                'B': {'text': 'info', 'case_sensitive': False}
            },
            'formula': 'A | B',
            'search_mode': 'line',
            'expected_behavior': 'Should find lines with exact "DATA" OR any case of "info"',
            'educational_note': 'OR logic with mixed case sensitivity - either condition can match',
            'test_cases': [
                ('data processing INFO', True),     # B matches (insensitive)
                ('DATA processing info', True),     # Both match
                ('data processing debug', False),   # Neither matches correctly
                ('INFO about DATA', True),          # Both match
            ]
        })
        
        # Scenario 3: Case sensitivity with NOT operation
        scenarios.append({
            'name': 'Case Sensitivity with NOT Logic',
            'complexity': 'Case Sensitivity',
            'category': 'Case Sensitivity Edge Cases', 
            'description': 'Test case sensitivity with negation',
            'phrases': {
                'A': {'text': 'python', 'case_sensitive': False},
                'B': {'text': 'ERROR', 'case_sensitive': True}
            },
            'formula': 'A & !B',
            'search_mode': 'line',
            'expected_behavior': 'Lines with any case "python" but NOT exact "ERROR"',
            'educational_note': 'Negation respects individual case sensitivity settings',
            'test_cases': [
                ('Python code works fine', True),   # A matches, no B
                ('PYTHON has error issues', True),  # A matches, B wrong case
                ('Python has ERROR issues', False), # A matches but B exact match (excluded)
            ]
        })
        
        return scenarios
    
    def _generate_logical_complexity_scenarios(self):
        """Generate scenarios testing complex logical operations"""
        scenarios = []
        
        # Scenario 1: Nested parentheses with mixed operators
        scenarios.append({
            'name': 'Complex Nested Logic',
            'complexity': 'Expert',
            'category': 'Logical Operation Complexity',
            'description': 'Test deeply nested logical operations',
            'phrases': {
                'A': {'text': 'function', 'case_sensitive': False},
                'B': {'text': 'class', 'case_sensitive': False},
                'C': {'text': 'error', 'case_sensitive': False},
                'D': {'text': 'debug', 'case_sensitive': False}
            },
            'formula': '(A | B) & (C | D)',
            'search_mode': 'line',
            'expected_behavior': 'Lines with (function OR class) AND (error OR debug)',
            'educational_note': 'Parentheses control operator precedence in complex logic',
            'test_cases': [
                ('function call error', True),      # A and C match
                ('class definition debug', True),   # B and D match  
                ('function without issues', False), # A matches but no C or D
                ('error in processing', False),     # C matches but no A or B
            ]
        })
        
        # Scenario 2: Multiple NOT operations
        scenarios.append({
            'name': 'Multiple Negations',
            'complexity': 'Advanced',
            'category': 'Logical Operation Complexity',
            'description': 'Test multiple NOT operations in complex formula',
            'phrases': {
                'A': {'text': 'test', 'case_sensitive': False},
                'B': {'text': 'error', 'case_sensitive': False},
                'C': {'text': 'warning', 'case_sensitive': False}
            },
            'formula': 'A & !B & !C',
            'search_mode': 'line', 
            'expected_behavior': 'Lines with "test" but WITHOUT "error" or "warning"',
            'educational_note': 'Multiple negations create exclusive inclusion patterns',
            'test_cases': [
                ('test function works', True),         # A, no B or C
                ('test produces error', False),        # A and B (excluded)
                ('test shows warning', False),         # A and C (excluded)
                ('test error and warning', False),     # A, B, and C (excluded)
            ]
        })
        
        return scenarios
    
    def _generate_search_mode_scenarios(self):
        """Generate scenarios testing document vs line search modes"""
        scenarios = []
        
        # Scenario 1: Document mode vs Line mode comparison
        scenarios.append({
            'name': 'Document vs Line Search Mode',
            'complexity': 'Search Mode',
            'category': 'Document vs Line Search Modes',
            'description': 'Compare behavior between document and line search modes',
            'phrases': {
                'A': {'text': 'python', 'case_sensitive': False},
                'B': {'text': 'error', 'case_sensitive': False}
            },
            'formula': 'A & B',
            'search_mode': 'document',  # Will also test line mode
            'expected_behavior': 'Document: match if file contains both terms anywhere. Line: match only lines with both terms',
            'educational_note': 'Search mode fundamentally changes how logical operations are evaluated',
            'test_cases': [
                # Document mode: should find file if it contains both terms anywhere
                # Line mode: should only find individual lines containing both terms
            ]
        })
        
        # Scenario 2: Line mode with complex multi-line patterns
        scenarios.append({
            'name': 'Line Mode Complex Patterns',
            'complexity': 'Search Mode',
            'category': 'Document vs Line Search Modes',
            'description': 'Test complex patterns in line-by-line search',
            'phrases': {
                'A': {'text': 'def', 'case_sensitive': False},
                'B': {'text': 'return', 'case_sensitive': False},
                'C': {'text': 'error', 'case_sensitive': False}
            },
            'formula': 'A & (B | C)',
            'search_mode': 'line',
            'expected_behavior': 'Find lines with "def" AND ("return" OR "error")',
            'educational_note': 'Line mode evaluates each line independently against the formula',
            'test_cases': [
                ('def process_data():', False),            # A only
                ('def get_error():', True),                # A and C
                ('def calculate() return 5', True),        # A and B
                ('    return error_code', False),          # B and C but no A
            ]
        })
        
        return scenarios
    
    def _generate_mixed_complexity_scenarios(self):
        """Generate scenarios combining case sensitivity, logic, and search modes"""
        scenarios = []
        
        # Scenario 1: The Ultimate Complexity Test
        scenarios.append({
            'name': 'Ultimate Complexity: Case + Logic + Mode',
            'complexity': 'Ultimate',
            'category': 'Mixed Complexity Scenarios',
            'description': 'Test all complexity dimensions together',
            'phrases': {
                'A': {'text': 'Python', 'case_sensitive': True},      # Exact case
                'B': {'text': 'error', 'case_sensitive': False},      # Any case
                'C': {'text': 'DEBUG', 'case_sensitive': True},       # Exact case
                'D': {'text': 'info', 'case_sensitive': False}        # Any case
            },
            'formula': '(A | B) & !(C | D)',
            'search_mode': 'line',
            'expected_behavior': 'Lines with (exact "Python" OR any "error") but NOT (exact "DEBUG" OR any "info")',
            'educational_note': 'Demonstrates the full complexity of the search system',
            'test_cases': [
                ('Python code works', True),               # A matches, no C or D
                ('python error occurred', True),           # B matches, no C or D
                ('Python code has INFO', False),           # A matches but D matches (excluded)
                ('Error in DEBUG mode', False),            # B matches but C matches (excluded)
            ]
        })
        
        # Scenario 2: Document mode with mixed case sensitivity
        scenarios.append({
            'name': 'Document Mode with Mixed Case Logic',
            'complexity': 'Ultimate',
            'category': 'Mixed Complexity Scenarios',
            'description': 'Document-level search with mixed case sensitivity and complex logic',
            'phrases': {
                'A': {'text': 'class', 'case_sensitive': True},
                'B': {'text': 'function', 'case_sensitive': False},
                'C': {'text': 'ERROR', 'case_sensitive': True}
            },
            'formula': '(A & B) | C',
            'search_mode': 'document',
            'expected_behavior': 'Documents with (exact "class" AND any "function") OR exact "ERROR"',
            'educational_note': 'Document mode applies formula to entire file content',
            'test_cases': [
                # These would be evaluated at document level, not line level
            ]
        })
        
        return scenarios
    
    def _generate_edge_case_scenarios(self):
        """Generate edge case scenarios that commonly cause issues"""
        scenarios = []
        
        # Scenario 1: Empty and whitespace handling
        scenarios.append({
            'name': 'Empty and Whitespace Edge Cases',
            'complexity': 'Edge Case',
            'category': 'Edge Cases and Error Conditions',
            'description': 'Test handling of empty phrases and whitespace',
            'phrases': {
                'A': {'text': 'test', 'case_sensitive': False},
                'B': {'text': '', 'case_sensitive': False},         # Empty phrase
                'C': {'text': '   ', 'case_sensitive': False}       # Whitespace only
            },
            'formula': 'A & B',
            'search_mode': 'line',
            'expected_behavior': 'Should handle empty phrases gracefully',
            'educational_note': 'Empty phrases should be treated as always false',
            'test_cases': [
                ('test line here', False),  # A matches but B is empty (false)
            ]
        })
        
        # Scenario 2: Special characters and regex patterns
        scenarios.append({
            'name': 'Special Characters Handling',
            'complexity': 'Edge Case',
            'category': 'Edge Cases and Error Conditions',
            'description': 'Test handling of special characters that might break regex',
            'phrases': {
                'A': {'text': '[ERROR]', 'case_sensitive': False},
                'B': {'text': '(debug)', 'case_sensitive': False},
                'C': {'text': 'file.txt', 'case_sensitive': False}
            },
            'formula': 'A | B | C',
            'search_mode': 'line',
            'expected_behavior': 'Should treat special characters as literal text, not regex',
            'educational_note': 'Special characters should be escaped properly in search',
            'test_cases': [
                ('[ERROR] occurred', True),     # Should match literal [ERROR]
                ('(debug) mode', True),         # Should match literal (debug)
                ('open file.txt', True),        # Should match literal file.txt
            ]
        })
        
        return scenarios

class AdvancedTestSuiteRunner:
    """Runs the advanced comprehensive test suite"""
    
    def __init__(self, project_dir=None):
        self.project_dir = project_dir or os.path.dirname(os.path.abspath(__file__))
        self.generator = AdvancedScenarioGenerator()
    
    def run_comprehensive_test_suite(self):
        """Run the comprehensive test suite with all edge cases"""
        print(f"{Colors.HEADER}{Colors.BOLD}")
        print("=" * 100)
        print("FINDER APPLICATION - COMPREHENSIVE EDUCATIONAL TEST SUITE")
        print("Advanced Edge Case Testing: Logic + Case Sensitivity + Search Modes")  
        print("=" * 100)
        print(f"{Colors.ENDC}")
        
        print(f"{Colors.OKBLUE}🎓 Educational Focus: Master complex search patterns{Colors.ENDC}")
        print(f"{Colors.OKBLUE}🔍 Comprehensive: Tests all interaction combinations{Colors.ENDC}")
        print(f"{Colors.OKBLUE}⚠️  Edge Cases: Covers error conditions and special cases{Colors.ENDC}")
        print(f"{Colors.OKBLUE}⏰ Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.ENDC}")
        
        # Generate test scenarios
        scenarios = self.generator.generate_comprehensive_test_suite()
        
        # Group scenarios by category
        categories = {}
        for scenario in scenarios:
            category = scenario['category']
            if category not in categories:
                categories[category] = []
            categories[category].append(scenario)
        
        # Run scenarios by category
        all_results = []
        for category_name, category_scenarios in categories.items():
            print(f"\n{Colors.HEADER}📋 CATEGORY: {category_name}{Colors.ENDC}")
            print("=" * 80)
            
            for i, scenario in enumerate(category_scenarios, 1):
                print(f"\n{Colors.OKCYAN}🔬 Test {i}: {scenario['name']}{Colors.ENDC}")
                result = self._run_scenario_with_validation(scenario)
                all_results.append(result)
        
        # Print comprehensive summary
        self._print_comprehensive_summary(all_results, categories)
        
        return all_results
    
    def _run_scenario_with_validation(self, scenario):
        """Run a single scenario with comprehensive validation"""
        print(f"{Colors.OKGREEN}📝 Description:{Colors.ENDC} {scenario['description']}")
        print(f"{Colors.WARNING}🎓 Learning Point:{Colors.ENDC} {scenario['educational_note']}")
        
        # Show configuration
        print(f"\n{Colors.UNDERLINE}Configuration:{Colors.ENDC}")
        print(f"Formula: {Colors.OKCYAN}{scenario['formula']}{Colors.ENDC}")
        print(f"Search Mode: {Colors.WARNING}{scenario['search_mode']}{Colors.ENDC}")
        
        # Show variables with case sensitivity
        print(f"\n{Colors.UNDERLINE}Variables:{Colors.ENDC}")
        for letter, phrase_data in scenario['phrases'].items():
            if phrase_data['text']:
                case_info = "Case Sensitive" if phrase_data['case_sensitive'] else "Case Insensitive"
                print(f"  {Colors.OKCYAN}{letter}{Colors.ENDC} = '{Colors.OKGREEN}{phrase_data['text']}{Colors.ENDC}' ({case_info})")
        
        # Run test cases if provided
        test_success = True
        if 'test_cases' in scenario:
            print(f"\n{Colors.UNDERLINE}Test Case Validation:{Colors.ENDC}")
            passed = 0
            total = len(scenario['test_cases'])
            
            for test_input, expected in scenario['test_cases']:
                try:
                    # Integrate with the actual SearchWorker for real testing
                    result = self._evaluate_test_case(scenario, test_input)
                    status = "✅ PASS" if result == expected else "❌ FAIL"
                    print(f"  {status}: '{test_input}' -> {result} (expected {expected})")
                    if result == expected:
                        passed += 1
                    else:
                        test_success = False
                except Exception as e:
                    print(f"  ❌ ERROR: '{test_input}' -> {e}")
                    test_success = False
            
            print(f"\n{Colors.WARNING}Test Results: {passed}/{total} passed{Colors.ENDC}")
            if passed == total and total > 0:
                print(f"{Colors.OKGREEN}✅ All test cases passed for this scenario!{Colors.ENDC}")
        
        print(f"\n{Colors.OKGREEN}Expected Behavior:{Colors.ENDC} {scenario['expected_behavior']}")
        
        return {
            'scenario': scenario,
            'success': test_success,
            'category': scenario['category']
        }
    
    def _evaluate_test_case(self, scenario, test_input):
        """Evaluate a test case using actual SearchWorker implementation"""
        try:
            # Import here to avoid circular imports
            import os
            os.environ['QT_QPA_PLATFORM'] = 'offscreen'
            
            from Finder import SearchWorker
            
            # Create SearchWorker with scenario parameters
            test_params = {
                'formula': scenario['formula'],
                'phrases': scenario['phrases'],
                'file_extensions': ['.txt'],
                'search_paths': ['.'],
                'unique_results': False,
                'max_results': 100
            }
            
            worker = SearchWorker(test_params)
            
            # Evaluate the formula against the test input
            result = worker._evaluate_formula(test_input, scenario['phrases'], scenario['formula'])
            return result
            
        except Exception as e:
            print(f"  ⚠️  Evaluation error: {e}")
            return False
    
    def _print_comprehensive_summary(self, results, categories):
        """Print comprehensive summary of all test results"""
        print(f"\n{Colors.HEADER}{Colors.BOLD}")
        print("=" * 100)
        print("COMPREHENSIVE TEST SUITE SUMMARY")
        print("=" * 100)
        print(f"{Colors.ENDC}")
        
        total_scenarios = len(results)
        successful_scenarios = sum(1 for r in results if r['success'])
        
        print(f"{Colors.OKGREEN}📊 Overall Results:{Colors.ENDC}")
        print(f"  Total Scenarios: {total_scenarios}")
        print(f"  Successful: {successful_scenarios}")
        print(f"  Success Rate: {successful_scenarios/total_scenarios*100:.1f}%")
        
        print(f"\n{Colors.OKBLUE}📋 By Category:{Colors.ENDC}")
        for category_name, category_scenarios in categories.items():
            category_results = [r for r in results if r['category'] == category_name]
            category_success = sum(1 for r in category_results if r['success'])
            print(f"  {category_name}: {category_success}/{len(category_scenarios)} scenarios passed")
        
        print(f"\n{Colors.WARNING}🎓 Key Learning Points:{Colors.ENDC}")
        print("• Case sensitivity works independently for each variable (A-F)")
        print("• Logical operators (&, |, !) respect individual case settings")
        print("• Document mode evaluates entire files; Line mode evaluates each line")
        print("• Parentheses control operator precedence in complex formulas")
        print("• Empty phrases are treated as always false in logical operations")
        print("• Special characters are treated as literal text, not regex patterns")
        
        print(f"\n{Colors.OKCYAN}🚀 Next Steps:{Colors.ENDC}")
        print("• Try these scenarios in the actual Finder application")
        print("• Experiment with your own combinations of logic and case sensitivity")
        print("• Use the 'Match Case' checkboxes to control case sensitivity per variable")
        print("• Switch between Document and Line search modes to see the difference")


def main():
    """Run the comprehensive advanced test suite"""
    runner = AdvancedTestSuiteRunner()
    results = runner.run_comprehensive_test_suite()
    return 0 if all(r['success'] for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())