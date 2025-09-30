# File: validate_compliance.py
# Path: /home/herb/Desktop/Finder/validate_compliance.py
# Standard: AIDEV-PascalCase-2.1
# Created: 2025-07-18
# Last Modified: 2025-07-18  13:44PM

"""
AIDEV-PascalCase-2.1 Design Standard Compliance Validator
Validates all Python and Markdown files for proper header format
"""

import os
import re
from datetime import datetime
from pathlib import Path

class ComplianceValidator:
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.files_checked = 0
        
    def validate_directory(self, directory_path):
        """Validate all files in directory"""
        print(f"🔍 Validating AIDEV-PascalCase-2.1 compliance in: {directory_path}")
        print("=" * 80)
        
        for root, dirs, files in os.walk(directory_path):
            for file in files:
                if file.endswith(('.py', '.md')):
                    file_path = os.path.join(root, file)
                    self._validate_file(file_path)
                    
        self._print_summary()
    
    def _validate_file(self, file_path):
        """Validate individual file"""
        self.files_checked += 1
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            self._check_header_format(file_path, content)
            self._check_timestamps(file_path, content)
            self._check_paths(file_path, content)
            
        except Exception as e:
            self.errors.append(f"❌ {file_path}: Could not read file - {e}")
    
    def _check_header_format(self, file_path, content):
        """Check header format compliance"""
        lines = content.split('\n')
        
        if len(lines) < 5:
            self.errors.append(f"❌ {file_path}: File too short for valid header")
            return
            
        # Check required header lines
        expected_patterns = [
            r'^# File: .+',
            r'^# Path: .+',
            r'^# Standard: AIDEV-PascalCase-2\.1',
            r'^# Created: \d{4}-\d{2}-\d{2}',
            r'^# Last Modified: \d{4}-\d{2}-\d{2}\s+\d{1,2}:\d{2}[AP]M'
        ]
        
        for i, pattern in enumerate(expected_patterns):
            if i >= len(lines) or not re.match(pattern, lines[i]):
                self.errors.append(f"❌ {file_path}: Line {i+1} header format invalid")
                return
                
        print(f"✅ {os.path.basename(file_path)}: Header format valid")
    
    def _check_timestamps(self, file_path, content):
        """Check timestamp authenticity"""
        lines = content.split('\n')
        
        # Extract timestamp from header
        for line in lines[:10]:
            if line.startswith('# Last Modified:'):
                timestamp_match = re.search(r'(\d{4}-\d{2}-\d{2})\s+(\d{1,2}:\d{2}[AP]M)', line)
                if timestamp_match:
                    date_str, time_str = timestamp_match.groups()
                    
                    # Check if date is today
                    today = datetime.now().strftime('%Y-%m-%d')
                    if date_str != today:
                        self.warnings.append(f"⚠️  {file_path}: Timestamp not from today ({date_str})")
                    
                    # Check reasonable time format
                    if not re.match(r'\d{1,2}:\d{2}[AP]M', time_str):
                        self.errors.append(f"❌ {file_path}: Invalid time format ({time_str})")
                break
    
    def _check_paths(self, file_path, content):
        """Check path accuracy"""
        lines = content.split('\n')
        
        # Extract path from header
        for line in lines[:10]:
            if line.startswith('# Path:'):
                header_path = line.replace('# Path:', '').strip()
                actual_path = os.path.abspath(file_path)
                
                if header_path != actual_path:
                    self.errors.append(f"❌ {file_path}: Path mismatch")
                    self.errors.append(f"    Header: {header_path}")
                    self.errors.append(f"    Actual: {actual_path}")
                break
    
    def _print_summary(self):
        """Print validation summary"""
        print("\n" + "=" * 80)
        print("📊 COMPLIANCE VALIDATION SUMMARY")
        print("=" * 80)
        
        print(f"📁 Files Checked: {self.files_checked}")
        print(f"❌ Errors: {len(self.errors)}")
        print(f"⚠️  Warnings: {len(self.warnings)}")
        
        if self.errors:
            print(f"\n🚨 ERRORS ({len(self.errors)}):")
            for error in self.errors:
                print(f"  {error}")
        
        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  {warning}")
        
        if not self.errors and not self.warnings:
            print("\n🎉 ALL FILES COMPLIANT!")
            print("✅ All files meet AIDEV-PascalCase-2.1 standards")
        elif not self.errors:
            print(f"\n✅ COMPLIANCE ACHIEVED!")
            print(f"🎯 No critical errors, only {len(self.warnings)} warnings")
        else:
            print(f"\n🔧 COMPLIANCE ISSUES FOUND")
            print(f"🚨 {len(self.errors)} errors need to be fixed")

if __name__ == "__main__":
    validator = ComplianceValidator()
    validator.validate_directory('.')