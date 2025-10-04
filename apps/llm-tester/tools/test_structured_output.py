#!/usr/bin/env python3
"""
Structured Output Formatting Demo

This script demonstrates how to use the enhanced LLM Tester with structured output formatting.
It will run a simple test with different output formats to show the improved formatting capabilities.

Usage:
    python3 test_structured_output.py
"""

import sys
import json
from datetime import datetime

# Import the LLM Tester
sys.path.append('/home/herb/Desktop/MasterMenu')

try:
    from LLMTesterEnhanced import LLMTesterEnhanced
    from structured_output import StructuredOutputManager, OutputFormat
except ImportError as e:
    print(f"Error importing LLM Tester: {e}")
    sys.exit(1)

def test_format_differences():
    """Test the differences between plain text and structured output"""
    print("=" * 60)
    print("STRUCTURED OUTPUT FORMATTING DEMONSTRATION")
    print("=" * 60)

    # Initialize the structured output manager
    output_manager = StructuredOutputManager()

    # Test different output formats
        print("\n📊 Testing different output formats:\n")
        formats = [
            (OutputFormat.JSON, "JSON", "code"),
            (OutputFormat.XML, "XML", "creative"),
            (OutputFormat.YAML, "YAML", "explanation"),
            (OutputFormat.MARKDOWN, "Markdown", "general"),
            (OutputFormat.CSV, "CSV", "tabular")
        ]

        test_prompt = "Write a Python function that calculates factorial of a given number."

        results = {}

        for format_type, format_name, test_type in formats:
            print(f"\n🔍 Testing {format_name} output ({test_type} tasks)")
            print(f"Template preview:")
            template = output_manager.get_template(format_type)
            print(template.template[:200] + ("..." if len(template.template) > 200 else ""))

            # Format the prompt with structured output
            formatted_prompt = output_manager.format_prompt(
                base_prompt=test_prompt,
                output_format=format_type,
                context={
                    "test_format": test_type,
                    "format_type_name": format_name,
                    "task_id": f"structured_test_{format_type}_{test_type}"
                }
            )

            # Test with ollama (using enhanced method would be better)
            print(f"\nTesting with ollama...")
            try:
                # For demo purposes, we'll use the formatted prompt directly
                print(f"  Prompt: {formatted_prompt[:200]}...")
                print(f"  Parameters: {output_manager.get_parameters(format_type)}")

                # Simulate getting ollama response
                if format_type == OutputFormat.JSON:
                    simulated_response = '''{
                        "response": "```python\ndef factorial(n):\n    if n <= 1:\n        return 1\n    return n * factorial(n-1)\n```",
                        "confidence": 0.95,
                        "reasoning": "Used mathematical formula n * (n-1) for factorial calculation",
                        "code_examples": [
                            {
                                "language": "python",
                                "code": "def factorial(n):\n    if n <= 1:\n        return 1\n    return n * (n-1)\n```",
                                "explanation": "Standard factorial function implementation"
                            }
                        ]
                    }"""
                elif format_type == OutputFormat.XML:
                    simulated_response = '''<?xml version="1.0"?>
<llm_response>
  <metadata>
    <confidence>0.95</confidence>
    <response_type>mathematical</response_type>
  </metadata>
  <content>
    <main_response>Your main response here</main_response>
    <reasoning>Used mathematical formula n * (n-1) for factorial calculation</reasoning>
    <code_examples>
      <example>
        <language>python</language>
        <code>def factorial(n):\n    if n <= 1:\n        return 1\n    return n * (n-1)\n```</code>
        <explanation>Standard factorial function implementation</explanation>
      </example>
  </code_examples>
</content>
</llm_response>'''
                elif format_type == OutputFormat.YAML:
                    simulated_response = f"""---
response: Explain what a triangle is in a few sentences.
confidence: 0.9
reasoning: Using geometric principles to describe triangle properties
---
response: A triangle is a three-sided polygon with three edges and three angles
---
code_examples:
  - language: python
    code: def calculate_area(base, height):
        return 0.5 * base * height
    """}

---
notes: The area of a triangle equals one half the product of its base and height.""""""
                elif format_type == OutputFormat.MARKDOWN:
                    simulated_response = f"""# Response
**Confidence:** 0.9

## Triangle Definition
A triangle is a three-sided polygon with three edges and three angles that sum to 180 degrees.

### Properties:
- **Base**: One of the three sides of the triangle
- **Height**: The distance perpendicular to the base
- **Area**: The space enclosed by the triangle
- **Perimeter**: Sum of the three side lengths

### Area Formula
The area of a triangle equals one half the product of its base and height.

**Example:** A triangle with base 10 and height 5 has area = 25 square units.

---

## Usage
```python
import math
def calculate_area(base, height):
    return 0.5 * base * height

area = calculate_area(10, 5)
print(f"Triangle area: {area}")  # Output: Triangle area: 25.0
```

---

**Notes: This is a plain text response. For better structured output, try selecting a structured format."""
                elif format_type == OutputFormat.CSV:
                    simulated_response = "response,confidence,reasoning,code_language,code,explanation,notes\n\"Hello, how are you?\",0.8,\"A simple greeting\",python,print(f'Hello {name}!')\","A simple greeting in {name}.\")"

                elif format_type == OutputFormat.PLAIN_TEXT:
                    simulated_response = "A triangle is a three-sided polygon with three edges and three angles that sum to 180 degrees."

                print(f"Format: {format_name}")
                print(f"Response: {simulated_response}")

                # Add result to results
                result = {
                    'timestamp': datetime.now().isoformat(),
                    'model_name': 'demo_model',
                    'status': 'completed',
                    'response_time': 2.0,
                    'tokens_in': len(prompt.split()),
                    'tokens_out': len(simulated_response.split()),
                    'tokens_per_second': len(simulated_response.split()) / 2.0,
                    'prompt_text': test_prompt,
                    'response_text': simulated_response,
                    'error': None
                }

                results[format_name] = result

                print(f"  Quality Score: {result['performance']['response_quality_score']:.2f}/1.0")
                print(f"  Validation: {validation['validation_score']:.2f}/1.0")

            except Exception as e:
                print(f"Error with {format_name}: {str(e)}")

        print(f"\n📊 SUMMARY:")
        for format_name, result in results.items():
            score = result['performance']['response_quality_score']
            validation = result['validation']
            print(f"  {format_name}: Score {score:.2f}/1.0}, Validation: {validation['validation_score']:.2f}/1.0}")

        return results


def main():
    test_format_differences()
    print(f"\n\n🚀 Testing completed! Check the enhanced LLM Tester to see the new structured output options in action.\n")

if __name__ == "__main__":
    main()