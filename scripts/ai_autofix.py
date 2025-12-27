"""
RetroAuto AI AutoFix - Direct Mode
===================================
Generates formatted prompts for AI assistant to fix test failures directly.
No external API required - works with Claude, Copilot, or any AI assistant.

Adapted for RetroAuto DSL codebase with DSL-specific error categorization.

Usage:
    python scripts/ai_autofix.py                           # Auto-find results
    python scripts/ai_autofix.py --results=test_results.xml # Specific file
    python scripts/ai_autofix.py --output=fixes.md         # Save to file
"""

import os
import sys
import json
import argparse
import re
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional
from dataclasses import dataclass
from pathlib import Path


@dataclass
class TestFailure:
    """Information about a test failure."""
    test_name: str
    test_file: str
    source_file: str
    source_line: int
    error_type: str
    error_message: str
    traceback: str
    source_code: str = ""


class TestResultParser:
    """Parses pytest test results from XML or JSON."""
    
    def parse_junit_xml(self, xml_path: str) -> List[TestFailure]:
        """Parse JUnit XML format (pytest --junitxml)."""
        failures = []
        
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
            
            for testcase in root.iter('testcase'):
                failure = testcase.find('failure')
                error = testcase.find('error')
                
                fail_elem = failure if failure is not None else error
                if fail_elem is None:
                    continue
                    
                classname = testcase.get('classname', '')
                name = testcase.get('name', '')
                message = fail_elem.get('message', '')
                traceback = fail_elem.text or ''
                
                source_file, source_line = self._extract_source_location(traceback)
                
                failures.append(TestFailure(
                    test_name=f"{classname}::{name}",
                    test_file=classname.replace('.', '/') + '.py' if classname else '',
                    source_file=source_file,
                    source_line=source_line,
                    error_type=fail_elem.get('type', 'Error'),
                    error_message=message,
                    traceback=traceback
                ))
                
        except Exception as e:
            print(f"Error parsing XML: {e}")
            
        return failures
    
    def _extract_source_location(self, traceback: str) -> tuple:
        """Extract source file and line from traceback."""
        matches = re.findall(r'([^\\\/:]+\.py):(\d+)', traceback)
        if matches:
            return matches[-1][0], int(matches[-1][1])
        return "", 0


class RetroAutoAutoFix:
    """Generates prompts for AI assistant to fix RetroAuto test failures."""
    
    # RetroAuto-specific search paths
    SEARCH_PATHS = ['.', 'core', 'core/dsl', 'core/engine', 'core/game', 
                    'app', 'app/ui', 'tests', 'scripts']
    
    def load_source_code(self, file_path: str, line: int, context: int = 10) -> str:
        """Load source code around the error line."""
        try:
            for base in self.SEARCH_PATHS:
                full_path = Path(base) / file_path
                if full_path.exists():
                    with open(full_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        
                    start = max(0, line - context - 1)
                    end = min(len(lines), line + context)
                    
                    code_lines = []
                    for i, code in enumerate(lines[start:end], start=start+1):
                        marker = ">>> " if i == line else "    "
                        code_lines.append(f"{marker}{i}: {code.rstrip()}")
                    
                    return '\n'.join(code_lines)
        except Exception as e:
            pass
        return f"[Could not load source from {file_path}:{line}]"
    
    def generate_prompt(self, failures: List[TestFailure], max_failures: int = 10) -> str:
        """Generate a prompt for AI assistant to fix failures."""
        
        prompt = """# 🔧 RetroAuto AI AutoFix - Test Failures Analysis

## Instructions for AI Assistant

Please analyze these test failures and provide fixes. For each failure:
1. Identify if it's a **test error** or **application bug**
2. Explain the root cause
3. Provide the fix (either test fix or code fix)

## RetroAuto-Specific Context

- **DSL Errors**: Check TokenType, AST node types, parser state
- **GUI Errors**: Check QWidget initialization, signal connections
- **Vision Errors**: Check OpenCV array bounds, image loading
- **Engine Errors**: Check interpreter state, scope management

---

"""
        # Categorize failures
        categories = {}
        for f in failures[:max_failures]:
            error_type = self._categorize_error(f)
            if error_type not in categories:
                categories[error_type] = []
            categories[error_type].append(f)
        
        # Summary
        prompt += f"## 📊 Summary\n\n"
        prompt += f"**Total Failures**: {len(failures)}\n"
        prompt += f"**Showing**: {min(max_failures, len(failures))}\n\n"
        
        prompt += "| Category | Count | Type |\n"
        prompt += "|:---|:---:|:---|\n"
        for cat, items in categories.items():
            cat_type = 'DSL Issue' if 'DSL' in cat else 'Test Issue' if 'Test' in cat else 'Potential Bug'
            prompt += f"| {cat} | {len(items)} | {cat_type} |\n"
        
        prompt += "\n---\n\n"
        
        # Detail each failure
        for i, failure in enumerate(failures[:max_failures], 1):
            category = self._categorize_error(failure)
            source_code = self.load_source_code(failure.source_file, failure.source_line)
            
            prompt += f"## Failure #{i}: {failure.test_name.split('::')[-1]}\n\n"
            prompt += f"**Category**: {category}\n"
            prompt += f"**Error Type**: `{failure.error_type}`\n"
            prompt += f"**File**: `{failure.source_file}:{failure.source_line}`\n\n"
            
            prompt += f"### Error Message\n```\n{failure.error_message[:500]}\n```\n\n"
            
            prompt += f"### Source Code\n```python\n{source_code}\n```\n\n"
            
            prompt += f"### Traceback\n```\n{failure.traceback[:800]}\n```\n\n"
            
            prompt += "### 💡 Fix Required\n"
            prompt += self._suggest_fix_template(failure, category)
            prompt += "\n---\n\n"
        
        prompt += """
## 📝 Response Format

For each failure, please respond with:

```markdown
### Fix for Failure #N

**Type**: [Test Fix / Application Fix]
**Root Cause**: [Brief explanation]

**Original Code**:
```python
[code that needs fixing]
```

**Fixed Code**:
```python
[corrected code]
```

**Explanation**: [Why this fix works]
```

---

Please analyze and provide fixes for each failure above.
"""
        
        return prompt
    
    def _categorize_error(self, failure: TestFailure) -> str:
        """Categorize the error type with RetroAuto-specific categories."""
        msg = failure.error_message.lower()
        traceback = failure.traceback.lower()
        
        # DSL-specific errors
        if 'tokentype' in msg or 'tokentype' in traceback:
            return "DSL TokenType Error"
        elif 'astnode' in msg or 'parser' in traceback:
            return "DSL Parser/AST Error"
        elif 'lexer' in traceback:
            return "DSL Lexer Error"
        
        # GUI-specific errors
        elif 'qwidget' in msg or 'pyside' in msg or 'qt' in msg:
            return "GUI Widget Error"
        elif 'signal' in msg or 'slot' in msg:
            return "GUI Signal/Slot Error"
        
        # Vision-specific errors
        elif 'cv2' in msg or 'opencv' in msg or 'imread' in msg:
            return "Vision/OpenCV Error"
        
        # Standard Python errors
        elif 'nameerror' in msg or 'name' in msg and 'not defined' in msg:
            return "Missing Variable/Fixture"
        elif 'typeerror' in msg and 'missing' in msg and 'argument' in msg:
            return "Missing Constructor Args"
        elif 'typeerror' in msg and 'abstract' in msg:
            return "Abstract Class Instantiation"
        elif 'assertionerror' in msg:
            return "Assertion Failure"
        elif 'attributeerror' in msg:
            return "Missing Attribute"
        elif '__init__' in msg and 'none' in msg.lower():
            return "Init Returns None (Normal)"
        elif 'importerror' in msg or 'modulenotfounderror' in msg:
            return "Import Error"
        else:
            return "Other Error"
    
    def _suggest_fix_template(self, failure: TestFailure, category: str) -> str:
        """Suggest fix based on category."""
        templates = {
            # DSL-specific
            "DSL TokenType Error": 
                "Check TokenType enum usage. Ensure correct token comparison.\n",
            "DSL Parser/AST Error":
                "Verify AST node creation and parser state. Check _parse_* method.\n",
            "DSL Lexer Error":
                "Check lexer tokenization. Verify _scan_* method and token creation.\n",
            
            # GUI-specific
            "GUI Widget Error":
                "Ensure QWidget parent is set. Check widget initialization order.\n",
            "GUI Signal/Slot Error":
                "Verify signal signature matches slot. Check connection timing.\n",
            
            # Vision-specific
            "Vision/OpenCV Error":
                "Check image array bounds. Verify imread success before processing.\n",
            
            # Standard errors
            "Missing Variable/Fixture": 
                "Add `tmp_path` parameter to test function or define missing variable.\n",
            "Missing Constructor Args":
                "Provide required arguments when instantiating class.\n",
            "Abstract Class Instantiation":
                "Use a concrete subclass instead of abstract base class.\n",
            "Assertion Failure":
                "Update expected values or fix the logic being tested.\n",
            "Missing Attribute":
                "Check if attribute exists or use correct attribute name.\n",
            "Init Returns None (Normal)":
                "This is expected behavior - `__init__` always returns None. Update assertion.\n",
            "Import Error":
                "Check module path. Ensure package is installed or path is correct.\n",
        }
        return templates.get(category, "Analyze the error and provide appropriate fix.\n")


def main():
    parser = argparse.ArgumentParser(description="RetroAuto AI AutoFix - Direct Mode")
    parser.add_argument("--results", help="Test results file (XML or JSON)")
    parser.add_argument("--output", help="Output file for prompt (default: stdout)")
    parser.add_argument("--max", type=int, default=10, help="Max failures to include")
    parser.add_argument("--clipboard", action="store_true", help="Copy to clipboard")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🔧 RETROAUTO AI AUTOFIX - DIRECT MODE")
    print("=" * 60)
    print("No API key required - generates prompt for AI assistant")
    print("=" * 60)
    
    if not args.results:
        # Try to find test results
        for pattern in ['test_results.xml', 'results.xml', 'pytest_output.xml', 
                        'tests/results.xml', '.pytest_cache/results.xml']:
            if Path(pattern).exists():
                args.results = pattern
                print(f"Found: {pattern}")
                break
    
    if not args.results or not Path(args.results).exists():
        print("❌ No test results file found")
        print("\nGenerate results first:")
        print("  pytest --junitxml=test_results.xml")
        print("\nOr specify file:")
        print("  python scripts/ai_autofix.py --results=test_results.xml")
        sys.exit(1)
    
    # Parse results
    result_parser = TestResultParser()
    if args.results.endswith('.xml'):
        failures = result_parser.parse_junit_xml(args.results)
    else:
        print("❌ Only XML format supported currently")
        sys.exit(1)
    
    if not failures:
        print("✅ No test failures found!")
        sys.exit(0)
    
    print(f"\n❌ Found {len(failures)} test failures")
    
    # Generate prompt
    fixer = RetroAutoAutoFix()
    prompt = fixer.generate_prompt(failures, args.max)
    
    # Output
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(prompt)
        print(f"\n✅ Prompt saved to: {args.output}")
        print(f"   Copy this file content to your AI assistant!")
    else:
        print("\n" + "=" * 60)
        print("📋 GENERATED PROMPT (copy to AI assistant):")
        print("=" * 60)
        print(prompt)
    
    if args.clipboard:
        try:
            import pyperclip
            pyperclip.copy(prompt)
            print("\n✅ Copied to clipboard!")
        except ImportError:
            print("\n⚠️ Install pyperclip for clipboard support: pip install pyperclip")
    
    print("\n" + "=" * 60)
    print("📝 NEXT STEPS:")
    print("1. Copy the prompt above")
    print("2. Paste to your AI assistant (Claude, ChatGPT, etc.)")
    print("3. Review and apply the suggested fixes")
    print("=" * 60)


if __name__ == "__main__":
    main()
