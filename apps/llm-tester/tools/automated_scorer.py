# File: automated_scorer.py
# Path: /home/herb/Desktop/LLM-Tester/automated_scorer.py
# Standard: AIDEV-PascalCase-2.1
# Created: 2025-10-01
# Last Modified: 2025-10-01 10:30PM

"""
Automated Scoring System for LLM Response Evaluation

This module provides comprehensive scoring capabilities for evaluating LLM responses
across different categories of tasks with provable solutions.

Features:
- Multi-dimensional scoring (Syntax, Accuracy, Completeness, Logic)
- Category-specific evaluation criteria
- Automated code execution and validation
- Detailed feedback generation
- Integration with parameter comparison framework
"""

import ast
import re
import json
import math
import subprocess
import sys
import time
from typing import Dict, Any, List, Tuple, Optional, Union, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime

from objective_test_suite import ObjectiveTestSuite, TestResult


class TaskCategory(Enum):
    """Categories of tasks with different evaluation criteria"""
    CODE_GENERATION = "code"
    MATHEMATICAL = "mathematical"
    LOGICAL_REASONING = "logical_reasoning"
    DATA_PROCESSING = "data_processing"
    CREATIVE = "creative"  # For subjective tasks
    TECHNICAL_EXPLANATION = "technical"


@dataclass
class ScoringDimensions:
    """Multi-dimensional scoring criteria"""
    syntax_score: float = 0.0      # Code syntax and structure
    accuracy_score: float = 0.0    # Correctness of the solution
    completeness_score: float = 0.0  # Coverage of requirements
    logic_score: float = 0.0       # Logical soundness
    efficiency_score: float = 0.0  # Code efficiency
    style_score: float = 0.0       # Code style and readability

    def overall_score(self) -> float:
        """Calculate weighted overall score"""
        weights = {
            'syntax_score': 0.15,
            'accuracy_score': 0.35,
            'completeness_score': 0.25,
            'logic_score': 0.15,
            'efficiency_score': 0.05,
            'style_score': 0.05
        }

        return sum(getattr(self, dim) * weight
                  for dim, weight in weights.items())


@dataclass
class DetailedScore:
    """Comprehensive scoring result with feedback"""
    task_id: str
    task_category: TaskCategory
    overall_score: float
    dimensions: ScoringDimensions
    execution_result: Optional[Any] = None
    expected_result: Optional[Any] = None
    execution_success: bool = False
    feedback: str = ""
    strengths: List[str] = None
    weaknesses: List[str] = None
    suggestions: List[str] = None
    execution_time: float = 0.0

    def __post_init__(self):
        if self.strengths is None:
            self.strengths = []
        if self.weaknesses is None:
            self.weaknesses = []
        if self.suggestions is None:
            self.suggestions = []


class AutomatedScorer:
    """Comprehensive automated scoring system"""

    def __init__(self):
        self.objective_suite = ObjectiveTestSuite()
        self.code_execution_cache = {}

    def score_response(self, task_id: str, llm_response: str,
                      task_category: TaskCategory = None,
                      expected_result: Any = None,
                      test_data: Tuple = None) -> DetailedScore:
        """
        Score an LLM response against an objective test case

        Args:
            task_id: Identifier for the task
            llm_response: The LLM's response text
            task_category: Category of the task
            expected_result: Expected correct result
            test_data: Test data for function calls

        Returns:
            DetailedScore with comprehensive evaluation
        """
        start_time = time.time()

        # Get test case info
        test_case = None
        for tc in self.objective_suite.test_cases:
            if tc.test_id == task_id:
                test_case = tc
                break

        if not test_case:
            # Create a basic scoring if no test case found
            return self._score_generic_response(task_id, llm_response, task_category)

        # Convert ProblemType to TaskCategory
        category_mapping = {
            'code': TaskCategory.CODE_GENERATION,
            'mathematical': TaskCategory.MATHEMATICAL,
            'logical_reasoning': TaskCategory.LOGICAL_REASONING,
            'data_processing': TaskCategory.DATA_PROCESSING
        }
        test_case.category = category_mapping.get(test_case.category.value, TaskCategory.TECHNICAL_EXPLANATION)

        # Extract and execute code if present
        execution_result = None
        execution_success = False
        execution_time = 0.0

        try:
            if test_case.category in [TaskCategory.CODE_GENERATION, TaskCategory.DATA_PROCESSING]:
                execution_result = self._execute_response_code(llm_response, test_case.test_data)
                execution_success = True
            elif test_case.category == TaskCategory.MATHEMATICAL:
                execution_result = self._extract_mathematical_result(llm_response)
                execution_success = execution_result is not None
            elif test_case.category == TaskCategory.LOGICAL_REASONING:
                execution_result = self._extract_logical_result(llm_response)
                execution_success = execution_result is not None
        except Exception as e:
            execution_success = False
            execution_time = time.time() - start_time

        execution_time = time.time() - start_time

        # Calculate dimensional scores
        dimensions = self._calculate_dimensional_scores(
            llm_response, test_case, execution_result, execution_success
        )

        # Generate feedback
        feedback_data = self._generate_feedback(
            llm_response, test_case, execution_result, execution_success, dimensions
        )

        return DetailedScore(
            task_id=task_id,
            task_category=test_case.category,
            overall_score=dimensions.overall_score(),
            dimensions=dimensions,
            execution_result=execution_result,
            expected_result=test_case.expected_result,
            execution_success=execution_success,
            feedback=feedback_data['feedback'],
            strengths=feedback_data['strengths'],
            weaknesses=feedback_data['weaknesses'],
            suggestions=feedback_data['suggestions'],
            execution_time=execution_time
        )

    def _execute_response_code(self, response: str, test_data: Optional[Tuple] = None) -> Any:
        """Extract and execute code from LLM response"""
        # Try to get code from objective suite first
        extracted_code = self.objective_suite._extract_code_from_response(response)
        if extracted_code:
            return self.objective_suite._execute_extracted_code(extracted_code, test_data)

        # Fallback: try to find and execute code directly
        return self._execute_code_directly(response, test_data)

    def _execute_code_directly(self, response: str, test_data: Optional[Tuple] = None) -> Any:
        """Direct code execution with safety measures"""
        # Extract code blocks
        code_pattern = r'```(?:python)?\s*(.*?)```'
        matches = re.findall(code_pattern, response, re.DOTALL)

        if not matches:
            # Look for function definitions
            func_pattern = r'def\s+\w+\s*\([^)]*\)\s*:.*?(?=\ndef|\Z)'
            matches = re.findall(func_pattern, response, re.DOTALL)

        if not matches:
            raise ValueError("No executable code found in response")

        code = matches[0].strip()

        # Create safe execution environment
        safe_globals = {
            '__builtins__': {
                'range': range, 'len': len, 'sum': sum, 'sorted': sorted,
                'set': set, 'list': list, 'int': int, 'float': float,
                'str': str, 'bool': bool, 'min': min, 'max': max,
                'abs': abs, 'round': round, 'enumerate': enumerate,
                'zip': zip, 'reversed': reversed, 'filter': filter,
                'map': map, 'all': all, 'any': any, 'print': lambda *args: None
            }
        }

        local_vars = {}

        try:
            exec(code, safe_globals, local_vars)

            # Find and execute function if test data provided
            if test_data:
                for name, func in local_vars.items():
                    if callable(func) and name != '<lambda>':
                        return func(*test_data)
            else:
                # Look for result variable or last function
                if 'result' in local_vars:
                    return local_vars['result']
                for name, value in local_vars.items():
                    if callable(value) and name != '<lambda>':
                        return value()  # Try to call without args

            return None

        except Exception as e:
            raise ValueError(f"Code execution failed: {str(e)}")

    def _extract_mathematical_result(self, response: str) -> Optional[Union[int, float]]:
        """Extract mathematical answer from response"""
        patterns = [
            r'(?i)(?:answer|result|solution)[s]?\s*(?:is|are)?\s*:?\s*([0-9]+\.?[0-9]*)',
            r'(?i)(?:equals?|=)\s*([0-9]+\.?[0-9]*)',
            r'(?i)(?:value\s+is|value=)\s*([0-9]+\.?[0-9]*)',
            r'\b([0-9]+\.?[0-9]*)\b'  # Last resort: any number
        ]

        for pattern in patterns:
            matches = re.findall(pattern, response)
            if matches:
                try:
                    value = matches[-1]  # Take last match
                    return float(value) if '.' in value else int(value)
                except ValueError:
                    continue

        return None

    def _extract_logical_result(self, response: str) -> Optional[Union[int, float, bool, str]]:
        """Extract logical reasoning answer"""
        # Try numerical extraction first
        numerical = self._extract_mathematical_result(response)
        if numerical is not None:
            return numerical

        # Look for specific logical indicators
        true_patterns = [
            r'(?i)\b(true|yes|correct|valid)\b',
            r'(?i)the\s+answer\s+is\s+(true|yes|correct|valid)'
        ]

        false_patterns = [
            r'(?i)\b(false|no|incorrect|invalid)\b',
            r'(?i)the\s+answer\s+is\s+(false|no|incorrect|invalid)'
        ]

        for pattern in true_patterns:
            if re.search(pattern, response):
                return True

        for pattern in false_patterns:
            if re.search(pattern, response):
                return False

        # Extract specific answer phrases
        answer_pattern = r'(?i)(?:the\s+)?answer\s+(?:is|=)\s+([^.!?]+)'
        matches = re.findall(answer_pattern, response)
        if matches:
            return matches[0].strip()

        return None

    def _calculate_dimensional_scores(self, response: str, test_case,
                                    execution_result: Any, execution_success: bool) -> ScoringDimensions:
        """Calculate scores across different dimensions"""
        dimensions = ScoringDimensions()

        # Syntax Score
        dimensions.syntax_score = self._score_syntax(response, test_case.category)

        # Accuracy Score
        dimensions.accuracy_score = self._score_accuracy(
            execution_result, test_case.expected_result, execution_success
        )

        # Completeness Score
        dimensions.completeness_score = self._score_completeness(response, test_case)

        # Logic Score
        dimensions.logic_score = self._score_logic(response, execution_success, execution_result)

        # Efficiency Score (for code tasks)
        if test_case.category in [TaskCategory.CODE_GENERATION, TaskCategory.DATA_PROCESSING]:
            dimensions.efficiency_score = self._score_efficiency(response, execution_result)
        else:
            dimensions.efficiency_score = 0.8  # Default for non-code tasks

        # Style Score
        dimensions.style_score = self._score_style(response, test_case.category)

        return dimensions

    def _score_syntax(self, response: str, category: TaskCategory) -> float:
        """Score code syntax and structure"""
        if category not in [TaskCategory.CODE_GENERATION, TaskCategory.DATA_PROCESSING]:
            return 0.8  # Default for non-code tasks

        try:
            # Extract code blocks
            code_pattern = r'```(?:python)?\s*(.*?)```'
            matches = re.findall(code_pattern, response, re.DOTALL)

            if not matches:
                # Look for function definitions
                func_pattern = r'def\s+\w+\s*\([^)]*\)\s*:.*?(?=\ndef|\Z)'
                matches = re.findall(func_pattern, response, re.DOTALL)

            if not matches:
                return 0.0  # No code found

            syntax_score = 0.0
            for code in matches:
                try:
                    ast.parse(code.strip())
                    syntax_score = max(syntax_score, 1.0)  # Valid syntax
                except SyntaxError:
                    syntax_score = max(syntax_score, 0.3)  # Some syntax issues

            return syntax_score

        except Exception:
            return 0.0

    def _score_accuracy(self, execution_result: Any, expected_result: Any, execution_success: bool) -> float:
        """Score accuracy of the result"""
        if not execution_success or execution_result is None:
            return 0.0

        if execution_result == expected_result:
            return 1.0

        # For numeric values, allow small tolerance
        if isinstance(execution_result, (int, float)) and isinstance(expected_result, (int, float)):
            tolerance = 1e-6
            if abs(execution_result - expected_result) <= tolerance:
                return 0.95
            else:
                error_percent = abs(execution_result - expected_result) / max(abs(expected_result), 1.0)
                return max(0.0, 1.0 - error_percent)

        # For lists, check content similarity
        if isinstance(execution_result, list) and isinstance(expected_result, list):
            if execution_result == expected_result:
                return 1.0
            elif set(execution_result) == set(expected_result):
                return 0.9  # Correct elements, wrong order
            else:
                matches = sum(1 for item in execution_result if item in expected_result)
                return matches / max(len(expected_result), len(execution_result))

        # For boolean values
        if isinstance(execution_result, bool) and isinstance(expected_result, bool):
            return 1.0 if execution_result == expected_result else 0.0

        # For strings, check content similarity
        if isinstance(execution_result, str) and isinstance(expected_result, str):
            if execution_result.strip().lower() == expected_result.strip().lower():
                return 1.0
            elif expected_result.lower() in execution_result.lower():
                return 0.7
            else:
                return 0.0

        return 0.0

    def _score_completeness(self, response: str, test_case) -> float:
        """Score completeness of the response"""
        score = 0.0

        # Check if response addresses the requirements
        requirements_lower = test_case.requirements.lower()
        response_lower = response.lower()

        # Check for key requirement indicators
        requirement_keywords = [
            'function', 'return', 'parameter', 'calculate', 'implement',
            'solve', 'algorithm', 'logic', 'handle', 'case', 'input'
        ]

        matched_keywords = sum(1 for keyword in requirement_keywords
                             if keyword in requirements_lower and keyword in response_lower)

        if requirement_keywords:
            score = matched_keywords / len(requirement_keywords)

        # Check response length (should be substantial but not too long)
        response_length = len(response.split())
        if response_length < 10:
            score *= 0.3  # Too short
        elif response_length > 500:
            score *= 0.8  # Too long, might include unnecessary content
        else:
            score *= 1.0  # Good length

        # Bonus for including examples or explanations
        if any(word in response_lower for word in ['example', 'for instance', 'such as']):
            score = min(1.0, score + 0.1)

        return min(1.0, score)

    def _score_logic(self, response: str, execution_success: bool, execution_result: Any) -> float:
        """Score logical soundness of the approach"""
        if not execution_success:
            return 0.0

        # Check for logical indicators in the response
        logical_indicators = [
            'because', 'therefore', 'thus', 'hence', 'since', 'due to',
            'algorithm', 'step', 'first', 'then', 'finally', 'approach',
            'method', 'strategy', 'solution', 'reasoning'
        ]

        response_lower = response.lower()
        logical_score = sum(1 for indicator in logical_indicators if indicator in response_lower)

        # Normalize score
        max_possible = len(logical_indicators)
        if max_possible > 0:
            logical_score = min(1.0, logical_score / (max_possible * 0.3))  # Expect ~30% of indicators

        # Bonus for structured approach
        if any(word in response_lower for word in ['step 1', 'first step', 'approach']):
            logical_score = min(1.0, logical_score + 0.2)

        return logical_score

    def _score_efficiency(self, response: str, execution_result: Any) -> float:
        """Score code efficiency"""
        if execution_result is None:
            return 0.0

        # Look for efficiency indicators
        efficiency_keywords = [
            'optimal', 'efficient', 'fast', 'quick', 'optimized',
            'complexity', 'o(n)', 'performance', 'speed'
        ]

        response_lower = response.lower()
        efficiency_mentions = sum(1 for keyword in efficiency_keywords if keyword in response_lower)

        # Basic efficiency score based on algorithm choice
        efficiency_score = 0.8  # Default for working solutions

        # Bonus for mentioning complexity or optimization
        if efficiency_mentions > 0:
            efficiency_score = min(1.0, efficiency_score + 0.2)

        # Penalty for obviously inefficient patterns
        inefficient_patterns = [
            r'for.*in.*range\(len\(',  # Iterating over indices
            r'while.*true',            # Infinite loops
            r'list.*index.*in.*range'  # O(n²) search in list
        ]

        for pattern in inefficient_patterns:
            if re.search(pattern, response):
                efficiency_score = max(0.0, efficiency_score - 0.3)

        return efficiency_score

    def _score_style(self, response: str, category: TaskCategory) -> float:
        """Score code style and readability"""
        if category not in [TaskCategory.CODE_GENERATION, TaskCategory.DATA_PROCESSING]:
            return 0.8  # Default for non-code tasks

        # Extract code for style checking
        code_pattern = r'```(?:python)?\s*(.*?)```'
        matches = re.findall(code_pattern, response, re.DOTALL)

        if not matches:
            return 0.0

        style_score = 0.0
        for code in matches:
            code_lines = code.strip().split('\n')

            # Check for docstrings
            has_docstring = any('"""' in line or "'''" in line for line in code_lines[:5])
            if has_docstring:
                style_score += 0.2

            # Check for variable naming (snake_case)
            var_pattern = r'\b[a-z][a-z0-9_]*[a-z0-9]\b'
            variables = re.findall(var_pattern, code)
            good_variables = sum(1 for var in variables if '_' in var or len(var) > 1)
            if variables:
                style_score += 0.2 * (good_variables / len(variables))

            # Check for proper indentation (4 spaces)
            indented_lines = [line for line in code_lines if line.startswith('    ')]
            if indented_lines:
                style_score += 0.2

            # Check for comments
            comment_lines = [line for line in code_lines if line.strip().startswith('#')]
            if comment_lines:
                style_score += 0.2 * min(1.0, len(comment_lines) / len(code_lines))

            # Check for reasonable line length
            long_lines = [line for line in code_lines if len(line) > 80]
            if not long_lines:
                style_score += 0.2

        return min(1.0, style_score)

    def _generate_feedback(self, response: str, test_case, execution_result: Any,
                          execution_success: bool, dimensions: ScoringDimensions) -> Dict[str, Any]:
        """Generate detailed feedback"""
        feedback = []
        strengths = []
        weaknesses = []
        suggestions = []

        # Overall assessment
        overall_score = dimensions.overall_score()
        if overall_score >= 0.9:
            feedback.append("Excellent solution! 🎉")
        elif overall_score >= 0.7:
            feedback.append("Good solution with room for improvement. 👍")
        elif overall_score >= 0.5:
            feedback.append("Partially correct solution. 📝")
        else:
            feedback.append("Solution needs significant improvement. 🔄")

        # Dimension-specific feedback
        if dimensions.syntax_score >= 0.8:
            strengths.append("Code syntax is correct and well-structured")
        elif dimensions.syntax_score < 0.5:
            weaknesses.append("Code has syntax errors")
            suggestions.append("Fix syntax errors before testing")

        if dimensions.accuracy_score >= 0.9:
            strengths.append("Solution produces the correct result")
        elif dimensions.accuracy_score < 0.5:
            weaknesses.append("Solution does not produce the expected result")
            suggestions.append("Review the algorithm logic and test with sample inputs")

        if dimensions.completeness_score >= 0.8:
            strengths.append("Response addresses all requirements")
        elif dimensions.completeness_score < 0.5:
            weaknesses.append("Response missing key requirements")
            suggestions.append("Ensure all requirements from the problem statement are addressed")

        if dimensions.logic_score >= 0.8:
            strengths.append("Logical reasoning is sound")
        elif dimensions.logic_score < 0.5:
            weaknesses.append("Logical approach needs improvement")
            suggestions.append("Review the problem-solving approach and algorithm choice")

        if dimensions.efficiency_score >= 0.8:
            strengths.append("Solution is efficient and well-optimized")
        elif dimensions.efficiency_score < 0.5:
            weaknesses.append("Solution could be more efficient")
            suggestions.append("Consider time complexity and look for optimization opportunities")

        if dimensions.style_score >= 0.8:
            strengths.append("Code is well-written and readable")
        elif dimensions.style_score < 0.5:
            weaknesses.append("Code style could be improved")
            suggestions.append("Add comments, use descriptive variable names, and follow style guidelines")

        # Execution-specific feedback
        if execution_success:
            strengths.append("Code executes successfully")
            if execution_result == test_case.expected_result:
                strengths.append("Produces the correct expected result")
            else:
                weaknesses.append(f"Expected: {test_case.expected_result}, Got: {execution_result}")
                suggestions.append("Debug the algorithm to match expected output")
        else:
            weaknesses.append("Code execution failed")
            suggestions.append("Fix runtime errors and test the implementation")

        feedback_text = " | ".join(feedback)

        return {
            'feedback': feedback_text,
            'strengths': strengths,
            'weaknesses': weaknesses,
            'suggestions': suggestions
        }

    def _score_generic_response(self, task_id: str, response: str,
                               task_category: TaskCategory = None) -> DetailedScore:
        """Score a response when no specific test case is found"""
        dimensions = ScoringDimensions(
            syntax_score=0.7,
            accuracy_score=0.0,  # Can't validate without expected result
            completeness_score=0.8,
            logic_score=0.7,
            efficiency_score=0.7,
            style_score=0.7
        )

        return DetailedScore(
            task_id=task_id,
            task_category=task_category or TaskCategory.TECHNICAL_EXPLANATION,
            overall_score=0.6,  # Average score
            dimensions=dimensions,
            execution_result=None,
            expected_result=None,
            execution_success=False,
            feedback="Generic evaluation - no specific test case found for validation",
            strengths=["Response provided"],
            weaknesses=["Cannot validate without expected result"],
            suggestions=["Provide a specific test case for accurate evaluation"]
        )

    def batch_score_responses(self, responses: List[Dict[str, Any]]) -> List[DetailedScore]:
        """Score multiple responses in batch"""
        scores = []

        for response_data in responses:
            score = self.score_response(
                task_id=response_data['task_id'],
                llm_response=response_data['response'],
                task_category=TaskCategory(response_data.get('category', 'technical')),
                expected_result=response_data.get('expected_result'),
                test_data=response_data.get('test_data')
            )
            scores.append(score)

        return scores

    def generate_scoring_report(self, scores: List[DetailedScore]) -> Dict[str, Any]:
        """Generate comprehensive scoring report"""
        if not scores:
            return {"error": "No scores to analyze"}

        # Overall statistics
        overall_scores = [s.overall_score for s in scores]
        avg_score = sum(overall_scores) / len(overall_scores)

        # Category breakdown
        category_scores = {}
        for score in scores:
            category = score.task_category.value
            if category not in category_scores:
                category_scores[category] = []
            category_scores[category].append(score.overall_score)

        category_stats = {}
        for category, scores_list in category_scores.items():
            category_stats[category] = {
                'count': len(scores_list),
                'average': sum(scores_list) / len(scores_list),
                'min': min(scores_list),
                'max': max(scores_list)
            }

        # Dimension averages
        dimension_averages = {}
        if scores:
            for dim in ['syntax_score', 'accuracy_score', 'completeness_score',
                       'logic_score', 'efficiency_score', 'style_score']:
                values = [getattr(s.dimensions, dim) for s in scores]
                dimension_averages[dim] = sum(values) / len(values)

        # Success rates
        execution_success_rate = sum(1 for s in scores if s.execution_success) / len(scores)

        return {
            'timestamp': datetime.now().isoformat(),
            'total_responses': len(scores),
            'overall_average_score': avg_score,
            'category_breakdown': category_stats,
            'dimension_averages': dimension_averages,
            'execution_success_rate': execution_success_rate,
            'individual_scores': [
                {
                    'task_id': s.task_id,
                    'category': s.task_category.value,
                    'overall_score': s.overall_score,
                    'execution_success': s.execution_success,
                    'execution_time': s.execution_time,
                    'feedback': s.feedback
                }
                for s in scores
            ]
        }


# Example usage
if __name__ == "__main__":
    scorer = AutomatedScorer()

    # Example LLM response
    example_response = """
    To calculate the area of a triangle, I'll write a Python function:

    ```python
    def calculate_triangle_area(base, height):
        return 0.5 * base * height

    # Example usage
    area = calculate_triangle_area(10, 5)
    print(f"The area is: {area}")
    ```

    This function takes the base and height as parameters and returns the area using the formula: area = 0.5 * base * height.
    """

    # Score the response
    score = scorer.score_response(
        task_id="code_triangle_area",
        llm_response=example_response
    )

    print(f"Task: {score.task_id}")
    print(f"Overall Score: {score.overall_score:.2f}")
    print(f"Execution Success: {score.execution_success}")
    print(f"Feedback: {score.feedback}")
    print(f"Strengths: {', '.join(score.strengths)}")
    if score.weaknesses:
        print(f"Weaknesses: {', '.join(score.weaknesses)}")
    if score.suggestions:
        print(f"Suggestions: {', '.join(score.suggestions)}")