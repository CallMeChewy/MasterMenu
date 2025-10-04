# File: performance_comparison_system.py
# Path: /home/herb/Desktop/LLM-Tester/performance_comparison_system.py
# Standard: AIDEV-PascalCase-2.1
# Created: 2025-10-01
# Last Modified: 2025-10-01 10:45PM

"""
Performance Comparison System for Parameter Optimization

This system provides comprehensive performance analysis and comparison capabilities
for LLM parameter optimization, integrating with the existing parameter comparison
framework and the comprehensive testing system.

Features:
- Multi-dimensional performance analysis
- Parameter impact assessment
- Statistical significance testing
- Performance trend analysis
- Optimization recommendations
- Automated parameter tuning suggestions
"""

import json
import csv
import statistics
import math
from typing import Dict, Any, List, Tuple, Optional, Union
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
import numpy as np
from scipy import stats

from comprehensive_test_system import ComprehensiveTestSystem, ComprehensiveEvaluationResult
from parameter_test_framework import ParameterTestResult, StatisticalAnalysis


@dataclass
class PerformanceMetrics:
    """Performance metrics for parameter configurations"""
    parameter_config: Dict[str, Any]
    overall_score: float
    objective_score: float
    reasoning_score: float
    structured_output_score: float
    execution_time: float
    cost_efficiency: float
    reliability_score: float
    consistency_score: float


@dataclass
class ComparisonResult:
    """Result of comparing two parameter configurations"""
    config_a: Dict[str, Any]
    config_b: Dict[str, Any]
    metrics_a: PerformanceMetrics
    metrics_b: PerformanceMetrics
    significance_tests: Dict[str, Any]
    winner: str
    improvement_percentage: float
    recommendation: str


@dataclass
class OptimizationSuggestion:
    """Suggestion for parameter optimization"""
    parameter: str
    current_value: Any
    suggested_value: Any
    expected_improvement: float
    confidence: float
    reasoning: str


class PerformanceComparisonSystem:
    """Advanced performance comparison and optimization system"""

    def __init__(self):
        self.test_system = ComprehensiveTestSystem()
        self.performance_history = []
        self.comparison_results = []
        self.optimization_suggestions = []

    def analyze_parameter_performance(self, test_results: List[ComprehensiveEvaluationResult],
                                    parameter_config: Dict[str, Any]) -> PerformanceMetrics:
        """
        Analyze performance for a specific parameter configuration

        Args:
            test_results: List of evaluation results for this configuration
            parameter_config: The parameter configuration used

        Returns:
            PerformanceMetrics with comprehensive analysis
        """
        if not test_results:
            raise ValueError("No test results provided for analysis")

        # Extract scores
        overall_scores = [r.overall_performance_score for r in test_results]
        objective_scores = [r.objective_result.score for r in test_results if r.objective_result]
        reasoning_scores = [r.logical_validation.reasoning_score for r in test_results if r.logical_validation]
        structured_scores = [r.structured_output_score for r in test_results]

        # Calculate execution metrics
        execution_times = [r.execution_time for r in test_results]

        # Calculate reliability (success rate)
        success_count = sum(1 for r in test_results if r.overall_performance_score >= 0.7)
        reliability_score = success_count / len(test_results)

        # Calculate consistency (low standard deviation = high consistency)
        if len(overall_scores) > 1:
            score_std = statistics.stdev(overall_scores)
            # Convert to consistency score (inverse of std dev, normalized)
            consistency_score = max(0.0, 1.0 - (score_std / 1.0))  # Assuming max std dev of 1.0
        else:
            consistency_score = 0.5  # Default for single measurement

        # Calculate cost efficiency (score per execution time)
        avg_execution_time = sum(execution_times) / len(execution_times)
        avg_overall_score = sum(overall_scores) / len(overall_scores)
        cost_efficiency = avg_overall_score / max(avg_execution_time, 0.001)  # Avoid division by zero

        return PerformanceMetrics(
            parameter_config=parameter_config,
            overall_score=avg_overall_score,
            objective_score=sum(objective_scores) / len(objective_scores) if objective_scores else 0.0,
            reasoning_score=sum(reasoning_scores) / len(reasoning_scores) if reasoning_scores else 0.0,
            structured_output_score=sum(structured_scores) / len(structured_scores) if structured_scores else 0.0,
            execution_time=avg_execution_time,
            cost_efficiency=cost_efficiency,
            reliability_score=reliability_score,
            consistency_score=consistency_score
        )

    def compare_configurations(self, results_a: List[ComprehensiveEvaluationResult],
                             config_a: Dict[str, Any],
                             results_b: List[ComprehensiveEvaluationResult],
                             config_b: Dict[str, Any]) -> ComparisonResult:
        """
        Compare two parameter configurations with statistical analysis

        Args:
            results_a: Test results for configuration A
            config_a: Parameter configuration A
            results_b: Test results for configuration B
            config_b: Parameter configuration B

        Returns:
            ComparisonResult with detailed analysis
        """
        # Analyze both configurations
        metrics_a = self.analyze_parameter_performance(results_a, config_a)
        metrics_b = self.analyze_parameter_performance(results_b, config_b)

        # Perform statistical significance tests
        significance_tests = self._perform_significance_tests(results_a, results_b)

        # Determine winner
        overall_improvement = ((metrics_b.overall_score - metrics_a.overall_score) /
                            max(metrics_a.overall_score, 0.001)) * 100

        if overall_improvement > 5:  # 5% threshold for meaningful improvement
            winner = "config_b"
        elif overall_improvement < -5:
            winner = "config_a"
        else:
            winner = "tie"

        # Generate recommendation
        recommendation = self._generate_comparison_recommendation(
            metrics_a, metrics_b, significance_tests, overall_improvement
        )

        return ComparisonResult(
            config_a=config_a,
            config_b=config_b,
            metrics_a=metrics_a,
            metrics_b=metrics_b,
            significance_tests=significance_tests,
            winner=winner,
            improvement_percentage=overall_improvement,
            recommendation=recommendation
        )

    def _perform_significance_tests(self, results_a: List[ComprehensiveEvaluationResult],
                                   results_b: List[ComprehensiveEvaluationResult]) -> Dict[str, Any]:
        """Perform statistical significance tests between configurations"""
        scores_a = [r.overall_performance_score for r in results_a]
        scores_b = [r.overall_performance_score for r in results_b]

        tests = {}

        try:
            # t-test for means
            t_stat, p_value = stats.ttest_ind(scores_a, scores_b)
            tests['t_test'] = {
                't_statistic': t_stat,
                'p_value': p_value,
                'significant': p_value < 0.05,
                'confidence': (1 - p_value) * 100
            }

            # Mann-Whitney U test (non-parametric)
            u_stat, u_p_value = stats.mannwhitneyu(scores_a, scores_b, alternative='two-sided')
            tests['mann_whitney'] = {
                'u_statistic': u_stat,
                'p_value': u_p_value,
                'significant': u_p_value < 0.05,
                'confidence': (1 - u_p_value) * 100
            }

            # Effect size (Cohen's d)
            pooled_std = math.sqrt(((len(scores_a) - 1) * statistics.variance(scores_a) +
                                  (len(scores_b) - 1) * statistics.variance(scores_b)) /
                                 (len(scores_a) + len(scores_b) - 2))
            cohens_d = (statistics.mean(scores_b) - statistics.mean(scores_a)) / pooled_std
            tests['effect_size'] = {
                'cohens_d': cohens_d,
                'magnitude': self._interpret_effect_size(abs(cohens_d))
            }

        except Exception as e:
            tests['error'] = str(e)

        return tests

    def _interpret_effect_size(self, cohens_d: float) -> str:
        """Interpret Cohen's d effect size"""
        if cohens_d < 0.2:
            return "negligible"
        elif cohens_d < 0.5:
            return "small"
        elif cohens_d < 0.8:
            return "medium"
        else:
            return "large"

    def _generate_comparison_recommendation(self, metrics_a: PerformanceMetrics,
                                          metrics_b: PerformanceMetrics,
                                          significance_tests: Dict[str, Any],
                                          improvement_percentage: float) -> str:
        """Generate recommendation based on comparison results"""
        parts = []

        # Overall performance comparison
        if improvement_percentage > 10:
            parts.append(f"Config B shows {improvement_percentage:.1f}% better overall performance")
        elif improvement_percentage < -10:
            parts.append(f"Config A shows {abs(improvement_percentage):.1f}% better overall performance")
        else:
            parts.append("Both configurations show similar overall performance")

        # Statistical significance
        if 't_test' in significance_tests and significance_tests['t_test']['significant']:
            confidence = significance_tests['t_test']['confidence']
            parts.append(f"Improvement is statistically significant ({confidence:.1f}% confidence)")
        else:
            parts.append("Improvement is not statistically significant")

        # Specific metric insights
        if metrics_b.reliability_score > metrics_a.reliability_score + 0.1:
            parts.append("Config B is more reliable")
        elif metrics_a.reliability_score > metrics_b.reliability_score + 0.1:
            parts.append("Config A is more reliable")

        if metrics_b.consistency_score > metrics_a.consistency_score + 0.1:
            parts.append("Config B is more consistent")
        elif metrics_a.consistency_score > metrics_b.consistency_score + 0.1:
            parts.append("Config A is more consistent")

        if metrics_b.cost_efficiency > metrics_a.cost_efficiency * 1.2:
            parts.append("Config B is more cost-effective")
        elif metrics_a.cost_efficiency > metrics_b.cost_efficiency * 1.2:
            parts.append("Config A is more cost-effective")

        return " | ".join(parts)

    def analyze_parameter_impact(self, all_results: List[Tuple[Dict[str, Any], List[ComprehensiveEvaluationResult]]]) -> Dict[str, Any]:
        """
        Analyze the impact of individual parameters on performance

        Args:
            all_results: List of (parameter_config, test_results) tuples

        Returns:
            Parameter impact analysis
        """
        if not all_results:
            return {"error": "No results provided"}

        # Collect all parameter values and corresponding scores
        parameter_analysis = {}

        for config, results in all_results:
            metrics = self.analyze_parameter_performance(results, config)

            for param_name, param_value in config.items():
                if param_name not in parameter_analysis:
                    parameter_analysis[param_name] = {
                        'values': [],
                        'scores': [],
                        'correlation': 0.0,
                        'optimal_range': None,
                        'impact_level': 'unknown'
                    }

                parameter_analysis[param_name]['values'].append(param_value)
                parameter_analysis[param_name]['scores'].append(metrics.overall_score)

        # Analyze each parameter
        for param_name, analysis in parameter_analysis.items():
            values = analysis['values']
            scores = analysis['scores']

            # Calculate correlation (for numeric parameters)
            if all(isinstance(v, (int, float)) for v in values):
                try:
                    correlation, p_value = stats.pearsonr(values, scores)
                    analysis['correlation'] = correlation
                    analysis['correlation_significance'] = p_value < 0.05
                except:
                    analysis['correlation'] = 0.0
                    analysis['correlation_significance'] = False

            # Determine impact level
            if abs(analysis['correlation']) > 0.7:
                analysis['impact_level'] = 'high'
            elif abs(analysis['correlation']) > 0.3:
                analysis['impact_level'] = 'medium'
            else:
                analysis['impact_level'] = 'low'

            # Find optimal value/range
            best_idx = scores.index(max(scores))
            analysis['best_value'] = values[best_idx]
            analysis['best_score'] = scores[best_idx]

            # For numeric parameters, suggest optimal range
            if isinstance(values[best_idx], (int, float)):
                nearby_values = [(v, s) for v, s in zip(values, scores)
                               if abs(v - values[best_idx]) <= (max(values) - min(values)) * 0.2]
                if nearby_values:
                    analysis['optimal_range'] = {
                        'min': min(v for v, s in nearby_values),
                        'max': max(v for v, s in nearby_values),
                        'avg_score': sum(s for v, s in nearby_values) / len(nearby_values)
                    }

        return parameter_analysis

    def generate_optimization_suggestions(self, parameter_impact: Dict[str, Any],
                                        current_config: Dict[str, Any]) -> List[OptimizationSuggestion]:
        """Generate optimization suggestions based on parameter impact analysis"""
        suggestions = []

        for param_name, analysis in parameter_impact.items():
            if param_name not in current_config:
                continue

            current_value = current_config[param_name]
            best_value = analysis.get('best_value')

            if best_value is None or best_value == current_value:
                continue  # No improvement needed

            # Calculate expected improvement
            current_scores = [s for v, s in zip(analysis['values'], analysis['scores']) if v == current_value]
            if current_scores:
                current_avg = sum(current_scores) / len(current_scores)
                expected_improvement = ((analysis['best_score'] - current_avg) / current_avg) * 100
            else:
                expected_improvement = 0.0

            # Generate reasoning
            reasoning_parts = []
            if analysis['impact_level'] == 'high':
                reasoning_parts.append(f"Parameter has high impact on performance")
            if analysis.get('correlation_significance', False):
                reasoning_parts.append(f"Strong correlation with results (r={analysis['correlation']:.2f})")
            if expected_improvement > 5:
                reasoning_parts.append(f"Expected {expected_improvement:.1f}% performance improvement")

            if not reasoning_parts:
                continue  # No strong reason to suggest change

            confidence = min(0.95, abs(analysis['correlation'])) if analysis.get('correlation', 0) != 0 else 0.5

            suggestions.append(OptimizationSuggestion(
                parameter=param_name,
                current_value=current_value,
                suggested_value=best_value,
                expected_improvement=expected_improvement,
                confidence=confidence,
                reasoning=" | ".join(reasoning_parts)
            ))

        # Sort by expected improvement
        suggestions.sort(key=lambda x: x.expected_improvement, reverse=True)

        return suggestions

    def create_performance_dashboard(self, all_results: List[Tuple[Dict[str, Any], List[ComprehensiveEvaluationResult]]]) -> Dict[str, Any]:
        """Create a comprehensive performance dashboard"""
        if not all_results:
            return {"error": "No results provided"}

        # Analyze all configurations
        all_metrics = []
        for config, results in all_results:
            metrics = self.analyze_parameter_performance(results, config)
            all_metrics.append(metrics)

        # Sort by overall performance
        all_metrics.sort(key=lambda x: x.overall_score, reverse=True)

        # Find best configuration
        best_config = all_metrics[0] if all_metrics else None

        # Parameter impact analysis
        parameter_impact = self.analyze_parameter_impact(all_results)

        # Generate optimization suggestions for current config (assume first is current)
        current_config = all_results[0][0] if all_results else {}
        suggestions = self.generate_optimization_suggestions(parameter_impact, current_config)

        # Performance distribution
        overall_scores = [m.overall_score for m in all_metrics]
        performance_distribution = {
            'excellent': sum(1 for s in overall_scores if s >= 0.9),
            'good': sum(1 for s in overall_scores if 0.7 <= s < 0.9),
            'adequate': sum(1 for s in overall_scores if 0.5 <= s < 0.7),
            'poor': sum(1 for s in overall_scores if s < 0.5)
        }

        # Key insights
        insights = []
        if best_config:
            insights.append(f"Best performing configuration achieves {best_config.overall_score:.3f} overall score")
            insights.append(f"Average performance across all configurations: {statistics.mean(overall_scores):.3f}")
            insights.append(f"Performance variation (std dev): {statistics.stdev(overall_scores):.3f}")

        high_impact_params = [p for p, a in parameter_impact.items()
                            if a.get('impact_level') == 'high']
        if high_impact_params:
            insights.append(f"High impact parameters: {', '.join(high_impact_params)}")

        return {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_configurations': len(all_results),
                'best_overall_score': best_config.overall_score if best_config else 0.0,
                'average_score': statistics.mean(overall_scores) if overall_scores else 0.0,
                'performance_range': {
                    'min': min(overall_scores) if overall_scores else 0.0,
                    'max': max(overall_scores) if overall_scores else 0.0
                }
            },
            'best_configuration': asdict(best_config) if best_config else None,
            'performance_distribution': performance_distribution,
            'parameter_impact': parameter_impact,
            'optimization_suggestions': [asdict(s) for s in suggestions[:5]],  # Top 5 suggestions
            'all_configurations': [asdict(m) for m in all_metrics],
            'key_insights': insights
        }

    def export_performance_analysis(self, dashboard_data: Dict[str, Any],
                                  format_type: str = "json") -> str:
        """Export performance analysis to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if format_type.lower() == "json":
            filename = f"performance_analysis_{timestamp}.json"
            filepath = Path.cwd() / filename

            with open(filepath, 'w') as f:
                json.dump(dashboard_data, f, indent=2, default=str)

        elif format_type.lower() == "csv":
            filename = f"performance_analysis_{timestamp}.csv"
            filepath = Path.cwd() / filename

            with open(filepath, 'w', newline='') as f:
                writer = csv.writer(f)

                # Write summary
                writer.writerow(['Performance Analysis Summary'])
                writer.writerow(['Metric', 'Value'])
                summary = dashboard_data.get('summary', {})
                for key, value in summary.items():
                    writer.writerow([key, value])

                # Write configurations
                writer.writerow([])
                writer.writerow(['All Configurations Performance'])
                writer.writerow(['Overall Score', 'Objective Score', 'Reasoning Score',
                               'Execution Time', 'Reliability', 'Consistency'])

                for config in dashboard_data.get('all_configurations', []):
                    writer.writerow([
                        config.get('overall_score', ''),
                        config.get('objective_score', ''),
                        config.get('reasoning_score', ''),
                        config.get('execution_time', ''),
                        config.get('reliability_score', ''),
                        config.get('consistency_score', '')
                    ])

                # Write parameter impact
                writer.writerow([])
                writer.writerow(['Parameter Impact Analysis'])
                writer.writerow(['Parameter', 'Best Value', 'Best Score', 'Correlation', 'Impact Level'])

                param_impact = dashboard_data.get('parameter_impact', {})
                for param, impact in param_impact.items():
                    writer.writerow([
                        param,
                        impact.get('best_value', ''),
                        impact.get('best_score', ''),
                        impact.get('correlation', ''),
                        impact.get('impact_level', '')
                    ])

        else:
            raise ValueError(f"Unsupported export format: {format_type}")

        return str(filepath)


# Example usage
if __name__ == "__main__":
    # This would typically be used with actual test results
    system = PerformanceComparisonSystem()

    # Example of how it would be used:
    print("Performance Comparison System initialized")
    print("Ready to analyze parameter configurations and provide optimization suggestions")
    print("Use with actual test results from parameter comparison framework")