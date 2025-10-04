# File: response_evaluator.py
# Path: /home/herb/Desktop/LLM-Tester/response_evaluator.py
# Standard: AIDEV-PascalCase-2.1
# Created: 2025-10-01
# Last Modified: 2025-10-01 8:15PM

"""
Response Quality Evaluator for LLM Parameter Comparison

This module provides tools to evaluate and score LLM responses across different
parameter configurations. It includes both automated metrics and human evaluation
frameworks.

Evaluation Categories:
1. Code Quality: Syntax correctness, logic, best practices
2. Accuracy: Factual correctness and problem-solving accuracy
3. Completeness: How well the response addresses all aspects of the prompt
4. Clarity: Readability, organization, and explanation quality
5. Creativity: Originality and novel approaches (for creative tasks)
"""

import re
import ast
import json
import time
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
from enum import Enum


class ResponseType(Enum):
    """Types of responses to evaluate differently"""
    CODE_GENERATION = "code"
    MATHEMATICAL = "math"
    CREATIVE_WRITING = "creative"
    TECHNICAL_EXPLANATION = "technical"
    LOGICAL_REASONING = "reasoning"
    UNKNOWN = "unknown"


@dataclass
class ResponseEvaluation:
    """Complete evaluation of a single response"""
    test_id: str
    model_name: str
    parameters: Dict[str, Any]
    prompt: str
    response: str
    response_type: ResponseType

    # Automated scores (0-10)
    syntax_score: float
    accuracy_score: float
    completeness_score: float
    clarity_score: float

    # Overall score (weighted average)
    overall_score: float

    # Detailed feedback
    feedback: Dict[str, str]
    issues_found: List[str]
    strengths: List[str]

    # Metadata
    evaluation_timestamp: str
    response_length: int
    execution_time: float


class ResponseEvaluator:
    """Main evaluator class for LLM responses"""

    def __init__(self):
        self.evaluation_results = []
        self.evaluation_criteria = {
            ResponseType.CODE_GENERATION: {
                'syntax': 0.3,
                'logic': 0.4,
                'completeness': 0.2,
                'clarity': 0.1
            },
            ResponseType.MATHEMATICAL: {
                'accuracy': 0.5,
                'method': 0.2,
                'completeness': 0.2,
                'clarity': 0.1
            },
            ResponseType.CREATIVE_WRITING: {
                'creativity': 0.4,
                'coherence': 0.3,
                'engagement': 0.2,
                'clarity': 0.1
            },
            ResponseType.TECHNICAL_EXPLANATION: {
                'accuracy': 0.4,
                'completeness': 0.3,
                'clarity': 0.2,
                'organization': 0.1
            },
            ResponseType.LOGICAL_REASONING: {
                'logic': 0.5,
                'accuracy': 0.3,
                'clarity': 0.2
            }
        }

    def classify_response_type(self, prompt: str, response: str) -> ResponseType:
        """Classify the type of response based on prompt and content"""
        prompt_lower = prompt.lower()
        response_lower = response.lower()

        # Code generation indicators
        if (any(keyword in prompt_lower for keyword in ['function', 'code', 'python', 'program', 'implement']) or
            '```python' in response_lower or 'def ' in response_lower or 'import ' in response_lower):
            return ResponseType.CODE_GENERATION

        # Mathematical indicators
        if (any(keyword in prompt_lower for keyword in ['calculate', 'area', 'formula', 'radius', 'triangle', 'circle']) or
            any(symbol in response for symbol in ['π', 'pi', '²', '^2', '=', '+', '-', '*', '/'])):
            return ResponseType.MATHEMATICAL

        # Creative writing indicators
        if (any(keyword in prompt_lower for keyword in ['story', 'poem', 'creative', 'imagine', 'describe']) or
            any(keyword in response_lower for keyword in ['once upon', 'imagined', 'character', 'narrative'])):
            return ResponseType.CREATIVE_WRITING

        # Technical explanation indicators
        if (any(keyword in prompt_lower for keyword in ['explain', 'how', 'what is', 'describe', 'compare']) and
            any(keyword in response_lower for keyword in ['works', 'process', 'method', 'approach', 'algorithm'])):
            return ResponseType.TECHNICAL_EXPLANATION

        # Logical reasoning indicators
        if (any(keyword in prompt_lower for keyword in ['solve', 'logic', 'puzzle', 'reasoning', 'problem']) or
            any(keyword in response_lower for keyword in ['therefore', 'because', 'since', 'thus', 'conclusion'])):
            return ResponseType.LOGICAL_REASONING

        return ResponseType.UNKNOWN

    def evaluate_code_response(self, response: str) -> Tuple[float, Dict[str, str], List[str], List[str]]:
        """Evaluate a code generation response"""
        syntax_score = 0.0
        logic_score = 0.0
        completeness_score = 0.0
        clarity_score = 0.0

        feedback = {}
        issues = []
        strengths = []

        # Extract code blocks
        code_blocks = re.findall(r'```(?:python)?\s*\n(.*?)\n```', response, re.DOTALL)
        if not code_blocks:
            # Try alternative code block detection
            code_blocks = re.findall(r'(def\s+\w+.*?(?:\n\ndef|\Z))', response, re.DOTALL)

        if not code_blocks:
            issues.append("No clear code blocks found")
            syntax_score = 2.0
        else:
            # Evaluate syntax of each code block
            valid_blocks = 0
            for i, code in enumerate(code_blocks):
                try:
                    ast.parse(code.strip())
                    valid_blocks += 1
                    strengths.append(f"Code block {i+1} has valid Python syntax")
                except SyntaxError as e:
                    issues.append(f"Syntax error in code block {i+1}: {str(e)}")

            syntax_score = (valid_blocks / len(code_blocks)) * 10.0
            feedback['code_blocks'] = f"{valid_blocks}/{len(code_blocks)} valid blocks"

        # Check for function definitions
        has_function = any('def ' in block for block in code_blocks)
        if has_function:
            strengths.append("Contains function definitions")
            logic_score += 2.0

        # Check for proper docstrings
        has_docstring = any('"""' in block or "'''" in block for block in code_blocks)
        if has_docstring:
            strengths.append("Includes docstrings")
            clarity_score += 1.0

        # Check for input/output examples
        has_examples = any('input(' in block or 'print(' in block for block in code_blocks)
        if has_examples:
            strengths.append("Includes input/output examples")
            completeness_score += 2.0

        # Check for error handling
        has_error_handling = any('try:' in block or 'if' in block for block in code_blocks)
        if has_error_handling:
            strengths.append("Includes error handling")
            logic_score += 1.0

        # Calculate overall scores
        logic_score = min(10.0, logic_score + 5.0)  # Base 5 + bonuses
        completeness_score = min(10.0, completeness_score + 6.0)  # Base 6 + bonuses
        clarity_score = min(10.0, clarity_score + 6.0)  # Base 6 + bonuses

        # General clarity assessment
        if len(response) > 500:
            clarity_score += 1.0
            strengths.append("Detailed explanation provided")
        elif len(response) < 100:
            clarity_score -= 2.0
            issues.append("Very brief response, lacks explanation")

        overall_score = (syntax_score * 0.3 + logic_score * 0.4 +
                        completeness_score * 0.2 + clarity_score * 0.1)

        feedback.update({
            'syntax_score': f"{syntax_score:.1f}/10",
            'logic_score': f"{logic_score:.1f}/10",
            'completeness_score': f"{completeness_score:.1f}/10",
            'clarity_score': f"{clarity_score:.1f}/10"
        })

        return overall_score, feedback, issues, strengths

    def evaluate_math_response(self, response: str) -> Tuple[float, Dict[str, str], List[str], List[str]]:
        """Evaluate a mathematical problem-solving response"""
        accuracy_score = 0.0
        method_score = 0.0
        completeness_score = 0.0
        clarity_score = 0.0

        feedback = {}
        issues = []
        strengths = []

        # Check for formula mention
        if 'formula' in response.lower() or '=' in response:
            strengths.append("Mentions formula")
            method_score += 2.0

        # Check for mathematical operations
        math_operations = sum(response.count(op) for op in ['+', '-', '*', '/', '^'])
        if math_operations > 0:
            strengths.append(f"Shows {math_operations} mathematical operations")
            method_score += min(3.0, math_operations)

        # Check for π usage in circle problems
        if any(pi_var in response for pi_var in ['π', 'math.pi', '3.14', '3.14159']):
            strengths.append("Uses π correctly")
            accuracy_score += 2.0

        # Check for step-by-step explanation
        step_indicators = ['step', 'first', 'second', 'third', 'next', 'then', 'finally']
        step_count = sum(response.lower().count(step) for step in step_indicators)
        if step_count >= 2:
            strengths.append("Provides step-by-step solution")
            clarity_score += 2.0
            completeness_score += 2.0

        # Check for final answer
        if any(indicator in response.lower() for indicator in ['answer', 'result', 'solution', '=']):
            strengths.append("Provides final answer")
            completeness_score += 2.0
        else:
            issues.append("No clear final answer provided")

        # Check for units
        if any(unit in response for unit in ['cm', 'm', 'units', 'square', 'cubic']):
            strengths.append("Includes units")
            accuracy_score += 1.0

        # General completeness
        if len(response) > 200:
            completeness_score += 1.0
        elif len(response) < 50:
            issues.append("Very brief response")
            completeness_score -= 2.0

        # Calculate scores
        accuracy_score = min(10.0, accuracy_score + 5.0)
        method_score = min(10.0, method_score + 4.0)
        completeness_score = min(10.0, completeness_score + 5.0)
        clarity_score = min(10.0, clarity_score + 6.0)

        overall_score = (accuracy_score * 0.5 + method_score * 0.2 +
                        completeness_score * 0.2 + clarity_score * 0.1)

        feedback.update({
            'accuracy_score': f"{accuracy_score:.1f}/10",
            'method_score': f"{method_score:.1f}/10",
            'completeness_score': f"{completeness_score:.1f}/10",
            'clarity_score': f"{clarity_score:.1f}/10"
        })

        return overall_score, feedback, issues, strengths

    def evaluate_creative_response(self, response: str) -> Tuple[float, Dict[str, str], List[str], List[str]]:
        """Evaluate a creative writing response"""
        creativity_score = 0.0
        coherence_score = 0.0
        engagement_score = 0.0
        clarity_score = 0.0

        feedback = {}
        issues = []
        strengths = []

        # Vocabulary diversity
        words = re.findall(r'\b\w+\b', response.lower())
        unique_words = set(words)
        if len(words) > 0:
            diversity_ratio = len(unique_words) / len(words)
            if diversity_ratio > 0.7:
                strengths.append("Good vocabulary diversity")
                creativity_score += 2.0
            elif diversity_ratio < 0.4:
                issues.append("Limited vocabulary diversity")
                creativity_score -= 1.0

        # Sentence structure variety
        sentences = re.split(r'[.!?]+', response)
        sentences = [s.strip() for s in sentences if s.strip()]
        if len(sentences) > 1:
            sentence_lengths = [len(s.split()) for s in sentences]
            length_variance = max(sentence_lengths) - min(sentence_lengths) if len(sentence_lengths) > 1 else 0
            if length_variance > 3:
                strengths.append("Varied sentence structure")
                clarity_score += 1.0

        # Length and completeness
        if len(response) > 300:
            strengths.append("Well-developed content")
            coherence_score += 2.0
        elif len(response) < 100:
            issues.append("Very brief creative content")
            coherence_score -= 2.0

        # Figurative language
        figurative_indicators = ['like', 'as', 'metaphor', 'simile', 'imagine', 'picture', 'vivid']
        figurative_count = sum(response.lower().count(indicator) for indicator in figurative_indicators)
        if figurative_count > 0:
            strengths.append("Uses figurative language")
            creativity_score += min(2.0, figurative_count)

        # General engagement indicators
        if any(word in response.lower() for word in ['imagine', 'picture', 'envision', 'experience']):
            engagement_score += 2.0
            strengths.append("Engaging and immersive")

        # Calculate scores
        creativity_score = min(10.0, creativity_score + 5.0)
        coherence_score = min(10.0, coherence_score + 6.0)
        engagement_score = min(10.0, engagement_score + 6.0)
        clarity_score = min(10.0, clarity_score + 7.0)

        overall_score = (creativity_score * 0.4 + coherence_score * 0.3 +
                        engagement_score * 0.2 + clarity_score * 0.1)

        feedback.update({
            'creativity_score': f"{creativity_score:.1f}/10",
            'coherence_score': f"{coherence_score:.1f}/10",
            'engagement_score': f"{engagement_score:.1f}/10",
            'clarity_score': f"{clarity_score:.1f}/10"
        })

        return overall_score, feedback, issues, strengths

    def evaluate_technical_response(self, response: str) -> Tuple[float, Dict[str, str], List[str], List[str]]:
        """Evaluate a technical explanation response"""
        accuracy_score = 0.0
        completeness_score = 0.0
        clarity_score = 0.0
        organization_score = 0.0

        feedback = {}
        issues = []
        strengths = []

        # Check for structured explanation
        structure_indicators = ['first', 'second', 'third', 'step', 'process', 'method']
        structure_count = sum(response.lower().count(indicator) for indicator in structure_indicators)
        if structure_count >= 2:
            strengths.append("Well-structured explanation")
            organization_score += 3.0

        # Check for examples
        if 'example' in response.lower() or 'for instance' in response.lower():
            strengths.append("Includes examples")
            completeness_score += 2.0

        # Check for technical terms
        technical_terms = ['algorithm', 'process', 'system', 'method', 'technique', 'approach']
        tech_count = sum(response.lower().count(term) for term in technical_terms)
        if tech_count > 0:
            strengths.append("Uses appropriate technical terminology")
            accuracy_score += min(2.0, tech_count)

        # Length and detail
        if len(response) > 400:
            strengths.append("Detailed explanation")
            completeness_score += 2.0
        elif len(response) < 100:
            issues.append("Very brief explanation")
            completeness_score -= 3.0

        # Clarity indicators
        if any(word in response.lower() for word in ['clearly', 'simply', 'easy', 'understand']):
            clarity_score += 1.0

        # Check for organization (lists, numbered points)
        if re.search(r'\d+\.', response) or re.search(r'[-*]', response):
            strengths.append("Uses lists or numbered points")
            organization_score += 2.0

        # Calculate scores
        accuracy_score = min(10.0, accuracy_score + 6.0)
        completeness_score = min(10.0, completeness_score + 6.0)
        clarity_score = min(10.0, clarity_score + 7.0)
        organization_score = min(10.0, organization_score + 5.0)

        overall_score = (accuracy_score * 0.4 + completeness_score * 0.3 +
                        clarity_score * 0.2 + organization_score * 0.1)

        feedback.update({
            'accuracy_score': f"{accuracy_score:.1f}/10",
            'completeness_score': f"{completeness_score:.1f}/10",
            'clarity_score': f"{clarity_score:.1f}/10",
            'organization_score': f"{organization_score:.1f}/10"
        })

        return overall_score, feedback, issues, strengths

    def evaluate_logical_response(self, response: str) -> Tuple[float, Dict[str, str], List[str], List[str]]:
        """Evaluate a logical reasoning response"""
        logic_score = 0.0
        accuracy_score = 0.0
        clarity_score = 0.0

        feedback = {}
        issues = []
        strengths = []

        # Check for logical connectors
        logical_connectors = ['therefore', 'because', 'since', 'thus', 'consequently', 'however', 'moreover']
        connector_count = sum(response.lower().count(connector) for connector in logical_connectors)
        if connector_count >= 2:
            strengths.append("Uses logical connectors")
            logic_score += min(3.0, connector_count)

        # Check for step-by-step reasoning
        if any(word in response.lower() for word in ['step', 'first', 'then', 'next', 'finally']):
            strengths.append("Provides step-by-step reasoning")
            logic_score += 2.0

        # Check for conclusion
        if any(word in response.lower() for word in ['conclusion', 'therefore', 'thus', 'answer', 'result']):
            strengths.append("Reaches clear conclusion")
            accuracy_score += 2.0
        else:
            issues.append("No clear conclusion provided")

        # Check for explanation of reasoning
        if 'explain' in response.lower() or 'reason' in response.lower():
            strengths.append("Explains reasoning process")
            clarity_score += 2.0

        # Length assessment
        if len(response) > 200:
            strengths.append("Detailed reasoning")
            accuracy_score += 1.0
        elif len(response) < 50:
            issues.append("Very brief reasoning")
            logic_score -= 2.0

        # Calculate scores
        logic_score = min(10.0, logic_score + 5.0)
        accuracy_score = min(10.0, accuracy_score + 6.0)
        clarity_score = min(10.0, clarity_score + 6.0)

        overall_score = (logic_score * 0.5 + accuracy_score * 0.3 + clarity_score * 0.2)

        feedback.update({
            'logic_score': f"{logic_score:.1f}/10",
            'accuracy_score': f"{accuracy_score:.1f}/10",
            'clarity_score': f"{clarity_score:.1f}/10"
        })

        return overall_score, feedback, issues, strengths

    def evaluate_response(self, test_id: str, model_name: str, parameters: Dict[str, Any],
                         prompt: str, response: str, execution_time: float = 0.0) -> ResponseEvaluation:
        """Main evaluation method that routes to appropriate evaluator"""

        response_type = self.classify_response_type(prompt, response)

        if response_type == ResponseType.CODE_GENERATION:
            overall_score, feedback, issues, strengths = self.evaluate_code_response(response)
        elif response_type == ResponseType.MATHEMATICAL:
            overall_score, feedback, issues, strengths = self.evaluate_math_response(response)
        elif response_type == ResponseType.CREATIVE_WRITING:
            overall_score, feedback, issues, strengths = self.evaluate_creative_response(response)
        elif response_type == ResponseType.TECHNICAL_EXPLANATION:
            overall_score, feedback, issues, strengths = self.evaluate_technical_response(response)
        elif response_type == ResponseType.LOGICAL_REASONING:
            overall_score, feedback, issues, strengths = self.evaluate_logical_response(response)
        else:
            # Default evaluation for unknown types
            overall_score = 5.0  # Neutral score
            feedback = {'note': 'Unknown response type, default score assigned'}
            issues = ['Could not classify response type']
            strengths = []

        evaluation = ResponseEvaluation(
            test_id=test_id,
            model_name=model_name,
            parameters=parameters,
            prompt=prompt,
            response=response,
            response_type=response_type,
            syntax_score=feedback.get('syntax_score', 5.0),
            accuracy_score=feedback.get('accuracy_score', 5.0),
            completeness_score=feedback.get('completeness_score', 5.0),
            clarity_score=feedback.get('clarity_score', 5.0),
            overall_score=overall_score,
            feedback=feedback,
            issues_found=issues,
            strengths=strengths,
            evaluation_timestamp=datetime.now().isoformat(),
            response_length=len(response),
            execution_time=execution_time
        )

        self.evaluation_results.append(evaluation)
        return evaluation

    def get_summary_statistics(self) -> Dict[str, Any]:
        """Get summary statistics for all evaluated responses"""
        if not self.evaluation_results:
            return {"error": "No evaluations available"}

        # Group by model and parameters
        model_stats = {}
        type_stats = {}

        for eval_result in self.evaluation_results:
            model_key = eval_result.model_name
            type_key = eval_result.response_type.value

            # Model statistics
            if model_key not in model_stats:
                model_stats[model_key] = {
                    'count': 0,
                    'scores': [],
                    'types': {}
                }

            model_stats[model_key]['count'] += 1
            model_stats[model_key]['scores'].append(eval_result.overall_score)

            if type_key not in model_stats[model_key]['types']:
                model_stats[model_key]['types'][type_key] = []
            model_stats[model_key]['types'][type_key].append(eval_result.overall_score)

            # Type statistics
            if type_key not in type_stats:
                type_stats[type_key] = {
                    'count': 0,
                    'scores': []
                }

            type_stats[type_key]['count'] += 1
            type_stats[type_key]['scores'].append(eval_result.overall_score)

        # Calculate averages
        for model in model_stats:
            scores = model_stats[model]['scores']
            model_stats[model]['average_score'] = sum(scores) / len(scores)
            model_stats[model]['min_score'] = min(scores)
            model_stats[model]['max_score'] = max(scores)

            for type_key in model_stats[model]['types']:
                type_scores = model_stats[model]['types'][type_key]
                model_stats[model]['types'][type_key] = {
                    'count': len(type_scores),
                    'average': sum(type_scores) / len(type_scores)
                }

        for type_key in type_stats:
            scores = type_stats[type_key]['scores']
            type_stats[type_key]['average_score'] = sum(scores) / len(scores)
            type_stats[type_key]['min_score'] = min(scores)
            type_stats[type_key]['max_score'] = max(scores)

        return {
            'total_evaluations': len(self.evaluation_results),
            'model_statistics': model_stats,
            'type_statistics': type_stats,
            'evaluation_timestamp': datetime.now().isoformat()
        }

    def export_evaluations(self, filename: str):
        """Export evaluations to JSON file"""
        export_data = {
            'summary': self.get_summary_statistics(),
            'evaluations': [
                {
                    'test_id': e.test_id,
                    'model_name': e.model_name,
                    'parameters': e.parameters,
                    'response_type': e.response_type.value,
                    'overall_score': e.overall_score,
                    'syntax_score': e.syntax_score,
                    'accuracy_score': e.accuracy_score,
                    'completeness_score': e.completeness_score,
                    'clarity_score': e.clarity_score,
                    'feedback': e.feedback,
                    'issues_found': e.issues_found,
                    'strengths': e.strengths,
                    'response_length': e.response_length,
                    'execution_time': e.execution_time,
                    'evaluation_timestamp': e.evaluation_timestamp
                }
                for e in self.evaluation_results
            ]
        }

        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2)

        print(f"Evaluations exported to {filename}")


# Example usage
if __name__ == "__main__":
    evaluator = ResponseEvaluator()

    # Example evaluation
    test_response = """```python
def calculate_triangle_area(base, height):
    return 0.5 * base * height

# Example usage
area = calculate_triangle_area(10, 5)
print(f"The area is: {area}")
```"""

    result = evaluator.evaluate_response(
        test_id="test_001",
        model_name="test_model",
        parameters={"temperature": 0.7},
        prompt="Create a function to calculate the area of a triangle given base and height.",
        response=test_response
    )

    print(f"Overall Score: {result.overall_score:.1f}/10")
    print(f"Response Type: {result.response_type.value}")
    print(f"Strengths: {result.strengths}")
    print(f"Issues: {result.issues_found}")