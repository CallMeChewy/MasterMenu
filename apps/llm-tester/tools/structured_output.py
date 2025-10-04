# File: structured_output.py
# Path: /home/herb/Desktop/LLM-Tester/structured_output.py
# Standard: AIDEV-PascalCase-2.1
# Created: 2025-10-01
# Last Modified: 2025-10-01 9:45PM

"""
Structured Output Formatting for LLM Responses

This module provides templates and formatting instructions for different structured output
formats (JSON, XML, YAML, CSV) to improve LLM response parsing and analysis.

Features:
- Prompt templates for different output formats
- Format-specific escape and validation
- Parsing utilities for structured responses
- Error handling and fallback mechanisms
"""

import json
import xml.etree.ElementTree as ET
from xml.dom import minidom
import re
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum


class OutputFormat(Enum):
    """Supported output formats"""
    JSON = "json"
    XML = "xml"
    YAML = "yaml"
    CSV = "csv"
    MARKDOWN = "markdown"
    PLAIN_TEXT = "plain_text"


@dataclass
class OutputTemplate:
    """Template for structured output format"""
    format_type: OutputFormat
    instruction: str
    template: str
    validation_schema: Optional[Dict[str, Any]] = None
    escape_chars: List[str] = None

    def __post_init__(self):
        if self.escape_chars is None:
            self.escape_chars = self._get_default_escape_chars()

    def _get_default_escape_chars(self) -> List[str]:
        """Get default escape characters for the format"""
        if self.format_type == OutputFormat.JSON:
            return ['"', '\\', '\n', '\t']
        elif self.format_type == OutputFormat.XML:
            return ['<', '>', '&', '"', "'"]
        elif self.format_type == OutputFormat.YAML:
            return ['"', '\\', '\n', ':']
        elif self.format_type == OutputFormat.CSV:
            [',', '"', '\n']
        return []


class StructuredOutputManager:
    """Manages structured output formatting for LLM responses"""

    def __init__(self):
        self.templates = self._initialize_templates()
        self.escape_sequences = self._initialize_escape_sequences()

    def _initialize_templates(self) -> Dict[OutputFormat, OutputTemplate]:
        """Initialize output format templates"""
        templates = {}

        # JSON Template
        templates[OutputFormat.JSON] = OutputTemplate(
            format_type=OutputFormat.JSON,
            instruction="Format your response as valid JSON with the following structure:",
            template="""```json
{{
  "response": "Your main response here",
  "confidence": 0.95,
  "reasoning": "Brief explanation of your approach",
  "code_examples": [
    {{
      "language": "python",
      "code": "Your code here",
      "explanation": "Brief explanation of what the code does"
    }}
  ],
  "additional_notes": "Any extra information or considerations"
}}
```""",
            validation_schema={
                "type": "object",
                "required": ["response", "confidence", "reasoning"],
                "properties": {
                    "response": {"type": "string"},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                    "reasoning": {"type": "string"},
                    "code_examples": {"type": "array"}
                }
            }
        )

        # XML Template
        templates[OutputFormat.XML] = OutputTemplate(
            format_type=OutputFormat.XML,
            instruction="Format your response as valid XML with the following structure:",
            template="""```xml
<llm_response>
  <metadata>
    <confidence>0.95</confidence>
    <response_type>code_generation</response_type>
  </metadata>
  <content>
    <main_response>Your main response here</main_response>
    <reasoning>Brief explanation of your approach</reasoning>
    <code_examples>
      <example>
        <language>python</language>
        <code>Your code here</code>
        <explanation>Brief explanation of what the code does</explanation>
      </example>
    </code_examples>
  </content>
  <additional_notes>Any extra information or considerations</additional_notes>
</llm_response>
```""",
            escape_chars=['<', '>', '&', '"', "'"]
        )

        # YAML Template
        templates[OutputFormat.YAML] = OutputTemplate(
            format_type=OutputFormat.YAML,
            instruction="Format your response as valid YAML with the following structure:",
            template="""```yaml
response: Your main response here
confidence: 0.95
reasoning: Brief explanation of your approach
code_examples:
  - language: python
    code: Your code here
    explanation: Brief explanation of what the code does
additional_notes: Any extra information or considerations
```""",
            escape_chars=['"', '\\', '\n', ':']
        )

        # CSV Template (for tabular data)
        templates[OutputFormat.CSV] = OutputTemplate(
            format_type=OutputFormat.CSV,
            instruction="Format your response as CSV with the following headers: response,confidence,reasoning,code_language,code,explanation,notes",
            template="response,confidence,reasoning,code_language,code,explanation,notes\n\"Your main response here\",0.95,\"Brief explanation\",\"python\",\"Your code here\",\"Brief explanation\",\"Any extra information\""
        )

        # Markdown Template (enhanced formatting)
        templates[OutputFormat.MARKDOWN] = OutputTemplate(
            format_type=OutputFormat.MARKDOWN,
            instruction="Format your response using Markdown with structured sections:",
            template="""# Response

**Confidence:** 0.95

## Main Response
Your main response here

## Reasoning
Brief explanation of your approach

## Code Examples

### Python
```python
Your code here
```
*Explanation:* Brief explanation of what the code does

## Additional Notes
Any extra information or considerations
"""
        )

        return templates

    def _initialize_escape_sequences(self) -> Dict[str, str]:
        """Initialize escape sequences for different formats"""
        return {
            'json': {
                '"': '\\"',
                '\\': '\\\\',
                '\n': '\\n',
                '\t': '\\t',
                '\r': '\\r'
            },
            'xml': {
                '<': '&lt;',
                '>': '&gt;',
                '&': '&amp;',
                '"': '&quot;',
                "'": '&apos;'
            },
            'yaml': {
                '"': '\\"',
                '\\': '\\\\',
                '\n': '\\n',
                ':': ':'
            },
            'csv': {
                '"': '""',
                ',': ',',
                '\n': '\\n'
            }
        }

    def get_template(self, format_type: OutputFormat) -> OutputTemplate:
        """Get template for specified format"""
        return self.templates.get(format_type, self.templates[OutputFormat.JSON])

    def format_prompt(self, base_prompt: str, output_format: OutputFormat,
                       context: Optional[Dict[str, Any]] = None) -> str:
        """
        Format a prompt with structured output instructions

        Args:
            base_prompt: The original prompt
            output_format: Desired output format
            context: Additional context for the response

        Returns:
            Formatted prompt with output formatting instructions
        """
        template = self.get_template(output_format)

        formatted_prompt = f"""{base_prompt}

{template.instruction}

{template.template}"""

        # Add context information if provided
        if context:
            context_section = "\n## Additional Context\n"
            for key, value in context.items():
                context_section += f"- {key}: {value}\n"
            formatted_prompt += context_section

        formatted_prompt += "\n\nIMPORTANT: Provide only the structured output in the specified format. Do not include additional explanatory text outside the structured format."

        return formatted_prompt

    def parse_response(self, response_text: str, output_format: OutputFormat) -> Dict[str, Any]:
        """
        Parse a structured response

        Args:
            response_text: The LLM response text
            output_format: Expected output format

        Returns:
            Parsed data as dictionary
        """
        try:
            if output_format == OutputFormat.JSON:
                return self._parse_json(response_text)
            elif output_format == OutputFormat.XML:
                return self._parse_xml(response_text)
            elif output_format == OutputFormat.YAML:
                return self._parse_yaml(response_text)
            elif output_format == OutputFormat.CSV:
                return self._parse_csv(response_text)
            elif output_format == OutputFormat.MARKDOWN:
                return self._parse_markdown(response_text)
            else:
                return {"error": f"Unsupported format: {output_format}"}
        except Exception as e:
            return {"error": f"Parsing failed: {str(e)}", "raw_response": response_text}

    def _parse_json(self, response_text: str) -> Dict[str, Any]:
        """Parse JSON response"""
        # Find JSON content between ```json tags
        json_match = re.search(r'```json\s*\n(.*?)\n```', response_text, re.DOTALL)
        if json_match:
            json_content = json_match.group(1).strip()
        else:
            # Try to find JSON content without code blocks
            json_start = response_text.find('{')
            if json_start != -1:
                # Find matching closing brace
                brace_count = 0
                for i, char in enumerate(response_text[json_start:]):
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            json_content = response_text[json_start:json_start + i + 1]
                            break
                else:
                    json_content = response_text[json_start:]
            else:
                raise ValueError("No JSON content found")

        return json.loads(json_content)

    def _parse_xml(self, response_text: str) -> Dict[str, Any]:
        """Parse XML response"""
        # Find XML content between ```xml tags
        xml_match = re.search(r'```xml\s*\n(.*?)\n```', response_text, re.DOTALL)
        if xml_match:
            xml_content = xml_match.group(1).strip()
        else:
            # Try to find root element
            root_match = re.search(r'<([^>\s]+)', response_text)
            if root_match:
                root_tag = root_match.group(1)
                end_tag = f"</{root_tag}>"
                start_pos = response_text.find(f"<{root_tag}")
                end_pos = response_text.find(end_tag)
                if end_pos != -1:
                    xml_content = response_text[start_pos:end_pos + len(end_tag)]
                else:
                    xml_content = response_text[start_pos:]
            else:
                raise ValueError("No XML content found")

        root = ET.fromstring(xml_content)
        return self._xml_to_dict(root)

    def _xml_to_dict(self, element) -> Dict[str, Any]:
        """Convert XML element to dictionary"""
        result = {}

        # Handle attributes
        if element.attrib:
            result.update(element.attrib)

        # Handle child elements
        for child in element:
            if len(list(element)) == 0:
                # Leaf node
                if child.tag in result:
                    if not isinstance(result[child.tag], list):
                        result[child.tag] = [result[child.tag]]
                    result[child.tag].append(child.text or "")
                else:
                    result[child.tag] = child.text or ""
            else:
                # Has children
                child_dict = self._xml_to_dict(child)
                if child.tag in result:
                    if not isinstance(result[child.tag], list):
                        result[child.tag] = [result[child.tag]]
                    result[child.tag].append(child_dict)
                else:
                    result[child.tag] = child_dict

        # Handle text content
        if element.text and element.text.strip():
            text_content = element.text.strip()
            if result:
                result["_text"] = text_content
            else:
                return text_content

        return result

    def _parse_yaml(self, response_text: str) -> Dict[str, Any]:
        """Parse YAML response"""
        # Try to import yaml library
        try:
            import yaml
        except ImportError:
            # Fallback parsing for basic YAML
            return self._parse_yaml_fallback(response_text)

        # Find YAML content between ```yaml tags
        yaml_match = re.search(r'```yaml\s*\n(.*?)\n```', response_text, re.DOTALL)
        if yaml_match:
            yaml_content = yaml_match.group(1).strip()
        else:
            # Use entire response as YAML
            yaml_content = response_text

        return yaml.safe_load(yaml_content)

    def _parse_yaml_fallback(self, response_text: str) -> Dict[str, Any]:
        """Fallback YAML parsing for simple structures"""
        result = {}
        lines = response_text.strip().split('\n')

        for line in lines:
            line = line.strip()
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()

                # Try to convert to appropriate type
                if value.lower() in ['true', 'false']:
                    result[key] = value.lower() == 'true'
                elif value.replace('.', '').replace('-', '').isdigit():
                    try:
                        if '.' in value:
                            result[key] = float(value)
                        else:
                            result[key] = int(value)
                    except ValueError:
                        result[key] = value
                else:
                    result[key] = value

        return result

    def _parse_csv(self, response_text: str) -> Dict[str, Any]:
        """Parse CSV response"""
        # Find CSV content between ```csv tags
        csv_match = re.search(r'```csv\s*\n(.*?)\n```', response_text, re.DOTALL)
        if csv_match:
            csv_content = csv_match.group(1).strip()
        else:
            # Use entire response as CSV
            csv_content = response_text.strip()

        lines = csv_content.split('\n')
        if not lines:
            return {"error": "Empty CSV content"}

        # Parse header
        headers = [h.strip().strip('"') for h in lines[0].split(',')]

        # Parse data rows
        rows = []
        for line in lines[1:]:
            if line.strip():
                # Handle quoted CSV
                values = self._parse_csv_line(line)
                if len(values) == len(headers):
                    rows.append(values)

        return {
            "headers": headers,
            "rows": rows,
            "total_rows": len(rows)
        }

    def _parse_csv_line(self, line: str) -> List[str]:
        """Parse a single CSV line handling quoted fields"""
        values = []
        current_value = ""
        in_quotes = False
        i = 0

        while i < len(line):
            char = line[i]

            if char == '"' and (i == 0 or line[i-1] == ',' or line[i-1] == '\n'):
                in_quotes = not in_quotes
            elif char == ',' and not in_quotes:
                values.append(current_value.strip().strip('"'))
                current_value = ""
            else:
                current_value += char

            i += 1

        # Add last value
        values.append(current_value.strip().strip('"'))
        return values

    def _parse_markdown(self, response_text: str) -> Dict[str, Any]:
        """Parse Markdown response"""
        import re

        result = {}

        # Extract confidence
        confidence_match = re.search(r'\*\*Confidence:\*\*\s*([\d.]+)', response_text)
        if confidence_match:
            result['confidence'] = float(confidence_match.group(1))

        # Extract main response
        main_response_match = re.search(r'## Main Response\n(.*?)(?=##|$)', response_text, re.DOTALL)
        if main_response_match:
            result['main_response'] = main_response_match.group(1).strip()

        # Extract reasoning
        reasoning_match = re.search(r'## Reasoning\n(.*?)(?=##|$)', response_text, re.DOTALL)
        if reasoning_match:
            result['reasoning'] = reasoning_match.group(1).strip()

        # Extract code examples
        code_examples = []
        code_pattern = r'### (\w+)\n```(\w+)\n(.*?)\n```'
        for match in re.finditer(code_pattern, response_text, re.DOTALL):
            language = match.group(1)
            code_lang = match.group(2)
            code = match.group(3)

            # Extract explanation
            explanation_match = re.search(r'\*Explanation:\*\s*(.*?)(?=\n|\n#|$)',
                                         response_text[match.end():], re.DOTALL)
            explanation = explanation_match.group(1).strip() if explanation_match else ""

            code_examples.append({
                'language': language,
                'code': code,
                'explanation': explanation
            })

        result['code_examples'] = code_examples

        # Extract additional notes
        notes_match = re.search(r'## Additional Notes\n(.*?)$', response_text, re.DOTALL)
        if notes_match:
            result['additional_notes'] = notes_match.group(1).strip()

        return result

    def escape_for_format(self, text: str, output_format: OutputFormat) -> str:
        """Escape text for the specified output format"""
        if output_format == OutputFormat.JSON:
            return json.dumps(text, ensure_ascii=False)
        elif output_format == OutputFormat.XML:
            # Escape for XML
            text = text.replace('&', '&amp;')
            text = text.replace('<', '&lt;')
            text = text.replace('>', '&gt;')
            text = text.replace('"', '&quot;')
            text = text.replace("'", '&apos;')
            return text
        elif output_format == OutputFormat.YAML:
            # Escape for YAML
            text = text.replace('\\', '\\\\')
            text = text.replace('"', '\\"')
            return text
        elif output_format == OutputFormat.CSV:
            # Escape for CSV
            if '"' in text or ',' in text or '\n' in text:
                text = text.replace('"', '""')
                text = f'"{text}"'
            return text
        else:
            return text

    def validate_response(self, response_text: str, output_format: OutputFormat) -> Dict[str, Any]:
        """Validate that a response conforms to the expected format"""
        try:
            parsed = self.parse_response(response_text, output_format)

            if "error" in parsed:
                return {
                    "valid": False,
                    "error": parsed["error"],
                    "suggestion": "Response does not match expected format"
                }

            # Basic validation checks
            validation_result = {
                "valid": True,
                "format": output_format.value,
                "parsed_structure": list(parsed.keys()) if isinstance(parsed, dict) else type(parsed).__name__
            }

            # Add format-specific validation
            if output_format == OutputFormat.JSON:
                validation_result.update(self._validate_json_structure(parsed))
            elif output_format == OutputFormat.XML:
                validation_result.update(self._validate_xml_structure(parsed))
            elif output_format == OutputFormat.CSV:
                validation_result.update(self._validate_csv_structure(parsed))

            return validation_result

        except Exception as e:
            return {
                "valid": False,
                "error": str(e),
                "suggestion": "Response could not be parsed or validated"
            }

    def _validate_json_structure(self, parsed: Dict[str, Any]) -> Dict[str, Any]:
        """Validate JSON structure"""
        required_fields = ["response", "confidence", "reasoning"]
        missing_fields = [field for field in required_fields if field not in parsed]

        validation = {
            "missing_required_fields": missing_fields,
            "has_code_examples": "code_examples" in parsed,
            "confidence_valid": isinstance(parsed.get("confidence"), (int, float)) and 0 <= parsed.get("confidence", -1) <= 1
        }

        validation["valid"] = len(missing_fields) == 0 and validation["confidence_valid"]

        return validation

    def _validate_xml_structure(self, parsed: Dict[str, Any]) -> Dict[str, Any]:
        """Validate XML structure"""
        validation = {
            "has_metadata": "metadata" in parsed,
            "has_content": "content" in parsed,
            "has_response": "main_response" in parsed.get("content", {})
        }

        validation["valid"] = validation["has_metadata"] and validation["has_content"]

        return validation

    def _validate_csv_structure(self, parsed: Dict[str, Any]) -> Dict[str, Any]:
        """Validate CSV structure"""
        validation = {
            "has_headers": "headers" in parsed,
            "has_rows": "rows" in parsed,
            "row_count": parsed.get("total_rows", 0),
            "column_count": len(parsed.get("headers", []))
        }

        validation["valid"] = validation["has_headers"] and validation["row_count"] > 0

        return validation


# Example usage
if __name__ == "__main__":
    manager = StructuredOutputManager()

    # Example: Format a prompt for JSON output
    base_prompt = "Create a function to calculate the area of a triangle given base and height."

    json_prompt = manager.format_prompt(
        base_prompt=base_prompt,
        output_format=OutputFormat.JSON,
        context={"task_type": "code_generation", "difficulty": "beginner"}
    )

    print("JSON Prompt:")
    print(json_prompt)
    print("\n" + "="*50 + "\n")

    # Example: Format a prompt for XML output
    xml_prompt = manager.format_prompt(
        base_prompt=base_prompt,
        output_format=OutputFormat.XML
    )

    print("XML Prompt:")
    print(xml_prompt)