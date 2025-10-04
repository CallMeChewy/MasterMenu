#!/usr/bin/env python3
"""
Complete LLM Test Results Evaluation Workflow

This script provides a complete workflow for evaluating LLM test results,
including response quality scoring, parameter analysis, and optimization recommendations.

Usage:
    python3 evaluate_test_results.py [csv_file] [max_evaluations]

Features:
- Parse malformed CSV data
- Evaluate response quality across multiple dimensions
- Generate optimization recommendations
- Export detailed reports
"""

import sys
import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

from csv_parser import RobustCSVParser, TestResult
from response_evaluator import ResponseEvaluator, ResponseEvaluation


class TestResultsEvaluator:
    """Complete evaluation workflow for LLM test results"""

    def __init__(self):
        self.parser = RobustCSVParser()
        self.evaluator = ResponseEvaluator()
        self.results = []
        self.evaluations = []

    def load_results(self, csv_file: str, max_lines: Optional[int] = None) -> bool:
        """Load and parse test results from CSV file"""
        print(f"🔍 Loading test results from: {csv_file}")

        if not os.path.exists(csv_file):
            print(f"❌ Error: File {csv_file} not found")
            return False

        self.results = self.parser.parse_csv_file(csv_file, max_lines)

        if not self.results:
            print("❌ No results could be parsed from the CSV file")
            return False

        print(f"✅ Successfully parsed {len(self.results)} results")

        # Show parsing statistics
        stats = self.parser.get_parse_statistics()
        print(f"📊 Parse success rate: {stats['success_rate']:.1f}%")

        if stats['failed_parses'] > 0:
            print(f"⚠️  {stats['failed_parses']} lines could not be parsed")
            print("   This is normal for CSV files with complex response text")

        return True

    def evaluate_responses(self, max_evaluations: Optional[int] = None) -> int:
        """Evaluate response quality for all completed tests"""
        completed_results = [r for r in self.results if r.status == "completed" and r.response_text]

        if max_evaluations:
            completed_results = completed_results[:max_evaluations]

        print(f"🧠 Evaluating {len(completed_results)} responses...")

        evaluated_count = 0

        for result in completed_results:
            # Extract parameters from result context
            parameters = self.extract_parameters(result)

            try:
                evaluation = self.evaluator.evaluate_response(
                    test_id=f"test_{result.row_number}",
                    model_name=result.model_name,
                    parameters=parameters,
                    prompt=result.prompt_text,
                    response=result.response_text,
                    execution_time=result.response_time
                )

                self.evaluations.append(evaluation)
                evaluated_count += 1

                # Progress indicator
                if evaluated_count % 10 == 0:
                    print(f"   Evaluated {evaluated_count}/{len(completed_results)} responses...")

            except Exception as e:
                print(f"   ⚠️  Error evaluating response {result.row_number}: {str(e)}")
                continue

        print(f"✅ Successfully evaluated {evaluated_count} responses")
        return evaluated_count

    def extract_parameters(self, result: TestResult) -> Dict[str, Any]:
        """
        Extract parameter information from the test result.

        This is a placeholder implementation. In a real test setup, you would
        encode parameter information in the test ID, prompt, or other metadata.
        """
        # For now, return default parameters
        # You should customize this based on how your parameter tests were structured

        return {
            "temperature": 0.7,
            "top_p": 0.9,
            "top_k": 40,
            "repeat_penalty": 1.1
        }

    def generate_analysis_report(self) -> Dict[str, Any]:
        """Generate comprehensive analysis report"""
        print("📈 Generating analysis report...")

        if not self.evaluations:
            return {"error": "No evaluations available for analysis"}

        # Basic statistics
        model_stats = {}
        type_stats = {}

        for eval_result in self.evaluations:
            # Model statistics
            if eval_result.model_name not in model_stats:
                model_stats[eval_result.model_name] = {
                    'scores': [],
                    'types': [],
                    'response_lengths': [],
                    'times': []
                }

            model_stats[eval_result.model_name]['scores'].append(eval_result.overall_score)
            model_stats[eval_result.model_name]['types'].append(eval_result.response_type.value)
            model_stats[eval_result.model_name]['response_lengths'].append(eval_result.response_length)
            if eval_result.execution_time > 0:
                model_stats[eval_result.model_name]['times'].append(eval_result.execution_time)

            # Type statistics
            if eval_result.response_type.value not in type_stats:
                type_stats[eval_result.response_type.value] = {
                    'scores': [],
                    'count': 0
                }

            type_stats[eval_result.response_type.value]['scores'].append(eval_result.overall_score)
            type_stats[eval_result.response_type.value]['count'] += 1

        # Calculate averages
        model_analysis = {}
        for model, stats in model_stats.items():
            scores = stats['scores']
            times = stats['times']
            lengths = stats['response_lengths']

            model_analysis[model] = {
                'total_evaluations': len(scores),
                'avg_score': sum(scores) / len(scores),
                'min_score': min(scores),
                'max_score': max(scores),
                'avg_response_time': sum(times) / len(times) if times else 0,
                'avg_response_length': sum(lengths) / len(lengths),
                'response_types': list(set(stats['types']))
            }

        type_analysis = {}
        for response_type, stats in type_stats.items():
            scores = stats['scores']
            type_analysis[response_type] = {
                'count': len(scores),
                'avg_score': sum(scores) / len(scores),
                'min_score': min(scores),
                'max_score': max(scores)
            }

        # Find best performing model and type
        best_model = max(model_analysis.items(), key=lambda x: x[1]['avg_score'])
        best_type = max(type_analysis.items(), key=lambda x: x[1]['avg_score'])

        # Generate recommendations
        recommendations = self.generate_recommendations(model_analysis, type_analysis)

        return {
            'evaluation_summary': {
                'total_evaluations': len(self.evaluations),
                'models_tested': len(model_analysis),
                'response_types_found': len(type_analysis),
                'analysis_timestamp': datetime.now().isoformat()
            },
            'model_performance': model_analysis,
            'response_type_analysis': type_analysis,
            'top_performers': {
                'best_model': {
                    'name': best_model[0],
                    'avg_score': best_model[1]['avg_score'],
                    'evaluations': best_model[1]['total_evaluations']
                },
                'best_response_type': {
                    'type': best_type[0],
                    'avg_score': best_type[1]['avg_score'],
                    'count': best_type[1]['count']
                }
            },
            'recommendations': recommendations
        }

    def generate_recommendations(self, model_analysis: Dict[str, Any], type_analysis: Dict[str, Any]) -> List[str]:
        """Generate optimization recommendations based on analysis"""
        recommendations = []

        # Model recommendations
        if model_analysis:
            best_model = max(model_analysis.items(), key=lambda x: x[1]['avg_score'])
            worst_model = min(model_analysis.items(), key=lambda x: x[1]['avg_score'])

            improvement_potential = best_model[1]['avg_score'] - worst_model[1]['avg_score']
            if improvement_potential > 2.0:
                recommendations.append(
                    f"Significant performance difference detected. "
                    f"{best_model[0]} performs {improvement_potential:.1f} points better than {worst_model[0]}."
                )

            # Speed vs Quality trade-offs
            fast_models = [(name, data) for name, data in model_analysis.items() if data['avg_response_time'] < 10]
            quality_models = [(name, data) for name, data in model_analysis.items() if data['avg_score'] > 7.0]

            if fast_models and quality_models:
                fast_name, fast_data = fast_models[0]
                quality_name, quality_data = quality_models[0]

                if fast_name != quality_name:
                    recommendations.append(
                        f"Consider {fast_name} for faster responses ({fast_data['avg_response_time']:.1f}s) "
                        f"or {quality_name} for higher quality ({quality_data['avg_score']:.1f} score)."
                    )

        # Response type recommendations
        if type_analysis:
            best_type = max(type_analysis.items(), key=lambda x: x[1]['avg_score'])
            if best_type[1]['avg_score'] > 7.0:
                recommendations.append(
                    f"Best performance achieved with {best_type[0]} tasks "
                    f"({best_type[1]['avg_score']:.1f} average score)."
                )

        # General recommendations
        avg_score = sum(data['avg_score'] for data in model_analysis.values()) / len(model_analysis)
        if avg_score < 5.0:
            recommendations.append(
                "Overall performance is below average. Consider reviewing prompt quality "
                "or adjusting model parameters for better results."
            )
        elif avg_score > 7.5:
            recommendations.append(
                "Overall performance is excellent. Current configuration is working well."
            )

        if not recommendations:
            recommendations.append("Continue monitoring performance and adjust parameters based on specific use cases.")

        return recommendations

    def export_results(self, output_file: Optional[str] = None) -> str:
        """Export evaluation results to file"""
        if not output_file:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"evaluation_results_{timestamp}.json"

        # Prepare export data
        export_data = {
            'export_info': {
                'timestamp': datetime.now().isoformat(),
                'total_results_loaded': len(self.results),
                'total_evaluations': len(self.evaluations),
                'parse_statistics': self.parser.get_parse_statistics()
            },
            'analysis_report': self.generate_analysis_report(),
            'detailed_evaluations': [
                {
                    'test_id': e.test_id,
                    'model_name': e.model_name,
                    'response_type': e.response_type.value,
                    'overall_score': e.overall_score,
                    'syntax_score': e.syntax_score,
                    'accuracy_score': e.accuracy_score,
                    'completeness_score': e.completeness_score,
                    'clarity_score': e.clarity_score,
                    'response_length': e.response_length,
                    'execution_time': e.execution_time,
                    'strengths': e.strengths,
                    'issues_found': e.issues_found,
                    'feedback': e.feedback
                }
                for e in self.evaluations
            ]
        }

        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)

            print(f"📄 Results exported to: {output_file}")
            return output_file

        except Exception as e:
            print(f"❌ Error exporting results: {str(e)}")
            return ""

    def print_summary(self):
        """Print a summary of the evaluation results"""
        if not self.evaluations:
            print("❌ No evaluations to display")
            return

        report = self.generate_analysis_report()
        summary = report['evaluation_summary']

        print("\n" + "="*60)
        print("📊 EVALUATION SUMMARY")
        print("="*60)

        print(f"Total Evaluations: {summary['total_evaluations']}")
        print(f"Models Tested: {summary['models_tested']}")
        print(f"Response Types: {summary['response_types_found']}")

        print(f"\n🏆 TOP PERFORMERS:")
        print(f"Best Model: {report['top_performers']['best_model']['name']}")
        print(f"  Score: {report['top_performers']['best_model']['avg_score']:.2f}")
        print(f"Best Response Type: {report['top_performers']['best_response_type']['type']}")
        print(f"  Score: {report['top_performers']['best_response_type']['avg_score']:.2f}")

        print(f"\n💡 RECOMMENDATIONS:")
        for i, rec in enumerate(report['recommendations'][:3], 1):
            print(f"{i}. {rec}")

        print("\n" + "="*60)


def main():
    """Main execution function"""
    print("🧪 LLM Test Results Evaluator")
    print("="*40)

    # Get input parameters
    csv_file = sys.argv[1] if len(sys.argv) > 1 else "/home/herb/Desktop/test_results_20251001_194846.csv"
    max_evaluations = int(sys.argv[2]) if len(sys.argv) > 2 else 50

    # Initialize evaluator
    evaluator = TestResultsEvaluator()

    # Load results
    if not evaluator.load_results(csv_file):
        print("❌ Failed to load test results")
        return 1

    # Evaluate responses
    evaluated_count = evaluator.evaluate_responses(max_evaluations)
    if evaluated_count == 0:
        print("❌ No responses were evaluated")
        return 1

    # Print summary
    evaluator.print_summary()

    # Export results
    output_file = evaluator.export_results()

    print(f"\n✅ Evaluation complete! {evaluated_count} responses analyzed.")
    if output_file:
        print(f"📁 Detailed results saved to: {output_file}")

    return 0


if __name__ == "__main__":
    sys.exit(main())