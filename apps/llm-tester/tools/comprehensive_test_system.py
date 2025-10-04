# File: comprehensive_test_system.py
# Path: /home/herb/Desktop/LLM-Tester/comprehensive_test_system.py
# Standard: AIDEV-PascalCase-2.1
# Created: 2025-10-01
# Last Modified: 2025-10-01 10:40PM

"""
Comprehensive LLM Testing System

This module integrates all testing components into a unified system for evaluating
LLM responses across different task categories with provable solutions.

Components:
- Objective Test Suite (code, math, logic, data processing)
- Automated Scoring System (multi-dimensional evaluation)
- Logical Validation Framework (specialized reasoning validation)
- Parameter Comparison Integration
- Structured Output Support

Features:
- Unified evaluation pipeline
- Comprehensive reporting
- Category-specific analysis
- Statistical validation
- Export capabilities
"""

import json
import csv
import time
import statistics
from typing import Dict, Any, List, Tuple, Optional, Union
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path

from objective_test_suite import ObjectiveTestSuite, TestResult, ProblemType
from automated_scorer import AutomatedScorer, DetailedScore, TaskCategory
from logical_validation_framework import LogicalValidator, LogicalValidationResult, LogicType
from structured_output import StructuredOutputManager, OutputFormat


@dataclass
class ComprehensiveEvaluationResult:
    """Complete evaluation result combining all scoring methods"""
    test_id: str
    task_category: str
    llm_response: str
    expected_result: Any
    objective_result: Optional[TestResult] = None
    detailed_score: Optional[DetailedScore] = None
    logical_validation: Optional[LogicalValidationResult] = None
    structured_output_score: float = 0.0
    overall_performance_score: float = 0.0
    evaluation_timestamp: str = ""
    execution_time: float = 0.0

    def __post_init__(self):
        if not self.evaluation_timestamp:
            self.evaluation_timestamp = datetime.now().isoformat()


class ComprehensiveTestSystem:
    """Unified testing system for comprehensive LLM evaluation"""

    def __init__(self):
        self.objective_suite = ObjectiveTestSuite()
        self.automated_scorer = AutomatedScorer()
        self.logical_validator = LogicalValidator()
        self.structured_output_manager = StructuredOutputManager()
        self.evaluation_results = []

    def evaluate_response(self, test_id: str, llm_response: str,
                         output_format: OutputFormat = OutputFormat.PLAIN_TEXT,
                         expected_result: Any = None,
                         logic_type: LogicType = None) -> ComprehensiveEvaluationResult:
        """
        Comprehensive evaluation of an LLM response

        Args:
            test_id: Identifier for the test case
            llm_response: The LLM's response
            output_format: Format of the response (for structured output evaluation)
            expected_result: Expected correct result
            logic_type: Type of logical reasoning (if applicable)

        Returns:
            ComprehensiveEvaluationResult with all evaluation components
        """
        start_time = time.time()

        # Get test case information
        test_case = None
        for tc in self.objective_suite.test_cases:
            if tc.test_id == test_id:
                test_case = tc
                break

        # Initialize result
        result = ComprehensiveEvaluationResult(
            test_id=test_id,
            task_category=test_case.category.value if test_case else "unknown",
            llm_response=llm_response,
            expected_result=expected_result or (test_case.expected_result if test_case else None)
        )

        # 1. Objective Test Evaluation
        if test_case:
            try:
                result.objective_result = self.objective_suite.evaluate_llm_response(test_id, llm_response)
            except Exception as e:
                print(f"Objective evaluation failed for {test_id}: {e}")

        # 2. Automated Scoring
        try:
            task_category = TaskCategory(test_case.category.value) if test_case else TaskCategory.TECHNICAL_EXPLANATION
            result.detailed_score = self.automated_scorer.score_response(
                task_id=test_id,
                llm_response=llm_response,
                task_category=task_category,
                expected_result=result.expected_result,
                test_data=test_case.test_data if test_case else None
            )
        except Exception as e:
            print(f"Automated scoring failed for {test_id}: {e}")

        # 3. Logical Validation (for reasoning tasks)
        if test_case and test_case.category == ProblemType.LOGICAL_REASONING:
            try:
                result.logical_validation = self.logical_validator.validate_logical_reasoning(
                    problem_id=test_id,
                    response=llm_response,
                    logic_type=logic_type or LogicType.DEDUCTIVE,
                    expected_conclusion=result.expected_result
                )
            except Exception as e:
                print(f"Logical validation failed for {test_id}: {e}")

        # 4. Structured Output Evaluation
        try:
            result.structured_output_score = self._evaluate_structured_output(
                llm_response, output_format
            )
        except Exception as e:
            print(f"Structured output evaluation failed for {test_id}: {e}")

        # 5. Calculate Overall Performance Score
        result.overall_performance_score = self._calculate_overall_score(result)
        result.execution_time = time.time() - start_time

        return result

    def _evaluate_structured_output(self, response: str, format_type: OutputFormat) -> float:
        """Evaluate structured output formatting"""
        if format_type == OutputFormat.PLAIN_TEXT:
            return 0.7  # Neutral score for plain text

        # Try to parse response according to format
        try:
            if format_type == OutputFormat.JSON:
                parsed = json.loads(response)
                # Check for required fields
                required_fields = ['response', 'confidence', 'reasoning']
                score = sum(1 for field in required_fields if field in parsed) / len(required_fields)
                return score

            elif format_type == OutputFormat.XML:
                # Basic XML validation
                if '<' in response and '>' in response:
                    # Check for required XML structure
                    has_root = '<llm_response>' in response or '<response>' in response
                    has_content = '<content>' in response or '<main_response>' in response
                    return 0.8 if (has_root and has_content) else 0.6
                return 0.0

            elif format_type == OutputFormat.YAML:
                # Basic YAML validation (key: value pairs)
                lines = response.strip().split('\n')
                yaml_lines = [line for line in lines if ':' in line and not line.strip().startswith('#')]
                return min(1.0, len(yaml_lines) / 3)  # Expect at least 3 key-value pairs

            elif format_type == OutputFormat.MARKDOWN:
                # Check for Markdown structure
                has_headers = any(line.startswith('#') for line in response.split('\n'))
                has_code = '```' in response
                has_emphasis = ('**' in response) or ('*' in response)
                score = 0.0
                if has_headers:
                    score += 0.4
                if has_code:
                    score += 0.3
                if has_emphasis:
                    score += 0.3
                return score

            elif format_type == OutputFormat.CSV:
                # Check CSV structure
                lines = response.strip().split('\n')
                if len(lines) >= 2:  # Header + at least one data row
                    header_cols = len(lines[0].split(','))
                    data_cols = len(lines[1].split(','))
                    return 1.0 if header_cols == data_cols else 0.7
                return 0.0

        except Exception:
            return 0.0  # Parsing failed

        return 0.5  # Default score

    def _calculate_overall_score(self, result: ComprehensiveEvaluationResult) -> float:
        """Calculate overall performance score from all evaluation components"""
        scores = []
        weights = []

        # Objective test score (weight: 0.3)
        if result.objective_result:
            scores.append(result.objective_result.score)
            weights.append(0.3)

        # Automated scoring (weight: 0.4)
        if result.detailed_score:
            scores.append(result.detailed_score.overall_score)
            weights.append(0.4)

        # Logical validation (weight: 0.2)
        if result.logical_validation:
            scores.append(result.logical_validation.reasoning_score)
            weights.append(0.2)

        # Structured output score (weight: 0.1)
        scores.append(result.structured_output_score)
        weights.append(0.1)

        if not scores:
            return 0.0

        # Calculate weighted average
        weighted_sum = sum(score * weight for score, weight in zip(scores, weights))
        total_weight = sum(weights)

        return weighted_sum / total_weight if total_weight > 0 else 0.0

    def batch_evaluate_responses(self, responses: List[Dict[str, Any]]) -> List[ComprehensiveEvaluationResult]:
        """Evaluate multiple responses in batch"""
        results = []

        for i, response_data in enumerate(responses):
            print(f"Evaluating response {i+1}/{len(responses)}: {response_data.get('test_id', 'unknown')}")

            result = self.evaluate_response(
                test_id=response_data['test_id'],
                llm_response=response_data['response'],
                output_format=OutputFormat(response_data.get('output_format', 'plain_text')),
                expected_result=response_data.get('expected_result'),
                logic_type=LogicType(response_data.get('logic_type', 'deductive')) if response_data.get('logic_type') else None
            )
            results.append(result)

        self.evaluation_results.extend(results)
        return results

    def generate_comprehensive_report(self, results: List[ComprehensiveEvaluationResult] = None) -> Dict[str, Any]:
        """Generate comprehensive evaluation report"""
        if results is None:
            results = self.evaluation_results

        if not results:
            return {"error": "No evaluation results available"}

        # Overall statistics
        overall_scores = [r.overall_performance_score for r in results]
        avg_overall_score = sum(overall_scores) / len(overall_scores)

        # Category breakdown
        category_scores = {}
        for result in results:
            category = result.task_category
            if category not in category_scores:
                category_scores[category] = []
            category_scores[category].append(result.overall_performance_score)

        category_stats = {}
        for category, scores in category_scores.items():
            category_stats[category] = {
                'count': len(scores),
                'average': sum(scores) / len(scores),
                'min': min(scores),
                'max': max(scores),
                'median': statistics.median(scores),
                'std_dev': statistics.stdev(scores) if len(scores) > 1 else 0.0
            }

        # Component analysis
        objective_scores = [r.objective_result.score for r in results if r.objective_result]
        detailed_scores = [r.detailed_score.overall_score for r in results if r.detailed_score]
        logical_scores = [r.logical_validation.reasoning_score for r in results if r.logical_validation]
        structured_scores = [r.structured_output_score for r in results]

        component_stats = {}
        if objective_scores:
            component_stats['objective_tests'] = {
                'count': len(objective_scores),
                'average': sum(objective_scores) / len(objective_scores),
                'success_rate': sum(1 for s in objective_scores if s >= 0.7) / len(objective_scores)
            }
        if detailed_scores:
            component_stats['automated_scoring'] = {
                'count': len(detailed_scores),
                'average': sum(detailed_scores) / len(detailed_scores),
                'high_quality_rate': sum(1 for s in detailed_scores if s >= 0.8) / len(detailed_scores)
            }
        if logical_scores:
            component_stats['logical_validation'] = {
                'count': len(logical_scores),
                'average': sum(logical_scores) / len(logical_scores),
                'valid_reasoning_rate': sum(1 for s in logical_scores if s >= 0.7) / len(logical_scores)
            }
        if structured_scores:
            component_stats['structured_output'] = {
                'count': len(structured_scores),
                'average': sum(structured_scores) / len(structured_scores),
                'well_formatted_rate': sum(1 for s in structured_scores if s >= 0.8) / len(structured_scores)
            }

        # Performance distribution
        performance_ranges = {
            'excellent (0.9-1.0)': sum(1 for s in overall_scores if s >= 0.9),
            'good (0.7-0.89)': sum(1 for s in overall_scores if 0.7 <= s < 0.9),
            'adequate (0.5-0.69)': sum(1 for s in overall_scores if 0.5 <= s < 0.7),
            'poor (0.0-0.49)': sum(1 for s in overall_scores if s < 0.5)
        }

        # Top and bottom performers
        sorted_results = sorted(results, key=lambda x: x.overall_performance_score, reverse=True)
        top_performers = sorted_results[:5]
        bottom_performers = sorted_results[-5:]

        return {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_evaluations': len(results),
                'average_overall_score': avg_overall_score,
                'score_distribution': performance_ranges,
                'evaluation_time_range': {
                    'min': min(r.execution_time for r in results),
                    'max': max(r.execution_time for r in results),
                    'average': sum(r.execution_time for r in results) / len(results)
                }
            },
            'category_analysis': category_stats,
            'component_analysis': component_stats,
            'top_performers': [
                {
                    'test_id': r.test_id,
                    'category': r.task_category,
                    'score': r.overall_performance_score,
                    'objective_score': r.objective_result.score if r.objective_result else None,
                    'detailed_score': r.detailed_score.overall_score if r.detailed_score else None
                }
                for r in top_performers
            ],
            'bottom_performers': [
                {
                    'test_id': r.test_id,
                    'category': r.task_category,
                    'score': r.overall_performance_score,
                    'main_issues': self._identify_main_issues(r)
                }
                for r in bottom_performers
            ],
            'detailed_results': [
                {
                    'test_id': r.test_id,
                    'category': r.task_category,
                    'overall_score': r.overall_performance_score,
                    'objective_score': r.objective_result.score if r.objective_result else None,
                    'detailed_score': r.detailed_score.overall_score if r.detailed_score else None,
                    'logical_score': r.logical_validation.reasoning_score if r.logical_validation else None,
                    'structured_score': r.structured_output_score,
                    'execution_time': r.execution_time
                }
                for r in results
            ]
        }

    def _identify_main_issues(self, result: ComprehensiveEvaluationResult) -> List[str]:
        """Identify main issues for poorly performing results"""
        issues = []

        if result.objective_result and result.objective_result.score < 0.5:
            issues.append("Objective test failure")

        if result.detailed_score and result.detailed_score.overall_score < 0.5:
            # Check dimensions
            dim = result.detailed_score.dimensions
            if dim.accuracy_score < 0.5:
                issues.append("Incorrect result")
            if dim.syntax_score < 0.5:
                issues.append("Syntax errors")
            if dim.completeness_score < 0.5:
                issues.append("Incomplete response")

        if result.logical_validation and result.logical_validation.reasoning_score < 0.5:
            issues.append("Logical reasoning issues")

        if result.structured_output_score < 0.5:
            issues.append("Poor formatting")

        if not issues:
            issues.append("General poor performance")

        return issues

    def export_results(self, results: List[ComprehensiveEvaluationResult] = None,
                      format_type: str = "json") -> str:
        """Export results to file"""
        if results is None:
            results = self.evaluation_results

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if format_type.lower() == "json":
            filename = f"comprehensive_evaluation_{timestamp}.json"
            filepath = Path.cwd() / filename

            export_data = []
            for result in results:
                data = {
                    'test_id': result.test_id,
                    'task_category': result.task_category,
                    'overall_performance_score': result.overall_performance_score,
                    'evaluation_timestamp': result.evaluation_timestamp,
                    'execution_time': result.execution_time,
                    'objective_result': asdict(result.objective_result) if result.objective_result else None,
                    'detailed_score': asdict(result.detailed_score) if result.detailed_score else None,
                    'logical_validation': asdict(result.logical_validation) if result.logical_validation else None,
                    'structured_output_score': result.structured_output_score
                }
                export_data.append(data)

            with open(filepath, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)

        elif format_type.lower() == "csv":
            filename = f"comprehensive_evaluation_{timestamp}.csv"
            filepath = Path.cwd() / filename

            with open(filepath, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'test_id', 'task_category', 'overall_score', 'objective_score',
                    'detailed_score', 'logical_score', 'structured_score',
                    'execution_time', 'timestamp'
                ])

                for result in results:
                    writer.writerow([
                        result.test_id,
                        result.task_category,
                        result.overall_performance_score,
                        result.objective_result.score if result.objective_result else '',
                        result.detailed_score.overall_score if result.detailed_score else '',
                        result.logical_validation.reasoning_score if result.logical_validation else '',
                        result.structured_output_score,
                        result.execution_time,
                        result.evaluation_timestamp
                    ])

        else:
            raise ValueError(f"Unsupported export format: {format_type}")

        return str(filepath)

    def run_objective_test_suite(self) -> Dict[str, Any]:
        """Run the complete objective test suite"""
        print("🧪 Running Comprehensive Objective Test Suite")
        print("=" * 60)

        # Get all test cases
        test_responses = []
        for test_case in self.objective_suite.test_cases:
            # Simulate LLM response by running the actual solution
            try:
                if test_case.test_data:
                    actual_result = test_case.solution_func(*test_case.test_data)
                else:
                    actual_result = test_case.solution_func()

                # Create a response that includes the solution
                response = f"Solution: {actual_result}"
                if hasattr(test_case.solution_func, '__name__'):
                    response = f"```python\n# {test_case.description}\n{actual_result}\n```"

                test_responses.append({
                    'test_id': test_case.test_id,
                    'response': response,
                    'expected_result': test_case.expected_result,
                    'output_format': 'json',
                    'logic_type': 'deductive' if test_case.category == ProblemType.LOGICAL_REASONING else None
                })

            except Exception as e:
                print(f"Error preparing test {test_case.test_id}: {e}")
                continue

        # Evaluate all responses
        results = self.batch_evaluate_responses(test_responses)

        # Generate comprehensive report
        report = self.generate_comprehensive_report(results)

        # Export results
        json_file = self.export_results(results, "json")
        csv_file = self.export_results(results, "csv")

        print(f"\n📊 Evaluation Complete!")
        print(f"Total Tests: {report['summary']['total_evaluations']}")
        print(f"Average Score: {report['summary']['average_overall_score']:.3f}")
        print(f"Results exported to: {json_file}")
        print(f"CSV exported to: {csv_file}")

        return report


# Example usage
if __name__ == "__main__":
    system = ComprehensiveTestSystem()

    # Run the complete test suite
    report = system.run_objective_test_suite()

    print(f"\n📈 Category Performance:")
    for category, stats in report['category_analysis'].items():
        print(f"  {category}: {stats['average']:.3f} avg ({stats['count']} tests)")

    print(f"\n🎯 Component Analysis:")
    for component, stats in report['component_analysis'].items():
        print(f"  {component}: {stats['average']:.3f} avg")