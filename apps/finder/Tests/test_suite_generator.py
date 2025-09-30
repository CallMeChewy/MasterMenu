# File: test_suite_generator.py
# Path: /home/herb/Desktop/Finder/Test/test_suite_generator.py
# Standard: AIDEV-PascalCase-2.1
# Created: 2025-07-18
# Last Modified: 2025-07-18  01:45PM
"""
Dynamic test suite generator for Finder application
Creates 5 different formulas from simple to complex on each run
Provides educational examples for users
"""

import os
import sys
import time
import random
from datetime import datetime

# Add the parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

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


class FormulaGenerator:
    """Generates formulas of different complexity levels"""
    
    def __init__(self):
        # Common search terms for different contexts
        self.python_terms = ['def', 'class', 'import', 'from', 'return', 'self', 'print', 'if', 'for', 'while']
        self.doc_terms = ['#', 'Standard', 'Design', 'File', 'Path', 'Created', 'Modified', 'TODO', 'NOTE', 'IMPORTANT']
        self.git_terms = ['git', 'commit', 'branch', 'merge', 'pull', 'push', 'GitHub', 'repository', 'clone', 'checkout']
        self.common_terms = ['error', 'warning', 'info', 'debug', 'test', 'function', 'method', 'variable', 'parameter', 'value']
        
        # Operators with different complexity
        self.simple_ops = ['A', 'B', 'A AND B', 'A OR B', 'NOT A']
        self.medium_ops = ['A & B', 'A | B', '!A', 'A && B', 'A || B']
        self.complex_ops = ['(A AND B) OR C', 'A AND (B OR C)', '(A OR B) AND (C OR D)']
        self.advanced_ops = ['A & B & !C', 'A | (B & C)', '(A | B) & !(C | D)']
        self.expert_ops = ['((A | B) & C) | (D & !E)', '(A & B & C) | (D & E & F)', 'A & (B | C) & !(D | E)']
    
    def generate_test_suite(self):
        """Generate 5 test scenarios with increasing complexity"""
        scenarios = []
        
        # Level 1: Simple single variable
        scenarios.append(self._generate_simple_scenario())
        
        # Level 2: Basic two-variable formula
        scenarios.append(self._generate_basic_scenario())
        
        # Level 3: Medium complexity with 3 variables
        scenarios.append(self._generate_medium_scenario())
        
        # Level 4: Advanced with 4-5 variables
        scenarios.append(self._generate_advanced_scenario())
        
        # Level 5: Expert level with complex logic
        scenarios.append(self._generate_expert_scenario())
        
        return scenarios
    
    def _generate_simple_scenario(self):
        """Generate simple single-variable scenario"""
        contexts = [
            {
                'name': 'Simple Python Search',
                'description': 'Find Python import statements',
                'file_types': ['.py'],
                'terms': self.python_terms
            },
            {
                'name': 'Simple Documentation Search',
                'description': 'Find documentation headers',
                'file_types': ['.md'],
                'terms': self.doc_terms
            },
            {
                'name': 'Simple Text Search',
                'description': 'Find common programming terms',
                'file_types': ['.txt', '.md'],
                'terms': self.common_terms
            }
        ]
        
        context = random.choice(contexts)
        term = random.choice(context['terms'])
        
        return {
            'complexity': 1,
            'name': context['name'],
            'description': context['description'],
            'file_types': context['file_types'],
            'phrases': {
                'A': {'text': term, 'case_sensitive': random.choice([True, False])},
                'B': {'text': '', 'case_sensitive': False},
                'C': {'text': '', 'case_sensitive': False},
                'D': {'text': '', 'case_sensitive': False},
                'E': {'text': '', 'case_sensitive': False},
                'F': {'text': '', 'case_sensitive': False}
            },
            'formula': 'A',
            'educational_note': 'This is the simplest search - just find content containing a single term.'
        }
    
    def _generate_basic_scenario(self):
        """Generate basic two-variable scenario"""
        contexts = [
            {
                'name': 'Basic Python AND Search',
                'description': 'Find Python functions with returns',
                'file_types': ['.py'],
                'terms': [('def', 'return'), ('class', 'self'), ('import', 'from')]
            },
            {
                'name': 'Basic Documentation AND Search',
                'description': 'Find design standard headers',
                'file_types': ['.md'],
                'terms': [('#', 'Standard'), ('Design', 'File'), ('Path', 'Created')]
            },
            {
                'name': 'Basic OR Search',
                'description': 'Find either functions or classes',
                'file_types': ['.py'],
                'terms': [('def', 'class'), ('import', 'from'), ('if', 'for')]
            }
        ]
        
        context = random.choice(contexts)
        term_pair = random.choice(context['terms'])
        operator = random.choice(['AND', 'OR', '&', '|'])
        
        return {
            'complexity': 2,
            'name': context['name'],
            'description': context['description'],
            'file_types': context['file_types'],
            'phrases': {
                'A': {'text': term_pair[0], 'case_sensitive': random.choice([True, False])},
                'B': {'text': term_pair[1], 'case_sensitive': random.choice([True, False])},
                'C': {'text': '', 'case_sensitive': False},
                'D': {'text': '', 'case_sensitive': False},
                'E': {'text': '', 'case_sensitive': False},
                'F': {'text': '', 'case_sensitive': False}
            },
            'formula': f'A {operator} B',
            'educational_note': f'This searches for content with both terms (AND) or either term (OR).'
        }
    
    def _generate_medium_scenario(self):
        """Generate medium complexity scenario"""
        contexts = [
            {
                'name': 'Medium Python Logic',
                'description': 'Find Python code with specific patterns',
                'file_types': ['.py'],
                'terms': [('def', 'return', 'self'), ('class', 'init', 'self'), ('import', 'from', 'os')]
            },
            {
                'name': 'Medium Documentation Logic',
                'description': 'Find documentation with exclusions',
                'file_types': ['.md'],
                'terms': [('#', 'Standard', 'Design'), ('File', 'Path', 'Created'), ('TODO', 'NOTE', 'IMPORTANT')]
            },
            {
                'name': 'Medium Git Logic',
                'description': 'Find git operations with conditions',
                'file_types': ['.py', '.sh'],
                'terms': [('git', 'commit', 'branch'), ('merge', 'pull', 'push'), ('GitHub', 'repository', 'clone')]
            }
        ]
        
        context = random.choice(contexts)
        terms = random.choice(context['terms'])
        
        formulas = [
            'A & B & C',
            'A | B | C',
            '(A & B) | C',
            'A & (B | C)',
            'A & B & !C',
            'A | (B & C)'
        ]
        
        formula = random.choice(formulas)
        
        return {
            'complexity': 3,
            'name': context['name'],
            'description': context['description'],
            'file_types': context['file_types'],
            'phrases': {
                'A': {'text': terms[0], 'case_sensitive': random.choice([True, False])},
                'B': {'text': terms[1], 'case_sensitive': random.choice([True, False])},
                'C': {'text': terms[2], 'case_sensitive': random.choice([True, False])},
                'D': {'text': '', 'case_sensitive': False},
                'E': {'text': '', 'case_sensitive': False},
                'F': {'text': '', 'case_sensitive': False}
            },
            'formula': formula,
            'educational_note': 'This uses parentheses to group conditions and NOT (!) to exclude terms.'
        }
    
    def _generate_advanced_scenario(self):
        """Generate advanced complexity scenario"""
        contexts = [
            {
                'name': 'Advanced Python Analysis',
                'description': 'Complex Python code pattern matching',
                'file_types': ['.py'],
                'terms': [('def', 'class', 'return', 'self'), ('import', 'from', 'os', 'sys'), ('if', 'for', 'while', 'try')]
            },
            {
                'name': 'Advanced Documentation Analysis',
                'description': 'Complex documentation pattern matching',
                'file_types': ['.md'],
                'terms': [('#', 'Standard', 'Design', 'File'), ('Path', 'Created', 'Modified', 'TODO'), ('NOTE', 'IMPORTANT', 'WARNING', 'ERROR')]
            },
            {
                'name': 'Advanced Multi-Language Search',
                'description': 'Search across multiple file types',
                'file_types': ['.py', '.md', '.txt'],
                'terms': [('Python', 'Java', 'JavaScript', 'C++'), ('function', 'method', 'class', 'variable'), ('error', 'warning', 'info', 'debug')]
            }
        ]
        
        context = random.choice(contexts)
        terms = random.choice(context['terms'])
        
        formulas = [
            '(A & B) | (C & D)',
            '(A | B) & (C | D)',
            'A & B & (C | D)',
            '(A & B & C) | D',
            'A | (B & C & D)',
            '(A | B) & C & !D'
        ]
        
        formula = random.choice(formulas)
        
        return {
            'complexity': 4,
            'name': context['name'],
            'description': context['description'],
            'file_types': context['file_types'],
            'phrases': {
                'A': {'text': terms[0], 'case_sensitive': random.choice([True, False])},
                'B': {'text': terms[1], 'case_sensitive': random.choice([True, False])},
                'C': {'text': terms[2], 'case_sensitive': random.choice([True, False])},
                'D': {'text': terms[3], 'case_sensitive': random.choice([True, False])},
                'E': {'text': '', 'case_sensitive': False},
                'F': {'text': '', 'case_sensitive': False}
            },
            'formula': formula,
            'educational_note': 'This uses complex grouping with multiple AND/OR combinations.'
        }
    
    def _generate_expert_scenario(self):
        """Generate expert level complexity scenario"""
        contexts = [
            {
                'name': 'Expert Code Architecture Analysis',
                'description': 'Complex architectural pattern detection',
                'file_types': ['.py'],
                'terms': [('def', 'class', 'import', 'return', 'self', 'super'), ('async', 'await', 'yield', 'lambda', 'decorator', 'property')]
            },
            {
                'name': 'Expert Documentation Structure',
                'description': 'Complex documentation structure analysis',
                'file_types': ['.md'],
                'terms': [('#', '##', '###', 'Standard', 'Design', 'File'), ('Path', 'Created', 'Modified', 'TODO', 'FIXME', 'NOTE')]
            },
            {
                'name': 'Expert Multi-Context Search',
                'description': 'Complex cross-language pattern matching',
                'file_types': ['.py', '.md', '.txt', '.json'],
                'terms': [('Python', 'Java', 'JavaScript', 'function', 'method', 'class'), ('error', 'warning', 'exception', 'debug', 'info', 'trace')]
            }
        ]
        
        context = random.choice(contexts)
        terms = random.choice(context['terms'])
        
        formulas = [
            '((A | B) & C) | (D & E)',
            '(A & B & C) | (D & E & F)',
            'A & (B | C) & !(D | E)',
            '(A & B) | (C & D) | (E & F)',
            '((A | B) & (C | D)) & !E',
            'A & ((B & C) | (D & E)) & !F'
        ]
        
        formula = random.choice(formulas)
        
        return {
            'complexity': 5,
            'name': context['name'],
            'description': context['description'],
            'file_types': context['file_types'],
            'phrases': {
                'A': {'text': terms[0], 'case_sensitive': random.choice([True, False])},
                'B': {'text': terms[1], 'case_sensitive': random.choice([True, False])},
                'C': {'text': terms[2], 'case_sensitive': random.choice([True, False])},
                'D': {'text': terms[3], 'case_sensitive': random.choice([True, False])},
                'E': {'text': terms[4], 'case_sensitive': random.choice([True, False])},
                'F': {'text': terms[5], 'case_sensitive': random.choice([True, False])},
            },
            'formula': formula,
            'educational_note': 'This is expert-level with nested groups, multiple conditions, and exclusions.'
        }


class TestSuiteRunner:
    """Runs the dynamic test suite with detailed reporting"""
    
    def __init__(self, project_dir=None):
        self.project_dir = project_dir or os.path.dirname(os.path.abspath(__file__))
        self.generator = FormulaGenerator()
    
    def run_educational_test_suite(self):
        """Run the educational test suite"""
        print(f"{Colors.HEADER}{Colors.BOLD}")
        print("=" * 90)
        print("FINDER APPLICATION - EDUCATIONAL TEST SUITE")
        print("Dynamic Formula Examples - Simple to Complex")
        print("=" * 90)
        print(f"{Colors.ENDC}")
        
        print(f"{Colors.OKBLUE}🎓 Learning Mode: This test suite demonstrates different search patterns{Colors.ENDC}")
        print(f"{Colors.OKBLUE}🔄 Dynamic: Each run generates 5 different formulas with varying complexity{Colors.ENDC}")
        print(f"{Colors.OKBLUE}📚 Educational: Learn how to construct effective search formulas{Colors.ENDC}")
        print(f"{Colors.OKBLUE}⏰ Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.ENDC}")
        
        # Generate test scenarios
        scenarios = self.generator.generate_test_suite()
        
        # Run each scenario
        results = []
        for i, scenario in enumerate(scenarios, 1):
            print(f"\n{Colors.OKCYAN}📊 Running Scenario {i}/5: Complexity Level {scenario['complexity']}{Colors.ENDC}")
            
            start_time = time.time()
            matches, files_searched = self._execute_scenario(scenario)
            execution_time = time.time() - start_time
            
            result = {
                'scenario': scenario,
                'matches': matches,
                'files_searched': files_searched,
                'execution_time': execution_time,
                'success': len(matches) > 0
            }
            results.append(result)
            
            self._print_scenario_summary(scenario, matches, files_searched, execution_time)
        
        # Print overall summary
        self._print_overall_summary(results)
        
        return results
    
    def _execute_scenario(self, scenario):
        """Execute a single test scenario"""
        matches = []
        files_searched = 0
        
        for root, dirs, files in os.walk(self.project_dir):
            for filename in files:
                if any(filename.endswith(ext) for ext in scenario['file_types']):
                    filepath = os.path.join(root, filename)
                    files_searched += 1
                    
                    try:
                        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                            for line_num, line in enumerate(f, 1):
                                if self._evaluate_formula(line, scenario['phrases'], scenario['formula']):
                                    matches.append({
                                        'file_path': filepath,
                                        'content': line.strip(),
                                        'line_number': line_num,
                                        'is_unique': True
                                    })
                                    
                                    # Limit matches for performance
                                    if len(matches) >= 100:
                                        break
                        
                        if len(matches) >= 100:
                            break
                    except Exception as e:
                        continue
        
        return matches, files_searched
    
    def _evaluate_formula(self, content, phrases, formula):
        """Evaluate formula against content (simplified version)"""
        # Normalize operators
        normalized_formula = self._normalize_operators(formula)
        
        # Create phrase value mapping
        phrase_values = {}
        for letter, phrase_data in phrases.items():
            phrase_text = phrase_data.get('text', '')
            case_sensitive = phrase_data.get('case_sensitive', False)
            
            if phrase_text.strip():
                if case_sensitive:
                    phrase_values[letter] = phrase_text in content
                else:
                    phrase_values[letter] = phrase_text.lower() in content.lower()
            else:
                phrase_values[letter] = False
        
        # Replace variables with values
        eval_formula = normalized_formula.upper()
        for letter in 'ABCDEF':
            eval_formula = eval_formula.replace(letter, str(phrase_values.get(letter, False)))
        
        # Replace operators
        eval_formula = eval_formula.replace('AND', ' and ')
        eval_formula = eval_formula.replace('OR', ' or ')
        eval_formula = eval_formula.replace('NOT', ' not ')
        eval_formula = eval_formula.replace('XOR', ' != ')
        
        try:
            return eval(eval_formula)
        except:
            return False
    
    def _normalize_operators(self, formula):
        """Normalize operators for evaluation"""
        operator_map = [
            ('&&', ' AND '),
            ('||', ' OR '),
            ('&', ' AND '),
            ('|', ' OR '),
            ('!', ' NOT '),
            ('~', ' NOT '),
            ('^', ' XOR ')
        ]
        
        normalized = formula
        for symbol, replacement in operator_map:
            normalized = normalized.replace(symbol, replacement)
        
        return normalized
    
    def _print_scenario_summary(self, scenario, matches, files_searched, execution_time):
        """Print summary for a single scenario"""
        print(f"\n{Colors.HEADER}{'='*80}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.HEADER}LEVEL {scenario['complexity']}: {scenario['name']}{Colors.ENDC}")
        print(f"{Colors.HEADER}{'='*80}{Colors.ENDC}")
        
        # Description and educational note
        print(f"{Colors.OKBLUE}📝 Description:{Colors.ENDC} {scenario['description']}")
        print(f"{Colors.OKBLUE}🎓 Learning Point:{Colors.ENDC} {scenario['educational_note']}")
        
        # Variables used
        print(f"\n{Colors.UNDERLINE}Variables Used:{Colors.ENDC}")
        for letter, phrase_data in scenario['phrases'].items():
            if phrase_data['text']:
                case_info = f" ({'Case Sensitive' if phrase_data['case_sensitive'] else 'Case Insensitive'})"
                print(f"  {Colors.VARIABLE}{letter}{Colors.ENDC} = '{Colors.VALUE}{phrase_data['text']}{Colors.ENDC}'{case_info}")
        
        # Formula
        print(f"\n{Colors.UNDERLINE}Formula:{Colors.ENDC}")
        colored_formula = self._colorize_formula(scenario['formula'])
        print(f"  {colored_formula}")
        
        # Complexity explanation
        complexity_explanations = {
            1: "Simple single variable - just checking if a term exists",
            2: "Basic logic - combining two terms with AND or OR",
            3: "Medium complexity - using parentheses and NOT operators",
            4: "Advanced logic - multiple grouped conditions",
            5: "Expert level - complex nested logic with exclusions"
        }
        
        print(f"\n{Colors.UNDERLINE}Complexity Level {scenario['complexity']}:{Colors.ENDC}")
        print(f"  {Colors.OKCYAN}{complexity_explanations[scenario['complexity']]}{Colors.ENDC}")
        
        # Results
        print(f"\n{Colors.UNDERLINE}Results:{Colors.ENDC}")
        print(f"  Files Searched: {Colors.WARNING}{files_searched}{Colors.ENDC}")
        print(f"  Execution Time: {Colors.WARNING}{execution_time:.3f}s{Colors.ENDC}")
        
        if matches:
            print(f"  {Colors.OKGREEN}✓ Found {len(matches)} matches{Colors.ENDC}")
            
            # Show first few matches
            for i, match in enumerate(matches[:3], 1):
                file_name = os.path.basename(match['file_path'])
                content_preview = match['content'][:50] + "..." if len(match['content']) > 50 else match['content']
                print(f"    {i}. {Colors.OKBLUE}{file_name}:{match['line_number']}{Colors.ENDC} - {content_preview}")
            
            if len(matches) > 3:
                print(f"    ... and {len(matches) - 3} more matches")
        else:
            print(f"  {Colors.WARNING}No matches found{Colors.ENDC}")
        
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
    
    def _print_overall_summary(self, results):
        """Print overall test suite summary"""
        print(f"\n{Colors.HEADER}{Colors.BOLD}")
        print("=" * 90)
        print("EDUCATIONAL TEST SUITE SUMMARY")
        print("=" * 90)
        print(f"{Colors.ENDC}")
        
        successful_tests = sum(1 for r in results if r['success'])
        total_matches = sum(len(r['matches']) for r in results)
        total_files = sum(r['files_searched'] for r in results)
        total_time = sum(r['execution_time'] for r in results)
        
        print(f"{Colors.OKGREEN}📊 Test Results:{Colors.ENDC}")
        print(f"  ✓ Scenarios Run: {len(results)}")
        print(f"  ✓ Successful Tests: {successful_tests}")
        print(f"  ✓ Total Matches: {total_matches}")
        print(f"  ✓ Files Searched: {total_files}")
        print(f"  ✓ Total Time: {total_time:.3f}s")
        print(f"  ✓ Success Rate: {(successful_tests/len(results)*100):.1f}%")
        
        print(f"\n{Colors.UNDERLINE}🎓 Learning Summary:{Colors.ENDC}")
        print(f"  📝 Level 1 (Simple): Single variable searches - good for basic content finding")
        print(f"  📝 Level 2 (Basic): Two variables with AND/OR - find related content")
        print(f"  📝 Level 3 (Medium): Parentheses and NOT - exclude unwanted content")
        print(f"  📝 Level 4 (Advanced): Multiple groups - complex relationship matching")
        print(f"  📝 Level 5 (Expert): Nested logic - sophisticated pattern detection")
        
        print(f"\n{Colors.UNDERLINE}💡 Usage Tips:{Colors.ENDC}")
        print(f"  • Start with simple formulas and gradually increase complexity")
        print(f"  • Use parentheses to group related conditions")
        print(f"  • Common operators: & (AND), | (OR), ! (NOT)")
        print(f"  • Case sensitivity affects search precision")
        print(f"  • Test formulas with this suite before complex searches")
        
        print(f"\n{Colors.HEADER}🔄 Run again to see different formula examples!{Colors.ENDC}")
        print(f"{Colors.HEADER}{'='*90}{Colors.ENDC}")


def main():
    """Main function to run the educational test suite"""
    runner = TestSuiteRunner()
    results = runner.run_educational_test_suite()
    
    # Return success if any tests found matches
    return any(r['success'] for r in results)


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)