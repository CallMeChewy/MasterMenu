# File: parameter_test_framework.py
# Path: /home/herb/Desktop/LLM-Tester/parameter_test_framework.py
# Standard: AIDEV-PascalCase-2.1
# Created: 2025-10-01
# Last Modified: 2025-10-01 6:45PM

"""
Parameter Comparison Test Framework for LLM Models

This framework provides structured testing methodologies for comparing how different
parameter settings affect model performance, response quality, and behavior patterns.

Test Methodologies:
1. Single Parameter Isolation: Test one parameter at a time
2. Parameter Sweep: Systematic variation across parameter ranges
3. Cross-Parameter Interaction: Test parameter combinations
4. Statistical Significance: Multiple iterations to ensure reliability
"""

import json
import time
import statistics
from datetime import datetime
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass, asdict


@dataclass
class ParameterTestConfig:
    """Configuration for parameter comparison tests"""
    model_name: str
    base_parameters: Dict[str, Any]
    test_parameters: List[Dict[str, Any]]
    test_prompts: List[str]
    iterations_per_config: int
    metrics_to_collect: List[str]

    def __post_init__(self):
        # Validate configuration
        required_metrics = ['response_time', 'tokens_per_second', 'response_length']
        for metric in required_metrics:
            if metric not in self.metrics_to_collect:
                self.metrics_to_collect.append(metric)


@dataclass
class TestResult:
    """Individual test result with metadata"""
    test_id: str
    timestamp: str
    model_name: str
    parameters: Dict[str, Any]
    prompt: str
    response_text: str
    metrics: Dict[str, float]
    iteration_number: int
    config_label: str


@dataclass
class ParameterComparison:
    """Statistical comparison between parameter configurations"""
    config_a_label: str
    config_b_label: str
    metric_name: str
    a_mean: float
    b_mean: float
    a_std: float
    b_std: float
    improvement_percent: float
    statistical_significance: float  # p-value
    confidence_level: float
    recommendation: str  # "A better", "B better", "No significant difference"


class ParameterTestFramework:
    """Main framework for conducting parameter comparison tests"""

    def __init__(self):
        self.test_configs = {}
        self.test_results = []
        self.comparisons = []

    def load_test_configs(self, config_file: str):
        """Load test configurations from JSON file"""
        try:
            with open(config_file, 'r') as f:
                configs = json.load(f)
                for config_name, config_data in configs.items():
                    self.test_configs[config_name] = ParameterTestConfig(**config_data)
        except FileNotFoundError:
            print(f"Config file {config_file} not found. Using default configurations.")
            self._create_default_configs()

    def _create_default_configs(self):
        """Create default test configurations if none provided"""
        # Configuration for temperature testing
        temp_config = ParameterTestConfig(
            model_name="llama3.1:8b",
            base_parameters={"temperature": 0.7, "top_p": 0.9, "top_k": 40},
            test_parameters=[
                {"temperature": 0.1, "top_p": 0.9, "top_k": 40, "label": "Low Temp (0.1)"},
                {"temperature": 0.3, "top_p": 0.9, "top_k": 40, "label": "Medium-Low Temp (0.3)"},
                {"temperature": 0.5, "top_p": 0.9, "top_k": 40, "label": "Medium Temp (0.5)"},
                {"temperature": 0.7, "top_p": 0.9, "top_k": 40, "label": "Default Temp (0.7)"},
                {"temperature": 0.9, "top_p": 0.9, "top_k": 40, "label": "High Temp (0.9)"},
                {"temperature": 1.2, "top_p": 0.9, "top_k": 40, "label": "Very High Temp (1.2)"}
            ],
            test_prompts=self._get_default_test_prompts(),
            iterations_per_config=5,
            metrics_to_collect=['response_time', 'tokens_per_second', 'response_length']
        )

        self.test_configs['temperature_comparison'] = temp_config

        # Configuration for top_p testing
        topp_config = ParameterTestConfig(
            model_name="llama3.1:8b",
            base_parameters={"temperature": 0.7, "top_p": 0.9, "top_k": 40},
            test_parameters=[
                {"temperature": 0.7, "top_p": 0.1, "top_k": 40, "label": "Very Low Top_P (0.1)"},
                {"temperature": 0.7, "top_p": 0.5, "top_k": 40, "label": "Low Top_P (0.5)"},
                {"temperature": 0.7, "top_p": 0.8, "top_k": 40, "label": "Medium Top_P (0.8)"},
                {"temperature": 0.7, "top_p": 0.9, "top_k": 40, "label": "Default Top_P (0.9)"},
                {"temperature": 0.7, "top_p": 0.95, "top_k": 40, "label": "High Top_P (0.95)"},
                {"temperature": 0.7, "top_p": 1.0, "top_k": 40, "label": "Max Top_P (1.0)"}
            ],
            test_prompts=self._get_default_test_prompts(),
            iterations_per_config=5,
            metrics_to_collect=['response_time', 'tokens_per_second', 'response_length']
        )

        self.test_configs['top_p_comparison'] = topp_config

    def _get_default_test_prompts(self):
        """Get default test prompts for parameter comparison"""
        return [
            # Creative tasks
            "Write a short story about a robot learning to paint.",
            "Explain quantum computing to a 10-year-old child.",

            # Analytical tasks
            "Compare and contrast renewable energy sources.",
            "Analyze the ethical implications of artificial intelligence.",

            # Technical tasks
            "Write a Python function to calculate factorial recursively.",
            "Explain the difference between REST and GraphQL APIs.",

            # Reasoning tasks
            "If a bat and ball cost $1.10 together, and the bat costs $1.00 more than the ball, how much does the ball cost?",
            "Solve this logic puzzle: There are three boxes labeled incorrectly. How can you fix all labels by drawing from only one box?",

            # Code generation
            "Create a function that validates email addresses in JavaScript.",
            "Write a SQL query to find duplicate records in a table."
        ]

    def design_parameter_sweep(self, parameter_name: str, min_val: float, max_val: float, steps: int) -> List[Dict[str, Any]]:
        """Create a parameter sweep configuration"""
        step_size = (max_val - min_val) / (steps - 1)
        sweep_configs = []

        base_params = {"temperature": 0.7, "top_p": 0.9, "top_k": 40, "repeat_penalty": 1.1}

        for i in range(steps):
            value = min_val + (i * step_size)
            config = base_params.copy()
            config[parameter_name] = value
            config["label"] = f"{parameter_name}={value:.2f}"
            sweep_configs.append(config)

        return sweep_configs

    def design_isolation_test(self, target_parameter: str, test_values: List[float]) -> List[Dict[str, Any]]:
        """Design tests that isolate a single parameter"""
        base_params = {"temperature": 0.7, "top_p": 0.9, "top_k": 40, "repeat_penalty": 1.1}
        isolation_configs = []

        for value in test_values:
            config = base_params.copy()
            config[target_parameter] = value
            config["label"] = f"{target_parameter}={value}"
            isolation_configs.append(config)

        return isolation_configs

    def calculate_statistical_significance(self, values_a: List[float], values_b: List[float]) -> float:
        """Calculate p-value for statistical significance testing"""
        try:
            # Use simple t-test approximation
            mean_a = statistics.mean(values_a)
            mean_b = statistics.mean(values_b)
            std_a = statistics.stdev(values_a) if len(values_a) > 1 else 0
            std_b = statistics.stdev(values_b) if len(values_b) > 1 else 0

            # Simple t-statistic calculation
            pooled_std = ((std_a**2 / len(values_a)) + (std_b**2 / len(values_b)))**0.5
            if pooled_std > 0:
                t_stat = abs(mean_a - mean_b) / pooled_std
                # Approximate p-value (simplified)
                import math
                p_value = 2 * (1 - math.erf(t_stat / (2**0.5)))
                return min(p_value, 1.0)  # Cap at 1.0
            else:
                return 1.0  # No significant difference
        except:
            return 1.0  # Conservative default

    def compare_configurations(self, config_a: str, config_b: str, metric: str) -> ParameterComparison:
        """Compare two parameter configurations for a specific metric"""
        # Filter results for each configuration
        results_a = [r for r in self.test_results if r.config_label == config_a and metric in r.metrics]
        results_b = [r for r in self.test_results if r.config_label == config_b and metric in r.metrics]

        if len(results_a) < 3 or len(results_b) < 3:
            raise ValueError("Insufficient data for comparison (minimum 3 iterations per config)")

        values_a = [r.metrics[metric] for r in results_a]
        values_b = [r.metrics[metric] for r in results_b]

        # Calculate statistics
        mean_a = statistics.mean(values_a)
        mean_b = statistics.mean(values_b)
        std_a = statistics.stdev(values_a) if len(values_a) > 1 else 0
        std_b = statistics.stdev(values_b) if len(values_b) > 1 else 0

        # Calculate improvement percentage
        if mean_b != 0:
            improvement_percent = ((mean_a - mean_b) / mean_b) * 100
        else:
            improvement_percent = 0

        # Calculate statistical significance
        p_value = self.calculate_statistical_significance(values_a, values_b)

        # Determine recommendation
        alpha = 0.05  # 95% confidence level
        if p_value < alpha:
            if improvement_percent > 0:
                recommendation = f"{config_a} better"
            else:
                recommendation = f"{config_b} better"
        else:
            recommendation = "No significant difference"

        return ParameterComparison(
            config_a_label=config_a,
            config_b_label=config_b,
            metric_name=metric,
            a_mean=mean_a,
            b_mean=mean_b,
            a_std=std_a,
            b_std=std_b,
            improvement_percent=improvement_percent,
            statistical_significance=p_value,
            confidence_level=1.0 - alpha,
            recommendation=recommendation
        )

    def generate_test_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        if not self.test_results:
            return {"error": "No test results available"}

        # Group results by configuration
        config_groups = {}
        for result in self.test_results:
            if result.config_label not in config_groups:
                config_groups[result.config_label] = []
            config_groups[result.config_label].append(result)

        # Calculate summary statistics for each configuration
        summary = {}
        for config_label, results in config_groups.items():
            metrics_summary = {}
            for metric in ['response_time', 'tokens_per_second', 'response_length']:
                values = [r.metrics[metric] for r in results if metric in r.metrics]
                if values:
                    metrics_summary[metric] = {
                        "mean": statistics.mean(values),
                        "std": statistics.stdev(values) if len(values) > 1 else 0,
                        "min": min(values),
                        "max": max(values),
                        "count": len(values)
                    }
            summary[config_label] = metrics_summary

        # Generate comparisons between configurations
        comparisons = []
        config_labels = list(config_groups.keys())
        for i, config_a in enumerate(config_labels):
            for config_b in config_labels[i+1:]:
                for metric in ['response_time', 'tokens_per_second', 'response_length']:
                    try:
                        comparison = self.compare_configurations(config_a, config_b, metric)
                        comparisons.append(asdict(comparison))
                    except ValueError:
                        continue

        return {
            "test_summary": {
                "total_tests": len(self.test_results),
                "configurations_tested": len(config_groups),
                "test_timestamp": datetime.now().isoformat(),
                "models_tested": list(set(r.model_name for r in self.test_results))
            },
            "configuration_summaries": summary,
            "comparisons": comparisons
        }


# Example usage and test configurations
if __name__ == "__main__":
    framework = ParameterTestFramework()
    framework.load_test_configs("parameter_test_configs.json")

    print("Available test configurations:")
    for config_name in framework.test_configs.keys():
        print(f"  - {config_name}")

    print("\nFramework ready for parameter comparison testing!")