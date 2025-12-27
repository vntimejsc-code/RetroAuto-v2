# 🔬 RetroAuto Code Review Request

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

## 📊 Change Summary

**Commit**: `fdd79c6e` - Feat: Add AI Reviewer + AI AutoFix tools from office_converter
**Author**: RetroAuto Dev
**Date**: 2025-12-27 10:39:53 +0700

**Stats**:
- Files Changed: 21
- Insertions: +3594
- Deletions: -186

**Files**:
- `core/dsl/ast.py` [DSL]
- `core/dsl/formatter.py` [DSL]
- `core/dsl/parser.py` [DSL]
- `merge_project.py` [CORE]
- `scripts/ai_autofix.py` [CORE]
- `scripts/ai_reviewer.py` [CORE]
- `scripts/generate_tests.py` [TEST]
- `tests/generated/test_generated_adapter.py` [TEST]
- `tests/generated/test_generated_ast.py` [TEST]
- `tests/generated/test_generated_autocomplete.py` [TEST]
- `tests/generated/test_generated_debugger.py` [TEST]
- `tests/generated/test_generated_diagnostics.py` [TEST]
- `tests/generated/test_generated_document.py` [TEST]
- `tests/generated/test_generated_formatter.py` [TEST]
- `tests/generated/test_generated_ir.py` [TEST]
- `tests/generated/test_generated_lexer.py` [TEST]
- `tests/generated/test_generated_module_loader.py` [TEST]
- `tests/generated/test_generated_parser.py` [TEST]
- `tests/generated/test_generated_semantic.py` [TEST]
- `tests/generated/test_generated_sync_manager.py` [TEST]


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

## 📝 Code Changes (Diff)

```diff
diff --git a/core/dsl/ast.py b/core/dsl/ast.py
index 3b56eee..53214a0 100644
--- a/core/dsl/ast.py
+++ b/core/dsl/ast.py
@@ -96,15 +96,15 @@ class BinaryExpr(ASTNode):
     """Binary operation: a + b, a == b, etc."""
 
     left: ASTNode
-    operator: str  # "+", "-", "==", "!=", "&&", "||", etc.
+    operator: str  # "+", "-", "==", "!=", "and", "or", etc.
     right: ASTNode
 
 
 @dataclass(kw_only=True)
 class UnaryExpr(ASTNode):
-    """Unary operation: !a, -b."""
+    """Unary operation: !a, not a, -b."""
 
-    operator: str  # "!", "-"
+    operator: str  # "!", "not", "-"
     operand: ASTNode
 
 
diff --git a/core/dsl/formatter.py b/core/dsl/formatter.py
index 2cfd76e..ac4f22f 100644
--- a/core/dsl/formatter.py
+++ b/core/dsl/formatter.py
@@ -380,7 +380,11 @@ class Formatter:
 
     def _format_unary(self, expr: UnaryExpr) -> None:
         """Format unary expression."""
-        self._write(expr.operator)
+        # 'not' keyword needs trailing space, '!' and '-' do not
+        if expr.operator == "not":
+            self._write("not ")
+        else:
+            self._write(expr.operator)
         self._format_expr(expr.operand)
 
     def _format_call(self, expr: CallExpr) -> None:
diff --git a/core/dsl/parser.py b/core/dsl/parser.py
index 3b97d23..bf578c6 100644
--- a/core/dsl/parser.py
+++ b/core/dsl/parser.py
@@ -1045,7 +1045,8 @@ class Parser:
         return left
 
     def _parse_unary(self) -> ASTNode:
-        """Parse ! - unary expression."""
+        """Parse ! / not / - unary expression."""
+        # Handle '!' (symbol form)
         if self._match(TokenType.NOT):
             start = self.tokens[self.pos - 1]
             operand = self._parse_unary()
@@ -1055,6 +1056,16 @@ class Parser:
                 operand=operand,
             )
 
+        # Handle 'not' (keyword form)
+        if self._match(TokenType.NOT_KW):
+            start = self.tokens[self.pos - 1]
+            operand = self._parse_unary()
+            return UnaryExpr(
+                span=self._span_from(start),
+                operator="not",
+                operand=operand,
+            )
+
         if self._match(TokenType.MINUS):
             start = self.tokens[self.pos - 1]
             operand = self._parse_unary()
diff --git a/merge_project.py b/merge_project.py
index 957e286..1c751c3 100644
--- a/merge_project.py
+++ b/merge_project.py
@@ -1,238 +1,292 @@
 """
-RetroAuto v2 - Project Context Merger
+RetroAuto v2 - Project Context Merger (Advanced Version)
 
 Gộp toàn bộ source code của dự án vào một file văn bản duy nhất.
-Hữu ích để chia sẻ context với AI hoặc review code.
+Tối ưu hóa cho việc chia sẻ context với LLM (ChatGPT, Claude, Gemini).
+
+Features:
+- Directory Tree View: Hiển thị cấu trúc thư mục
+- Smart Ignore: Hỗ trợ .gitignore và danh sách mặc định
+- Token Estimator: Ước lượng số token
+- Clipboard: Tự động copy (nếu có pyperclip)
 
 Usage:
     python merge_project.py
-    python merge_project.py --output custom_output.txt
-    python merge_project.py --extensions .py .js .ts
+    python merge_project.py --tree-only
+    python merge_project.py --clipboard
 """
 
 import argparse
 import os
+import sys
+import fnmatch
 from pathlib import Path
 from datetime import datetime
 
-# Các thư mục cần bỏ qua
-IGNORE_DIRS = {
-    '.git',
-    '__pycache__',
-    'venv',
-    '.venv',
-    'env',
-    'node_modules',
-    '.idea',
-    '.vscode',
-    '.mypy_cache',
-    '.pytest_cache',
-    '.ruff_cache',
-    '.coverage',
-    'dist',
-    'build',
-    'eggs',
-    '*.egg-info',
-    '.tox',
-    '.nox',
-    'htmlcov',
+# Cố gắng import pyperclip
+try:
+    import pyperclip
+    HAS_CLIPBOARD = True
+except ImportError:
+    HAS_CLIPBOARD = False
+
+# Các thư mục cần bỏ qua mặc định (kể cả khi không có .gitignore)
+DEFAULT_IGNORE_DIRS = {
+    '.git', '__pycache__', 'venv', '.venv', 'env', 'node_modules',
+    '.idea', '.vscode', '.mypy_cache', '.pytest_cache', '.ruff_cache',
+    '.coverage', 'dist', 'build', 'eggs', '*.egg-info', '.tox', '.nox', 'htmlcov',
+    'site-packages'
 }
 
-# Các đuôi file mặc định
-DEFAULT_EXTENSIONS = {'.py'}
-
-# Các file cần bỏ qua
-IGNORE_FILES = {
-    'project_context.txt',  # File output
-    '.gitignore',
-    '.pre-commit-config.yaml',
-    'mypy.ini',
-    'pyproject.toml',
-    'setup.py',
-    'setup.cfg',
+# Các file cần bỏ qua mặc định
+DEFAULT_IGNORE_FILES = {
+    'project_context.txt', '.gitignore', '.pre-commit-config.yaml',
+    'mypy.ini', 'pyproject.toml', 'setup.py', 'setup.cfg', '*.pyc', '*.pyd',
+    '*.db', '*.sqlite', '*.png', '*.jpg', '*.jpeg', '*.gif', '*.ico', '*.svg',
+    '*.exe', '*.dll', '*.so', '*.dylib', '*.bin', '*.pkl', '*.log'
 }
 
+class ProjectMerger:
+    def __init__(self, root_dir: Path, extensions: set[str], use_gitignore: bool = True):
+        self.root_dir = root_dir
+        self.extensions = extensions
+        self.ignore_patterns = set()
+        
+        # Load ignore patterns
+        self.load_default_ignores()
+        if use_gitignore:
+            self.load_gitignore()
+
+    def load_default_ignores(self):
+        self.ignore_patterns.update(DEFAULT_IGNORE_DIRS)
+        self.ignore_patterns.update(DEFAULT_IGNORE_FILES)
 
-def should_ignore_dir(dir_name: str) -> bool:
-    """Kiểm tra xem thư mục có nên bỏ qua không."""
-    return dir_name in IGNORE_DIRS or dir_name.startswith('.')
+    def load_gitignore(self):
+        """Đọc file .gitignore nếu tồn tại."""
+        gitignore_path = self.root_dir / '.gitignore'
+        if gitignore_path.exists():
+            try:
+                with open(gitignore_path, 'r', encoding='utf-8') as f:
+                    for line in f:
+                        line = line.strip()
+                        if line and not line.startswith('#'):
+                            self.ignore_patterns.add(line)
+                            # Support directory specific patterns
+                            if line.endswith('/'):
+                                self.ignore_patterns.add(line[:-1])
+            except Exception as e:
+                print(f"[!] Warning: Could not read .gitignore: {e}")
+
+    def should_ignore(self, path: Path) -> bool:
+        """Kiểm tra xem path có matches với bất kỳ pattern nào không."""
+        name = path.name
+        rel_path = str(path.relative_to(self.root_dir))
+        
+        # Check hidden files/dirs
+        if name.startswith('.'):
+            return True
+            
+        for pattern in self.ignore_patterns:
+            if fnmatch.fnmatch(name, pattern) or fnmatch.fnmatch(rel_path, pattern):
+                return True
+            if path.is_dir() and fnmatch.fnmatch(name + '/', pattern):
+                return True
+        return False
 
+    def generate_tree(self) -> list[str]:
+        """Tạo cấu trúc cây thư mục."""
+        tree_lines = ["Directory Structure:", "."]
+        
+        def _add_to_tree(directory: Path, prefix: str = ""):
+            try:
+                # Lọc và sắp xếp: thư mục trước, file sau
+                items = sorted(list(directory.iterdir()), key=lambda x: (not x.is_dir(), x.name.lower()))
+                items = [x for x in items if not self.should_ignore(x)]
+                
+                count = len(items)
+                for i, item in enumerate(items):
+                    is_last = (i == count - 1)
+                    connector = "└── " if is_last else "├── "
+                    
+                    tree_lines.append(f"{prefix}{connector}{item.name}")
+                    
+                    if item.is_dir():
+                        extension = "    " if is_last else "│   "
+                        _add_to_tree(item, prefix + extension)
+            except PermissionError:
+                pass
 
-def should_ignore_file(file_name: str) -> bool:
-    """Kiểm tra xem file có nên bỏ qua không."""
-    return file_name in IGNORE_FILES
+        _add_to_tree(self.root_dir)
+        return tree_lines
 
+    def estimate_tokens(self, text: str) -> int:
+        """Ước lượng số token (quy tắc: 1 token ~ 4 chars)."""
+        return len(text) // 4
 
-def merge_project(
-    root_dir: Path,
-    output_file: Path,
-    extensions: set[str],
-    include_line_numbers: bool = False,
-) -> dict:
-    """
-    Gộp tất cả source code vào một file.
-    
-    Args:
-        root_dir: Thư mục gốc của dự án
-        output_file: File output
-        extensions: Các đuôi file cần lấy
-        include_line_numbers: Thêm số dòng vào mỗi dòng code
+    def merge(self, output_file: Path, include_line_numbers: bool = False, tree_only: bool = False):
+        stats = {
+            'files_processed': 0,
+            'files_skipped': 0,
+            'total_lines': 0,
+            'total_tokens': 0,
+            'tree_str': ""
+        }
         
-    Returns:
-        Dict với thống kê
-    """
-    stats = {
-        'files_processed': 0,
-        'files_skipped': 0,
-        'total_lines': 0,
-        'total_chars': 0,
-        'errors': [],
-    }
-    
-    separator = "=" * 80
-    
-    with open(output_file, 'w', encoding='utf-8') as out:
-        # Header
-        out.write(f"{separator}\n")
-        out.write(f"PROJECT CONTEXT - {root_dir.name}\n")
-        out.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
-        out.write(f"Extensions: {', '.join(sorted(extensions))}\n")
-        out.write(f"{separator}\n\n")
+        separator = "=" * 80
+        content_buffer = []
+
+        # 1. Generate Tree
+        print("[*] Generating directory tree...")
+        tree_lines = self.generate_tree()
+        stats['tree_str'] = "\n".join(tree_lines)
         
-        # Duyệt đệ quy
-        for dirpath, dirnames, filenames in os.walk(root_dir):
-            # Loại bỏ các thư mục cần ignore (in-place để os.walk không đi vào)
-            dirnames[:] = [d for d in dirnames if not should_ignore_dir(d)]
+        if tree_only:
+            with open(output_file, 'w', encoding='utf-8') as out:
+                out.write(stats['tree_str'])
+            return stats
+
+        # 2. Header Content
+        head_info = [
+            separator,
+            f"PROJECT CONTEXT - {self.root_dir.name}",
+            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
+            f"Extensions: {', '.join(sorted(self.extensions))}",
+            separator,
+            "",
+            stats['tree_str'],
+            "",
+            separator,
+            ""
+        ]
+        content_buffer.extend(head_info)
+
+        # 3. Process Files
+        print("[*] Processing files...")
+        for dirpath, dirnames, filenames in os.walk(self.root_dir):
+            # Lọc thư mục (in-place modification)
+            dirnames[:] = [d for d in dirnames 
+                          if not self.should_ignore(Path(dirpath) / d)]
             
             for filename in sorted(filenames):
-                # Kiểm tra extension
-                file_ext = os.path.splitext(filename)[1].lower()
-                if file_ext not in extensions:
+                filepath = Path(dirpath) / filename
+                
+                if self.should_ignore(filepath):
                     continue
-                    
-                # Kiểm tra file ignore
-                if should_ignore_file(filename):
-                    stats['files_skipped'] += 1
+
+                if filepath.suffix.lower() not in self.extensions:
                     continue
-                
-                filepath = Path(dirpath) / filename
-                relative_path = filepath.relative_to(root_dir)
+
+                rel_path = filepath.relative_to(self.root_dir)
                 
                 try:
-                    # Đọc file với xử lý encoding
-                    content = filepath.read_text(encoding='utf-8', errors='replace')
-                    lines = content.splitlines()
+                    file_content = filepath.read_text(encoding='utf-8', errors='replace')
+                    lines = file_content.splitlines()
                     
-                    # Ghi header cho file
-                    out.write(f"\n{separator}\n")
-                    out.write(f"FILE PATH: {relative_path}\n")
-                    out.write(f"LINES: {len(lines)}\n")
-                    out.write(f"{separator}\n\n")
+                    # File Header
+                    content_buffer.append(f"\n{separator}")
+                    content_buffer.append(f"FILE PATH: {rel_path}")
+                    content_buffer.append(f"LINES: {len(lines)}")
+                    content_buffer.append(f"{separator}\n")
                     
-                    # Ghi nội dung
+                    # File Content
                     if include_line_numbers:
-                        for i, line in enumerate(lines, 1):
-                            out.write(f"{i:4d}: {line}\n")
+                        # Dùng list comprehension nhanh hơn vòng lặp
+                        numbered_lines = [f"{i:4d}: {line}" for i, line in enumerate(lines, 1)]
+                        content_buffer.extend(numbered_lines)
                     else:
-                        out.write(content)
-                    
-                    out.write("\n")
+                        content_buffer.append(file_content)
                     
-                    # Cập nhật stats
                     stats['files_processed'] += 1
                     stats['total_lines'] += len(lines)
-                    stats['total_chars'] += len(content)
                     
                 except Exception as e:
-                    stats['errors'].append(f"{relative_path}: {e}")
+                    print(f"[!] Error reading {rel_path}: {e}")
                     stats['files_skipped'] += 1
+
+        # 4. Footer
+        content_buffer.append(f"\n{separator}")
+        content_buffer.append("END OF PROJECT CONTEXT")
         
-        # Footer
-        out.write(f"\n{separator}\n")
-        out.write("END OF PROJECT CONTEXT\n")
-        out.write(f"Total files: {stats['files_processed']}\n")
-        out.write(f"Total lines: {stats['total_lines']}\n")
-        out.write(f"{separator}\n")
-    
-    return stats
+        # 5. Token Estimation & Final Write
+        full_text = "\n".join(content_buffer)
+        stats['total_tokens'] = self.estimate_tokens(full_text)
+        
+        content_buffer.append(f"Total files: {stats['files_processed']}")
+        content_buffer.append(f"Total lines: {stats['total_lines']}")
+        content_buffer.append(f"Estimated tokens: ~{stats['total_tokens']:,}")
+        content_buffer.append(separator)
+        
+        # Write to file
+        final_output = "\n".join(content_buffer)
+        with open(output_file, 'w', encoding='utf-8') as f:
+            f.write(final_output)
 
+        return stats
 
 def main():
-    parser = argparse.ArgumentParser(
-        description='Gộp source code dự án vào một file văn bản'
-   
```

*[Diff truncated - showing first 15000 characters]*
