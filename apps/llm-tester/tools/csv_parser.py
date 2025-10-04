# File: csv_parser.py
# Path: /home/herb/Desktop/LLM-Tester/csv_parser.py
# Standard: AIDEV-PascalCase-2.1
# Created: 2025-10-01
# Last Modified: 2025-10-01 8:30PM

"""
Robust CSV Parser for LLM Test Results

This module provides robust parsing of LLM test results CSV files that may have
malformed data due to response text containing commas, quotes, and newlines.

Features:
- Handles malformed CSV rows with embedded commas and quotes
- Recovers from parsing errors with detailed error reporting
- Extracts clean, structured data for analysis
- Provides data validation and cleaning
"""

import csv
import re
import json
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime


@dataclass
class TestResult:
    """Structured representation of a single test result"""
    timestamp: str
    model_name: str
    status: str
    response_time: float
    tokens_in: int
    tokens_out: int
    tokens_per_second: float
    prompt_text: str
    response_text: str
    error: Optional[str] = None
    row_number: int = 0
    parsing_issues: List[str] = None

    def __post_init__(self):
        if self.parsing_issues is None:
            self.parsing_issues = []


class RobustCSVParser:
    """Robust CSV parser for malformed LLM test results"""

    def __init__(self):
        self.parse_errors = []
        self.successful_parses = 0
        self.failed_parses = 0

    def clean_model_name(self, model_field: str) -> str:
        """Clean and standardize model names"""
        model = model_field.strip()
        # Remove common artifacts
        model = re.sub(r'[^\w\.\-:]', '', model)
        return model if model else "unknown"

    def parse_response_time(self, time_field: str) -> float:
        """Parse response time field"""
        try:
            time_str = time_field.strip()
            return float(time_str)
        except (ValueError, AttributeError):
            return 0.0

    def parse_token_count(self, token_field: str) -> int:
        """Parse token count fields"""
        try:
            token_str = token_field.strip()
            return int(float(token_str))  # Handle cases like "1.0"
        except (ValueError, AttributeError):
            return 0

    def parse_tokens_per_second(self, tps_field: str) -> float:
        """Parse tokens per second field"""
        try:
            tps_str = tps_field.strip()
            return float(tps_str)
        except (ValueError, AttributeError):
            return 0.0

    def extract_text_field(self, line_parts: List[str], start_index: int, field_name: str) -> Tuple[str, int]:
        """
        Extract a text field that may contain commas and quotes.
        Returns the cleaned text and the index of the next field.
        """
        if start_index >= len(line_parts):
            return "", start_index

        text_parts = []
        current_index = start_index
        in_quotes = False
        quote_char = None

        while current_index < len(line_parts):
            part = line_parts[current_index].strip()

            if not in_quotes:
                # Check if this part starts a quoted field
                if part.startswith('"') and part.endswith('"') and len(part) > 1:
                    # Single quoted part
                    text_parts.append(part[1:-1])
                    current_index += 1
                    break
                elif part.startswith('"'):
                    # Start of multi-part quoted field
                    in_quotes = True
                    quote_char = '"'
                    text_parts.append(part[1:])  # Remove opening quote
                elif part.startswith("'"):
                    in_quotes = True
                    quote_char = "'"
                    text_parts.append(part[1:])
                else:
                    # Unquoted text
                    text_parts.append(part)
                    current_index += 1
                    break
            else:
                # Inside a quoted field
                if part.endswith(quote_char):
                    # End of quoted field
                    text_parts.append(part[:-1])  # Remove closing quote
                    in_quotes = False
                    current_index += 1
                    break
                else:
                    # Continuation of quoted field
                    text_parts.append(part)
                    current_index += 1

        # Clean up the extracted text
        cleaned_text = ' '.join(text_parts).strip()

        # Remove any remaining quote artifacts
        cleaned_text = re.sub(r'["""]+$', '', cleaned_text)
        cleaned_text = re.sub(r'^["""]+', '', cleaned_text)

        return cleaned_text, current_index

    def parse_csv_line(self, line: str, line_number: int) -> Optional[TestResult]:
        """Parse a single CSV line with robust error handling"""
        try:
            # Split by commas first
            parts = [part.strip() for part in line.split(',')]

            if len(parts) < 8:
                self.parse_errors.append(f"Line {line_number}: Too few fields ({len(parts)} < 8)")
                self.failed_parses += 1
                return None

            # Parse each field
            timestamp = parts[0].strip() if parts[0] else ""
            model_name = self.clean_model_name(parts[1] if len(parts) > 1 else "")
            status = parts[2].strip() if len(parts) > 2 else "unknown"
            response_time = self.parse_response_time(parts[3] if len(parts) > 3 else "0")
            tokens_in = self.parse_token_count(parts[4] if len(parts) > 4 else "0")
            tokens_out = self.parse_token_count(parts[5] if len(parts) > 5 else "0")
            tokens_per_second = self.parse_tokens_per_second(parts[6] if len(parts) > 6 else "0")

            # Extract prompt text (may contain commas)
            prompt_text, next_index = self.extract_text_field(parts, 7, "prompt")

            # Extract response text (may contain commas and quotes)
            response_text = ""
            if next_index < len(parts):
                response_text, _ = self.extract_text_field(parts, next_index, "response")

            # Handle error field if present
            error = None
            if len(parts) > next_index + 1 and parts[next_index + 1].strip():
                error_field = ' '.join(parts[next_index + 1:]).strip()
                error = error_field.strip('"').strip("'")

            # Clean up text fields
            prompt_text = re.sub(r'\s+', ' ', prompt_text).strip()
            response_text = re.sub(r'\s+', ' ', response_text).strip()

            # Create result object
            result = TestResult(
                timestamp=timestamp,
                model_name=model_name,
                status=status,
                response_time=response_time,
                tokens_in=tokens_in,
                tokens_out=tokens_out,
                tokens_per_second=tokens_per_second,
                prompt_text=prompt_text,
                response_text=response_text,
                error=error,
                row_number=line_number
            )

            # Add parsing issues if detected
            if model_name == "unknown":
                result.parsing_issues.append("Model name could not be parsed")
            if not prompt_text:
                result.parsing_issues.append("Prompt text is empty")
            if not response_text and status == "completed":
                result.parsing_issues.append("Response text is empty despite completed status")

            self.successful_parses += 1
            return result

        except Exception as e:
            self.parse_errors.append(f"Line {line_number}: Parse error - {str(e)}")
            self.failed_parses += 1
            return None

    def parse_csv_file(self, file_path: str, max_lines: Optional[int] = None) -> List[TestResult]:
        """
        Parse the entire CSV file

        Args:
            file_path: Path to CSV file
            max_lines: Maximum number of lines to parse (None for all lines)

        Returns:
            List of parsed TestResult objects
        """
        results = []

        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as file:
                lines = file.readlines()

            # Skip header if present
            start_line = 1
            if lines and 'timestamp' in lines[0].lower():
                start_line = 2

            end_line = len(lines)
            if max_lines:
                end_line = min(len(lines), start_line + max_lines)

            print(f"Parsing lines {start_line} to {end_line} of {len(lines)} total lines")

            for line_num in range(start_line, end_line):
                line = lines[line_num - 1].strip()

                if not line:
                    continue  # Skip empty lines

                result = self.parse_csv_line(line, line_num)
                if result:
                    results.append(result)

                # Progress reporting for large files
                if len(results) % 1000 == 0:
                    print(f"Parsed {len(results)} results so far...")

        except FileNotFoundError:
            print(f"Error: File '{file_path}' not found")
            return []
        except Exception as e:
            print(f"Error reading file: {str(e)}")
            return []

        return results

    def get_parse_statistics(self) -> Dict[str, Any]:
        """Get statistics about the parsing process"""
        return {
            'successful_parses': self.successful_parses,
            'failed_parses': self.failed_parses,
            'total_lines': self.successful_parses + self.failed_parses,
            'success_rate': (self.successful_parses / (self.successful_parses + self.failed_parses) * 100)
                          if (self.successful_parses + self.failed_parses) > 0 else 0,
            'parse_errors': self.parse_errors[:10]  # First 10 errors
        }

    def filter_results(self, results: List[TestResult],
                       model_filter: Optional[str] = None,
                       status_filter: Optional[str] = None,
                       min_score: Optional[float] = None) -> List[TestResult]:
        """
        Filter results based on criteria

        Args:
            results: List of TestResult objects
            model_filter: Filter by model name (partial match)
            status_filter: Filter by status
            min_score: Filter by minimum tokens_per_second score

        Returns:
            Filtered list of results
        """
        filtered = results

        if model_filter:
            filtered = [r for r in filtered if model_filter.lower() in r.model_name.lower()]

        if status_filter:
            filtered = [r for r in filtered if r.status == status_filter]

        if min_score is not None:
            filtered = [r for r in filtered if r.tokens_per_second >= min_score]

        return filtered

    def get_summary_statistics(self, results: List[TestResult]) -> Dict[str, Any]:
        """Get summary statistics for parsed results"""
        if not results:
            return {"error": "No results to analyze"}

        # Basic counts
        total_tests = len(results)
        completed_tests = len([r for r in results if r.status == "completed"])
        failed_tests = len([r for r in results if r.status == "error"])

        # Model statistics
        model_counts = {}
        for result in results:
            model_counts[result.model_name] = model_counts.get(result.model_name, 0) + 1

        # Performance statistics
        response_times = [r.response_time for r in results if r.response_time > 0]
        tokens_per_second = [r.tokens_per_second for r in results if r.tokens_per_second > 0]
        response_lengths = [len(r.response_text) for r in results]

        # Calculate averages
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        avg_tokens_per_second = sum(tokens_per_second) / len(tokens_per_second) if tokens_per_second else 0
        avg_response_length = sum(response_lengths) / len(response_lengths) if response_lengths else 0

        return {
            'total_tests': total_tests,
            'completed_tests': completed_tests,
            'failed_tests': failed_tests,
            'success_rate': (completed_tests / total_tests * 100) if total_tests > 0 else 0,
            'model_distribution': model_counts,
            'performance_stats': {
                'avg_response_time': avg_response_time,
                'avg_tokens_per_second': avg_tokens_per_second,
                'avg_response_length': avg_response_length,
                'min_response_time': min(response_times) if response_times else 0,
                'max_response_time': max(response_times) if response_times else 0,
                'min_tokens_per_second': min(tokens_per_second) if tokens_per_second else 0,
                'max_tokens_per_second': max(tokens_per_second) if tokens_per_second else 0
            }
        }

    def export_parsed_results(self, results: List[TestResult], filename: str):
        """Export parsed results to clean JSON format"""
        export_data = {
            'export_timestamp': datetime.now().isoformat(),
            'parse_statistics': self.get_parse_statistics(),
            'summary_statistics': self.get_summary_statistics(results),
            'results': [
                {
                    'timestamp': r.timestamp,
                    'model_name': r.model_name,
                    'status': r.status,
                    'response_time': r.response_time,
                    'tokens_in': r.tokens_in,
                    'tokens_out': r.tokens_out,
                    'tokens_per_second': r.tokens_per_second,
                    'prompt_text': r.prompt_text,
                    'response_text': r.response_text,
                    'error': r.error,
                    'response_length': len(r.response_text),
                    'parsing_issues': r.parsing_issues
                }
                for r in results
            ]
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

        print(f"Exported {len(results)} parsed results to {filename}")


# Example usage
if __name__ == "__main__":
    parser = RobustCSVParser()

    # Parse the CSV file
    results = parser.parse_csv_file("/home/herb/Desktop/test_results_20251001_194846.csv")

    # Show statistics
    stats = parser.get_parse_statistics()
    print(f"Parsing Statistics:")
    print(f"  Successful: {stats['successful_parses']}")
    print(f"  Failed: {stats['failed_parses']}")
    print(f"  Success Rate: {stats['success_rate']:.1f}%")

    # Show summary
    summary = parser.get_summary_statistics(results)
    print(f"\nSummary Statistics:")
    print(f"  Total Tests: {summary['total_tests']}")
    print(f"  Completed: {summary['completed_tests']}")
    print(f"  Failed: {summary['failed_tests']}")
    print(f"  Avg Response Time: {summary['performance_stats']['avg_response_time']:.2f}s")
    print(f"  Avg Tokens/Second: {summary['performance_stats']['avg_tokens_per_second']:.1f}")

    # Export clean results
    parser.export_parsed_results(results, "/home/herb/Desktop/clean_test_results.json")