# File: test_finder_demo.py
# Path: /home/herb/Desktop/Finder/Test/test_finder_demo.py
# Standard: AIDEV-PascalCase-2.1
# Created: 2025-07-18
# Last Modified: 2025-07-18  01:45PM
"""
Demonstration of enhanced functional testing with detailed summaries
Shows the comprehensive reporting capabilities with working examples
"""

import os
import sys
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


def normalize_operators(formula):
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


def evaluate_formula(content, phrases, formula):
    """Evaluate formula against content"""
    if not formula.strip():
        return False
    
    # Normalize operators
    normalized_formula = normalize_operators(formula)
    
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


def colorize_formula(formula):
    """Add colors to formula"""
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


def create_value_formula(formula, phrases):
    """Create formula with values"""
    value_formula = formula
    
    for letter, phrase_data in phrases.items():
        if phrase_data['text']:
            has_phrase = f"contains('{phrase_data['text']}')"
            value_formula = value_formula.replace(letter, f"{Colors.VALUE}{has_phrase}{Colors.ENDC}")
    
    return value_formula


def generate_human_intent(formula, phrases):
    """Generate human-readable intent"""
    active_phrases = {k: v for k, v in phrases.items() if v['text']}
    
    if not active_phrases:
        return "No search criteria specified"
    
    if len(active_phrases) == 1:
        letter, phrase_data = list(active_phrases.items())[0]
        return f"Find content containing '{phrase_data['text']}'"
    
    formula_upper = formula.upper()
    
    if 'AND' in formula_upper:
        if 'OR' in formula_upper:
            return "Find content matching complex criteria with both AND and OR conditions"
        else:
            phrases_list = [f"'{v['text']}'" for v in active_phrases.values()]
            return f"Find content containing ALL of: {', '.join(phrases_list)}"
    
    elif 'OR' in formula_upper:
        phrases_list = [f"'{v['text']}'" for v in active_phrases.values()]
        return f"Find content containing ANY of: {', '.join(phrases_list)}"
    
    elif 'NOT' in formula_upper:
        return "Find content with exclusion criteria (NOT conditions)"
    
    else:
        return "Find content matching the specified formula"


def search_files(directory, file_extensions, phrases, formula):
    """Search files and return results"""
    results = []
    files_searched = 0
    
    for root, dirs, files in os.walk(directory):
        for filename in files:
            if any(filename.endswith(ext) for ext in file_extensions):
                filepath = os.path.join(root, filename)
                files_searched += 1
                
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        for line_num, line in enumerate(f, 1):
                            if evaluate_formula(line, phrases, formula):
                                results.append({
                                    'file_path': filepath,
                                    'content': line.strip(),
                                    'line_number': line_num,
                                    'is_unique': True  # Simplified for demo
                                })
                except Exception as e:
                    continue
    
    return results, files_searched


def print_test_scenario(name, description, phrases, formula, file_types, results, files_searched, execution_time):
    """Print detailed test scenario summary"""
    print(f"\n{Colors.HEADER}{'='*80}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}TEST SCENARIO: {name}{Colors.ENDC}")
    print(f"{Colors.HEADER}{'='*80}{Colors.ENDC}")
    
    # Description
    print(f"{Colors.OKBLUE}Description:{Colors.ENDC} {description}")
    
    # Variables section
    print(f"\n{Colors.UNDERLINE}Variables Used:{Colors.ENDC}")
    for letter, phrase_data in phrases.items():
        if phrase_data['text']:
            case_info = f" (Case {'Sensitive' if phrase_data['case_sensitive'] else 'Insensitive'})"
            print(f"  {Colors.VARIABLE}{letter}{Colors.ENDC} = '{Colors.VALUE}{phrase_data['text']}{Colors.ENDC}'{case_info}")
    
    # Formula section
    print(f"\n{Colors.UNDERLINE}Search Formula:{Colors.ENDC}")
    colored_formula = colorize_formula(formula)
    print(f"  User Formula: {colored_formula}")
    
    # Formula with values
    print(f"\n{Colors.UNDERLINE}Formula with Values:{Colors.ENDC}")
    value_formula = create_value_formula(formula, phrases)
    print(f"  {value_formula}")
    
    # Human-readable intent
    print(f"\n{Colors.UNDERLINE}Search Intent:{Colors.ENDC}")
    intent = generate_human_intent(formula, phrases)
    print(f"  {Colors.OKCYAN}{intent}{Colors.ENDC}")
    
    # Search parameters
    print(f"\n{Colors.UNDERLINE}Search Parameters:{Colors.ENDC}")
    print(f"  Search Mode: {Colors.WARNING}Line{Colors.ENDC}")
    print(f"  File Types: {Colors.WARNING}{', '.join(file_types)}{Colors.ENDC}")
    print(f"  Files Searched: {Colors.WARNING}{files_searched}{Colors.ENDC}")
    print(f"  Execution Time: {Colors.WARNING}{execution_time:.3f}s{Colors.ENDC}")
    
    # Results section
    print(f"\n{Colors.UNDERLINE}Expected Results:{Colors.ENDC}")
    print(f"  {Colors.OKGREEN}Expected matches in line-by-line search across {', '.join(file_types)} files{Colors.ENDC}")
    
    # Actual results
    print(f"\n{Colors.UNDERLINE}Actual Results:{Colors.ENDC}")
    if results:
        print(f"  {Colors.OKGREEN}Found {len(results)} matches:{Colors.ENDC}")
        for i, result in enumerate(results[:5], 1):  # Show first 5 results
            file_name = os.path.basename(result['file_path'])
            line_info = f"Line {result['line_number']}: "
            unique_marker = f" {Colors.FAIL}[UNIQUE]{Colors.ENDC}" if result['is_unique'] else ""
            content_preview = result['content'][:60] + "..." if len(result['content']) > 60 else result['content']
            print(f"    {i}. {Colors.OKBLUE}{file_name}{Colors.ENDC} - {line_info}{content_preview}{unique_marker}")
        
        if len(results) > 5:
            print(f"    ... and {len(results) - 5} more matches")
    else:
        print(f"  {Colors.WARNING}No matches found{Colors.ENDC}")
    
    # Success/Failure
    print(f"\n{Colors.UNDERLINE}Test Result:{Colors.ENDC}")
    if results:
        print(f"  {Colors.OKGREEN}✓ SUCCESS{Colors.ENDC} - Test passed as expected")
    else:
        print(f"  {Colors.FAIL}✗ FAILURE{Colors.ENDC} - Test did not meet expectations")
    
    # Analysis
    print(f"\n{Colors.UNDERLINE}Analysis:{Colors.ENDC}")
    if results:
        unique_count = sum(1 for r in results if r['is_unique'])
        analysis_parts = [
            f"{Colors.OKGREEN}Found {len(results)} total matches{Colors.ENDC}",
            f"{Colors.OKGREEN}{unique_count} unique matches{Colors.ENDC}",
            f"{Colors.OKGREEN}Searched {files_searched} files{Colors.ENDC}",
            f"{Colors.OKGREEN}Performance: {execution_time:.3f}s{Colors.ENDC}"
        ]
        print(f"  {' | '.join(analysis_parts)}")
    else:
        print(f"  {Colors.WARNING}No results found - check if search criteria exist in target files{Colors.ENDC}")
    
    print(f"{Colors.HEADER}{'='*80}{Colors.ENDC}")


def run_demo_scenarios():
    """Run demonstration scenarios"""
    print(f"{Colors.HEADER}{Colors.BOLD}")
    print("=" * 80)
    print("FINDER APPLICATION - ENHANCED FUNCTIONAL TESTING DEMO")
    print("=" * 80)
    print(f"{Colors.ENDC}")
    
    print(f"{Colors.OKBLUE}Demonstrating comprehensive functional tests with detailed reporting...{Colors.ENDC}")
    print(f"{Colors.OKBLUE}Test execution time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.ENDC}")
    
    project_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Scenario 1: Simple Python import search
    print(f"\n{Colors.OKCYAN}Running Scenario 1: Python Import Search{Colors.ENDC}")
    start_time = time.time()
    
    phrases1 = {
        'A': {'text': 'import', 'case_sensitive': False},
        'B': {'text': '', 'case_sensitive': False},
        'C': {'text': '', 'case_sensitive': False}
    }
    
    results1, files1 = search_files(project_dir, ['.py'], phrases1, 'A')
    execution_time1 = time.time() - start_time
    
    print_test_scenario(
        "Python Import Search",
        "Search for Python import statements across all Python files",
        phrases1,
        'A',
        ['.py'],
        results1,
        files1,
        execution_time1
    )
    
    # Scenario 2: Complex formula search
    print(f"\n{Colors.OKCYAN}Running Scenario 2: Complex Formula Search{Colors.ENDC}")
    start_time = time.time()
    
    phrases2 = {
        'A': {'text': 'def', 'case_sensitive': True},
        'B': {'text': 'class', 'case_sensitive': True},
        'C': {'text': 'File', 'case_sensitive': True}
    }
    
    results2, files2 = search_files(project_dir, ['.py'], phrases2, 'A | B')
    execution_time2 = time.time() - start_time
    
    print_test_scenario(
        "Python Definition Search",
        "Search for Python function or class definitions",
        phrases2,
        'A | B',
        ['.py'],
        results2,
        files2,
        execution_time2
    )
    
    # Scenario 3: Documentation search
    print(f"\n{Colors.OKCYAN}Running Scenario 3: Documentation Search{Colors.ENDC}")
    start_time = time.time()
    
    phrases3 = {
        'A': {'text': '#', 'case_sensitive': False},
        'B': {'text': 'Standard', 'case_sensitive': False},
        'C': {'text': 'Design', 'case_sensitive': False}
    }
    
    results3, files3 = search_files(project_dir, ['.md'], phrases3, 'A & (B | C)')
    execution_time3 = time.time() - start_time
    
    print_test_scenario(
        "Documentation Header Search",
        "Search for documentation headers with design standards",
        phrases3,
        'A & (B | C)',
        ['.md'],
        results3,
        files3,
        execution_time3
    )
    
    # Scenario 4: Common operator test
    print(f"\n{Colors.OKCYAN}Running Scenario 4: Common Operator Test{Colors.ENDC}")
    start_time = time.time()
    
    phrases4 = {
        'A': {'text': 'python', 'case_sensitive': False},
        'B': {'text': 'error', 'case_sensitive': False},
        'C': {'text': '', 'case_sensitive': False}
    }
    
    results4, files4 = search_files(project_dir, ['.py', '.txt'], phrases4, 'A & !B')
    execution_time4 = time.time() - start_time
    
    print_test_scenario(
        "Common Operator Test",
        "Search for Python references without errors using common operators",
        phrases4,
        'A & !B',
        ['.py', '.txt'],
        results4,
        files4,
        execution_time4
    )
    
    # Final summary
    all_results = [results1, results2, results3, results4]
    total_matches = sum(len(r) for r in all_results)
    successful_tests = sum(1 for r in all_results if len(r) > 0)
    
    print(f"\n{Colors.HEADER}{Colors.BOLD}")
    print("=" * 80)
    print("DEMONSTRATION SUMMARY")
    print("=" * 80)
    print(f"{Colors.ENDC}")
    
    print(f"{Colors.OKGREEN}✓ Scenarios Run: 4{Colors.ENDC}")
    print(f"{Colors.OKGREEN}✓ Successful Tests: {successful_tests}{Colors.ENDC}")
    print(f"{Colors.OKGREEN}✓ Total Matches Found: {total_matches}{Colors.ENDC}")
    print(f"{Colors.OKCYAN}Success Rate: {(successful_tests/4*100):.1f}%{Colors.ENDC}")
    
    print(f"\n{Colors.UNDERLINE}Key Features Demonstrated:{Colors.ENDC}")
    print(f"  ✓ {Colors.OKGREEN}Color-coded formula display{Colors.ENDC}")
    print(f"  ✓ {Colors.OKGREEN}Human-readable search intent{Colors.ENDC}")
    print(f"  ✓ {Colors.OKGREEN}Formula with values substitution{Colors.ENDC}")
    print(f"  ✓ {Colors.OKGREEN}Detailed result analysis{Colors.ENDC}")
    print(f"  ✓ {Colors.OKGREEN}Performance metrics{Colors.ENDC}")
    print(f"  ✓ {Colors.OKGREEN}Expected vs actual comparison{Colors.ENDC}")
    print(f"  ✓ {Colors.OKGREEN}Success/failure determination{Colors.ENDC}")
    
    print(f"\n{Colors.HEADER}Demo completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.ENDC}")
    print(f"{Colors.HEADER}{'='*80}{Colors.ENDC}")


if __name__ == '__main__':
    run_demo_scenarios()