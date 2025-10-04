#!/usr/bin/env python3
# File: parameter_optimization_lab.py
# Path: /home/herb/Desktop/LLM-Tester/parameter_optimization_lab.py
# Standard: AIDEV-PascalCase-2.1
# Created: 2025-10-04
# Last Modified: 2025-10-04 04:20AM

"""
Parameter Optimization Lab - Exhaustive search for the perfect parameter sweet spot
Finds 100% accuracy with minimum consistent response time through systematic exploration
"""

import pandas as pd
import numpy as np
import time
import json
import statistics
from typing import Dict, List, Tuple, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import threading
import queue
from datetime import datetime, timedelta

class OptimizationStatus(Enum):
    EXPLORING = "exploring_parameter_space"
    REFINING = "refining_best_candidates"
    VALIDATING = "validating_consistency"
    CONVERGED = "converged_on_optimal"
    FAILED = "failed_to_converge"

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
        return asdict(self)

    def __str__(self) -> str:
        return f"T{self.temperature:.2f}_C{self.num_ctx}_P{self.num_predict}_R{self.repeat_penalty:.2f}_K{self.top_k}_P{self.top_p:.2f}"

    def distance_to(self, other: 'ParameterConfig') -> float:
        """Calculate Euclidean distance to another configuration"""
        return np.sqrt(
            (self.temperature - other.temperature) ** 2 +
            (self.num_ctx - other.num_ctx) ** 2 / 1000 +  # Normalize
            (self.num_predict - other.num_predict) ** 2 / 100 +
            (self.repeat_penalty - other.repeat_penalty) ** 2 +
            (self.top_k - other.top_k) ** 2 / 10 +
            (self.top_p - other.top_p) ** 2
        )

@dataclass
class TestResult:
    """Result from a single parameter test"""
    config: ParameterConfig
    response: str
    response_time: float
    accuracy_score: float
    token_count: int
    error_count: int
    timestamp: datetime

@dataclass
class OptimizationTarget:
    """What we're trying to achieve"""
    prompt: str
    model: str
    target_accuracy: float = 1.0  # 100% accuracy
    max_time_seconds: float = 300.0  # 5 minutes per test
    consistency_threshold: float = 0.95  # 95% consistency required

@dataclass
class OptimizationProgress:
    """Real-time progress tracking"""
    status: OptimizationStatus
    current_iteration: int
    total_tests_run: int
    best_config_found: Optional[ParameterConfig]
    best_accuracy: float
    best_time: float
    convergence_score: float  # 0.0 to 1.0
    estimated_time_remaining: Optional[timedelta]
    current_test: Optional[str]

class ParameterOptimizationLab:
    """Exhaustive parameter optimization laboratory"""

    def __init__(self, target: OptimizationTarget, model_function: Callable):
        self.target = target
        self.model_function = model_function
        self.test_results: List[TestResult] = []
        self.optimization_history: List[Dict] = []
        self.stop_requested = False

        # Optimization state
        self.current_status = OptimizationStatus.EXPLORING
        self.best_config = None
        self.best_accuracy = 0.0
        self.best_time = float('inf')
        self.convergence_history = []

        # Parameter search space
        self.parameter_ranges = {
            'temperature': np.arange(0.1, 1.01, 0.05),  # 0.1 to 1.0
            'num_ctx': [512, 1024, 2048, 4096, 8192, 16384],
            'num_predict': [128, 256, 512, 1024, 2048, 4096],
            'repeat_penalty': np.arange(1.0, 1.51, 0.05),  # 1.0 to 1.5
            'top_k': list(range(1, 51)),  # 1 to 50
            'top_p': np.arange(0.7, 1.01, 0.02)  # 0.7 to 1.0
        }

        # Progress tracking
        self.progress_queue = queue.Queue()
        self.start_time = None

    def calculate_accuracy(self, response: str) -> float:
        """Calculate accuracy score with strict criteria"""
        score = 1.0

        # Prompt-specific accuracy checks with strict scoring
        if "circle" in self.target.prompt.lower() and "area" in self.target.prompt.lower():
            # Circle area prompt - must be perfect
            if "math.pi" not in response:
                score -= 0.5
            if "maths.pi" in response:  # Wrong module name
                score -= 0.3
            if "def " not in response:
                score -= 0.3
            if "return " not in response:
                score -= 0.2
            if "import math" not in response:
                score -= 0.2
            if "radius" not in response:
                score -= 0.1
            # Check for correct formula
            if "pi * radius ** 2" not in response and "math.pi * radius * radius" not in response:
                score -= 0.3

        elif "prime" in self.target.prompt.lower():
            # Prime numbers prompt - must be perfect
            expected_primes = ["2", "3", "5", "7", "11", "13", "17", "19", "23", "29"]
            primes_found = sum(1 for prime in expected_primes if prime in response)
            score += min(0.5, primes_found * 0.05)

            if primes_found != len(expected_primes):
                score -= 0.5  # Missing primes
            if "def " not in response:
                score -= 0.2
            if "%" not in response:  # Must use modulo operation
                score -= 0.2

        elif "email" in self.target.prompt.lower():
            # Email validation prompt - must be perfect
            if "@" not in response or "." not in response:
                score -= 0.4
            if "re" not in response.lower() and "regex" not in response.lower():
                score -= 0.3
            if "def " not in response:
                score -= 0.2
            # Check for proper email validation logic
            if r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$" not in response:
                score -= 0.2

        elif "linked list" in self.target.prompt.lower():
            # Linked list prompt - must be perfect
            if "next" not in response.lower():
                score -= 0.3
            if "def " not in response:
                score -= 0.2
            if "class " not in response:
                score -= 0.2
            if "reverse" not in response.lower():
                score -= 0.2

        # General code quality checks
        if "```python" not in response:
            score -= 0.1
        if len(response.split()) < 20:
            score -= 0.2
        if "Error" in response or "TODO" in response or "FIXME" in response:
            score -= 0.3
        if "pass" in response and len(response) < 50:  # Empty implementation
            score -= 0.4

        return max(0.0, min(1.0, score))

    def test_configuration(self, config: ParameterConfig, validation_cycles: int = 5) -> Optional[TestResult]:
        """Test a configuration with validation cycles"""
        try:
            # Run the test with timeout
            start_time = time.time()

            # Call the actual model
            response = self.model_function(
                model=self.target.model,
                prompt=self.target.prompt,
                parameters=config.to_dict()
            )

            response_time = time.time() - start_time

            # Check if response time is acceptable
            if response_time > self.target.max_time_seconds:
                return None

            # Calculate accuracy
            accuracy = self.calculate_accuracy(response)
            token_count = len(response.split())
            error_count = response.count("Error") + response.count("TODO")

            result = TestResult(
                config=config,
                response=response,
                response_time=response_time,
                accuracy_score=accuracy,
                token_count=token_count,
                error_count=error_count,
                timestamp=datetime.now()
            )

            self.test_results.append(result)
            return result

        except Exception as e:
            print(f"❌ Configuration {config} failed: {e}")
            return None

    def validate_configuration(self, config: ParameterConfig, cycles: int = 10) -> Dict:
        """Validate a configuration multiple times for consistency"""
        validation_results = []

        for i in range(cycles):
            if self.stop_requested:
                break

            result = self.test_configuration(config, validation_cycles=1)
            if result:
                validation_results.append(result)

            # Report progress
            self.progress_queue.put({
                'type': 'validation_progress',
                'cycle': i + 1,
                'total_cycles': cycles,
                'config': str(config)
            })

        if not validation_results:
            return {'valid': False, 'reason': 'No successful tests'}

        # Calculate statistics
        accuracies = [r.accuracy_score for r in validation_results]
        times = [r.response_time for r in validation_results]

        avg_accuracy = statistics.mean(accuracies)
        std_accuracy = statistics.stdev(accuracies) if len(accuracies) > 1 else 0
        avg_time = statistics.mean(times)
        std_time = statistics.stdev(times) if len(times) > 1 else 0

        # Check consistency
        accuracy_consistency = 1.0 - (std_accuracy / avg_accuracy) if avg_accuracy > 0 else 0
        time_consistency = 1.0 - (std_time / avg_time) if avg_time > 0 else 0

        overall_consistency = (accuracy_consistency + time_consistency) / 2

        return {
            'valid': True,
            'avg_accuracy': avg_accuracy,
            'std_accuracy': std_accuracy,
            'avg_time': avg_time,
            'std_time': std_time,
            'consistency_score': overall_consistency,
            'meets_target': avg_accuracy >= self.target.target_accuracy and overall_consistency >= self.target.consistency_threshold,
            'validation_results': validation_results
        }

    def generate_parameter_space(self) -> List[ParameterConfig]:
        """Generate initial parameter space for exploration"""
        configs = []

        # Generate systematic combinations
        temperatures = [0.1, 0.3, 0.5, 0.7, 0.9]
        contexts = [1024, 2048, 4096, 8192]
        predictions = [256, 512, 1024, 2048]
        repeats = [1.0, 1.1, 1.2, 1.3]
        top_ks = [10, 20, 30, 40, 50]
        top_ps = [0.8, 0.85, 0.9, 0.95]

        # Generate combinations (not full factorial to keep it manageable)
        for temp in temperatures:
            for ctx in contexts:
                for pred in predictions:
                    for repeat in repeats:
                        configs.append(ParameterConfig(
                            temperature=temp,
                            num_ctx=ctx,
                            num_predict=pred,
                            repeat_penalty=repeat,
                            top_k=25,  # Default
                            top_p=0.9   # Default
                        ))

        # Add top_k and top_p variations
        for k in top_ks:
            configs.append(ParameterConfig(
                temperature=0.5, num_ctx=2048, num_predict=512,
                repeat_penalty=1.1, top_k=k, top_p=0.9
            ))

        for p in top_ps:
            configs.append(ParameterConfig(
                temperature=0.5, num_ctx=2048, num_predict=512,
                repeat_penalty=1.1, top_k=25, top_p=p
            ))

        return configs

    def refine_around_best(self, best_config: ParameterConfig, radius: float = 0.2) -> List[ParameterConfig]:
        """Generate refined configurations around the best found"""
        refined = []

        # Create variations around the best configuration
        temp_range = [max(0.1, best_config.temperature - radius),
                      min(1.0, best_config.temperature + radius)]
        ctx_range = [max(512, best_config.num_ctx - 1024),
                     min(16384, best_config.num_ctx + 1024)]
        pred_range = [max(128, best_config.num_predict - 256),
                       min(4096, best_config.num_predict + 256)]
        repeat_range = [max(1.0, best_config.repeat_penalty - 0.1),
                        min(1.5, best_config.repeat_penalty + 0.1)]

        # Generate refined combinations
        for temp in np.arange(temp_range[0], temp_range[1] + 0.05, 0.05):
            for ctx in ctx_range:
                for pred in pred_range:
                    for repeat in np.arange(repeat_range[0], repeat_range[1] + 0.02, 0.02):
                        refined.append(ParameterConfig(
                            temperature=temp,
                            num_ctx=ctx,
                            num_predict=pred,
                            repeat_penalty=repeat,
                            top_k=best_config.top_k,
                            top_p=best_config.top_p
                        ))

        return refined

    def run_exhaustive_optimization(self) -> OptimizationProgress:
        """Run exhaustive optimization until convergence or stop"""
        self.start_time = datetime.now()
        self.current_status = OptimizationStatus.EXPLORING

        # Phase 1: Broad exploration
        print("🔬 Phase 1: Broad parameter space exploration...")
        configs = self.generate_parameter_space()

        best_overall_result = None
        best_validation_score = 0.0

        for i, config in enumerate(configs):
            if self.stop_requested:
                break

            # Test configuration
            result = self.test_configuration(config)
            if result and result.accuracy_score > self.best_accuracy:
                self.best_accuracy = result.accuracy_score
                self.best_config = config
                best_overall_result = result

                # Validate new best
                validation = self.validate_configuration(config, cycles=5)
                if validation['valid']:
                    validation_score = validation['avg_accuracy'] * validation['consistency_score']
                    if validation_score > best_validation_score:
                        best_validation_score = validation_score
                        print(f"🏆 New best: {config} - Accuracy: {validation['avg_accuracy']:.3f}, Consistency: {validation['consistency_score']:.3f}")

            # Update progress
            progress = OptimizationProgress(
                status=self.current_status,
                current_iteration=i + 1,
                total_tests_run=len(self.test_results),
                best_config_found=self.best_config,
                best_accuracy=self.best_accuracy,
                best_time=self.best_time,
                convergence_score=min(1.0, self.best_accuracy),
                estimated_time_remaining=timedelta(seconds=int((len(configs) - i - 1) * 2)),
                current_test=f"Exploring: {config}"
            )

            self.progress_queue.put({'type': 'progress', 'progress': progress})

        # Phase 2: Refinement around best candidates
        if self.best_config and not self.stop_requested:
            print("\n🔬 Phase 2: Refining around best candidates...")
            self.current_status = OptimizationStatus.REFINING

            refined_configs = self.refine_around_best(self.best_config)

            for i, config in enumerate(refined_configs):
                if self.stop_requested:
                    break

                result = self.test_configuration(config)
                if result and result.accuracy_score > self.best_accuracy:
                    self.best_accuracy = result.accuracy_score
                    self.best_config = config
                    best_overall_result = result

                    # Validate refined candidate
                    validation = self.validate_configuration(config, cycles=10)
                    if validation['valid'] and validation['meets_target']:
                        print(f"🎯 OPTIMAL FOUND: {config}")
                        print(f"   Accuracy: {validation['avg_accuracy']:.3f} ± {validation['std_accuracy']:.3f}")
                        print(f"   Time: {validation['avg_time']:.2f} ± {validation['std_time']:.2f}s")
                        print(f"   Consistency: {validation['consistency_score']:.3f}")

                        self.current_status = OptimizationStatus.CONVERGED
                        break

                # Update progress
                progress = OptimizationProgress(
                    status=self.current_status,
                    current_iteration=i + 1,
                    total_tests_run=len(self.test_results),
                    best_config_found=self.best_config,
                    best_accuracy=self.best_accuracy,
                    best_time=self.best_time,
                    convergence_score=min(1.0, self.best_accuracy),
                    estimated_time_remaining=timedelta(seconds=int((len(refined_configs) - i - 1) * 3)),
                    current_test=f"Refining: {config}"
                )

                self.progress_queue.put({'type': 'progress', 'progress': progress})

        # Phase 3: Final validation
        if self.best_config and not self.stop_requested:
            print("\n🔬 Phase 3: Final validation...")
            self.current_status = OptimizationStatus.VALIDATING

            final_validation = self.validate_configuration(self.best_config, cycles=20)

            if final_validation['valid'] and final_validation['meets_target']:
                self.current_status = OptimizationStatus.CONVERGED
                print(f"✅ CONVERGED ON OPTIMAL PARAMETERS!")
                print(f"   Configuration: {self.best_config}")
                print(f"   Final Accuracy: {final_validation['avg_accuracy']:.3f} ± {final_validation['std_accuracy']:.3f}")
                print(f"   Final Time: {final_validation['avg_time']:.2f} ± {final_validation['std_time']:.2f}s")
                print(f"   Consistency: {final_validation['consistency_score']:.3f}")
                print(f"   Total Tests Run: {len(self.test_results)}")
            else:
                self.current_status = OptimizationStatus.FAILED
                print(f"❌ Failed to achieve target consistency")

        # Final progress update
        final_progress = OptimizationProgress(
            status=self.current_status,
            current_iteration=len(self.test_results),
            total_tests_run=len(self.test_results),
            best_config_found=self.best_config,
            best_accuracy=self.best_accuracy,
            best_time=self.best_time,
            convergence_score=1.0 if self.current_status == OptimizationStatus.CONVERGED else self.best_accuracy,
            estimated_time_remaining=timedelta(0),
            current_test="Complete"
        )

        return final_progress

    def stop_optimization(self):
        """Stop the optimization process"""
        self.stop_requested = True
        print("🛑 Stop requested - optimization will halt gracefully")

    def save_results(self, filename: str = None):
        """Save comprehensive optimization results"""
        if filename is None:
            timestamp = int(datetime.now().timestamp())
            filename = f"optimization_lab_results_{timestamp}.json"

        results = {
            'target': {
                'prompt': self.target.prompt,
                'model': self.target.model,
                'target_accuracy': self.target.target_accuracy,
                'consistency_threshold': self.target.consistency_threshold
            },
            'optimization_info': {
                'start_time': self.start_time.isoformat() if self.start_time else None,
                'end_time': datetime.now().isoformat(),
                'total_tests_run': len(self.test_results),
                'final_status': self.current_status.value,
                'converged': self.current_status == OptimizationStatus.CONVERGED
            },
            'best_result': {
                'config': self.best_config.to_dict() if self.best_config else None,
                'accuracy': float(self.best_accuracy),
                'time': float(self.best_time)
            },
            'test_results': [
                {
                    'config': r.config.to_dict(),
                    'accuracy': r.accuracy_score,
                    'time': r.response_time,
                    'tokens': r.token_count,
                    'timestamp': r.timestamp.isoformat()
                }
                for r in self.test_results
            ],
            'optimization_history': self.optimization_history
        }

        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)

        print(f"💾 Results saved to: {filename}")
        return filename

def demo_optimization_lab():
    """Demo the optimization lab"""
    # Mock model function for demo
    def mock_model_function(model, prompt, parameters):
        # Simulate processing time based on parameters
        time.sleep(parameters['temperature'] * 0.5 + parameters['num_predict'] / 1000)

        # Generate mock response
        if "circle" in prompt.lower():
            if parameters['temperature'] < 0.3:
                return """```python
import math

def circle_area(radius):
    \"\"\"Calculate the area of a circle given its radius.\"\"\"
    return math.pi * radius ** 2

# Example usage
print(circle_area(5))  # 78.53981633974483
```"""
            else:
                return """```python
import math
def circle_area(r):
    return math.pi * r * r
```"""
        else:
            return f"# Mock response for {prompt[:30]} with temp {parameters['temperature']}"

    # Set up optimization target
    target = OptimizationTarget(
        prompt="Create a Python function to calculate the area of a circle given its radius.",
        model="phi3:3.8b",
        target_accuracy=1.0,
        max_time_seconds=30.0,
        consistency_threshold=0.95
    )

    # Create and run optimization lab
    lab = ParameterOptimizationLab(target, mock_model_function)

    print("🧪 PARAMETER OPTIMIZATION LAB DEMO")
    print("=" * 60)
    print(f"🎯 Target: 100% accuracy with 95% consistency")
    print(f"📝 Prompt: {target.prompt}")
    print(f"🤖 Model: {target.model}")
    print("=" * 60)

    # Run optimization (with reduced scope for demo)
    progress = lab.run_exhaustive_optimization()

    # Save results
    lab.save_results()

    return lab, progress

if __name__ == "__main__":
    demo_optimization_lab()