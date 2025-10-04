# File: objective_test_suite.py
# Path: /home/herb/Desktop/LLM-Tester/objective_test_suite.py
# Standard: AIDEV-PascalCase-2.1
# Created: 2025-10-01
# Last Modified: 2025-10-01 10:25PM

"""
Objective Test Suite for Code and Logic Problems

This module contains test cases that have clear, provable solutions.
Each test case includes:
- Problem description with specific requirements
- Test function or code skeleton
- Clear expected results
- Complete working implementation
- Multiple data validation checks

Categories:
1. Code Generation (functions, classes, algorithms)
2. Mathematical Computation (formulas, calculations)
3. Logical Reasoning (puzzles, logic problems)
4. Data Processing (parsing, validation)
"""

import json
import ast
import re
import math
import subprocess
import sys
from typing import Dict, Any, List, Tuple, Optional, Union
from dataclasses import dataclass
from enum import Enum
from datetime import datetime


class ProblemType(Enum):
    """Categories of objective problems"""
    CODE_GENERATION = "code"
    MATHEMATICAL = "mathematical"
    LOGICAL_REASONING = "logical_reasoning"
    DATA_PROCESSING = "data_processing"


@dataclass
class TestResult:
    """Result of running a test case"""
    test_id: str
    passed: bool
    score: float  # 0.0 to 1.0
    actual_result: Any
    expected_result: Any
    execution_time: float
    error_message: Optional[str] = None
    feedback: str = ""


@dataclass
class TestCase:
    """Represents a single test case with provable solution"""
    test_id: str
    category: ProblemType
    description: str
    requirements: str
    expected_result: Any
    solution_func: callable
    test_data: Optional[Tuple] = None
    validation_func: Optional[callable] = None

    def run_test(self) -> TestResult:
        """Execute the test and return detailed results"""
        import time
        start_time = time.time()

        try:
            if self.test_data:
                actual_result = self.solution_func(*self.test_data)
            else:
                actual_result = self.solution_func()

            execution_time = time.time() - start_time

            # Validate result
            if self.validation_func:
                validation_result = self.validation_func(actual_result, self.expected_result)
                passed = validation_result['passed']
                score = validation_result['score']
                feedback = validation_result['feedback']
            else:
                passed, score, feedback = self._default_validation(actual_result, self.expected_result)

            return TestResult(
                test_id=self.test_id,
                passed=passed,
                score=score,
                actual_result=actual_result,
                expected_result=self.expected_result,
                execution_time=execution_time,
                feedback=feedback
            )

        except Exception as e:
            execution_time = time.time() - start_time
            return TestResult(
                test_id=self.test_id,
                passed=False,
                score=0.0,
                actual_result=None,
                expected_result=self.expected_result,
                execution_time=execution_time,
                error_message=str(e),
                feedback=f"Error: {str(e)}"
            )

    def _default_validation(self, actual: Any, expected: Any) -> Tuple[bool, float, str]:
        """Default validation logic for comparing results"""
        if actual == expected:
            return True, 1.0, "Perfect match"

        # For numeric values, allow small tolerance
        if isinstance(actual, (int, float)) and isinstance(expected, (int, float)):
            tolerance = 1e-6
            if abs(actual - expected) <= tolerance:
                return True, 0.95, f"Match within tolerance ({tolerance})"
            else:
                error_percent = abs(actual - expected) / max(abs(expected), 1.0) * 100
                return False, max(0, 1.0 - error_percent/100), f"Off by {error_percent:.2f}%"

        # For lists/sequences, check content similarity
        if isinstance(actual, list) and isinstance(expected, list):
            if actual == expected:
                return True, 1.0, "Perfect list match"
            elif set(actual) == set(expected):
                return True, 0.9, "Correct elements, wrong order"
            else:
                matches = sum(1 for item in actual if item in expected)
                score = matches / max(len(expected), len(actual))
                return False, score, f"Only {matches}/{len(expected)} elements correct"

        # For strings, check if they contain the same information
        if isinstance(actual, str) and isinstance(expected, str):
            if actual.strip() == expected.strip():
                return True, 1.0, "Perfect string match"
            else:
                # Check if expected content is present in actual
                if expected.lower() in actual.lower():
                    return True, 0.8, "Contains expected content"
                else:
                    return False, 0.0, "No match found"

        return False, 0.0, f"Type mismatch or incorrect result"


class ObjectiveTestSuite:
    """Automated test suite for objective problems"""

    def __init__(self):
        self.test_cases = self._create_test_cases()
        self.results = []

    def _create_test_cases(self) -> List[TestCase]:
        """Create all test cases with provable solutions"""
        test_cases = []

        # Code Generation Tests
        test_cases.append(TestCase(
            test_id="code_triangle_area",
            category=ProblemType.CODE_GENERATION,
            description="Write a Python function to calculate the area of a triangle given base and height",
            requirements="Function should take base and height as parameters and return the area",
            expected_result=25.0,
            solution_func=lambda base, height: 0.5 * base * height,
            test_data=(10, 5)
        ))

        test_cases.append(TestCase(
            test_id="code_factorial",
            category=ProblemType.CODE_GENERATION,
            description="Write a function to calculate factorial of a number",
            requirements="Handle n=0, n=1, and positive integers correctly",
            expected_result=120,
            solution_func=self._factorial_solution,
            test_data=(5,)
        ))

        test_cases.append(TestCase(
            test_id="code_prime_check",
            category=ProblemType.CODE_GENERATION,
            description="Write a function to check if a number is prime",
            requirements="Return True for prime numbers, False for composite",
            expected_result=False,
            solution_func=self._is_prime_solution,
            test_data=(15,)
        ))

        # Mathematical Tests
        test_cases.append(TestCase(
            test_id="math_fibonacci",
            category=ProblemType.MATHEMATICAL,
            description="Generate Fibonacci sequence up to n terms",
            requirements="Return list of first n Fibonacci numbers",
            expected_result=[0, 1, 1, 2, 3, 5, 8, 13, 21, 34],
            solution_func=self._fibonacci_solution,
            test_data=(10,)
        ))

        test_cases.append(TestCase(
            test_id="math_gcd",
            category=ProblemType.MATHEMATICAL,
            description="Calculate greatest common divisor of two numbers",
            requirements="Use Euclidean algorithm",
            expected_result=6,
            solution_func=self._gcd_solution,
            test_data=(54, 24)
        ))

        # Logical Reasoning Tests
        test_cases.append(TestCase(
            test_id="logic_puzzle",
            category=ProblemType.LOGICAL_REASONING,
            description="A bat and ball cost $1.10. The bat costs $1.00 more than the ball. How much does the ball cost?",
            requirements="Use logical deduction, not trial and error",
            expected_result=0.05,
            solution_func=lambda: 0.05  # Ball costs $0.05, bat costs $1.05
        ))

        test_cases.append(TestCase(
            test_id="logic_sequence",
            category=ProblemType.LOGICAL_REASONING,
            description="Find the next number in sequence: 2, 4, 8, 16, ?",
            requirements="Identify the pattern and apply it",
            expected_result=32,
            solution_func=lambda: 32  # Powers of 2
        ))

        # Data Processing Tests
        test_cases.append(TestCase(
            test_id="data_sort_numbers",
            category=ProblemType.DATA_PROCESSING,
            description="Sort a list of numbers in ascending order",
            requirements="Return sorted list without modifying original",
            expected_result=[1, 2, 3, 5, 8],
            solution_func=lambda arr: sorted(arr.copy()),
            test_data=([3, 1, 4, 5, 2],)
        ))

        test_cases.append(TestCase(
            test_id="data_unique_elements",
            category=ProblemType.DATA_PROCESSING,
            description="Extract unique elements from a list",
            requirements="Return list of unique elements in order of first appearance",
            expected_result=[1, 2, 3, 4],
            solution_func=self._unique_elements_solution,
            test_data=([1, 2, 2, 3, 1, 4, 2],)
        ))

        test_cases.append(TestCase(
            test_id="data_sum_nested",
            category=ProblemType.DATA_PROCESSING,
            description="Sum all numbers in a nested list structure",
            requirements="Handle nested lists of arbitrary depth",
            expected_result=36,
            solution_func=self._sum_nested_solution,
            test_data=([[1, 2], [3, [4, 5]], 6],)
        ))

        return test_cases

    # Solution implementations
    def _factorial_solution(self, n: int) -> int:
        """Calculate factorial"""
        if n <= 1:
            return 1
        result = 1
        for i in range(2, n + 1):
            result *= i
        return result

    def _is_prime_solution(self, n: int) -> bool:
        """Check if number is prime"""
        if n <= 1:
            return False
        if n <= 3:
            return True
        if n % 2 == 0 or n % 3 == 0:
            return False
        i = 5
        while i * i <= n:
            if n % i == 0 or n % (i + 2) == 0:
                return False
            i += 6
        return True

    def _fibonacci_solution(self, n: int) -> List[int]:
        """Generate Fibonacci sequence"""
        if n <= 0:
            return []
        elif n == 1:
            return [0]

        sequence = [0, 1]
        while len(sequence) < n:
            sequence.append(sequence[-1] + sequence[-2])
        return sequence

    def _gcd_solution(self, a: int, b: int) -> int:
        """Calculate GCD using Euclidean algorithm"""
        while b:
            a, b = b, a % b
        return a

    def _unique_elements_solution(self, lst: List[int]) -> List[int]:
        """Extract unique elements preserving order"""
        seen = set()
        result = []
        for item in lst:
            if item not in seen:
                seen.add(item)
                result.append(item)
        return result

    def _sum_nested_solution(self, data: List) -> int:
        """Sum all numbers in nested list"""
        total = 0
        for item in data:
            if isinstance(item, list):
                total += self._sum_nested_solution(item)
            elif isinstance(item, (int, float)):
                total += item
        return total

    def run_all_tests(self) -> Dict[str, Any]:
        """Run all test cases and return summary"""
        self.results = []

        for test_case in self.test_cases:
            print(f"Running {test_case.test_id}...")
            result = test_case.run_test()
            self.results.append(result)

            status = "✅" if result.passed else "❌"
            print(f"  {status} {result.test_id}: Score {result.score:.2f}")
            if result.error_message:
                print(f"    Error: {result.error_message}")

        return self.generate_summary()

    def generate_summary(self) -> Dict[str, Any]:
        """Generate summary of all test results"""
        if not self.results:
            return {"error": "No test results available"}

        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.passed)
        failed_tests = total_tests - passed_tests
        average_score = sum(r.score for r in self.results) / total_tests
        total_time = sum(r.execution_time for r in self.results)

        # Group by category
        category_results = {}
        for result in self.results:
            test_case = next(t for t in self.test_cases if t.test_id == result.test_id)
            category = test_case.category.value
            if category not in category_results:
                category_results[category] = []
            category_results[category].append(result)

        category_summary = {}
        for category, results in category_results.items():
            category_summary[category] = {
                "total": len(results),
                "passed": sum(1 for r in results if r.passed),
                "average_score": sum(r.score for r in results) / len(results),
                "results": [{"test_id": r.test_id, "score": r.score, "passed": r.passed} for r in results]
            }

        return {
            "timestamp": datetime.now().isoformat(),
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": passed_tests / total_tests,
            "average_score": average_score,
            "total_execution_time": total_time,
            "category_breakdown": category_summary,
            "all_results": [
                {
                    "test_id": r.test_id,
                    "passed": r.passed,
                    "score": r.score,
                    "execution_time": r.execution_time,
                    "error_message": r.error_message,
                    "feedback": r.feedback
                }
                for r in self.results
            ]
        }

    def evaluate_llm_response(self, test_id: str, llm_response: str) -> TestResult:
        """Evaluate LLM response against a specific test case"""
        test_case = next((t for t in self.test_cases if t.test_id == test_id), None)
        if not test_case:
            raise ValueError(f"Test case {test_id} not found")

        try:
            # Try to extract code from LLM response and execute it
            extracted_code = self._extract_code_from_response(llm_response)
            if extracted_code:
                # Create a temporary function from extracted code
                actual_result = self._execute_extracted_code(extracted_code, test_case.test_data)
            else:
                # For non-code responses, try to parse the answer directly
                actual_result = self._parse_numerical_answer(llm_response)

            # Validate the result
            if test_case.validation_func:
                validation_result = test_case.validation_func(actual_result, test_case.expected_result)
                passed = validation_result['passed']
                score = validation_result['score']
                feedback = validation_result['feedback']
            else:
                passed, score, feedback = test_case._default_validation(actual_result, test_case.expected_result)

            return TestResult(
                test_id=test_id,
                passed=passed,
                score=score,
                actual_result=actual_result,
                expected_result=test_case.expected_result,
                execution_time=0.0,
                feedback=feedback
            )

        except Exception as e:
            return TestResult(
                test_id=test_id,
                passed=False,
                score=0.0,
                actual_result=None,
                expected_result=test_case.expected_result,
                execution_time=0.0,
                error_message=f"Failed to evaluate LLM response: {str(e)}",
                feedback=f"Could not extract or execute code from response"
            )

    def _extract_code_from_response(self, response: str) -> Optional[str]:
        """Extract Python code from LLM response"""
        # Look for code blocks
        code_block_pattern = r'```(?:python)?\s*(.*?)```'
        matches = re.findall(code_block_pattern, response, re.DOTALL)
        if matches:
            return matches[0].strip()

        # Look for function definitions
        func_pattern = r'def\s+\w+\s*\([^)]*\)\s*:.*?(?=\ndef|\Z)'
        matches = re.findall(func_pattern, response, re.DOTALL)
        if matches:
            return matches[0].strip()

        return None

    def _execute_extracted_code(self, code: str, test_data: Optional[Tuple] = None) -> Any:
        """Execute extracted code safely"""
        # Create a safe execution environment
        safe_globals = {
            '__builtins__': {
                'range': range,
                'len': len,
                'sum': sum,
                'sorted': sorted,
                'set': set,
                'list': list,
                'int': int,
                'float': float,
                'str': str,
                'bool': bool,
                'print': lambda *args: None,  # Suppress print
            }
        }

        local_vars = {}

        try:
            exec(code, safe_globals, local_vars)

            # Try to find a function to call
            if test_data:
                # Look for functions that take arguments
                for name, func in local_vars.items():
                    if callable(func) and name != '<lambda>':
                        return func(*test_data)
            else:
                # Look for main result or lambda
                if 'result' in local_vars:
                    return local_vars['result']
                for name, value in local_vars.items():
                    if not callable(value) and not name.startswith('_'):
                        return value

            # If no function found, evaluate as expression
            return eval(code, safe_globals)

        except Exception as e:
            raise ValueError(f"Code execution failed: {str(e)}")

    def _parse_numerical_answer(self, response: str) -> Optional[Union[int, float]]:
        """Parse numerical answer from text response"""
        # Look for numbers in the response
        number_patterns = [
            r'(?i)(?:answer|result|solution)[s]?\s*(?:is|are)?\s*:?\s*([0-9]+\.?[0-9]*)',
            r'(?i)(?:costs?|equals?)\s*\$?([0-9]+\.?[0-9]*)',
            r'(?i)(?:next\s+number|answer)\s*(?:is)?\s*([0-9]+\.?[0-9]*)',
            r'\b([0-9]+\.?[0-9]*)\b'  # Any number
        ]

        for pattern in number_patterns:
            matches = re.findall(pattern, response)
            if matches:
                try:
                    value = matches[0]
                    return float(value) if '.' in value else int(value)
                except ValueError:
                    continue

        return None


# Usage example
if __name__ == "__main__":
    suite = ObjectiveTestSuite()
    summary = suite.run_all_tests()

    print(f"\n📊 Test Suite Summary:")
    print(f"Total Tests: {summary['total_tests']}")
    print(f"Passed: {summary['passed_tests']}")
    print(f"Failed: {summary['failed_tests']}")
    print(f"Success Rate: {summary['success_rate']:.2%}")
    print(f"Average Score: {summary['average_score']:.2f}")
    print(f"Total Time: {summary['total_execution_time']:.3f}s")

    print(f"\n📈 Category Breakdown:")
    for category, data in summary['category_breakdown'].items():
        print(f"  {category}: {data['passed']}/{data['total']} passed (avg score: {data['average_score']:.2f})")