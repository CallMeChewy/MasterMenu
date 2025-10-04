# File: results_analyzer.py
# Path: /home/herb/Desktop/LLM-Tester/results_analyzer.py
# Standard: AIDEV-PascalCase-2.1
# Created: 2025-10-01
# Last Modified: 2025-10-01 9:00PM

"""
Comprehensive LLM Test Results Analyzer

This module provides complete analysis and visualization capabilities for LLM parameter
comparison test results. It combines CSV parsing, response evaluation, and statistical
analysis to provide actionable insights.

Features:
- Parse and clean malformed CSV test results
- Evaluate response quality across multiple dimensions
- Statistical analysis of parameter effects
- Generate comprehensive reports and visualizations
- Parameter optimization recommendations
"""

import json
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from collections import defaultdict
import pandas as pd

from csv_parser import RobustCSVParser, TestResult
from response_evaluator import ResponseEvaluator, ResponseEvaluation


class ResultsAnalyzer:
    """Comprehensive analyzer for LLM test results"""

    def __init__(self):
        self.parser = RobustCSVParser()
        self.evaluator = ResponseEvaluator()
        self.test_results = []
        self.evaluations = []
        self.analysis_cache = {}

    def load_and_parse_results(self, csv_file: str, max_lines: Optional[int] = None) -> bool:
        """Load and parse test results from CSV file"""
        print(f"Loading results from {csv_file}...")

        self.test_results = self.parser.parse_csv_file(csv_file, max_lines)

        if not self.test_results:
            print("No results could be parsed from the CSV file.")
            return False

        print(f"Successfully parsed {len(self.test_results)} results.")

        # Show parsing statistics
        stats = self.parser.get_parse_statistics()
        print(f"Parse success rate: {stats['success_rate']:.1f}%")

        if stats['parse_errors']:
            print(f"Parse errors: {len(stats['parse_errors'])}")
            for error in stats['parse_errors'][:3]:
                print(f"  {error}")

        return True

    def evaluate_all_responses(self) -> int:
        """Evaluate all parsed responses"""
        if not self.test_results:
            print("No test results available for evaluation.")
            return 0

        print(f"Evaluating {len(self.test_results)} responses...")
        evaluated_count = 0

        for result in self.test_results:
            if result.status == "completed" and result.response_text:
                # Extract parameters (this will need to be implemented based on your test setup)
                parameters = self.extract_parameters_from_context(result)

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

                # Progress reporting
                if evaluated_count % 100 == 0:
                    print(f"Evaluated {evaluated_count} responses...")

        print(f"Completed evaluation of {evaluated_count} responses.")
        return evaluated_count

    def extract_parameters_from_context(self, result: TestResult) -> Dict[str, Any]:
        """
        Extract parameter information from the test result context.
        This is a placeholder - you'll need to customize this based on how your
        parameter tests were structured in the original testing.
        """
        # For now, return empty parameters
        # In your actual test setup, you might have encoded parameters in:
        # - The test ID
        # - The prompt text
        # - The filename or other metadata
        # - A separate parameter mapping file

        return {
            "temperature": 0.7,  # Default - customize based on your test setup
            "top_p": 0.9,
            "top_k": 40,
            "repeat_penalty": 1.1
        }

    def get_parameter_groups(self) -> Dict[str, List[ResponseEvaluation]]:
        """Group evaluations by parameter configurations"""
        groups = defaultdict(list)

        for eval_result in self.evaluations:
            # Create a parameter key for grouping
            # Customize this based on your actual parameter structure
            param_key = self.create_parameter_key(eval_result.parameters)
            groups[param_key].append(eval_result)

        return dict(groups)

    def create_parameter_key(self, parameters: Dict[str, Any]) -> str:
        """Create a standardized key for parameter configuration"""
        # Customize this based on which parameters you varied in your tests
        key_parts = []

        if 'temperature' in parameters:
            key_parts.append(f"temp={parameters['temperature']}")
        if 'top_p' in parameters:
            key_parts.append(f"top_p={parameters['top_p']}")
        if 'top_k' in parameters:
            key_parts.append(f"top_k={parameters['top_k']}")
        if 'repeat_penalty' in parameters:
            key_parts.append(f"rep_pen={parameters['repeat_penalty']}")

        return "_".join(key_parts) if key_parts else "default"

    def analyze_parameter_effects(self) -> Dict[str, Any]:
        """Analyze how different parameters affect response quality"""
        if not self.evaluations:
            return {"error": "No evaluations available for analysis"}

        param_groups = self.get_parameter_groups()
        analysis = {}

        for param_key, group_evals in param_groups.items():
            scores = [e.overall_score for e in group_evals]
            response_times = [e.execution_time for e in group_evals if e.execution_time > 0]
            response_lengths = [e.response_length for e in group_evals]

            analysis[param_key] = {
                'count': len(group_evals),
                'avg_score': np.mean(scores),
                'std_score': np.std(scores),
                'min_score': np.min(scores),
                'max_score': np.max(scores),
                'avg_response_time': np.mean(response_times) if response_times else 0,
                'avg_response_length': np.mean(response_lengths),
                'response_types': self.analyze_response_types(group_evals)
            }

        return analysis

    def analyze_response_types(self, evaluations: List[ResponseEvaluation]) -> Dict[str, Any]:
        """Analyze distribution of response types in a group"""
        type_counts = defaultdict(int)
        type_scores = defaultdict(list)

        for eval_result in evaluations:
            type_key = eval_result.response_type.value
            type_counts[type_key] += 1
            type_scores[type_key].append(eval_result.overall_score)

        type_analysis = {}
        for type_key, count in type_counts.items():
            scores = type_scores[type_key]
            type_analysis[type_key] = {
                'count': count,
                'avg_score': np.mean(scores),
                'std_score': np.std(scores)
            }

        return type_analysis

    def compare_parameter_configurations(self, param1: str, param2: str) -> Dict[str, Any]:
        """Compare two parameter configurations"""
        param_effects = self.analyze_parameter_effects()

        if param1 not in param_effects or param2 not in param_effects:
            return {"error": "One or both parameter configurations not found"}

        config1 = param_effects[param1]
        config2 = param_effects[param2]

        # Calculate improvement
        score_improvement = ((config1['avg_score'] - config2['avg_score']) /
                            config2['avg_score'] * 100) if config2['avg_score'] > 0 else 0

        return {
            'configuration_1': {
                'parameters': param1,
                'avg_score': config1['avg_score'],
                'std_score': config1['std_score'],
                'count': config1['count']
            },
            'configuration_2': {
                'parameters': param2,
                'avg_score': config2['avg_score'],
                'std_score': config2['std_score'],
                'count': config2['count']
            },
            'comparison': {
                'score_improvement_percent': score_improvement,
                'time_difference': config1['avg_response_time'] - config2['avg_response_time'],
                'length_difference': config1['avg_response_length'] - config2['avg_response_length'],
                'better_config': param1 if score_improvement > 0 else param2
            }
        }

    def get_model_performance_analysis(self) -> Dict[str, Any]:
        """Analyze performance by model"""
        model_stats = defaultdict(lambda: {
            'scores': [], 'times': [], 'lengths': [], 'types': defaultdict(int)
        })

        for eval_result in self.evaluations:
            model = eval_result.model_name
            model_stats[model]['scores'].append(eval_result.overall_score)
            if eval_result.execution_time > 0:
                model_stats[model]['times'].append(eval_result.execution_time)
            model_stats[model]['lengths'].append(eval_result.response_length)
            model_stats[model]['types'][eval_result.response_type.value] += 1

        analysis = {}
        for model, stats in model_stats.items():
            analysis[model] = {
                'total_evaluations': len(stats['scores']),
                'avg_score': np.mean(stats['scores']),
                'std_score': np.std(stats['scores']),
                'min_score': np.min(stats['scores']),
                'max_score': np.max(stats['scores']),
                'avg_response_time': np.mean(stats['times']) if stats['times'] else 0,
                'avg_response_length': np.mean(stats['lengths']),
                'response_type_distribution': dict(stats['types'])
            }

        return analysis

    def generate_optimization_recommendations(self) -> Dict[str, Any]:
        """Generate recommendations for parameter optimization"""
        param_effects = self.analyze_parameter_effects()

        if not param_effects:
            return {"error": "No parameter effects data available"}

        # Find best performing configuration
        best_config = max(param_effects.items(), key=lambda x: x[1]['avg_score'])
        worst_config = min(param_effects.items(), key=lambda x: x[1]['avg_score'])

        recommendations = {
            'best_configuration': {
                'parameters': best_config[0],
                'avg_score': best_config[1]['avg_score'],
                'count': best_config[1]['count']
            },
            'worst_configuration': {
                'parameters': worst_config[0],
                'avg_score': worst_config[1]['avg_score'],
                'count': worst_config[1]['count']
            },
            'improvement_potential': best_config[1]['avg_score'] - worst_config[1]['avg_score'],
            'recommendations': []
        }

        # Generate specific recommendations based on parameter analysis
        recommendations['recommendations'] = self.generate_parameter_specific_recommendations(param_effects)

        return recommendations

    def generate_parameter_specific_recommendations(self, param_effects: Dict[str, Any]) -> List[str]:
        """Generate specific parameter recommendations"""
        recommendations = []

        # Temperature analysis
        temp_configs = {k: v for k, v in param_effects.items() if 'temp=' in k}
        if len(temp_configs) >= 2:
            temps = []
            scores = []
            for config, data in temp_configs.items():
                temp = float(config.split('temp=')[1].split('_')[0])
                temps.append(temp)
                scores.append(data['avg_score'])

            correlation = np.corrcoef(temps, scores)[0, 1] if len(temps) > 1 else 0

            if correlation > 0.5:
                recommendations.append("Higher temperatures correlate with better scores - consider using temperature > 0.7")
            elif correlation < -0.5:
                recommendations.append("Lower temperatures correlate with better scores - consider using temperature < 0.5")
            else:
                recommendations.append("Temperature has minimal impact on scores - focus on other parameters")

        # Performance vs Quality trade-off
        fast_configs = sorted(param_effects.items(), key=lambda x: x[1]['avg_response_time'])
        if len(fast_configs) >= 2:
            fastest = fast_configs[0]
            slowest = fast_configs[-1]

            if fastest[1]['avg_score'] >= slowest[1]['avg_score'] * 0.9:
                recommendations.append(f"Use {fastest[0]} for optimal balance of speed and quality")
            else:
                recommendations.append("Higher quality comes at the cost of speed - adjust based on your priorities")

        return recommendations

    def create_visualizations(self, output_dir: str = "/home/herb/Desktop/LLM-Tester/visualizations"):
        """Create visualization plots for the analysis results"""
        import os
        os.makedirs(output_dir, exist_ok=True)

        print(f"Creating visualizations in {output_dir}...")

        # 1. Parameter Effects Heatmap
        self.create_parameter_heatmap(output_dir)

        # 2. Model Performance Comparison
        self.create_model_performance_chart(output_dir)

        # 3. Score Distribution
        self.create_score_distribution(output_dir)

        # 4. Response Type Analysis
        self.create_response_type_analysis(output_dir)

        print(f"Visualizations saved to {output_dir}")

    def create_parameter_heatmap(self, output_dir: str):
        """Create heatmap of parameter effects"""
        param_effects = self.analyze_parameter_effects()

        if not param_effects:
            return

        # Extract data for heatmap
        configs = list(param_effects.keys())
        scores = [param_effects[c]['avg_score'] for c in configs]

        # Create a simple text-based heatmap for now
        # In a full implementation, you'd use matplotlib/seaborn
        with open(f"{output_dir}/parameter_heatmap.txt", 'w') as f:
            f.write("Parameter Configuration Effects\n")
            f.write("=" * 50 + "\n\n")

            for config, data in sorted(param_effects.items(), key=lambda x: x[1]['avg_score'], reverse=True):
                f.write(f"{config:<30} | Score: {data['avg_score']:.2f} | Count: {data['count']}\n")
                f.write(f"{'-'*30}-|---------|--------\n")

    def create_model_performance_chart(self, output_dir: str):
        """Create model performance comparison chart"""
        model_analysis = self.get_model_performance_analysis()

        with open(f"{output_dir}/model_performance.txt", 'w') as f:
            f.write("Model Performance Analysis\n")
            f.write("=" * 30 + "\n\n")

            for model, data in sorted(model_analysis.items(), key=lambda x: x[1]['avg_score'], reverse=True):
                f.write(f"{model}\n")
                f.write(f"  Average Score: {data['avg_score']:.2f}\n")
                f.write(f"  Evaluations: {data['total_evaluations']}\n")
                f.write(f"  Response Types: {', '.join(data['response_type_distribution'].keys())}\n")
                f.write("\n")

    def create_score_distribution(self, output_dir: str):
        """Create score distribution analysis"""
        if not self.evaluations:
            return

        scores = [e.overall_score for e in self.evaluations]

        with open(f"{output_dir}/score_distribution.txt", 'w') as f:
            f.write("Score Distribution Analysis\n")
            f.write("=" * 30 + "\n\n")

            f.write(f"Total Evaluations: {len(scores)}\n")
            f.write(f"Mean Score: {np.mean(scores):.2f}\n")
            f.write(f"Std Deviation: {np.std(scores):.2f}\n")
            f.write(f"Min Score: {np.min(scores):.2f}\n")
            f.write(f"Max Score: {np.max(scores):.2f}\n")
            f.write(f"25th Percentile: {np.percentile(scores, 25):.2f}\n")
            f.write(f"75th Percentile: {np.percentile(scores, 75):.2f}\n")

    def create_response_type_analysis(self, output_dir: str):
        """Create response type analysis"""
        type_stats = self.evaluator.get_summary_statistics()['type_statistics']

        with open(f"{output_dir}/response_type_analysis.txt", 'w') as f:
            f.write("Response Type Analysis\n")
            f.write("=" * 25 + "\n\n")

            for response_type, data in type_stats.items():
                f.write(f"{response_type}\n")
                f.write(f"  Count: {data['count']}\n")
                f.write(f"  Average Score: {data['average_score']:.2f}\n")
                f.write(f"  Score Range: {data['min_score']:.2f} - {data['max_score']:.2f}\n")
                f.write("\n")

    def generate_comprehensive_report(self, output_file: str = None) -> str:
        """Generate a comprehensive analysis report"""
        if not output_file:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"/home/herb/Desktop/LLM-Tester/analysis_report_{timestamp}.json"

        print("Generating comprehensive analysis report...")

        report = {
            'analysis_timestamp': datetime.now().isoformat(),
            'data_summary': {
                'total_results': len(self.test_results),
                'evaluated_responses': len(self.evaluations),
                'parse_statistics': self.parser.get_parse_statistics()
            },
            'parameter_effects': self.analyze_parameter_effects(),
            'model_performance': self.get_model_performance_analysis(),
            'optimization_recommendations': self.generate_optimization_recommendations(),
            'evaluator_summary': self.evaluator.get_summary_statistics()
        }

        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"Comprehensive report saved to {output_file}")
        return output_file


# Example usage
if __name__ == "__main__":
    analyzer = ResultsAnalyzer()

    # Load and analyze results
    if analyzer.load_and_parse_results("/home/herb/Desktop/test_results_20251001_194846.csv", max_lines=2000):
        # Evaluate responses
        evaluated_count = analyzer.evaluate_all_responses()

        if evaluated_count > 0:
            # Generate comprehensive analysis
            report_file = analyzer.generate_comprehensive_report()

            # Create visualizations
            analyzer.create_visualizations()

            # Show some key findings
            recommendations = analyzer.generate_optimization_recommendations()
            print("\nKey Recommendations:")
            for rec in recommendations.get('recommendations', []):
                print(f"  • {rec}")
        else:
            print("No responses were evaluated successfully.")
    else:
        print("Failed to load test results.")