#!/usr/bin/env python3
# File: focused_parameter_test.py
# Path: /home/herb/Desktop/LLM-Tester/focused_parameter_test.py
# Standard: AIDEV-PascalCase-2.1
# Created: 2025-10-04
# Last Modified: 2025-10-04 04:01AM

"""
Focused Parameter Test - Proper statistical analysis for one prompt at a time
Tests each prompt with systematic parameter variations until optimal settings are found
"""

import pandas as pd
import numpy as np
import time
import json
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import statistics

@dataclass
class ParameterConfig:
    """Configuration for LLM parameters"""
    temperature: float
    num_ctx: int
    num_predict: int
    repeat_penalty: float
    top_k: int
    top_p: float

    def to_dict(self) -> Dict:
        return {
            'temperature': self.temperature,
            'num_ctx': self.num_ctx,
            'num_predict': self.num_predict,
            'repeat_penalty': self.repeat_penalty,
            'top_k': self.top_k,
            'top_p': self.top_p
        }

    def __str__(self) -> str:
        return f"T{self.temperature}_C{self.num_ctx}_P{self.num_predict}_R{self.repeat_penalty}_K{self.top_k}_P{self.top_p}"

@dataclass
class TestRun:
    """Single test run result"""
    config: ParameterConfig
    cycle: int
    response: str
    response_time: float
    accuracy_score: float
    token_count: int
    error_count: int

class FocusedParameterTest:
    """Focused parameter testing for a single prompt"""

    def __init__(self, prompt: str, model: str):
        self.prompt = prompt
        self.model = model
        self.test_runs: List[TestRun] = []
        self.best_config: Optional[ParameterConfig] = None
        self.best_score: float = 0.0

    def calculate_accuracy(self, response: str) -> float:
        """Calculate accuracy score for the response"""
        score = 1.0

        # Prompt-specific accuracy checks
        if "circle" in self.prompt.lower() and "area" in self.prompt.lower():
            # Circle area prompt
            if "math.pi" in response:
                score += 0.3
            if "maths.pi" in response:
                score -= 0.4
            if "import math" in response:
                score += 0.2
            if "def " in response and "return " in response:
                score += 0.2
            if "radius" in response:
                score += 0.1

        elif "prime" in self.prompt.lower():
            # Prime numbers prompt
            primes = ["2", "3", "5", "7", "11", "13", "17", "19", "23", "29"]
            prime_count = sum(1 for prime in primes if prime in response)
            score += min(0.4, prime_count * 0.04)
            if "def " in response:
                score += 0.2
            if "%" in response or "modulo" in response.lower():
                score += 0.1

        elif "email" in self.prompt.lower():
            # Email validation prompt
            if "@" in response and "." in response:
                score += 0.3
            if "re" in response or "regex" in response.lower():
                score += 0.2
            if "def " in response:
                score += 0.2

        elif "linked list" in self.prompt.lower():
            # Linked list prompt
            if "next" in response.lower():
                score += 0.2
            if "def " in response:
                score += 0.2
            if "class " in response:
                score += 0.1

        # General code quality
        if "```python" in response:
            score += 0.1
        if "Error" in response or "TODO" in response:
            score -= 0.2
        if len(response.split()) < 10:
            score -= 0.3

        return max(0.0, min(1.0, score))

    def generate_test_configurations(self) -> List[ParameterConfig]:
        """Generate systematic test configurations"""
        configs = []

        # Test temperature range systematically
        for temp in [0.1, 0.3, 0.5, 0.7, 0.9]:
            configs.append(ParameterConfig(
                temperature=temp,
                num_ctx=2048,
                num_predict=512,
                repeat_penalty=1.1,
                top_k=25,
                top_p=0.9
            ))

        # Test context sizes
        for ctx in [1024, 2048, 4096, 8192]:
            configs.append(ParameterConfig(
                temperature=0.5,
                num_ctx=ctx,
                num_predict=512,
                repeat_penalty=1.1,
                top_k=25,
                top_p=0.9
            ))

        # Test output limits
        for pred in [256, 512, 1024, 2048]:
            configs.append(ParameterConfig(
                temperature=0.5,
                num_ctx=2048,
                num_predict=pred,
                repeat_penalty=1.1,
                top_k=25,
                top_p=0.9
            ))

        # Test repeat penalties
        for repeat in [1.0, 1.1, 1.2, 1.3]:
            configs.append(ParameterConfig(
                temperature=0.5,
                num_ctx=2048,
                num_predict=512,
                repeat_penalty=repeat,
                top_k=25,
                top_p=0.9
            ))

        # Test top_k values
        for k in [10, 20, 30, 40, 50]:
            configs.append(ParameterConfig(
                temperature=0.5,
                num_ctx=2048,
                num_predict=512,
                repeat_penalty=1.1,
                top_k=k,
                top_p=0.9
            ))

        # Test top_p values
        for p in [0.8, 0.85, 0.9, 0.95, 1.0]:
            configs.append(ParameterConfig(
                temperature=0.5,
                num_ctx=2048,
                num_predict=512,
                repeat_penalty=1.1,
                top_k=25,
                top_p=p
            ))

        # Add some combined best configs
        best_combos = [
            (0.3, 1024, 256, 1.2, 20, 0.85),  # Conservative
            (0.5, 2048, 512, 1.1, 25, 0.9),   # Balanced
            (0.7, 1024, 512, 1.0, 40, 0.95),   # Fast
            (0.4, 4096, 1024, 1.15, 30, 0.88), # High quality
        ]

        for combo in best_combos:
            configs.append(ParameterConfig(*combo))

        return configs

    def test_configuration(self, config: ParameterConfig, cycles: int = 5) -> List[TestRun]:
        """Test a configuration multiple times for statistical significance"""
        runs = []

        print(f"\n🔧 Testing configuration: {config}")
        print(f"   📋 Temperature: {config.temperature}, Context: {config.num_ctx}, Predict: {config.num_predict}")
        print(f"   🔄 Running {cycles} cycles for statistical significance...")

        for cycle in range(cycles):
            try:
                start_time = time.time()

                # Call the actual model (this would need to be connected to your LLM-Tester)
                response = self.call_model_with_config(config)

                end_time = time.time()

                # Calculate metrics
                response_time = end_time - start_time
                accuracy = self.calculate_accuracy(response)
                token_count = len(response.split())
                error_count = response.count("Error") + response.count("TODO")

                run = TestRun(
                    config=config,
                    cycle=cycle + 1,
                    response=response,
                    response_time=response_time,
                    accuracy_score=accuracy,
                    token_count=token_count,
                    error_count=error_count
                )

                runs.append(run)
                self.test_runs.append(run)

                print(f"      Cycle {cycle + 1}: {accuracy:.3f} accuracy, {response_time:.1f}s, {token_count} tokens")

            except Exception as e:
                print(f"      Cycle {cycle + 1}: ERROR - {e}")

        return runs

    def call_model_with_config(self, config: ParameterConfig) -> str:
        """Call the model with specific parameters (mock for demo)"""
        # Simulate model response time based on parameters
        base_time = 3.0 if "3.8b" in self.model else 8.0
        time_factor = (2.0 - config.temperature) + (config.num_predict / 512) + (config.num_ctx / 4096)
        time.sleep(base_time * time_factor * 0.05)  # Scale down for demo

        # Generate mock response based on prompt and config
        if "circle" in self.prompt.lower():
            if config.temperature < 0.4:
                return f"""```python
import math

def circle_area(radius):
    \"\"\"Calculate the area of a circle given its radius.\"\"\"
    return math.pi * radius ** 2

# Example
area = circle_area(5)
print(f"Area: {{area}}")
```"""
            elif config.temperature > 0.6:
                return f"""```python
import maths
def area(r):
    return maths.pi * r * r
print(area(5))
```"""
            else:
                return f"""```python
import math
def circle_area(radius):
    return math.pi * radius ** 2
```"""

        elif "prime" in self.prompt.lower():
            if config.temperature < 0.4:
                return """```python
def is_prime(n):
    if n < 2:
        return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False
    return True

primes = [i for i in range(2, 30) if is_prime(i)]
print(primes)  # [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]
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
            return f"```python\n# Response for {self.prompt[:30]}...\n# Temp: {config.temperature}\ndef solution():\n    return 'result'\n```"

    def run_optimization(self, cycles_per_config: int = 5) -> None:
        """Run complete parameter optimization"""
        print(f"🎯 FOCUSED PARAMETER OPTIMIZATION")
        print(f"=" * 60)
        print(f"📝 Prompt: {self.prompt}")
        print(f"🤖 Model: {self.model}")
        print(f"🔧 Testing parameter space systematically...")
        print(f"📊 Cycles per configuration: {cycles_per_config}")
        print("=" * 60)

        configs = self.generate_test_configurations()
        print(f"📋 Generated {len(configs)} test configurations")

        results_summary = []

        for i, config in enumerate(configs, 1):
            print(f"\n📍 Configuration {i}/{len(configs)}")

            # Test this configuration multiple times
            runs = self.test_configuration(config, cycles_per_config)

            if runs:
                # Calculate statistics
                accuracies = [r.accuracy_score for r in runs]
                times = [r.response_time for r in runs]
                tokens = [r.token_count for r in runs]

                avg_accuracy = statistics.mean(accuracies)
                std_accuracy = statistics.stdev(accuracies) if len(accuracies) > 1 else 0
                avg_time = statistics.mean(times)
                avg_tokens = statistics.mean(tokens)

                results_summary.append({
                    'config': config,
                    'avg_accuracy': avg_accuracy,
                    'std_accuracy': std_accuracy,
                    'avg_time': avg_time,
                    'avg_tokens': avg_tokens,
                    'runs': len(runs)
                })

                print(f"   📊 Results: {avg_accuracy:.3f} ± {std_accuracy:.3f} accuracy, {avg_time:.1f}s avg")

                # Update best if this is better
                if avg_accuracy > self.best_score:
                    self.best_score = avg_accuracy
                    self.best_config = config
                    print(f"   🏆 NEW BEST! Accuracy: {avg_accuracy:.3f}")

        # Final analysis
        self.analyze_results(results_summary)

    def analyze_results(self, results_summary: List[Dict]) -> None:
        """Analyze the test results and find optimal parameters"""
        print(f"\n📊 OPTIMIZATION ANALYSIS")
        print("=" * 60)

        if not results_summary:
            print("❌ No successful test runs!")
            return

        # Sort by accuracy
        results_summary.sort(key=lambda x: x['avg_accuracy'], reverse=True)

        print(f"\n🏆 TOP 5 CONFIGURATIONS:")
        for i, result in enumerate(results_summary[:5], 1):
            config = result['config']
            print(f"\n{i}. Configuration: {config}")
            print(f"   🎯 Accuracy: {result['avg_accuracy']:.3f} ± {result['std_accuracy']:.3f}")
            print(f"   ⏱️  Time: {result['avg_time']:.1f}s")
            print(f"   📝 Tokens: {result['avg_tokens']:.0f}")

        # Parameter analysis
        print(f"\n🔍 PARAMETER PERFORMANCE ANALYSIS:")
        param_analysis = {
            'temperature': {},
            'num_ctx': {},
            'num_predict': {},
            'repeat_penalty': {},
            'top_k': {},
            'top_p': {}
        }

        for result in results_summary:
            config = result['config']
            accuracy = result['avg_accuracy']

            for param_name, param_value in [
                ('temperature', config.temperature),
                ('num_ctx', config.num_ctx),
                ('num_predict', config.num_predict),
                ('repeat_penalty', config.repeat_penalty),
                ('top_k', config.top_k),
                ('top_p', config.top_p)
            ]:
                if param_value not in param_analysis[param_name]:
                    param_analysis[param_name][param_value] = []
                param_analysis[param_name][param_value].append(accuracy)

        print(f"\n📈 BEST PARAMETER VALUES:")
        for param_name, values in param_analysis.items():
            if values:
                # Find best performing value
                best_value = max(values.keys(), key=lambda k: np.mean(values[k]))
                avg_performance = np.mean(values[best_value])
                print(f"   {param_name}: {best_value} (avg accuracy: {avg_performance:.3f})")

        # Convergence analysis
        print(f"\n📊 CONVERGENCE ANALYSIS:")
        if self.best_config:
            best_results = [r for r in results_summary if r['config'].temperature == self.best_config.temperature and
                           r['config'].num_ctx == self.best_config.num_ctx]
            if best_results:
                print(f"   🎯 Best accuracy achieved: {self.best_score:.3f}")
                print(f"   ⚙️  Optimal parameters: {self.best_config}")
                print(f"   📈 Parameter space explored: {len(results_summary)} configurations")
                print(f"   🔄 Total test runs: {sum(r['runs'] for r in results_summary)}")

        # Save results
        self.save_optimization_results(results_summary)

    def save_optimization_results(self, results_summary: List[Dict]) -> None:
        """Save optimization results to file"""
        filename = f"parameter_optimization_{self.model}_{int(time.time())}.json"

        data = {
            'prompt': self.prompt,
            'model': self.model,
            'timestamp': time.time(),
            'best_config': self.best_config.to_dict() if self.best_config else None,
            'best_score': self.best_score,
            'total_configurations_tested': len(results_summary),
            'total_runs': len(self.test_runs),
            'results_summary': [
                {
                    'config': r['config'].to_dict(),
                    'avg_accuracy': r['avg_accuracy'],
                    'std_accuracy': r['std_accuracy'],
                    'avg_time': r['avg_time'],
                    'avg_tokens': r['avg_tokens'],
                    'runs': r['runs']
                }
                for r in results_summary
            ],
            'detailed_runs': [
                {
                    'config': run.config.to_dict(),
                    'cycle': run.cycle,
                    'accuracy': run.accuracy_score,
                    'time': run.response_time,
                    'tokens': run.token_count
                }
                for run in self.test_runs
            ]
        }

        with open(filename, 'w') as f:
            json.dump(data, f, indent=2, default=str)

        print(f"\n💾 Results saved to: {filename}")

def test_single_prompt():
    """Test optimization for a single prompt"""
    prompt = "Create a Python function to calculate the area of a circle given its radius."
    model = "phi3:3.8b"

    tester = FocusedParameterTest(prompt, model)
    tester.run_optimization(cycles_per_config=3)

if __name__ == "__main__":
    test_single_prompt()