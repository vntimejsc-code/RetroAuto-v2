#!/usr/bin/env python3
"""
IQDS AST Scanner v2.0 - Intelligent Quality Defense System

An AST-based static analyzer that understands code context.

Improvements over v1.0:
- Lazy import allowlist (reduces false positives)
- Severity classification (P0/P1/P2)
- Union[A, B] syntax detection (backward compat)
- Configurable via CLI args
- JSON report output
"""

import ast
import sys
import os
import json
import argparse
from pathlib import Path
from typing import Set, List, Dict, Tuple
from enum import Enum
from dataclasses import dataclass, field, asdict
from datetime import datetime


class Severity(Enum):
    ERROR = "error"      # P0 - Must fix immediately
    WARNING = "warning"  # P1 - Should fix soon
    INFO = "info"        # P2 - Nice to have


# Lazy imports that are ALLOWED (heavy/optional dependencies)
LAZY_IMPORT_ALLOWLIST = {
    # Heavy optional dependencies
    "pynput", "mss", "cv2", "numpy", "PIL", "pyautogui",
    # Typing modules (always safe)
    "typing", "typing_extensions",
    # PySide6 widgets (often lazy for performance)
    "PySide6.QtWidgets", "PySide6.QtGui", "PySide6.QtCore",
    # Core modules for circular import avoidance
    "core.models", "core.recorder", "core.engine",
}


@dataclass
class Issue:
    file: str
    line: int
    severity: Severity
    category: str
    message: str
    
    def to_github_format(self) -> str:
        return f"::{self.severity.value} file={self.file},line={self.line}::[{self.category}] {self.message}"
    
    def to_dict(self) -> dict:
        return {
            "file": self.file,
            "line": self.line,
            "severity": self.severity.value,
            "category": self.category,
            "message": self.message,
        }


class BugHunter(ast.NodeVisitor):
    def __init__(self, filename: str, known_unions: Set[str] = None, strict: bool = False):
        self.filename = filename
        self.union_aliases: Set[str] = known_unions.copy() if known_unions else set()
        self.issues: List[Issue] = []
        self.strict = strict  # If True, report all lazy imports

    def visit_Assign(self, node: ast.Assign):
        """Detect Type Aliases: A = B | C or A = Union[B, C]"""
        # Modern syntax: A = B | C
        if isinstance(node.value, ast.BinOp) and isinstance(node.value.op, ast.BitOr):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    self.union_aliases.add(target.id)
        
        # Legacy syntax: A = Union[B, C]
        if isinstance(node.value, ast.Subscript):
            if isinstance(node.value.value, ast.Name) and node.value.value.id == "Union":
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        self.union_aliases.add(target.id)
        
        # Annotated syntax: Action = Annotated[Union[...], ...]
        if isinstance(node.value, ast.Subscript):
            if isinstance(node.value.value, ast.Name) and node.value.value.id == "Annotated":
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        self.union_aliases.add(target.id)
        
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        """Detect instantiation of Union Aliases."""
        func_name = ""
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
        
        if func_name and func_name in self.union_aliases:
            self.issues.append(Issue(
                file=self.filename,
                line=node.lineno,
                severity=Severity.ERROR,
                category="UNION_INSTANTIATION",
                message=f"'{func_name}' is a Type Union, not a class. Use specific classes like Click(), TypeText()."
            ))
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Detect lazy imports inside functions."""
        self._check_lazy_imports(node)
        self.generic_visit(node)
    
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        """Also check async functions."""
        self._check_lazy_imports(node)
        self.generic_visit(node)
    
    def _check_lazy_imports(self, node):
        """Check for lazy imports in function body."""
        for child in node.body:
            if isinstance(child, ast.ImportFrom):
                module = child.module or ""
                # Check if any part of module path is in allowlist
                if not self._is_allowed_import(module) and self.strict:
                    self.issues.append(Issue(
                        file=self.filename,
                        line=child.lineno,
                        severity=Severity.INFO,
                        category="LAZY_IMPORT",
                        message=f"Import inside function '{node.name}'. Consider moving to top-level."
                    ))
            elif isinstance(child, ast.Import):
                for alias in child.names:
                    if not self._is_allowed_import(alias.name) and self.strict:
                        self.issues.append(Issue(
                            file=self.filename,
                            line=child.lineno,
                            severity=Severity.INFO,
                            category="LAZY_IMPORT",
                            message=f"Import inside function '{node.name}'. Consider moving to top-level."
                        ))
    
    def _is_allowed_import(self, module_name: str) -> bool:
        """Check if import is in allowlist."""
        for allowed in LAZY_IMPORT_ALLOWLIST:
            if module_name.startswith(allowed) or allowed in module_name:
                return True
        return False


def scan_file(filepath: str, known_unions: Set[str] = None, strict: bool = False) -> Tuple[List[Issue], Set[str]]:
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            source = f.read()
        
        tree = ast.parse(source, filename=filepath)
        hunter = BugHunter(filepath, known_unions, strict)
        hunter.visit(tree)
        return hunter.issues, hunter.union_aliases
        
    except SyntaxError as e:
        return [Issue(filepath, e.lineno or 0, Severity.ERROR, "SYNTAX", str(e.msg))], set()
    except Exception as e:
        return [Issue(filepath, 0, Severity.ERROR, "SCANNER_CRASH", str(e))], set()


def find_python_files(targets: List[str]) -> List[str]:
    """Recursively find all Python files in targets."""
    files = []
    for target in targets:
        if os.path.isfile(target) and target.endswith(".py"):
            files.append(target)
        elif os.path.isdir(target):
            for root, _, filenames in os.walk(target):
                for f in filenames:
                    if f.endswith(".py"):
                        files.append(os.path.join(root, f))
    return files


def main():
    parser = argparse.ArgumentParser(description="IQDS AST Scanner v2.0")
    parser.add_argument("targets", nargs="*", default=["app", "core"], help="Files or directories to scan")
    parser.add_argument("--strict", action="store_true", help="Report all lazy imports (verbose)")
    parser.add_argument("--json", type=str, help="Output JSON report to file")
    parser.add_argument("--models", type=str, default="core/models.py", help="Path to models file for Union detection")
    args = parser.parse_args()
    
    print("IQDS AST Scanner v2.0")
    start_time = datetime.now()
    
    # Phase 1: Discover Union types from models file
    print(f".. Scanning knowledge base ({args.models})")
    known_unions: Set[str] = set()
    if os.path.exists(args.models):
        _, known_unions = scan_file(args.models)
    known_unions.add("Action")  # Ensure core union is always tracked
    print(f"   Found Union Types: {', '.join(sorted(known_unions))}")
    
    # Phase 2: Scan target files
    files = find_python_files(args.targets)
    print(f".. Scanning {len(files)} files in {args.targets}")
    
    all_issues: List[Issue] = []
    for filepath in files:
        issues, _ = scan_file(filepath, known_unions, args.strict)
        all_issues.extend(issues)
    
    # Phase 3: Report
    errors = [i for i in all_issues if i.severity == Severity.ERROR]
    warnings = [i for i in all_issues if i.severity == Severity.WARNING]
    infos = [i for i in all_issues if i.severity == Severity.INFO]
    
    # Print issues
    for issue in all_issues:
        print(issue.to_github_format())
    
    # Timing
    duration = (datetime.now() - start_time).total_seconds()
    
    # Summary
    print(f"\n{'='*50}")
    print(f"Duration: {duration:.2f}s | Files: {len(files)}")
    print(f"Errors: {len(errors)} | Warnings: {len(warnings)} | Info: {len(infos)}")
    
    # JSON report
    if args.json:
        report = {
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": duration,
            "files_scanned": len(files),
            "summary": {
                "errors": len(errors),
                "warnings": len(warnings),
                "info": len(infos),
            },
            "issues": [i.to_dict() for i in all_issues],
        }
        with open(args.json, "w") as f:
            json.dump(report, f, indent=2)
        print(f"Report saved to: {args.json}")
    
    if errors:
        print(f"\n[X] {len(errors)} critical issues found!")
        sys.exit(1)
    else:
        print("\n[OK] No critical issues detected.")
        sys.exit(0)


if __name__ == "__main__":
    main()
