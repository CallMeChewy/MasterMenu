#!/usr/bin/env python3
# File: parameter_optimization_analyzer.py
# Path: /home/herb/Desktop/LLM-Tester/parameter_optimization_analyzer.py
# Standard: AIDEV-PascalCase-2.1
# Created: 2025-10-04
# Last Modified: 2025-10-04 07:22AM

"""
Parameter Optimization Analyzer - Extracts optimal parameter settings from test results
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import matplotlib.pyplot as plt
import seaborn as sns

class ParameterOptimizationAnalyzer:
    """Analyzes test results to find optimal parameter settings"""

    def __init__(self, csv_file_path: str):
        self.csv_file = csv_file_path
        self.csv_file_path = csv_file_path
        self.df = None
        self.analysis_results = {}
        self.load_data()

    def load_data(self):
        """Load and preprocess the CSV data"""
        print("📊 Loading test results...")

        try:
            self.df = pd.read_csv(self.csv_file_path)

            # Clean the data
            self.df = self.df[self.df['status'] == 'completed']  # Only successful tests

            # Extract parameters from response text (if available)
            # For now, we'll work with the timing and token data
            print(f"   ✅ Loaded {len(self.df)} test results")
            print(f"   📅 Models: {self.df['model_name'].unique()}")
            print(f"   🎯 Date range: {self.df['timestamp'].min()} to {self.df['timestamp'].max()}")

        except Exception as e:
            print(f"❌ Error loading data: {e}")
            return False

        return True

    def extract_prompt_types(self) -> Dict[str, str]:
        """Extract prompt types from the data"""
        prompt_types = {}

        # Look for keywords in prompts to categorize them
        for _, row in self.df.iterrows():
            prompt = row['prompt_text'].lower()

            if 'circle' in prompt and 'area' in prompt:
                prompt_types[row['prompt_text']] = 'circle_area'
            elif 'prime' in prompt and ('number' in prompt or 'under' in prompt):
                prompt_types[row['prompt_text']] = 'prime_numbers'
            elif 'linked list' in prompt and ('reverse' in prompt or 'in-place' in prompt):
                prompt_types[row['prompt_text']] = 'linked_list'
            elif 'email' in prompt and ('valid' in prompt or 'validate' in prompt):
                prompt_types[row['prompt_text']] = 'email_validation'
            else:
                prompt_types[row['prompt_text']] = 'other'

        return prompt_types

    def analyze_performance_by_parameters(self) -> Dict:
        """Analyze performance patterns to infer optimal parameters"""
        print("\n🔍 Analyzing performance patterns...")

        analysis = {
            'model_performance': {},
            'fast_performers': [],
            'slow_performers': [],
            'high_throughput': [],
            'low_throughput': []
        }

        # Model-level analysis
        for model in self.df['model_name'].unique():
            model_data = self.df[self.df['model_name'] == model]

            model_stats = {
                'avg_time': model_data['response_time'].mean(),
                'avg_tokens': model_data['tokens_out'].mean(),
                'throughput': model_data['tokens_per_second'].mean(),
                'total_tests': len(model_data),
                'fastest': model_data['response_time'].min(),
                'slowest': model_data['response_time'].max()
            }

            analysis['model_performance'][model] = model_stats

            # Classify performance
            if model_stats['avg_time'] < 20:
                analysis['fast_performers'].append(model)
            elif model_stats['avg_time'] > 40:
                analysis['slow_performers'].append(model)

            if model_stats['throughput'] > 30:
                analysis['high_throughput'].append(model)
            elif model_stats['throughput'] < 15:
                analysis['low_throughput'].append(model)

        return analysis

    def find_optimal_settings_by_task(self) -> Dict:
        """Find optimal settings for each task type"""
        print("\n🎯 Finding optimal settings by task type...")

        prompt_types = self.extract_prompt_types()
        optimal_settings = {}

        # Group by prompt type
        for prompt_text, prompt_type in prompt_types.items():
            # Filter data for this specific prompt
            prompt_data = self.df[self.df['prompt_text'] == prompt_text]

            # Find the best performing test for this prompt
            best_performer = prompt_data.loc[prompt_data['tokens_per_second'].idxmax()]

            # Infer optimal parameters based on performance characteristics
            inferred_params = self._infer_optimal_parameters(best_performer)

            optimal_settings[prompt_type] = {
                'prompt': prompt_text,
                'optimal_model': best_performer['model_name'],
                'performance': {
                    'time': best_performer['response_time'],
                    'tokens': best_performer['tokens_out'],
                    'throughput': best_performer['tokens_per_second']
                },
                'inferred_parameters': inferred_params,
                'sample_count': len(prompt_data)
            }

        return optimal_settings

    def _infer_optimal_parameters(self, test_row: pd.Series) -> Dict:
        """Infer optimal parameters based on test performance characteristics"""

        time = test_row['response_time']
        tokens = test_row['tokens_out']
        throughput = test_row['tokens_per_second']
        model = test_row['model_name']

        # Infer parameters based on performance patterns
        inferred = {
            'model': model,
            'estimated_temperature': self._estimate_temperature(time, tokens, model),
            'estimated_context_size': self._estimate_context_size(tokens, model),
            'estimated_output_limit': self._estimate_output_limit(tokens, model),
            'performance_category': self._categorize_performance(time, throughput)
        }

        return inferred

    def _estimate_temperature(self, time: float, tokens: int, model: str) -> float:
        """Estimate temperature based on response time and verbosity"""

        # Adjust for model size
        if '3.8b' in model.lower():
            # Small model typically faster
            base_temp = 0.7
        else:
            # Large model typically slower
            base_temp = 0.3

        # Adjust based on response time
        if time < 5:
            # Very fast - likely high temperature
            return min(1.0, base_temp + 0.3)
        elif time > 60:
            # Very slow - likely low temperature with large output
            return max(0.1, base_temp - 0.2)
        else:
            # Medium time - moderate temperature
            return base_temp

        # Adjust based on token count
        if tokens > 1000:
            # Very verbose - lower temperature
            return base_temp - 0.1
        elif tokens < 200:
            # Very concise - higher temperature
            return base_temp + 0.1

        return base_temp

    def _estimate_context_size(self, tokens: int, model: str) -> int:
        """Estimate context window size based on output tokens"""

        # Typical ratio: output tokens ≈ 0.1 * context_size for reasonable generation
        if tokens > 0:
            estimated_ctx = min(tokens * 10, 8192)
            # Round to common sizes
            common_sizes = [1024, 2048, 4096, 8192]
            return min(common_sizes, key=lambda x: abs(x - estimated_ctx))
        return 2048

    def _estimate_output_limit(self, tokens: int, model: str) -> int:
        """Estimate num_predict parameter based on output tokens"""

        # Round to common sizes
        common_sizes = [128, 256, 512, 1024, 2048, 4096]
        return min(common_sizes, key=lambda x: abs(x - tokens))

    def _categorize_performance(self, time: float, throughput: float) -> str:
        """Categorize performance characteristics"""
        if time < 10 and throughput > 30:
            return "EXCELLENT_SPEED"
        elif time < 20 and throughput > 20:
            return "GOOD_SPEED"
        elif time < 30:
            return "MODERATE_SPEED"
        else:
            return "SLOW_SPEED"

    def generate_optimization_recommendations(self) -> Dict:
        """Generate specific optimization recommendations"""
        print("\n💡 Generating optimization recommendations...")

        analysis = self.analyze_performance_by_parameters()
        optimal_settings = self.find_optimal_settings_by_task()

        recommendations = {
            'model_rankings': [],
            'task_specific_settings': optimal_settings,
            'general_recommendations': []
        }

        # Rank models by different criteria
        model_performance = analysis['model_performance']

        # Speed ranking
        speed_ranking = sorted(model_performance.items(), key=lambda x: x[1]['avg_time'])
        recommendations['model_rankings'].append({
            'criteria': 'FASTEST_RESPONSE',
            'ranking': speed_ranking
        })

        # Throughput ranking
        throughput_ranking = sorted(model_performance.items(), key=lambda x: x[1]['throughput'], reverse=True)
        recommendations['model_rankings'].append({
            'criteria': 'HIGHEST_THROUGHPUT',
            'ranking': throughput_ranking
        })

        # Generate general recommendations
        if analysis['fast_performers']:
            recommendations['general_recommendations'].append(
                f"Fast performers: {', '.join(analysis['fast_performers'])}"
            )

        if analysis['slow_performers']:
            recommendations['general_recommendations'].append(
                f"Slow performers: {', '.join(analysis['slow_performers'])} - consider parameter optimization"
            )

        # Task-specific recommendations
        for task_type, settings in optimal_settings.items():
            model = settings['optimal_model']
            performance = settings['performance']
            params = settings['inferred_parameters']

            recommendations['task_specific_settings'][task_type] = {
                'best_model': model,
                'expected_performance': f"{performance['time']:.1f}s, {performance['throughput']:.1f} tokens/s",
                'recommended_parameters': params,
                'rationale': f"Best balance of speed and accuracy for {task_type.replace('_', ' ').title()}"
            }

        return recommendations

    def create_performance_visualizations(self) -> None:
        """Create visualizations of the analysis"""
        print("\n📈 Creating performance visualizations...")

        try:
            # Set up the plot style
            plt.style.use('default')
            fig, axes = plt.subplots(2, 2, figsize=(15, 12))
            fig.suptitle('LLM Model Performance Analysis', fontsize=16, fontweight='bold')

            # 1. Response Time Distribution
            self.df.boxplot(column='response_time', by='model_name', ax=axes[0, 0])
            axes[0, 0].set_title('Response Time Distribution by Model')
            axes[0, 0].set_ylabel('Response Time (seconds)')

            # 2. Throughput Comparison
            model_throughput = self.df.groupby('model_name')['tokens_per_second'].mean()
            model_throughput.plot(kind='bar', ax=axes[0, 1])
            axes[0, 1].set_title('Average Throughput by Model')
            axes[0, 1].set_ylabel('Tokens/Second')
            axes[0, 1].tick_params(rotation=45)

            # 3. Tokens vs Time Scatter
            for model in self.df['model_name'].unique():
                model_data = self.df[self.df['model_name'] == model]
                axes[1, 0].scatter(model_data['response_time'], model_data['tokens_out'],
                              label=model, alpha=0.6, s=50)
            axes[1, 0].set_xlabel('Response Time (seconds)')
            axes[1, 0].set_ylabel('Output Tokens')
            axes[1, 0].set_title('Response Time vs Output Tokens')
            axes[1, 0].legend()

            # 4. Performance Summary Heatmap
            summary_data = []
            for model in self.df['model_name'].unique():
                model_data = self.df[self.df['model_name'] == model]
                summary_data.append({
                    'Model': model,
                    'Avg Time': model_data['response_time'].mean(),
                    'Avg Tokens': model_data['tokens_out'].mean(),
                    'Throughput': model_data['tokens_per_second'].mean()
                })

            summary_df = pd.DataFrame(summary_data)
            correlation_data = summary_df[['Avg Time', 'Avg Tokens', 'Throughput']]
            correlation_matrix = correlation_data.corr()

            im = axes[1, 1].imshow(correlation_matrix, cmap='coolwarm', aspect='auto', vmin=-1, vmax=1)
            axes[1, 1].set_xticks(range(len(correlation_data.columns)))
            axes[1, 1].set_yticks(range(len(correlation_data.columns)))
            axes[1, 1].set_xticklabels(correlation_data.columns, rotation=45)
            axes[1, 1].set_yticklabels(correlation_data.columns)
            axes[1, 1].set_title('Performance Correlation Matrix')

            # Add correlation values to heatmap
            for i in range(len(correlation_data.columns)):
                for j in range(len(correlation_data.columns)):
                    text = axes[1, 1].text(j, i, f'{correlation_data.iloc[i, j]:.2f}',
                                   ha='center', va='center', color='black')

            plt.tight_layout()

            # Save the plot
            output_file = self.csv_file_path.replace('.csv', '_performance_analysis.png')
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            plt.show()

            print(f"   📊 Visualization saved to: {output_file}")

        except Exception as e:
            print(f"   ❌ Error creating visualizations: {e}")

    def generate_optimal_settings_table(self) -> None:
        """Generate a clear table of optimal settings"""
        print("\n📋 OPTIMAL PARAMETER SETTINGS TABLE")
        print("=" * 80)

        recommendations = self.generate_optimization_recommendations()

        print(f"\n🏆 MODEL RANKINGS")
        print("-" * 50)

        for ranking in recommendations['model_rankings']:
            print(f"\n{ranking['criteria'].replace('_', ' ').title()}:")
            for i, (model, stats) in enumerate(ranking['ranking'][:3], 1):
                print(f"   {i}. {model}: {stats['avg_time']:.1f}s avg, {stats['throughput']:.1f} tokens/s")

        print(f"\n🎯 TASK-SPECIFIC OPTIMAL SETTINGS")
        print("-" * 50)

        for task_type, settings in recommendations['task_specific_settings'].items():
            print(f"\n📝 {task_type.replace('_', ' ').title()}:")
            print(f"   🤖️  Best Model: {settings['best_model']}")
            print(f"   ⚡  Performance: {settings['expected_performance']}")
            print(f"   🔧  Temperature: {settings['recommended_parameters']['estimated_temperature']:.2f}")
            print(f"   📄  Context: {settings['recommended_parameters']['estimated_context_size']}")
            print(f"   📤  Max Output: {settings['recommended_parameters']['estimated_output_limit']}")
            print(f"   💡  {settings['rationale']}")

    def save_analysis_results(self, output_file: str = None):
        """Save analysis results to file"""
        if output_file is None:
            output_file = self.csv_file_path.replace('.csv', '_optimization_analysis.json')

        results = {
            'analysis_date': pd.Timestamp.now().isoformat(),
            'source_file': self.csv_file_path,
            'total_tests': len(self.df),
            'analysis_results': self.analysis_results,
            'optimal_settings': self.generate_optimization_recommendations()
        }

        try:
            import json
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            print(f"\n💾 Analysis results saved to: {output_file}")
        except Exception as e:
            print(f"❌ Error saving results: {e}")

    def run_complete_analysis(self):
        """Run the complete analysis pipeline"""
        print("🔍 PARAMETER OPTIMIZATION ANALYZER")
        print("=" * 50)
        print(f"📁 Analyzing: {self.csv_file_path}")

        if not self.load_data():
            return False

        # Run analysis components
        self.analysis_results['performance'] = self.analyze_performance_by_parameters()
        self.analysis_results['optimal_settings'] = self.find_optimal_settings_by_task()
        self.analysis_results['recommendations'] = self.generate_optimization_recommendations()

        # Generate outputs
        self.generate_optimal_settings_table()
        self.create_performance_visualizations()
        self.save_analysis_results()

        print(f"\n🎉 ANALYSIS COMPLETE!")
        print(f"📊 Check the generated visualizations and saved results file.")

        return True

def analyze_test_results(csv_file_path: str):
    """Main function to analyze test results"""
    analyzer = ParameterOptimizationAnalyzer(csv_file_path)
    return analyzer.run_complete_analysis()

if __name__ == "__main__":
    # Analyze the latest test results
    csv_file = "/home/herb/Desktop/test_results_20251004_034144.csv"
    analyze_test_results(csv_file)