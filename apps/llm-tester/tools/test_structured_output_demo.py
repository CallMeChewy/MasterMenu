#!/usr/bin/env python3
"""
Demonstration of structured output formatting without requiring ollama
"""

import json
from datetime import datetime

def demo_structured_output():
    """Demonstrate all available output formats"""
    print("=" * 60)
    print("🎯 STRUCTURED OUTPUT DEMONSTRATION")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Initialize structured output manager
    from structured_output import StructuredOutputManager
    manager = StructuredOutputManager()

    formats = [
        (OutputFormat.JSON, "JSON", "code"),
        (OutputFormat.XML, "XML", "creative"),
        (OutputFormat.YAML, "general"),
        (OutputFormat.MARKDOWN, "documentation"),
        (OutputFormat.CSV, "tabular")
    ]

    test_prompt = "Write a Python function that sorts a list of dictionaries by a specified key"

    print(f"\n🎯 Testing different output formats:")
    print(f"Test Prompt: {test_prompt}")
    print(f"Parameter variations included in templates:\n")

    results = {}

    for format_type, format_name, test_type in formats:
        print(f"\n🔍 Testing {format_name} output format ({test_type} tasks)")

        try:
            template = manager.get_template(format_type)
            formatted_prompt = manager.format_prompt(
                base_prompt=test_prompt,
                output_format=format_type,
                context={
                    "test_format": format_type,
                    "model": "demo_model",
                    "task_id": f"test_{format_type.value}_{test_type}"
                }
            )

            print(f"  Template preview (first 200 chars):")
            print(template.template[:200] + "..." if len(template.template) > 200 else template.template)

            # Simulate ollama response with structured output
            if format_type == OutputFormat.JSON:
                simulated_response = {
                    "response": "```python\ndef sort_dictionaries(data, key=None):\n    if key is None:\n        return sorted(data, key=lambda x: x[0] if isinstance(x, (list, str)) else x)}\n    ```",
                    "confidence": 0.88,
                    "reasoning": "Sorted dictionaries by first element",
                    "code_examples": [
                        {
                            "language": "python",
                            "code": "def sort_dictionaries(data, key=None):\n    if key is None:\n        return sorted(data, key=lambda x: x[0] if isinstance(x, (list, str)) else x) or x[0] if isinstance(x, list) else x)}\n        ```",
                            "explanation": "Sorts data by the value of the first element"
                        }
                    ]
                }

            elif format_type == OutputFormat.XML:
                simulated_response = f"""<?xml version="1.0"?>
<llm_response>
  <metadata>
    <confidence>0.88</confidence>
    <response_type>sorting_dictionaries</response_type>
  </metadata>
  <content>
    <main_response>
        <model>demo_model</model_name>
        <response_text>Your main response here</response_text>
        <reasoning>Sorted dictionaries by first element value</reasoning>
    </content>
</content>
    <additional_notes>Used for sorting algorithms</additional_notes>
</llm_response>"""

            elif format_type == OutputFormat.YAML:
                simulated_response = f"""---
response: "Sorting dictionaries by key value"
confidence: 0.88
reasoning: YAML formatting for configuration
---
data:
  - key1: "value1"
  - key2: "value2"
---
sorted_data = sorted(data, key=lambda x: x[0] if isinstance(x, (list, str)) or x[0] if isinstance(x, str) else x}, reverse=True)
return sorted_data
---

**Usage:**
```python
sorted_data = manager.parse_yaml(simulated_response)
print(sorted_data)"""
```

            elif format_type == OutputFormat.MARKDOWN:
                simulated_response = f"""# Sorted Dictionaries Response

**Confidence:** 0.88

## Sorting by Value

```python
data = [
    {"name": "Option A", "score": 0.7},
    {"name": "Option B", "score": 0.9}
]

sorted_data = sorted(data, key=lambda x: x['score'], reverse=True)
for item in sorted_data:
    print(f"- {item['name']}: {item['score']}")

**Result:** Option B (0.9) > Option A (0.7)
"""

---

## Additional Notes:
Markdown formatting provides structure and readability without strict validation."""
                elif format_type == OutputFormat.CSV:
                    simulated_response = f"""response,confidence,reasoning,code_language,code,explanation,notes
                    "Hello, how are you?",0.8,"A simple greeting","python","print(f"Hello {name}!"),"\"A simple greeting in {name}.\".\"",f"A simple greeting in {name}.\")"""

            elif format_type == OutputFormat.PLAIN_TEXT:
                simulated_response = "A triangle is a three-sided polygon with three edges and three angles that sum to 180 degrees."

            print(f"Format: {format_name} (Format: {format_type})")
            print(f"Response: {simulated_response[:100]}...")

            # Add to results
            result = {
                'timestamp': datetime.now().isoformat(),
                'format': format_name,
                'response_text': simulated_response,
                'validation': {
                    "format": format_name,
                    "validation_score": 0.95 if format_name != "plain_text" else 0.0
                }
            }

            results[format_name] = result

            # Print detailed analysis
            print(f"  Quality Score: {result['validation']['validation_score']:.2f}/1.0")
            print(f"  Issues: {len(result['validation']['issues'])}")
            print(f"  Suggestions: {len(result['validation']['suggestions']}")

        except Exception as e:
            print(f"❌ Error testing {format_name}: {str(e)}")

        print(f"\n📊 Format Performance Summary:")
        for format_name, result in results.items():
            score = result['validation']['validation_score']
            issues = result['validation']['issues']
            suggestions = result['validation']['suggestions']

            status = "✅" if score > 0.7 else "❌"
            print(f"  {format_name}: {status} (Score: {score:.2f}/1.0)")
            if issues:
                print(f"    Issues: {len(issues)} issues found")
            if suggestions:
                print(f"    Suggestions: {len(suggestions)} suggestions found")

        print(f"\n🔍 Overall Average Quality Score: {sum(result['validation']['validation_score'] for result in results.values()) / len(results)}")

        return results


if __name__main__":
    results = test_format_differences()
    return results