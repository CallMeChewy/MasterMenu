# File: logical_validation_framework.py
# Path: /home/herb/Desktop/LLM-Tester/logical_validation_framework.py
# Standard: AIDEV-PascalCase-2.1
# Created: 2025-10-01
# Last Modified: 2025-10-01 10:35PM

"""
Logical Reasoning Validation Framework

This framework provides specialized validation for logical reasoning problems,
including puzzles, deductive reasoning, and pattern recognition tasks.

Features:
- Logical consistency checking
- Deductive reasoning validation
- Pattern recognition testing
- Formal logic evaluation
- Step-by-step reasoning analysis
"""

import re
import ast
import json
import math
from typing import Dict, Any, List, Tuple, Optional, Union
from dataclasses import dataclass
from enum import Enum
from datetime import datetime


class LogicType(Enum):
    """Types of logical reasoning problems"""
    DEDUCTIVE = "deductive"         # Deductive reasoning (if A then B)
    INDUCTIVE = "inductive"         # Inductive reasoning (pattern recognition)
    ABDUCTIVE = "abductive"         # Abductive reasoning (best explanation)
    MATHEMATICAL = "mathematical"   # Mathematical logic
    SPATIAL = "spatial"            # Spatial reasoning
    CAUSAL = "causal"              # Causal reasoning
    CONDITIONAL = "conditional"     # Conditional statements


@dataclass
class LogicalValidationResult:
    """Result of logical reasoning validation"""
    problem_id: str
    logic_type: LogicType
    is_valid: bool
    confidence: float
    reasoning_score: float
    conclusion_correct: bool
    steps_valid: List[bool]
    feedback: str
    logical_errors: List[str]
    suggestions: List[str]


class LogicalValidator:
    """Specialized validator for logical reasoning problems"""

    def __init__(self):
        self.validation_rules = self._initialize_validation_rules()

    def _initialize_validation_rules(self) -> Dict[str, Any]:
        """Initialize validation rules for different logic types"""
        return {
            LogicType.DEDUCTIVE: {
                'required_elements': ['premise', 'conclusion', 'reasoning'],
                'valid_connectors': ['therefore', 'thus', 'hence', 'so', 'consequently'],
                'logical_patterns': [
                    r'if.*then.*therefore',
                    r'since.*therefore',
                    r'because.*thus'
                ]
            },
            LogicType.INDUCTIVE: {
                'required_elements': ['pattern', 'observation', 'generalization'],
                'pattern_indicators': ['pattern', 'sequence', 'trend', 'regularity'],
                'generalization_words': ['therefore', 'thus', 'in general', 'usually']
            },
            LogicType.MATHEMATICAL: {
                'required_elements': ['formula', 'calculation', 'result'],
                'math_indicators': ['equals', 'calculate', 'formula', 'equation'],
                'valid_operators': ['+', '-', '*', '/', '=', '<', '>']
            },
            LogicType.SPATIAL: {
                'required_elements': ['spatial_relationship', 'position', 'orientation'],
                'spatial_words': ['above', 'below', 'left', 'right', 'north', 'south'],
                'relationship_words': ['adjacent', 'opposite', 'parallel', 'perpendicular']
            }
        }

    def validate_logical_reasoning(self, problem_id: str, response: str,
                                 logic_type: LogicType,
                                 expected_conclusion: Any = None,
                                 premises: List[str] = None) -> LogicalValidationResult:
        """
        Validate logical reasoning in a response

        Args:
            problem_id: Identifier for the logical problem
            response: The LLM's response text
            logic_type: Type of logical reasoning
            expected_conclusion: Expected correct conclusion (if available)
            premises: Given premises for the problem

        Returns:
            LogicalValidationResult with detailed analysis
        """
        # Extract reasoning components
        reasoning_components = self._extract_reasoning_components(response, logic_type)

        # Validate logical structure
        structure_valid = self._validate_logical_structure(response, logic_type)

        # Check reasoning steps
        steps_analysis = self._analyze_reasoning_steps(response, logic_type)

        # Validate conclusion
        conclusion_analysis = self._validate_conclusion(
            response, expected_conclusion, logic_type, premises
        )

        # Calculate overall scores
        reasoning_score = self._calculate_reasoning_score(
            reasoning_components, structure_valid, steps_analysis, conclusion_analysis
        )

        # Identify logical errors
        logical_errors = self._identify_logical_errors(response, logic_type)

        # Generate feedback and suggestions
        feedback, suggestions = self._generate_logical_feedback(
            reasoning_score, logical_errors, logic_type, reasoning_components
        )

        # Overall validity
        is_valid = (structure_valid and
                   conclusion_analysis['correct'] and
                   len(logical_errors) == 0 and
                   reasoning_score >= 0.7)

        return LogicalValidationResult(
            problem_id=problem_id,
            logic_type=logic_type,
            is_valid=is_valid,
            confidence=reasoning_score,
            reasoning_score=reasoning_score,
            conclusion_correct=conclusion_analysis['correct'],
            steps_valid=steps_analysis['valid_steps'],
            feedback=feedback,
            logical_errors=logical_errors,
            suggestions=suggestions
        )

    def _extract_reasoning_components(self, response: str, logic_type: LogicType) -> Dict[str, Any]:
        """Extract key reasoning components from response"""
        components = {
            'has_premises': False,
            'has_conclusion': False,
            'has_reasoning': False,
            'has_examples': False,
            'has_counterexamples': False,
            'premises': [],
            'conclusions': [],
            'reasoning_steps': []
        }

        response_lower = response.lower()

        # Extract premises (given statements)
        premise_indicators = ['given', 'assume', 'suppose', 'we know that', 'since', 'because']
        for indicator in premise_indicators:
            pattern = f'{indicator}.*?[.!?]'
            matches = re.findall(pattern, response_lower, re.IGNORECASE)
            components['premises'].extend(matches)

        if components['premises']:
            components['has_premises'] = True

        # Extract conclusions
        conclusion_indicators = ['therefore', 'thus', 'hence', 'so', 'consequently', 'in conclusion']
        for indicator in conclusion_indicators:
            pattern = f'{indicator}.*?[.!?]'
            matches = re.findall(pattern, response_lower, re.IGNORECASE)
            components['conclusions'].extend(matches)

        if components['conclusions']:
            components['has_conclusion'] = True

        # Extract reasoning steps
        step_indicators = ['first', 'second', 'then', 'next', 'finally', 'step']
        for indicator in step_indicators:
            pattern = f'{indicator}.*?[.!?]'
            matches = re.findall(pattern, response_lower, re.IGNORECASE)
            components['reasoning_steps'].extend(matches)

        if components['reasoning_steps']:
            components['has_reasoning'] = True

        # Check for examples
        example_indicators = ['for example', 'for instance', 'such as']
        components['has_examples'] = any(indicator in response_lower for indicator in example_indicators)

        return components

    def _validate_logical_structure(self, response: str, logic_type: LogicType) -> bool:
        """Validate the logical structure of the response"""
        if logic_type not in self.validation_rules:
            return True  # Default to valid if no specific rules

        rules = self.validation_rules[logic_type]
        response_lower = response.lower()

        # Check for required elements
        if 'required_elements' in rules:
            for element in rules['required_elements']:
                if element == 'premise' and not any(word in response_lower for word in ['given', 'assume', 'since']):
                    return False
                elif element == 'conclusion' and not any(word in response_lower for word in ['therefore', 'thus', 'hence']):
                    return False
                elif element == 'reasoning' and not any(word in response_lower for word in ['because', 'reason', 'step']):
                    return False

        # Check for valid logical connectors
        if 'valid_connectors' in rules:
            has_connector = any(connector in response_lower for connector in rules['valid_connectors'])
            if not has_connector:
                return False

        # Check logical patterns
        if 'logical_patterns' in rules:
            has_pattern = any(re.search(pattern, response_lower, re.IGNORECASE)
                            for pattern in rules['logical_patterns'])
            if not has_pattern:
                return False

        return True

    def _analyze_reasoning_steps(self, response: str, logic_type: LogicType) -> Dict[str, Any]:
        """Analyze the reasoning steps in the response"""
        steps_analysis = {
            'valid_steps': [],
            'invalid_steps': [],
            'step_count': 0,
            'logical_flow': True
        }

        # Extract step indicators
        step_patterns = [
            r'(?:first|step\s*1|initially)[^.!?]*[.!?]',
            r'(?:second|step\s*2|then|next)[^.!?]*[.!?]',
            r'(?:third|step\s*3|finally|last)[^.!?]*[.!?]'
        ]

        for i, pattern in enumerate(step_patterns):
            matches = re.findall(pattern, response, re.IGNORECASE)
            for match in matches:
                steps_analysis['step_count'] += 1
                # Simple validation: check if step contains reasoning
                step_valid = len(match.strip()) > 10  # Minimum length check
                if step_valid:
                    steps_analysis['valid_steps'].append(True)
                else:
                    steps_analysis['invalid_steps'].append(match)

        # Check logical flow (simplified)
        if steps_analysis['step_count'] > 1:
            # Check if steps are in reasonable order
            order_indicators = ['first', 'second', 'third', 'then', 'next', 'finally']
            response_lower = response.lower()
            order_count = sum(1 for indicator in order_indicators if indicator in response_lower)
            steps_analysis['logical_flow'] = order_count >= min(2, steps_analysis['step_count'])

        return steps_analysis

    def _validate_conclusion(self, response: str, expected_conclusion: Any,
                           logic_type: LogicType, premises: List[str] = None) -> Dict[str, Any]:
        """Validate the conclusion against expected result"""
        conclusion_analysis = {
            'correct': False,
            'extracted_conclusion': None,
            'confidence': 0.0
        }

        # Extract conclusion from response
        conclusion_patterns = [
            r'(?:therefore|thus|hence|so|consequently)[^.!?]*([^.!?]*)',
            r'(?:answer|result|solution)[^.!?]*([^.!?]*)',
            r'(?:the\s+)?answer\s+is[:\s]+([^.!?]*)'
        ]

        for pattern in conclusion_patterns:
            matches = re.findall(pattern, response, re.IGNORECASE)
            if matches:
                conclusion_analysis['extracted_conclusion'] = matches[0].strip()
                break

        # If we have an expected conclusion, compare it
        if expected_conclusion is not None and conclusion_analysis['extracted_conclusion']:
            conclusion_analysis['correct'] = self._compare_conclusions(
                conclusion_analysis['extracted_conclusion'], expected_conclusion, logic_type
            )

            if conclusion_analysis['correct']:
                conclusion_analysis['confidence'] = 0.9
            else:
                conclusion_analysis['confidence'] = 0.3

        return conclusion_analysis

    def _compare_conclusions(self, extracted: str, expected: Any, logic_type: LogicType) -> bool:
        """Compare extracted conclusion with expected result"""
        extracted = extracted.lower().strip()

        # Convert expected to string for comparison
        expected_str = str(expected).lower()

        # Direct string comparison
        if extracted == expected_str:
            return True

        # Check if expected is contained in extracted
        if expected_str in extracted or extracted in expected_str:
            return True

        # Numerical comparison for mathematical logic
        if logic_type == LogicType.MATHEMATICAL:
            try:
                # Extract numbers
                extracted_num = re.findall(r'[0-9]+\.?[0-9]*', extracted)
                expected_num = re.findall(r'[0-9]+\.?[0-9]*', expected_str)
                if extracted_num and expected_num:
                    return float(extracted_num[0]) == float(expected_num[0])
            except ValueError:
                pass

        # Boolean comparison
        if isinstance(expected, bool):
            true_indicators = ['true', 'yes', 'correct', 'valid']
            false_indicators = ['false', 'no', 'incorrect', 'invalid']

            if expected and any(indicator in extracted for indicator in true_indicators):
                return True
            elif not expected and any(indicator in extracted for indicator in false_indicators):
                return True

        return False

    def _calculate_reasoning_score(self, components: Dict[str, Any],
                                 structure_valid: bool, steps_analysis: Dict[str, Any],
                                 conclusion_analysis: Dict[str, Any]) -> float:
        """Calculate overall reasoning score"""
        score = 0.0

        # Component scoring (0.3)
        component_score = 0.0
        if components['has_premises']:
            component_score += 0.1
        if components['has_conclusion']:
            component_score += 0.1
        if components['has_reasoning']:
            component_score += 0.1
        score += component_score

        # Structure scoring (0.2)
        if structure_valid:
            score += 0.2

        # Steps scoring (0.2)
        if steps_analysis['step_count'] > 0:
            step_score = min(1.0, len(steps_analysis['valid_steps']) / max(1, steps_analysis['step_count']))
            score += 0.2 * step_score

        # Conclusion scoring (0.3)
        conclusion_score = conclusion_analysis.get('confidence', 0.0)
        score += 0.3 * conclusion_score

        return min(1.0, score)

    def _identify_logical_errors(self, response: str, logic_type: LogicType) -> List[str]:
        """Identify common logical errors"""
        errors = []
        response_lower = response.lower()

        # Common logical fallacies
        fallacy_patterns = {
            'circular_reasoning': [r'because.*therefore.*because', r'since.*thus.*since'],
            'hasty_generalization': [r'all.*always', r'never.*ever', r'every.*always'],
            'false_cause': [r'after.*therefore', r'because.*after'],
            'ad_hominem': [r'you.*stupid', r'your.*wrong.*because'],
            'slippery_slope': [r'will.*lead.*to.*then.*then']
        }

        for fallacy, patterns in fallacy_patterns.items():
            for pattern in patterns:
                if re.search(pattern, response_lower):
                    errors.append(f"Potential {fallacy.replace('_', ' ')}")
                    break

        # Type-specific errors
        if logic_type == LogicType.DEDUCTIVE:
            if 'if' in response_lower and 'then' not in response_lower:
                errors.append("Incomplete conditional reasoning")

        elif logic_type == LogicType.MATHEMATICAL:
            # Check for calculation errors (simplified)
            if 'calculate' in response_lower and '=' not in response_lower:
                errors.append("Missing calculation or result")

        return errors

    def _generate_logical_feedback(self, reasoning_score: float, logical_errors: List[str],
                                 logic_type: LogicType, components: Dict[str, Any]) -> Tuple[str, List[str]]:
        """Generate feedback and suggestions"""
        feedback_parts = []
        suggestions = []

        # Overall assessment
        if reasoning_score >= 0.8:
            feedback_parts.append("Excellent logical reasoning! 🎯")
        elif reasoning_score >= 0.6:
            feedback_parts.append("Good logical reasoning with room for improvement. 👍")
        elif reasoning_score >= 0.4:
            feedback_parts.append("Adequate reasoning but needs work. 📝")
        else:
            feedback_parts.append("Logical reasoning needs significant improvement. 🔄")

        # Specific feedback based on components
        if not components['has_premises']:
            feedback_parts.append("Missing clear premises")
            suggestions.append("Clearly state the given information or assumptions")

        if not components['has_conclusion']:
            feedback_parts.append("Missing clear conclusion")
            suggestions.append("Provide a clear conclusion using words like 'therefore' or 'thus'")

        if not components['has_reasoning']:
            feedback_parts.append("Missing reasoning steps")
            suggestions.append("Show step-by-step reasoning process")

        # Error-specific feedback
        if logical_errors:
            feedback_parts.append(f"Logical issues detected: {', '.join(logical_errors)}")
            suggestions.extend(self._get_error_suggestions(logical_errors))

        # Type-specific suggestions
        if logic_type == LogicType.DEDUCTIVE:
            suggestions.append("Ensure your conclusion logically follows from premises")
        elif logic_type == LogicType.INDUCTIVE:
            suggestions.append("Provide sufficient examples to support generalization")
        elif logic_type == LogicType.MATHEMATICAL:
            suggestions.append("Show calculations and verify results")

        feedback = " | ".join(feedback_parts)
        return feedback, suggestions

    def _get_error_suggestions(self, logical_errors: List[str]) -> List[str]:
        """Get specific suggestions for logical errors"""
        suggestions = []

        for error in logical_errors:
            if 'circular' in error:
                suggestions.append("Avoid using the conclusion as a premise")
            elif 'hasty generalization' in error:
                suggestions.append("Provide more evidence before making general claims")
            elif 'false cause' in error:
                suggestions.append("Distinguish correlation from causation")
            elif 'conditional' in error:
                suggestions.append("Complete conditional statements with 'then' clauses")

        return suggestions

    def batch_validate_logical_responses(self, responses: List[Dict[str, Any]]) -> List[LogicalValidationResult]:
        """Validate multiple logical reasoning responses"""
        results = []

        for response_data in responses:
            result = self.validate_logical_reasoning(
                problem_id=response_data['problem_id'],
                response=response_data['response'],
                logic_type=LogicType(response_data.get('logic_type', 'deductive')),
                expected_conclusion=response_data.get('expected_conclusion'),
                premises=response_data.get('premises')
            )
            results.append(result)

        return results

    def generate_validation_report(self, results: List[LogicalValidationResult]) -> Dict[str, Any]:
        """Generate comprehensive validation report"""
        if not results:
            return {"error": "No validation results to analyze"}

        # Overall statistics
        valid_count = sum(1 for r in results if r.is_valid)
        total_count = len(results)
        avg_reasoning_score = sum(r.reasoning_score for r in results) / total_count

        # Logic type breakdown
        type_stats = {}
        for result in results:
            logic_type = result.logic_type.value
            if logic_type not in type_stats:
                type_stats[logic_type] = {'total': 0, 'valid': 0, 'avg_score': 0.0}

            type_stats[logic_type]['total'] += 1
            if result.is_valid:
                type_stats[logic_type]['valid'] += 1
            type_stats[logic_type]['avg_score'] += result.reasoning_score

        # Calculate averages
        for logic_type, stats in type_stats.items():
            stats['avg_score'] /= stats['total']
            stats['success_rate'] = stats['valid'] / stats['total']

        # Common errors
        all_errors = []
        for result in results:
            all_errors.extend(result.logical_errors)

        error_frequency = {}
        for error in all_errors:
            error_frequency[error] = error_frequency.get(error, 0) + 1

        return {
            'timestamp': datetime.now().isoformat(),
            'total_responses': total_count,
            'valid_responses': valid_count,
            'invalid_responses': total_count - valid_count,
            'overall_success_rate': valid_count / total_count,
            'average_reasoning_score': avg_reasoning_score,
            'logic_type_breakdown': type_stats,
            'common_errors': sorted(error_frequency.items(), key=lambda x: x[1], reverse=True),
            'individual_results': [
                {
                    'problem_id': r.problem_id,
                    'logic_type': r.logic_type.value,
                    'is_valid': r.is_valid,
                    'reasoning_score': r.reasoning_score,
                    'conclusion_correct': r.conclusion_correct,
                    'error_count': len(r.logical_errors)
                }
                for r in results
            ]
        }


# Example usage and test cases
if __name__ == "__main__":
    validator = LogicalValidator()

    # Example logical reasoning response
    example_response = """
    Given that all humans are mortal, and Socrates is a human,
    we can conclude that Socrates is mortal.

    First, we know that all humans are mortal (premise 1).
    Second, we know that Socrates is a human (premise 2).
    Therefore, Socrates must be mortal because he belongs to the group of humans.
    """

    # Validate the response
    result = validator.validate_logical_reasoning(
        problem_id="socrates_mortality",
        response=example_response,
        logic_type=LogicType.DEDUCTIVE,
        expected_conclusion="Socrates is mortal"
    )

    print(f"Problem: {result.problem_id}")
    print(f"Logic Type: {result.logic_type.value}")
    print(f"Is Valid: {result.is_valid}")
    print(f"Reasoning Score: {result.reasoning_score:.2f}")
    print(f"Conclusion Correct: {result.conclusion_correct}")
    print(f"Feedback: {result.feedback}")
    if result.logical_errors:
        print(f"Logical Errors: {', '.join(result.logical_errors)}")
    if result.suggestions:
        print(f"Suggestions: {', '.join(result.suggestions)}")