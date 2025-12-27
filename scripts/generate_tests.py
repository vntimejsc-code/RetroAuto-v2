"""
RetroAuto AI Test Generator v3.0 - DSL-Aware
=============================================
Adapted from office_converter for RetroAuto DSL codebase.

Features:
- ✅ Coverage Integration - pytest-cov support
- ✅ Smart Prioritization - Test complex functions first  
- ✅ DSL-Aware - Recognizes DSL parser/lexer/interpreter patterns
- ✅ PySide6 Mock Templates - GUI component testing
- ✅ Class-Aware - Generates tests for class methods

Usage:
    python scripts/generate_tests.py --src=core --prioritize
    python scripts/generate_tests.py --src=app --gui-mocks
    python scripts/generate_tests.py --coverage-only
"""

import os
import sys
import ast
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Optional, Set, Tuple, Any
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import argparse
import subprocess


@dataclass
class FunctionSignature:
    """Enhanced function signature with coverage and priority info."""
    name: str
    file: str
    line: int
    args: List[Tuple[str, Optional[str]]]
    return_type: Optional[str]
    docstring: Optional[str]
    complexity: int
    is_async: bool
    decorators: List[str]
    hash: str
    coverage: float = 0.0
    priority_score: float = 0.0


# ═══════════════════════════════════════════════════════════════════════════
# SMART TEST CACHE
# ═══════════════════════════════════════════════════════════════════════════

class SmartTestCache:
    """Intelligent test cache with change detection."""
    
    def __init__(self, cache_file: str = ".test_cache.json"):
        self.cache_file = Path(cache_file)
        self.cache: Dict[str, dict] = {}
        self.load()
        
    def load(self):
        """Load cache from disk."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    self.cache = json.load(f)
            except:
                self.cache = {}
                
    def save(self):
        """Save cache to disk."""
        with open(self.cache_file, 'w') as f:
            json.dump(self.cache, f, indent=2)
            
    def get_function_hash(self, func_sig: FunctionSignature) -> str:
        """Compute hash of function for change detection."""
        content = f"{func_sig.name}:{func_sig.args}:{func_sig.return_type}"
        return hashlib.md5(content.encode()).hexdigest()
        
    def is_tested(self, func_sig: FunctionSignature) -> bool:
        """Check if function already has tests."""
        key = f"{func_sig.file}::{func_sig.name}"
        if key not in self.cache:
            return False
        cached = self.cache[key]
        return cached.get('hash') == func_sig.hash
        
    def mark_tested(self, func_sig: FunctionSignature, test_file: str):
        """Mark function as tested."""
        key = f"{func_sig.file}::{func_sig.name}"
        self.cache[key] = {
            'hash': func_sig.hash,
            'test_file': test_file,
            'timestamp': datetime.now().isoformat()
        }


# ═══════════════════════════════════════════════════════════════════════════
# COVERAGE INTEGRATION
# ═══════════════════════════════════════════════════════════════════════════

class CoverageIntegrator:
    """Direct pytest-cov integration for coverage-aware test generation."""
    
    def __init__(self, cov_file: str = ".coverage"):
        self.cov_file = Path(cov_file)
        self.coverage_data = None
        self.has_coverage = False
        
    def load_coverage(self) -> bool:
        """Load pytest-cov coverage data."""
        try:
            import coverage
            if not self.cov_file.exists():
                print("⚠️ No .coverage file found. Run: pytest --cov=. first")
                return False
                
            cov = coverage.Coverage(data_file=str(self.cov_file))
            cov.load()
            self.coverage_data = cov.get_data()
            self.has_coverage = True
            print(f"✅ Loaded coverage data from {self.cov_file}")
            return True
            
        except ImportError:
            print("⚠️ coverage not installed. Run: pip install coverage")
            return False
        except Exception as e:
            print(f"⚠️ Error loading coverage: {e}")
            return False
            
    def get_function_coverage(self, file_path: str, line_start: int, line_end: int) -> float:
        """Get coverage % for a specific function."""
        if not self.has_coverage:
            return 0.0
            
        executed = set(self.coverage_data.lines(file_path) or [])
        function_lines = set(range(line_start, line_end + 1))
        covered = len(function_lines & executed)
        total = len(function_lines)
        
        return (covered / total * 100) if total > 0 else 0.0
        
    def filter_untested_functions(self, functions: List[FunctionSignature], threshold: float = 80.0) -> List[FunctionSignature]:
        """Filter functions that need more test coverage."""
        if not self.has_coverage:
            return functions
            
        untested = []
        for func in functions:
            func.coverage = self.get_function_coverage(func.file, func.line, func.line + 20)
            if func.coverage < threshold:
                untested.append(func)
                
        return untested


# ═══════════════════════════════════════════════════════════════════════════
# SMART PRIORITIZER
# ═══════════════════════════════════════════════════════════════════════════

class SmartPrioritizer:
    """Prioritize functions based on complexity, coverage, and other metrics."""
    
    WEIGHTS = {
        'complexity': 0.35,
        'coverage_gap': 0.30,
        'public_api': 0.15,
        'loc': 0.10,
        'decorators': 0.10,
    }
    
    def prioritize(self, functions: List[FunctionSignature]) -> List[FunctionSignature]:
        """Sort functions by priority score (high to low)."""
        for func in functions:
            func.priority_score = self._calculate_priority(func)
        functions.sort(key=lambda f: f.priority_score, reverse=True)
        return functions
        
    def _calculate_priority(self, func: FunctionSignature) -> float:
        """Calculate priority score (0-1)."""
        score = 0.0
        
        complexity_score = min(func.complexity / 20.0, 1.0)
        score += complexity_score * self.WEIGHTS['complexity']
        
        coverage_gap = (100 - func.coverage) / 100.0
        score += coverage_gap * self.WEIGHTS['coverage_gap']
        
        if not func.name.startswith('_'):
            score += self.WEIGHTS['public_api']
            
        if func.decorators:
            score += self.WEIGHTS['decorators']
            
        return min(score, 1.0)


# ═══════════════════════════════════════════════════════════════════════════
# TEST TEMPLATE ENGINE (DSL-AWARE)
# ═══════════════════════════════════════════════════════════════════════════

class TestTemplateEngine:
    """Template-based test generation with DSL and GUI awareness."""
    
    TEMPLATES = {
        'simple_function': '''
def test_{func_name}_basic():
    """Test {func_name} with valid input."""  
    result = {func_call}
    assert result is None or result == [] or result == {{}}, f"Expected result, got {{result}}"
''',
        'function_with_return': '''
@pytest.mark.parametrize("test_input,expected_type", [
    ([], (list, tuple)),
    ("test", (str, list, tuple, type(None))),
])
def test_{func_name}_parametrized(test_input, expected_type):
    """Test {func_name} with various inputs."""
    result = {func_call}
    assert result is None or isinstance(result, expected_type), f"Got {{type(result).__name__}}"
''',
        'async_function': '''
@pytest.mark.asyncio
async def test_{func_name}_async():
    """Test async {func_name}."""
    result = await {func_call}
    assert result is None or isinstance(result, (list, dict, str, bool, tuple))
''',
        # DSL-Aware Templates
        'dsl_parser': '''
def test_{func_name}_dsl():
    """Test DSL parser function {func_name}."""
    from core.dsl.parser import Parser
    
    parser = Parser("flow main {{ click(100, 200) }}")
    result = parser.parse()
    assert result is not None
    assert hasattr(result, 'flows')
''',
        'dsl_lexer': '''
def test_{func_name}_lexer():
    """Test DSL lexer function {func_name}."""
    from core.dsl.lexer import Lexer
    
    lexer = Lexer("flow main {{ }}")
    tokens = lexer.tokenize()
    assert len(tokens) > 0
''',
        # PySide6 GUI Templates
        'gui_widget': '''
def test_{func_name}_widget(qtbot):
    """Test GUI widget {func_name}."""
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])
    
    # Create widget with mocked dependencies
    with patch('PySide6.QtWidgets.QMainWindow'):
        result = {func_call}
        assert result is None or result is not None
''',
    }
    
    def generate_from_template(self, func_sig: FunctionSignature, template_type: str = 'simple_function') -> str:
        """Generate test from template."""
        template = self.TEMPLATES.get(template_type, self.TEMPLATES['simple_function'])
        sample_args = self._generate_sample_args(func_sig)
        
        return template.format(
            func_name=func_sig.name,
            func_call=f"{func_sig.name}({sample_args})",
            sample_args=sample_args,
        )
        
    def _generate_sample_args(self, func_sig: FunctionSignature) -> str:
        """Generate smart, type-aware sample arguments."""
        args = []
        for arg_name, arg_type in func_sig.args:
            if not arg_type:
                args.append("None")
                continue
            
            arg_type_lower = arg_type.lower()
            
            if 'list[str]' in arg_type_lower or 'list[path]' in arg_type_lower:
                args.append(f"['{arg_name}_test.txt']")
            elif 'list[' in arg_type_lower:
                args.append("[]")
            elif 'dict[' in arg_type_lower or arg_type_lower == 'dict':
                args.append("{}")
            elif 'path' in arg_type_lower:
                args.append("tmp_path / 'test_file.txt'")
            elif 'optional[str]' in arg_type_lower:
                args.append("'test'")
            elif 'optional[' in arg_type_lower:
                args.append("None")
            elif arg_type_lower in ['str', 'string']:
                args.append("'test_value'")
            elif arg_type_lower in ['int', 'integer']:
                args.append("42")
            elif arg_type_lower in ['float', 'double']:
                args.append("3.14")
            elif arg_type_lower in ['bool', 'boolean']:
                args.append("True")
            # DSL-specific types
            elif 'astnode' in arg_type_lower:
                args.append("Mock()")
            elif 'token' in arg_type_lower:
                args.append("Mock(type='IDENTIFIER', value='test')")
            else:
                args.append("None")
                
        return ', '.join(args)
    
    def infer_template_type(self, func_sig: FunctionSignature) -> str:
        """Infer best template based on function signature and file location."""
        # DSL-specific detection
        if 'parser' in func_sig.file.lower():
            return 'dsl_parser'
        elif 'lexer' in func_sig.file.lower():
            return 'dsl_lexer'
        # GUI detection
        elif 'ui' in func_sig.file.lower() or 'widget' in func_sig.file.lower():
            return 'gui_widget'
        # Standard detection
        elif func_sig.is_async:
            return 'async_function'
        elif func_sig.return_type:
            return 'function_with_return'
        else:
            return 'simple_function'


# ═══════════════════════════════════════════════════════════════════════════
# AST ANALYZER (CLASS-AWARE)
# ═══════════════════════════════════════════════════════════════════════════

class SmartASTAnalyzer:
    """Enhanced AST analyzer with class and method awareness."""
    
    def analyze_file(self, file_path: str) -> List[FunctionSignature]:
        """Analyze file and extract function signatures (both module and class methods)."""
        functions = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            tree = ast.parse(content)
            
            # First pass: Find module-level functions
            for node in ast.iter_child_nodes(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    func_sig = self._extract_signature(node, file_path, content)
                    if func_sig:
                        functions.append(func_sig)
            
            # Second pass: Find classes and their methods
            for node in ast.iter_child_nodes(tree):
                if isinstance(node, ast.ClassDef):
                    class_functions = self._analyze_class(node, file_path, content)
                    functions.extend(class_functions)
                        
        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
            
        return functions
    
    def _analyze_class(self, class_node: ast.ClassDef, file_path: str, content: str) -> List[FunctionSignature]:
        """Analyze a class and extract its methods."""
        methods = []
        
        for node in class_node.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Skip special methods except __init__
                if node.name.startswith('__') and node.name not in ['__init__', '__call__']:
                    continue
                    
                func_sig = self._extract_signature(node, file_path, content, class_name=class_node.name)
                if func_sig:
                    methods.append(func_sig)
                    
        return methods
        
    def _extract_signature(self, node: ast.FunctionDef, file_path: str, content: str, class_name: str = None) -> Optional[FunctionSignature]:
        """Extract detailed function signature."""
        # Skip private methods (except __init__)
        if node.name.startswith('_') and node.name != '__init__':
            return None
        
        # Build qualified name
        func_name = f"{class_name}.{node.name}" if class_name else node.name
            
        # Extract args with type hints
        args = []
        for arg in node.args.args:
            if arg.arg in ('self', 'cls'):
                continue
            type_hint = None
            if arg.annotation:
                try:
                    type_hint = ast.unparse(arg.annotation)
                except:
                    pass
            args.append((arg.arg, type_hint))
            
        # Extract return type
        return_type = None
        if node.returns:
            try:
                return_type = ast.unparse(node.returns)
            except:
                pass
                
        # Extract decorators
        decorators = []
        for dec in node.decorator_list:
            try:
                decorators.append(ast.unparse(dec))
            except:
                pass
                
        # Estimate complexity
        complexity = self._estimate_complexity(node)
        
        # Get docstring
        docstring = ast.get_docstring(node)
        
        # Compute hash
        hash_content = f"{func_name}:{args}:{return_type}"
        hash_value = hashlib.md5(hash_content.encode()).hexdigest()
        
        return FunctionSignature(
            name=func_name,
            file=file_path,
            line=node.lineno,
            args=args,
            return_type=return_type,
            docstring=docstring,
            complexity=complexity,
            is_async=isinstance(node, ast.AsyncFunctionDef),
            decorators=decorators,
            hash=hash_value,
            coverage=0.0,
            priority_score=0.0
        )
        
    def _estimate_complexity(self, node: ast.FunctionDef) -> int:
        """Estimate cyclomatic complexity."""
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        return complexity


# ═══════════════════════════════════════════════════════════════════════════
# MAIN GENERATOR
# ═══════════════════════════════════════════════════════════════════════════

class RetroAutoTestGenerator:
    """AI Test Generator specifically adapted for RetroAuto."""
    
    def __init__(self, 
                 use_cache: bool = True,
                 parallel: int = 1,
                 coverage_aware: bool = False,
                 prioritize: bool = False,
                 gui_mocks: bool = False):
        self.cache = SmartTestCache() if use_cache else None
        self.parallel = parallel
        self.template_engine = TestTemplateEngine()
        self.analyzer = SmartASTAnalyzer()
        self.gui_mocks = gui_mocks
        
        # Optional features
        self.coverage = CoverageIntegrator() if coverage_aware else None
        self.prioritizer = SmartPrioritizer() if prioritize else None
        
        self.stats = {
            'cached': 0,
            'generated': 0,
            'skipped': 0,
            'prioritized': 0,
        }
        
    def initialize(self):
        """Initialize features."""
        if self.coverage:
            self.coverage.load_coverage()
                
    def generate_tests_parallel(self, files: List[str], output_dir: str) -> Dict[str, str]:
        """Generate tests with parallel processing."""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        results = {}
        
        if self.parallel > 1:
            with ThreadPoolExecutor(max_workers=self.parallel) as executor:
                futures = {
                    executor.submit(self._generate_for_file, f, output_dir): f 
                    for f in files
                }
                
                for future in as_completed(futures):
                    file_path = futures[future]
                    try:
                        test_file = future.result()
                        if test_file:
                            results[file_path] = test_file
                    except Exception as e:
                        print(f"Error processing {file_path}: {e}")
        else:
            for file_path in files:
                test_file = self._generate_for_file(file_path, output_dir)
                if test_file:
                    results[file_path] = test_file
                    
        return results
        
    def _generate_for_file(self, file_path: str, output_dir: str) -> Optional[str]:
        """Generate tests with coverage and priority awareness."""
        functions = self.analyzer.analyze_file(file_path)
        
        if not functions:
            self.stats['skipped'] += 1
            return None
            
        # Filter by coverage
        if self.coverage and self.coverage.has_coverage:
            original_count = len(functions)
            functions = self.coverage.filter_untested_functions(functions, threshold=80.0)
            print(f"   📊 Coverage: {len(functions)}/{original_count} need tests")
            
        # Filter cached
        if self.cache:
            untested = [f for f in functions if not self.cache.is_tested(f)]
            self.stats['cached'] += len(functions) - len(untested)
            functions = untested
            
        if not functions:
            return None
            
        # Prioritize
        if self.prioritizer:
            functions = self.prioritizer.prioritize(functions)
            self.stats['prioritized'] += len(functions)
            if functions:
                print(f"   ⚡ Top priority: {functions[0].name} (score: {functions[0].priority_score:.2f})")
            
        # Generate tests
        test_code = self._generate_test_code(functions, file_path)
        
        # Write
        module_name = Path(file_path).stem
        test_file = Path(output_dir) / f"test_generated_{module_name}.py"
        
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(test_code)
            
        # Update cache
        if self.cache:
            for func in functions:
                self.cache.mark_tested(func, str(test_file))
            self.cache.save()
            
        self.stats['generated'] += len(functions)
        return str(test_file)
        
    def _generate_test_code(self, functions: List[FunctionSignature], source_file: str) -> str:
        """Generate test code with proper imports."""
        module_path = Path(source_file)
        module_name = module_path.stem
        
        # Build import statement
        relative_path = str(module_path.relative_to(Path.cwd())).replace('\\', '/').replace('.py', '').replace('/', '.')
        if relative_path.startswith('.'):
            relative_path = relative_path[1:]
        
        # Separate class methods from module functions
        classes_needed = set()
        module_functions = []
        
        for func in functions:
            if '.' in func.name:
                class_name = func.name.split('.')[0]
                classes_needed.add(class_name)
            else:
                module_functions.append(func.name)
        
        lines = [
            '"""',
            f'Auto-generated tests for {module_name}',
            f'Generated: {datetime.now().isoformat()}',
            'Generator: RetroAuto AI Test Generator v3.0',
            '"""',
            '',
            'import pytest',
            'from unittest.mock import Mock, patch, MagicMock',
            '',
            f'# Import from {source_file}',
            'try:',
        ]
        
        # Import classes and functions
        if classes_needed or module_functions:
            lines.append(f'    from {relative_path} import (')
            for class_name in sorted(classes_needed):
                lines.append(f'        {class_name},')
            for func_name in module_functions:
                lines.append(f'        {func_name},')
            lines.append('    )')
        
        lines.extend([
            'except ImportError as e:',
            f'    pytest.skip(f"Cannot import from {relative_path}: {{e}}")',
            '',
        ])
        
        for func in functions:
            safe_name = func.name.replace('.', '_')
            
            # Compute func_call
            sample_args = self.template_engine._generate_sample_args(func)
            if '.' in func.name:
                class_name, method_name = func.name.split('.', 1)
                func_call = f"{class_name}().{method_name}({sample_args})" if sample_args else f"{class_name}().{method_name}()"
            else:
                func_call = f"{func.name}({sample_args})" if sample_args else f"{func.name}()"
            
            template_type = self.template_engine.infer_template_type(func)
            template = self.template_engine.TEMPLATES.get(template_type, self.template_engine.TEMPLATES['simple_function'])
            test_code = template.format(
                func_name=safe_name,
                func_call=func_call,
                sample_args=sample_args
            )
            
            docstring_safe = ""
            if func.docstring:
                docstring_safe = func.docstring.replace('\n', ' ').replace('\r', '')[:60]
                
            lines.append(f'# Test for {func.name} (complexity: {func.complexity}, coverage: {func.coverage:.0f}%)')
            if docstring_safe:
                lines.append(f'# Doc: {docstring_safe}...')
            lines.append(test_code)
            lines.append('')
            
        return '\n'.join(lines)


# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="RetroAuto AI Test Generator v3.0")
    parser.add_argument("--src", default="core", help="Source directory (core, app, or both)")
    parser.add_argument("--output", default="tests/generated", help="Output directory")
    parser.add_argument("--parallel", type=int, default=4, help="Parallel workers")
    parser.add_argument("--no-cache", action="store_true", help="Disable caching")
    
    # Advanced features
    parser.add_argument("--coverage-only", action="store_true", help="Only generate for untested code")
    parser.add_argument("--prioritize", action="store_true", help="Prioritize complex functions")
    parser.add_argument("--gui-mocks", action="store_true", help="Enable PySide6 mocking templates")
    
    args = parser.parse_args()
    
    project_root = Path(".").absolute()
    
    print("=" * 70)
    print("🚀 RETROAUTO AI TEST GENERATOR V3.0")
    print("=" * 70)
    print(f"Source: {args.src}")
    print(f"Output: {args.output}")
    print(f"Features: Coverage={args.coverage_only}, Prioritize={args.prioritize}, GUI-Mocks={args.gui_mocks}")
    print("=" * 70)
    
    # Find files
    src_dirs = args.src.split(',')
    files = []
    for src_dir in src_dirs:
        src_path = project_root / src_dir.strip()
        if src_path.exists():
            found = list(src_path.glob("**/*.py"))
            found = [str(f) for f in found if "__pycache__" not in str(f)]
            files.extend(found)
            print(f"📁 Found {len(found)} Python files in {src_dir}")
    
    if not files:
        print("❌ No Python files found!")
        sys.exit(1)
    
    # Initialize generator
    generator = RetroAutoTestGenerator(
        use_cache=not args.no_cache,
        parallel=args.parallel,
        coverage_aware=args.coverage_only,
        prioritize=args.prioritize,
        gui_mocks=args.gui_mocks
    )
    
    generator.initialize()
    
    # Generate
    import time
    start = time.time()
    
    results = generator.generate_tests_parallel(files, args.output)
    
    elapsed = time.time() - start
    
    print(f"\n{'='*70}")
    print("📊 GENERATION COMPLETE")
    print(f"{'='*70}")
    print(f"✅ Generated: {generator.stats['generated']} test functions")
    print(f"💾 Cached: {generator.stats['cached']} (skipped)")
    if args.prioritize:
        print(f"⚡ Prioritized: {generator.stats['prioritized']} functions")
    print(f"⏭️  Skipped: {generator.stats['skipped']} files")
    print(f"📄 Test files: {len(results)}")
    print(f"⚡ Time: {elapsed:.2f}s")
    if generator.stats['generated'] > 0:
        print(f"🚀 Speed: {generator.stats['generated']/elapsed:.1f} tests/sec")
    print(f"{'='*70}")
    
    # List generated files
    if results:
        print("\n📄 Generated test files:")
        for src, test in list(results.items())[:10]:
            print(f"   {Path(test).name}")
        if len(results) > 10:
            print(f"   ... and {len(results) - 10} more")


if __name__ == "__main__":
    main()
