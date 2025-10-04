#!/usr/bin/env python3
"""
Quick Analysis of LLM Test Results
Analyzes the available test results CSV file to extract meaningful insights
"""

import re
from collections import defaultdict

def analyze_csv_file(filename):
    """Perform quick analysis of the CSV file"""
    print(f"Analyzing {filename}...\n")

    try:
        with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: File {filename} not found")
        return

    lines = content.split('\n')
    print(f"Total lines in file: {len(lines)}")

    # Look for model patterns
    model_patterns = []
    common_models = [
        'phi3:3.8b', 'qwen2.5-coder:7b', 'qwen2.5:7b', 'llava:7b',
        'mistral:7b', 'llama3:8b', 'deepseek-r1:8b', 'gemma3:4b'
    ]

    model_counts = defaultdict(int)
    prompt_counts = defaultdict(int)
    status_counts = defaultdict(int)

    # Simple pattern matching for models
    for model in common_models:
        pattern = re.escape(model)
        count = len(re.findall(pattern, content, re.IGNORECASE))
        if count > 0:
            model_counts[model] = count
            print(f"Found {model}: {count} occurrences")

    # Look for prompt patterns
    prompts = [
        'Create a function to calculate the area of a triangle',
        'Write a program to print all prime numbers',
        'Explain what a blockchain is',
        'Solve this logic puzzle',
        'Write a short story',
        'Create a poem'
    ]

    print(f"\nPrompt Analysis:")
    for prompt in prompts[:5]:  # First 5 prompts
        # Find variations of the prompt
        count = 0
        patterns = [
            prompt.lower(),
            prompt.split()[0].lower(),  # First word
        ]

        for pattern in patterns:
            count += len(re.findall(pattern, content, re.IGNORECASE))

        if count > 0:
            print(f"  {prompt[:50]}...: {count} occurrences")

    # Look for status indicators
    completed_count = len(re.findall(r'completed', content, re.IGNORECASE))
    error_count = len(re.findall(r'error', content, re.IGNORECASE))

    print(f"\nStatus Analysis:")
    print(f"  Completed: {completed_count}")
    print(f"  Errors: {error_count}")

    # Look for common response patterns
    print(f"\nResponse Patterns:")
    code_blocks = len(re.findall(r'```python', content, re.IGNORECASE))
    function_defs = len(re.findall(r'def\s+\w+', content))
    print(f"  Python code blocks: {code_blocks}")
    print(f"  Function definitions: {function_defs}")

    # Try to extract some sample responses
    print(f"\nSample Analysis:")

    # Look for successful Python function definitions
    python_functions = re.findall(r'def\s+(\w+)[^:]*:(.*?)``', content, re.DOTALL | re.IGNORECASE)

    print(f"Found {len(python_functions)} potential Python functions")

    for i, (func_name, func_body) in enumerate(python_functions[:3]):
        print(f"\n  Function {i+1}: {func_name}")
        print(f"    Length: {len(func_body)} characters")

        # Check for key components
        has_return = 'return' in func_body.lower()
        has_params = '(' in func_body
        print(f"    Has return statement: {has_return}")
        print(f"    Has parameters: {has_params}")

    # Basic statistics
    total_chars = len(content)
    print(f"\nFile Statistics:")
    print(f"  Total characters: {total_chars:,}")
    print(f"  Approximate file size: {total_chars / 1024:.1f} KB")

    return {
        'model_counts': dict(model_counts),
        'completed_count': completed_count,
        'error_count': error_count,
        'code_blocks': code_blocks,
        'function_definitions': function_defs
    }

def extract_model_performance(filename):
    """Try to extract model performance data"""
    print(f"\n{'='*50}")
    print("MODEL PERFORMANCE ANALYSIS")
    print('='*50)

    model_performance = defaultdict(lambda: {
        'responses': [],
        'times': [],
        'tokens': []
    })

    try:
        with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"Error: File {filename} not found")
        return

    # Simple regex to extract some data
    # This is a basic approach - the CSV is heavily malformed
    for line_num, line in enumerate(lines[:500]):  # First 500 lines for speed
        # Look for model names
        for model in ['phi3:3.8b', 'qwen2.5-coder:7b', 'llama3:8b', 'mistral:7b']:
            if model.lower() in line.lower():
                # Look for timing information nearby
                time_match = re.search(r'(\d+\.\d+)', line)
                if time_match:
                    model_performance[model]['times'].append(float(time_match.group(1)))

                # Look for response characteristics
                if 'def ' in line and '```' in line:
                    model_performance[model]['responses'].append('code_generation')
                elif len(line) > 200:
                    model_performance[model]['responses'].append('detailed')

                break

    # Report findings
    print("Model Performance Summary:")
    for model, data in model_performance.items():
        if data['times']:
            avg_time = sum(data['times']) / len(data['times'])
            print(f"\n{model}:")
            print(f"  Test runs found: {len(data['times'])}")
            print(f"  Average response time: {avg_time:.2f}s")
            print(f"  Response types: {list(set(data['responses']))}")

def main():
    filename = "/home/herb/Desktop/test_results_20251001_194846.csv"

    # Basic analysis
    basic_stats = analyze_csv_file(filename)

    # Try to extract performance data
    extract_model_performance(filename)

    print(f"\n{'='*50}")
    print("ANALYSIS COMPLETE")
    print('='*50)

    print("\nKey Findings:")
    print(f"• The CSV file contains complex, malformed data that makes parsing challenging")
    print(f"• Multiple models were tested including {len(basic_stats['model_counts'])} different ones")
    print(f"• {basic_stats['completed_count']} completed tests vs {basic_stats['error_count']} errors")
    print(f"• {basic_stats['code_blocks']} code blocks and {basic_stats['function_definitions']} functions found")

    print("\nRecommendations:")
    print("• Consider exporting future test results in a more structured format")
    print("• The current CSV needs significant pre-processing for automated analysis")
    print("• Manual review of specific model responses would be valuable")
    print("• Focus on the most promising models identified in the basic analysis")

if __name__ == "__main__":
    main()