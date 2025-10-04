#!/usr/bin/env python3
# File: adaptive_parameter_optimizer.py
# Path: /home/herb/Desktop/LLM-Tester/adaptive_parameter_optimizer.py
# Standard: AIDEV-PascalCase-2.1
# Created: 2025-10-04
# Last Modified: 2025-10-04 03:05AM

"""
Adaptive Parameter Optimizer - Self-tuning mechanism for finding optimal LLM parameters
that balance accuracy (must be perfect) and speed (as fast as possible).
"""

import time
import json
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

class OptimizationStrategy(Enum):
    ACCURACY_FIRST = "accuracy_first"      # Must be 100% accurate, speed secondary
    SPEED_FIRST = "speed_first"            # Must be fast, accuracy acceptable
    BALANCED = "balanced"                  # Optimize both equally

@dataclass
class ParameterSet:
    """Represents a set of LLM parameters"""
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

@dataclass
class TestResult:
    """Results from a single parameter test"""
    parameters: ParameterSet
    accuracy_score: float  # 0.0 to 1.0
    response_time: float
    token_count: int
    error_count: int
    code_quality_score: float  # 0.0 to 1.0

    @property
    def speed_score(self) -> float:
        """Calculate speed score (lower time = higher score)"""
        # Normalize: 1s = 1.0, 60s = 0.0
        return max(0.0, 1.0 - (self.response_time / 60.0))

    @property
    def efficiency_score(self) -> float:
        """Overall efficiency score combining accuracy and speed"""
        return self.accuracy_score * 0.7 + self.speed_score * 0.3

class AdaptiveParameterOptimizer:
    """Self-tuning parameter optimization system"""

    def __init__(self, model_name: str, optimization_strategy: OptimizationStrategy = OptimizationStrategy.BALANCED):
        self.model_name = model_name
        self.strategy = optimization_strategy
        self.test_history: List[TestResult] = []
        self.best_result: Optional[TestResult] = None

        # Parameter search space
        self.param_ranges = {
            'temperature': (0.1, 1.0, 0.1),      # min, max, step
            'num_ctx': (1024, 4096, 512),
            'num_predict': (128, 1024, 128),
            'repeat_penalty': (1.0, 1.5, 0.1),
            'top_k': (10, 50, 5),
            'top_p': (0.7, 1.0, 0.05)
        }

        # Starting parameters based on model size
        self.start_params = self._get_starting_parameters()

    def _get_starting_parameters(self) -> ParameterSet:
        """Get sensible starting parameters based on model size"""
        if "3.8b" in self.model_name.lower() or "small" in self.model_name.lower():
            return ParameterSet(
                temperature=0.5,
                num_ctx=2048,
                num_predict=512,
                repeat_penalty=1.1,
                top_k=25,
                top_p=0.9
            )
        else:  # Large models
            return ParameterSet(
                temperature=0.3,
                num_ctx=2048,
                num_predict=256,
                repeat_penalty=1.2,
                top_k=20,
                top_p=0.85
            )

    def generate_parameter_variations(self, base_params: ParameterSet, generation: int) -> List[ParameterSet]:
        """Generate parameter variations based on optimization strategy"""
        variations = []

        # Adapt step size based on generation
        step_multiplier = max(0.1, 1.0 / (generation * 0.5))

        # Generate variations using different strategies
        strategies = [
            self._vary_temperature,
            self._vary_context_and_output,
            self._vary_sampling,
            self._balanced_variation
        ]

        for strategy in strategies:
            var_params = strategy(base_params, step_multiplier)
            if var_params not in variations:
                variations.append(var_params)

        # Add some random exploration
        for _ in range(min(3, generation)):
            random_params = self._random_variation(base_params, step_multiplier)
            if random_params not in variations:
                variations.append(random_params)

        return variations[:min(8, len(variations))]  # Limit variations per iteration

    def _vary_temperature(self, base: ParameterSet, multiplier: float) -> ParameterSet:
        """Vary temperature for accuracy/speed balance"""
        temp_range = self.param_ranges['temperature']
        step = (temp_range[1] - temp_range[0]) * multiplier * 0.2

        new_temp = max(temp_range[0], min(temp_range[1], base.temperature + step))
        return ParameterSet(
            temperature=new_temp,
            num_ctx=base.num_ctx,
            num_predict=base.num_predict,
            repeat_penalty=base.repeat_penalty,
            top_k=base.top_k,
            top_p=base.top_p
        )

    def _vary_context_and_output(self, base: ParameterSet, multiplier: float) -> ParameterSet:
        """Vary context and prediction limits for efficiency"""
        ctx_range = self.param_ranges['num_ctx']
        pred_range = self.param_ranges['num_predict']

        # Reduce context and output for speed
        if self.strategy == OptimizationStrategy.SPEED_FIRST:
            ctx_step = -ctx_range[2] * multiplier * 2
            pred_step = -pred_range[2] * multiplier * 2
        else:
            ctx_step = ctx_range[2] * multiplier
            pred_step = pred_range[2] * multiplier

        new_ctx = max(ctx_range[0], min(ctx_range[1], base.num_ctx + ctx_step))
        new_pred = max(pred_range[0], min(pred_range[1], base.num_predict + pred_step))

        return ParameterSet(
            temperature=base.temperature,
            num_ctx=int(new_ctx),
            num_predict=int(new_pred),
            repeat_penalty=base.repeat_penalty,
            top_k=base.top_k,
            top_p=base.top_p
        )

    def _vary_sampling(self, base: ParameterSet, multiplier: float) -> ParameterSet:
        """Vary sampling parameters (top_k, top_p, repeat_penalty)"""
        new_top_k = max(10, min(50, int(base.top_k * (1 + multiplier * 0.2))))
        new_top_p = max(0.7, min(1.0, base.top_p + (multiplier * 0.05)))
        new_repeat = max(1.0, min(1.5, base.repeat_penalty + (multiplier * 0.05)))

        return ParameterSet(
            temperature=base.temperature,
            num_ctx=base.num_ctx,
            num_predict=base.num_predict,
            repeat_penalty=new_repeat,
            top_k=new_top_k,
            top_p=new_top_p
        )

    def _balanced_variation(self, base: ParameterSet, multiplier: float) -> ParameterSet:
        """Small balanced variation in all parameters"""
        return ParameterSet(
            temperature=max(0.1, min(1.0, base.temperature + (multiplier * 0.1))),
            num_ctx=max(1024, min(4096, int(base.num_ctx + (multiplier * 256)))),
            num_predict=max(128, min(1024, int(base.num_predict + (multiplier * 64)))),
            repeat_penalty=max(1.0, min(1.5, base.repeat_penalty + (multiplier * 0.05))),
            top_k=max(10, min(50, int(base.top_k + (multiplier * 5)))),
            top_p=max(0.7, min(1.0, base.top_p + (multiplier * 0.02)))
        )

    def _random_variation(self, base: ParameterSet, multiplier: float) -> ParameterSet:
        """Random parameter variation for exploration"""
        return ParameterSet(
            temperature=np.random.uniform(0.1, 1.0),
            num_ctx=int(np.random.choice([1024, 2048, 3072, 4096])),
            num_predict=int(np.random.choice([128, 256, 512, 768, 1024])),
            repeat_penalty=np.random.uniform(1.0, 1.5),
            top_k=int(np.random.choice([10, 20, 30, 40, 50])),
            top_p=np.random.uniform(0.7, 1.0)
        )

    def evaluate_parameters(self, prompt: str, parameters: ParameterSet,
                          test_model_func) -> TestResult:
        """Test a parameter set and return results"""
        print(f"🔬 Testing: temp={parameters.temperature:.2f}, "
              f"ctx={parameters.num_ctx}, pred={parameters.num_predict}, "
              f"top_k={parameters.top_k}")

        start_time = time.time()

        # Call the model with these parameters
        try:
            response = test_model_func(prompt, parameters.to_dict())
            end_time = time.time()

            # Analyze the response
            accuracy_score = self._calculate_accuracy(prompt, response)
            code_quality_score = self._calculate_code_quality(response)
            token_count = len(response.split())
            error_count = self._count_errors(response)

            result = TestResult(
                parameters=parameters,
                accuracy_score=accuracy_score,
                response_time=end_time - start_time,
                token_count=token_count,
                error_count=error_count,
                code_quality_score=code_quality_score
            )

            print(f"   ✅ Score: {result.efficiency_score:.2f} "
                  f"(acc: {accuracy_score:.2f}, time: {result.response_time:.1f}s)")

            return result

        except Exception as e:
            print(f"   ❌ Error: {e}")
            return TestResult(
                parameters=parameters,
                accuracy_score=0.0,
                response_time=999.0,
                token_count=0,
                error_count=1,
                code_quality_score=0.0
            )

    def _calculate_accuracy(self, prompt: str, response: str) -> float:
        """Calculate accuracy score based on prompt-response analysis"""
        score = 1.0

        # Check for common errors
        if "maths.pi" in response:
            score -= 0.3  # Wrong module name
        if "SyntaxError" in response or "Error" in response:
            score -= 0.5  # Runtime or syntax errors
        if "TODO" in response or "FIXME" in response:
            score -= 0.2  # Incomplete implementation

        # Check for correct patterns
        if "import math" in response and "math.pi" in response:
            score += 0.1  # Correct import and usage
        if "def " in response and "return " in response:
            score += 0.1  # Proper function structure
        if "# " in response or '"""' in response:
            score += 0.05  # Has documentation

        return max(0.0, min(1.0, score))

    def _calculate_code_quality(self, response: str) -> float:
        """Calculate code quality score"""
        quality = 0.5  # Base score

        # Positive indicators
        if "import " in response:
            quality += 0.1
        if "def " in response:
            quality += 0.1
        if "return " in response:
            quality += 0.1
        if "for " in response or "while " in response:
            quality += 0.05
        if len(response.split()) > 50:  # Substantial response
            quality += 0.05

        # Negative indicators
        if response.count("```") < 2:  # No proper code block
            quality -= 0.2
        if len(response) < 50:  # Too short
            quality -= 0.1

        return max(0.0, min(1.0, quality))

    def _count_errors(self, response: str) -> int:
        """Count obvious errors in the response"""
        errors = 0
        error_indicators = ["maths.pi", "SyntaxError", "NameError", "TODO", "FIXME", "pass #"]
        for indicator in error_indicators:
            errors += response.count(indicator)
        return errors

    def optimize_parameters(self, prompt: str, test_model_func,
                           max_iterations: int = 10, target_accuracy: float = 0.95) -> ParameterSet:
        """Main optimization loop"""
        print(f"🚀 Starting parameter optimization for {self.model_name}")
        print(f"📋 Strategy: {self.strategy.value}")
        print(f"🎯 Target accuracy: {target_accuracy}")
        print(f"🔄 Max iterations: {max_iterations}")
        print("=" * 60)

        current_params = self.start_params
        best_params = current_params
        best_score = 0.0

        for iteration in range(max_iterations):
            print(f"\n📍 Iteration {iteration + 1}/{max_iterations}")

            # Test current parameters
            current_result = self.evaluate_parameters(prompt, current_params, test_model_func)
            self.test_history.append(current_result)

            # Update best result
            current_score = self._calculate_fitness_score(current_result)
            if current_score > best_score:
                best_score = current_score
                best_params = current_params
                self.best_result = current_result
                print(f"🏆 New best! Score: {best_score:.3f}")

                # Check if we've reached target
                if current_result.accuracy_score >= target_accuracy:
                    print(f"✅ Target accuracy achieved! ({current_result.accuracy_score:.3f})")
                    break

            # Generate variations for next iteration
            if iteration < max_iterations - 1:
                variations = self.generate_parameter_variations(current_params, iteration + 1)

                # Test variations and pick the best
                best_variation_result = current_result
                best_variation_params = current_params

                for var_params in variations:
                    var_result = self.evaluate_parameters(prompt, var_params, test_model_func)
                    var_score = self._calculate_fitness_score(var_result)

                    if var_score > best_score:
                        best_score = var_score
                        best_params = var_params
                        best_variation_result = var_result
                        best_variation_params = var_params
                        print(f"🎯 Found better variation! Score: {best_score:.3f}")

                current_params = best_variation_params

        print(f"\n🎉 OPTIMIZATION COMPLETE!")
        print(f"🏆 Best parameters: {best_params}")
        if self.best_result:
            print(f"📊 Best accuracy: {self.best_result.accuracy_score:.3f}")
            print(f"⚡ Best time: {self.best_result.response_time:.1f}s")
            print(f"💎 Best efficiency score: {best_score:.3f}")

        return best_params

    def _calculate_fitness_score(self, result: TestResult) -> float:
        """Calculate overall fitness score based on optimization strategy"""
        if self.strategy == OptimizationStrategy.ACCURACY_FIRST:
            # Accuracy is paramount (80%), speed secondary (20%)
            return (result.accuracy_score * 0.8) + (result.speed_score * 0.2)
        elif self.strategy == OptimizationStrategy.SPEED_FIRST:
            # Speed is paramount (60%), accuracy important (40%)
            return (result.speed_score * 0.6) + (result.accuracy_score * 0.4)
        else:  # BALANCED
            # Equal weighting
            return result.efficiency_score

    def save_optimization_results(self, filename: str):
        """Save optimization results to file"""
        results = {
            'model_name': self.model_name,
            'strategy': self.strategy.value,
            'best_parameters': self.best_result.parameters.to_dict() if self.best_result else None,
            'best_score': self._calculate_fitness_score(self.best_result) if self.best_result else 0.0,
            'test_history': [
                {
                    'parameters': r.parameters.to_dict(),
                    'accuracy_score': r.accuracy_score,
                    'response_time': r.response_time,
                    'efficiency_score': r.efficiency_score
                }
                for r in self.test_history
            ]
        }

        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)

        print(f"💾 Results saved to {filename}")

def demo_optimizer():
    """Demo the adaptive parameter optimizer"""
    print("🧪 ADAPTIVE PARAMETER OPTIMIZER DEMO")
    print("=" * 50)

    # Mock model function for demo
    def mock_model_func(prompt: str, params: Dict) -> str:
        # Simulate different model behaviors based on parameters
        time.sleep(params['temperature'] * 2)  # Simulate processing time

        if params['temperature'] < 0.3:
            # Low temp = verbose but accurate
            return f"""```python
import math
def solve(prompt):
    # This is a very detailed solution with perfect accuracy
    return math.pi * 3**2  # Perfect result
```"""
        elif params['temperature'] > 0.7:
            # High temp = fast but error-prone
            return f"""```python
import maths
def solve():
    return maths.pi * 3**2  # Has errors
```"""
        else:
            # Medium temp = balanced
            return f"""```python
import math
def solve():
    return math.pi * 9
```"""

    # Create optimizer
    optimizer = AdaptiveParameterOptimizer(
        model_name="phi3:3.8b",
        optimization_strategy=OptimizationStrategy.BALANCED
    )

    # Run optimization
    test_prompt = "Create a Python function to calculate the area of a circle with radius 3"
    best_params = optimizer.optimize_parameters(
        prompt=test_prompt,
        test_model_func=mock_model_func,
        max_iterations=8,
        target_accuracy=0.9
    )

    # Save results
    optimizer.save_optimization_results("optimization_demo_results.json")

    return optimizer

if __name__ == "__main__":
    demo_optimizer()