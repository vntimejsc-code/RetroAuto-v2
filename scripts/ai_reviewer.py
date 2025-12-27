"""
RetroAuto AI Code Reviewer - Direct Mode
=========================================
Generates formatted prompts for AI assistant to review code changes.
No external API required - works with Claude, Copilot, or any AI assistant.

Adapted for RetroAuto DSL codebase with DSL-specific review rules.

Usage:
    python scripts/ai_reviewer.py                    # Review last commit
    python scripts/ai_reviewer.py --base=HEAD~5     # Review last 5 commits
    python scripts/ai_reviewer.py --output=review.md # Save to file
"""

import os
import sys
import subprocess
import argparse
import re
from typing import Optional, Dict, List
from dataclasses import dataclass
from pathlib import Path


@dataclass
class FileChange:
    """Represents a changed file."""
    path: str
    additions: int
    deletions: int
    diff: str


class RetroAutoReviewer:
    """Generates prompts for AI assistant to review RetroAuto code."""
    
    REVIEW_PROMPT = """# 🔬 RetroAuto Code Review Request

## Instructions for AI Assistant

Please review these code changes following the **5-Layer Deep Scan Protocol**:

1. **SECURITY** - Check for command injection, file path traversal, hardcoded secrets
2. **PERFORMANCE** - Check for O(n²) loops, memory leaks, blocking I/O in GUI
3. **RELIABILITY** - Check error handling, race conditions, type safety  
4. **DSL CORRECTNESS** - Check parser/lexer/AST consistency, token handling
5. **PYTHONIC** - Check modern Python practices, f-strings, pathlib, PEP8

## RetroAuto-Specific Checks

- **DSL Parser**: Verify TokenType handling, AST node creation
- **PySide6 GUI**: Check signal/slot connections, thread safety
- **Image Matching**: Verify OpenCV usage, ROI bounds checking
- **Script Engine**: Check interpreter state management

## Scoring Guide
- **90-100**: Excellent, merge immediately
- **75-89**: Good, minor suggestions
- **<75**: Issues found, needs fixes

---

"""
    
    RESPONSE_FORMAT = """
## 📝 Expected Response Format

```markdown
## 🔬 Code Review Report

### Score: [0-100]/100

### 📋 Summary
[1-2 sentence summary of changes]

### ⚠️ Issues Found

| # | Type | Severity | Line | Issue | Fix |
|---|------|----------|------|-------|-----|
| 1 | SECURITY/PERF/DSL/LOGIC | HIGH/MEDIUM/LOW | Line# | Description | Suggested fix |

### ✅ Good Practices Observed
- [List good things about the code]

### 💡 Suggestions
- [Optional improvements]

### Verdict: APPROVE / REQUEST_CHANGES / COMMENT
```

---

Please review the code changes below:
"""

    # RetroAuto-specific patterns to check
    DSL_PATTERNS = [
        (r'TokenType\.\w+', "Token handling", "DSL"),
        (r'ASTNode|UnaryExpr|BinaryExpr', "AST manipulation", "DSL"),
        (r'_parse_\w+', "Parser method", "DSL"),
        (r'QThread|QRunnable|moveToThread', "Threading", "GUI"),
        (r'cv2\.\w+|imread|imwrite', "OpenCV usage", "VISION"),
        (r'execute\(|run_flow|_eval', "Script execution", "ENGINE"),
    ]

    def get_git_diff(self, base: str = "HEAD~1", target: str = "HEAD") -> str:
        """Get git diff between two refs."""
        try:
            result = subprocess.run(
                ["git", "diff", base, target, "--", "*.py"],
                capture_output=True, text=True, encoding='utf-8'
            )
            return result.stdout
        except Exception as e:
            print(f"Error getting git diff: {e}")
            return ""
    
    def get_diff_stats(self, base: str = "HEAD~1", target: str = "HEAD") -> Dict:
        """Get statistics about the diff."""
        try:
            result = subprocess.run(
                ["git", "diff", "--stat", base, target, "--", "*.py"],
                capture_output=True, text=True, encoding='utf-8'
            )
            
            lines = result.stdout.strip().split('\n')
            files_changed = 0
            insertions = 0
            deletions = 0
            
            if lines:
                summary = lines[-1] if lines else ""
                
                files_match = re.search(r'(\d+) files? changed', summary)
                ins_match = re.search(r'(\d+) insertions?', summary)
                del_match = re.search(r'(\d+) deletions?', summary)
                
                files_changed = int(files_match.group(1)) if files_match else 0
                insertions = int(ins_match.group(1)) if ins_match else 0
                deletions = int(del_match.group(1)) if del_match else 0
            
            return {
                "files_changed": files_changed,
                "insertions": insertions,
                "deletions": deletions
            }
        except Exception:
            return {"files_changed": 0, "insertions": 0, "deletions": 0}
    
    def get_changed_files(self, base: str = "HEAD~1", target: str = "HEAD") -> List[str]:
        """Get list of changed Python files."""
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only", base, target, "--", "*.py"],
                capture_output=True, text=True, encoding='utf-8'
            )
            return [f.strip() for f in result.stdout.strip().split('\n') if f.strip()]
        except Exception:
            return []
    
    def get_commit_info(self, ref: str = "HEAD") -> Dict:
        """Get commit information."""
        try:
            result = subprocess.run(
                ["git", "log", "-1", "--format=%H|%s|%an|%ai", ref],
                capture_output=True, text=True, encoding='utf-8'
            )
            parts = result.stdout.strip().split('|')
            return {
                "hash": parts[0][:8] if parts else "",
                "message": parts[1] if len(parts) > 1 else "",
                "author": parts[2] if len(parts) > 2 else "",
                "date": parts[3] if len(parts) > 3 else ""
            }
        except Exception:
            return {"hash": "", "message": "", "author": "", "date": ""}
    
    def generate_prompt(self, base: str = "HEAD~1", target: str = "HEAD") -> str:
        """Generate review prompt for AI assistant."""
        
        diff = self.get_git_diff(base, target)
        stats = self.get_diff_stats(base, target)
        files = self.get_changed_files(base, target)
        commit = self.get_commit_info(target)
        
        # Build prompt
        prompt = self.REVIEW_PROMPT
        
        # Add context
        prompt += f"## 📊 Change Summary\n\n"
        prompt += f"**Commit**: `{commit['hash']}` - {commit['message']}\n"
        prompt += f"**Author**: {commit['author']}\n"
        prompt += f"**Date**: {commit['date']}\n\n"
        
        prompt += f"**Stats**:\n"
        prompt += f"- Files Changed: {stats['files_changed']}\n"
        prompt += f"- Insertions: +{stats['insertions']}\n"
        prompt += f"- Deletions: -{stats['deletions']}\n\n"
        
        if files:
            prompt += f"**Files**:\n"
            # Tag files by component
            for f in files[:20]:
                tag = self._categorize_file(f)
                prompt += f"- `{f}` [{tag}]\n"
            prompt += "\n"
        
        # Add response format
        prompt += self.RESPONSE_FORMAT
        
        # Add diff
        prompt += f"\n## 📝 Code Changes (Diff)\n\n"
        prompt += f"```diff\n{diff[:15000]}\n```\n"
        
        if len(diff) > 15000:
            prompt += f"\n*[Diff truncated - showing first 15000 characters]*\n"
        
        return prompt
    
    def _categorize_file(self, file_path: str) -> str:
        """Categorize file by component."""
        if 'dsl' in file_path.lower():
            return 'DSL'
        elif 'ui' in file_path.lower() or 'app' in file_path.lower():
            return 'GUI'
        elif 'engine' in file_path.lower():
            return 'ENGINE'
        elif 'vision' in file_path.lower() or 'game' in file_path.lower():
            return 'VISION'
        elif 'test' in file_path.lower():
            return 'TEST'
        else:
            return 'CORE'
    
    def quick_analysis(self, diff: str) -> Dict:
        """Quick static analysis of the diff."""
        issues = []
        
        # Common issues + RetroAuto-specific
        patterns = [
            (r'except\s*:', "Generic except clause", "RELIABILITY"),
            (r'except\s+Exception\s*:', "Catching all exceptions", "RELIABILITY"),
            (r'TODO|FIXME|HACK|XXX', "TODO/FIXME comment", "MAINTAINABILITY"),
            (r'password\s*=\s*["\'][^"\']+["\']', "Possible hardcoded password", "SECURITY"),
            (r'api_key\s*=\s*["\'][^"\']+["\']', "Possible hardcoded API key", "SECURITY"),
            (r'print\(', "Print statement (use logging)", "MAINTAINABILITY"),
            (r'time\.sleep\(', "Blocking sleep", "PERFORMANCE"),
            (r'\.format\(', "Old-style format (use f-string)", "PYTHONIC"),
            # RetroAuto-specific
            (r'QThread\.sleep', "Blocking GUI thread", "GUI"),
            (r'while\s+True.*QApplication', "Infinite loop in GUI", "GUI"),
            (r'TokenType\.\w+\s*==\s*["\']', "Wrong TokenType comparison", "DSL"),
            (r'cv2\.imread\([^)]+\)\s*$', "Missing imread check", "VISION"),
        ]
        
        for pattern, msg, category in patterns:
            matches = re.findall(pattern, diff, re.IGNORECASE)
            if matches:
                issues.append({
                    "pattern": pattern,
                    "message": msg,
                    "category": category,
                    "count": len(matches)
                })
        
        return {
            "issues": issues,
            "lines_added": diff.count('\n+'),
            "lines_removed": diff.count('\n-')
        }


def main():
    parser = argparse.ArgumentParser(description="RetroAuto AI Code Reviewer - Direct Mode")
    parser.add_argument("--base", default="HEAD~1", help="Base ref for diff")
    parser.add_argument("--target", default="HEAD", help="Target ref for diff")
    parser.add_argument("--output", help="Output file for prompt")
    parser.add_argument("--clipboard", action="store_true", help="Copy to clipboard")
    parser.add_argument("--quick", action="store_true", help="Quick static analysis only")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🔬 RETROAUTO AI CODE REVIEWER - DIRECT MODE")
    print("=" * 60)
    print("No API key required - generates prompt for AI assistant")
    print("=" * 60)
    
    reviewer = RetroAutoReviewer()
    
    # Check if in git repo
    diff = reviewer.get_git_diff(args.base, args.target)
    if not diff:
        print("❌ No Python changes found or not in a git repository")
        sys.exit(1)
    
    stats = reviewer.get_diff_stats(args.base, args.target)
    print(f"\n📊 Changes: {stats['files_changed']} files, "
          f"+{stats['insertions']}/-{stats['deletions']} lines")
    
    # Quick analysis
    if args.quick:
        print("\n🔍 Quick Static Analysis:")
        analysis = reviewer.quick_analysis(diff)
        if analysis['issues']:
            for issue in analysis['issues']:
                print(f"   ⚠️ [{issue['category']}] {issue['message']} ({issue['count']}x)")
        else:
            print("   ✅ No obvious issues found")
        sys.exit(0)
    
    # Generate full prompt
    prompt = reviewer.generate_prompt(args.base, args.target)
    
    # Output
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(prompt)
        print(f"\n✅ Prompt saved to: {args.output}")
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
            print("\n⚠️ Install pyperclip for clipboard support")
    
    print("\n" + "=" * 60)
    print("📝 NEXT STEPS:")
    print("1. Copy the prompt above")
    print("2. Paste to your AI assistant (Claude, ChatGPT, etc.)")
    print("3. Review the feedback and apply suggestions")
    print("=" * 60)


if __name__ == "__main__":
    main()
