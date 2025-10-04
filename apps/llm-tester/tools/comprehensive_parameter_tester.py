#!/usr/bin/env python3
# File: comprehensive_parameter_tester.py
# Path: /home/herb/Desktop/LLM-Tester/comprehensive_parameter_tester.py
# Standard: AIDEV-PascalCase-2.1
# Created: 2025-10-04
# Last Modified: 2025-10-04 03:52AM

"""
Comprehensive Parameter Tester - Proper statistical analysis of LLM parameters
Tests each prompt with multiple parameter combinations and multiple cycles for significance
"""

import pandas as pd
import numpy as np
import time
import json
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import itertools

@dataclass
class TestConfiguration:
    """Configuration for a single parameter test"""
    temperature: float
    num_ctx: int
    num_predict: int
    repeat_penalty: float
    top_k: int
    top_p: float

    def to_dict(self) -> Dict:
        return asdict(self)

    def get_id(self) -> str:
        """Get unique ID for this configuration"""
        return f"t{self.temperature}_c{self.num_ctx}_p{self.num_predict}_r{self.repeat_penalty}_k{self.top_k}_p{self.top_p}"

@dataclass
class TestResult:
    """Results from a single test run"""
    config: TestConfiguration
    prompt: str
    model: str
    cycle: int
    response: str
    response_time: float
    accuracy_score: float
    error_count: int
    token_count: int

    def to_dict(self) -> Dict:
        return {
            'config_id': self.config.get_id(),
            'config': self.config.to_dict(),
            'prompt': self.prompt,
            'model': self.model,
            'cycle': self.cycle,
            'response': self.response,
            'response_time': self.response_time,
            'accuracy_score': self.accuracy_score,
            'error_count': self.error_count,
            'token_count': self.token_count
        }

class ComprehensiveParameterTester:
    """Comprehensive parameter testing system"""

    def __init__(self, models: List[str], prompts: List[str]):
        self.models = models
        self.prompts = prompts
        self.results: List[TestResult] = []
        self.best_results: Dict[str, TestResult] = {}  # best result per prompt/model

        # Define parameter ranges to test
        self.parameter_ranges = {
            'temperature': [0.3, 0.5, 0.7],
            'num_ctx': [1024, 2048, 4096],
            'num_predict': [256, 512, 1024],
            'repeat_penalty': [1.0, 1.1, 1.2],
            'top_k': [20, 30, 40],
            'top_p': [0.85, 0.9, 0.95]
        }

        # Generate all combinations (reduced for practicality)
        self.configurations = self._generate_test_configurations()

    def _generate_test_configurations(self) -> List[TestConfiguration]:
        """Generate test configurations - sample the parameter space intelligently"""
        configs = []

        # Start with some sensible baseline configurations
        baseline_configs = [
            # Conservative (accuracy first)
            TestConfiguration(0.3, 2048, 512, 1.2, 20, 0.85),
            # Balanced
            TestConfiguration(0.5, 2048, 512, 1.1, 25, 0.9),
            # Fast (speed first)
            TestConfiguration(0.7, 1024, 256, 1.0, 40, 0.95),
            # High context
            TestConfiguration(0.5, 4096, 1024, 1.1, 25, 0.9),
            # Low context
            TestConfiguration(0.7, 1024, 512, 1.0, 30, 0.95),
        ]

        # Add some systematic variations
        for temp in [0.3, 0.5, 0.7]:
            for ctx in [1024, 2048, 4096]:
                for pred in [256, 512, 1024]:
                    configs.append(TestConfiguration(
                        temperature=temp,
                        num_ctx=ctx,
                        num_predict=pred,
                        repeat_penalty=1.1,
                        top_k=25,
                        top_p=0.9
                    ))

        # Add baseline configs
        configs.extend(baseline_configs)

        # Remove duplicates and limit to reasonable number
        unique_configs = []
        seen_ids = set()
        for config in configs:
            config_id = config.get_id()
            if config_id not in seen_ids:
                seen_ids.add(config_id)
                unique_configs.append(config)

        return unique_configs[:20]  # Limit to 20 configurations for practical testing

    def calculate_accuracy(self, prompt: str, response: str) -> float:
        """Calculate accuracy score for a prompt-response pair"""
        score = 1.0

        # Check for specific errors based on prompt type
        if "circle" in prompt.lower() and "area" in prompt.lower():
            # Circle area specific checks
            if "math.pi" not in response:
                score -= 0.4
            if "maths.pi" in response:  # Wrong module
                score -= 0.5
            if "def " in response and "return " in response:
                score += 0.2
            if "import math" in response:
                score += 0.2

        elif "prime" in prompt.lower():
            # Prime number specific checks
            if any(num in response for num in ["2, 3, 5, 7, 11, 13, 17, 19, 23, 29"]):
                score += 0.3
            if "for " in response and "%" in response:
                score += 0.2
            if "def " in response:
                score += 0.2

        elif "email" in prompt.lower():
            # Email validation specific checks
            if "@" in response and "." in response:
                score += 0.3
            if "import re" in response or "regex" in response.lower():
                score += 0.2
            if "def " in response:
                score += 0.2

        elif "linked list" in prompt.lower():
            # Linked list specific checks
            if "class " in response or "struct " in response:
                score += 0.2
            if "next" in response.lower():
                score += 0.2
            if "def " in response:
                score += 0.2

        # General coding checks
        if "```python" in response or "def " in response:
            score += 0.1
        if "SyntaxError" in response or "NameError" in response:
            score -= 0.3
        if "TODO" in response or "FIXME" in response:
            score -= 0.2

        # Check for reasonable length
        if len(response.split()) < 20:
            score -= 0.3
        elif len(response.split()) > 500:
            score -= 0.1

        return max(0.0, min(1.0, score))

    def run_comprehensive_test(self, cycles_per_config: int = 3, model_test_func=None) -> None:
        """Run comprehensive parameter testing"""
        print("🔬 COMPREHENSIVE PARAMETER TESTING")
        print("=" * 60)
        print(f"📊 Testing {len(self.models)} models × {len(self.prompts)} prompts × {len(self.configurations)} configs × {cycles_per_config} cycles")
        print(f"🔄 Total tests: {len(self.models) * len(self.prompts) * len(self.configurations) * cycles_per_config}")
        print("=" * 60)

        total_tests = len(self.models) * len(self.prompts) * len(self.configurations) * cycles_per_config
        test_count = 0

        for model in self.models:
            print(f"\n🤖 Testing model: {model}")
            print("-" * 40)

            for prompt in self.prompts:
                print(f"\n📝 Prompt: {prompt[:50]}...")

                # Track best result for this prompt/model
                best_score = 0.0
                best_config = None
                best_results = []

                for config in self.configurations:
                    print(f"\n🔧 Testing config: {config.get_id()}")

                    # Run multiple cycles for statistical significance
                    cycle_results = []
                    for cycle in range(cycles_per_config):
                        test_count += 1
                        progress = (test_count / total_tests) * 100
                        print(f"  🔄 Cycle {cycle + 1}/{cycles_per_config} [{progress:.1f}%]")

                        # Call the model with current parameters
                        try:
                            start_time = time.time()

                            if model_test_func:
                                response = model_test_func(model, prompt, config.to_dict())
                            else:
                                # Mock response for demo
                                response = self._mock_model_response(prompt, config, model)

                            end_time = time.time()

                            # Calculate metrics
                            response_time = end_time - start_time
                            accuracy = self.calculate_accuracy(prompt, response)
                            error_count = response.count("Error") + response.count("TODO")
                            token_count = len(response.split())

                            result = TestResult(
                                config=config,
                                prompt=prompt,
                                model=model,
                                cycle=cycle + 1,
                                response=response,
                                response_time=response_time,
                                accuracy_score=accuracy,
                                error_count=error_count,
                                token_count=token_count
                            )

                            self.results.append(result)
                            cycle_results.append(result)

                            print(f"    ⏱️  {response_time:.1f}s | 🎯 {accuracy:.3f} | 📝 {token_count} tokens")

                        except Exception as e:
                            print(f"    ❌ Error: {e}")
                            continue

                    # Calculate average for this configuration
                    if cycle_results:
                        avg_accuracy = np.mean([r.accuracy_score for r in cycle_results])
                        avg_time = np.mean([r.response_time for r in cycle_results])

                        print(f"  📊 Config average: {avg_accuracy:.3f} accuracy, {avg_time:.1f}s")

                        # Update best if this is better
                        if avg_accuracy > best_score:
                            best_score = avg_accuracy
                            best_config = config
                            best_results = cycle_results

                            print(f"  🏆 NEW BEST! Score: {best_score:.3f}")

                # Store best result for this prompt/model
                if best_config and best_results:
                    avg_result = TestResult(
                        config=best_config,
                        prompt=prompt,
                        model=model,
                        cycle=0,  # Summary result
                        response=best_results[0].response,
                        response_time=np.mean([r.response_time for r in best_results]),
                        accuracy_score=best_score,
                        error_count=int(np.mean([r.error_count for r in best_results])),
                        token_count=int(np.mean([r.token_count for r in best_results]))
                    )
                    self.best_results[f"{model}_{prompt[:30]}"] = avg_result

                    print(f"\n✅ Best for {model}/{prompt[:30]}: {best_score:.3f}")
                    print(f"   Config: {best_config.get_id()}")

    def _mock_model_response(self, prompt: str, config: TestConfiguration, model: str) -> str:
        """Mock model response for testing (replace with actual model calls)"""
        # Simulate processing time based on parameters
        base_time = 2.0 if "3.8b" in model else 5.0
        time_factor = (1.0 - config.temperature) * 2 + (config.num_predict / 512) + (config.num_ctx / 2048)
        time.sleep(base_time * time_factor * 0.1)  # Scale down for demo

        # Generate mock response based on prompt and parameters
        if "circle" in prompt.lower():
            if config.temperature < 0.4:
                return f"""```python
import math

def circle_area(radius):
    \"\"\"Calculate the area of a circle given its radius.\"\"\"
    return math.pi * radius ** 2

# Example usage
area = circle_area(5)
print(f"The area is {area:.2f}")
```"""
            elif config.temperature > 0.6:
                return f"""```python
import maths

def circle_area(r):
    return maths.pi * r * r

print(circle_area(5))
```"""
            else:
                return f"""```python
import math
def circle_area(radius):
    return math.pi * radius ** 2
```"""

        elif "prime" in prompt.lower():
            if config.temperature < 0.4:
                return """```python
def is_prime(n):
    \"\"\"Check if a number is prime.\"\"\"
    if n < 2:
        return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False
    return True

# Print primes under 30
primes = [n for n in range(2, 30) if is_prime(n)]
print(primes)
```"""
            else:
                return """```python
def find_primes(limit):
    primes = []
    for num in range(2, limit):
        is_prime = True
        for i in range(2, num):
            if num % i == 0:
                is_prime = False
                break
        if is_prime:
            primes.append(num)
    return primes

print(find_primes(30))
```"""

        else:
            return f"```python\n# Response for prompt: {prompt[:50]}...\n# Temperature: {config.temperature}\ndef solution():\n    pass\n```"

    def generate_optimization_report(self) -> Dict:
        """Generate comprehensive optimization report"""
        print("\n📊 GENERATING OPTIMIZATION REPORT")
        print("=" * 50)

        report = {
            'test_summary': {
                'total_models': len(self.models),
                'total_prompts': len(self.prompts),
                'total_configurations': len(self.configurations),
                'total_tests': len(self.results),
                'best_results': len(self.best_results)
            },
            'model_performance': {},
            'prompt_specific_optimal': {},
            'parameter_analysis': {},
            'recommendations': []
        }

        # Analyze model performance
        for model in self.models:
            model_results = [r for r in self.best_results.values() if r.model == model]
            if model_results:
                avg_accuracy = np.mean([r.accuracy_score for r in model_results])
                avg_time = np.mean([r.response_time for r in model_results])

                report['model_performance'][model] = {
                    'average_accuracy': avg_accuracy,
                    'average_time': avg_time,
                    'best_prompt': max(model_results, key=lambda x: x.accuracy_score).prompt[:50],
                    'best_accuracy': max([r.accuracy_score for r in model_results]),
                    'optimal_config': max(model_results, key=lambda x: x.accuracy_score).config.to_dict()
                }

        # Prompt-specific optimal settings
        for prompt in self.prompts:
            prompt_key = prompt[:30]
            prompt_results = {}

            for model in self.models:
                key = f"{model}_{prompt_key}"
                if key in self.best_results:
                    result = self.best_results[key]
                    prompt_results[model] = {
                        'accuracy': result.accuracy_score,
                        'time': result.response_time,
                        'config': result.config.to_dict()
                    }

            report['prompt_specific_optimal'][prompt[:50]] = prompt_results

        # Parameter analysis
        param_performance = {}
        for param in ['temperature', 'num_ctx', 'num_predict', 'repeat_penalty', 'top_k', 'top_p']:
            param_performance[param] = {}

            for result in self.best_results.values():
                value = getattr(result.config, param)
                if value not in param_performance[param]:
                    param_performance[param][value] = []
                param_performance[param][value].append(result.accuracy_score)

            # Calculate average performance for each parameter value
            for value in param_performance[param]:
                param_performance[param][value] = np.mean(param_performance[param][value])

        report['parameter_analysis'] = param_performance

        # Generate recommendations
        best_overall = max(self.best_results.values(), key=lambda x: x.accuracy_score)
        report['recommendations'].append({
            'type': 'best_overall',
            'model': best_overall.model,
            'prompt': best_overall.prompt[:50],
            'accuracy': best_overall.accuracy_score,
            'config': best_overall.config.to_dict()
        })

        # Find best parameter values
        best_params = {}
        for param, values in param_performance.items():
            if values:
                best_value = max(values.keys(), key=lambda k: values[k])
                best_params[param] = {
                    'value': best_value,
                    'performance': values[best_value]
                }

        report['recommendations'].append({
            'type': 'best_parameters',
            'parameters': best_params
        })

        return report

    def save_results(self, filename: str = None) -> None:
        """Save all results to file"""
        if filename is None:
            filename = f"comprehensive_test_results_{int(time.time())}.json"

        data = {
            'test_info': {
                'timestamp': time.time(),
                'models': self.models,
                'prompts': self.prompts,
                'configurations_tested': len(self.configurations)
            },
            'results': [r.to_dict() for r in self.results],
            'best_results': {k: r.to_dict() for k, r in self.best_results.items()},
            'optimization_report': self.generate_optimization_report()
        }

        with open(filename, 'w') as f:
            json.dump(data, f, indent=2, default=str)

        print(f"💾 Results saved to: {filename}")

    def print_optimization_summary(self) -> None:
        """Print a clear optimization summary"""
        report = self.generate_optimization_report()

        print("\n🎯 COMPREHENSIVE OPTIMIZATION RESULTS")
        print("=" * 60)

        print("\n📊 MODEL PERFORMANCE:")
        for model, perf in report['model_performance'].items():
            print(f"\n🤖 {model}:")
            print(f"   📈 Average Accuracy: {perf['average_accuracy']:.3f}")
            print(f"   ⏱️  Average Time: {perf['average_time']:.1f}s")
            print(f"   🏆 Best Accuracy: {perf['best_accuracy']:.3f}")
            print(f"   📋 Best Prompt: {perf['best_prompt']}")
            print(f"   🔧 Optimal Config: {perf['optimal_config']}")

        print("\n📝 PROMPT-SPECIFIC OPTIMAL SETTINGS:")
        for prompt, models in report['prompt_specific_optimal'].items():
            print(f"\n📋 {prompt}:")
            for model, result in models.items():
                print(f"   🤖 {model}:")
                print(f"      🎯 Accuracy: {result['accuracy']:.3f}")
                print(f"      ⏱️  Time: {result['time']:.1f}s")
                print(f"      🔧 Config: {result['config']}")

        print("\n🔍 PARAMETER PERFORMANCE ANALYSIS:")
        for param, values in report['parameter_analysis'].items():
            best_value = max(values.keys(), key=lambda k: values[k])
            print(f"\n⚙️  {param}:")
            print(f"   🏆 Best Value: {best_value} (avg accuracy: {values[best_value]:.3f})")
            for value, perf in sorted(values.items(), key=lambda x: x[1], reverse=True)[:3]:
                print(f"   📊 {value}: {perf:.3f}")

        print("\n💡 RECOMMENDATIONS:")
        for rec in report['recommendations']:
            if rec['type'] == 'best_overall':
                print(f"\n🏆 BEST OVERALL COMBINATION:")
                print(f"   🤖 Model: {rec['model']}")
                print(f"   📋 Prompt: {rec['prompt']}")
                print(f"   🎯 Accuracy: {rec['accuracy']:.3f}")
                print(f"   🔧 Parameters: {rec['config']}")
            elif rec['type'] == 'best_parameters':
                print(f"\n⚙️  BEST PARAMETER VALUES:")
                for param, info in rec['parameters'].items():
                    print(f"   {param}: {info['value']} (performance: {info['performance']:.3f})")

def demo_comprehensive_tester():
    """Demo the comprehensive parameter tester"""
    models = ["phi3:3.8b", "phi3:14b"]
    prompts = [
        "Create a Python function to calculate the area of a circle given its radius.",
        "Write a program to print all prime numbers under 30.",
        "Write a program that validates if a string is a valid email address.",
        "Create a function to reverse a linked list in-place."
    ]

    tester = ComprehensiveParameterTester(models, prompts)

    # Run the test (with mock responses for demo)
    tester.run_comprehensive_test(cycles_per_config=2)

    # Generate and display results
    tester.print_optimization_summary()
    tester.save_results()

    return tester

if __name__ == "__main__":
    demo_comprehensive_tester()