"""
RetroAuto v2 - Project Context Merger (Advanced Version)

Gộp toàn bộ source code của dự án vào một file văn bản duy nhất.
Tối ưu hóa cho việc chia sẻ context với LLM (ChatGPT, Claude, Gemini).

Features:
- Directory Tree View: Hiển thị cấu trúc thư mục
- Smart Ignore: Hỗ trợ .gitignore và danh sách mặc định
- Token Estimator: Ước lượng số token
- Clipboard: Tự động copy (nếu có pyperclip)

Usage:
    python merge_project.py
    python merge_project.py --tree-only
    python merge_project.py --clipboard
"""

import argparse
import os
import sys
import fnmatch
from pathlib import Path
from datetime import datetime

# Cố gắng import pyperclip
try:
    import pyperclip
    HAS_CLIPBOARD = True
except ImportError:
    HAS_CLIPBOARD = False

# Các thư mục cần bỏ qua mặc định (kể cả khi không có .gitignore)
DEFAULT_IGNORE_DIRS = {
    '.git', '__pycache__', 'venv', '.venv', 'env', 'node_modules',
    '.idea', '.vscode', '.mypy_cache', '.pytest_cache', '.ruff_cache',
    '.coverage', 'dist', 'build', 'eggs', '*.egg-info', '.tox', '.nox', 'htmlcov',
    'site-packages'
}

# Các file cần bỏ qua mặc định
DEFAULT_IGNORE_FILES = {
    'project_context.txt', '.gitignore', '.pre-commit-config.yaml',
    'mypy.ini', 'pyproject.toml', 'setup.py', 'setup.cfg', '*.pyc', '*.pyd',
    '*.db', '*.sqlite', '*.png', '*.jpg', '*.jpeg', '*.gif', '*.ico', '*.svg',
    '*.exe', '*.dll', '*.so', '*.dylib', '*.bin', '*.pkl', '*.log'
}

class ProjectMerger:
    def __init__(self, root_dir: Path, extensions: set[str], use_gitignore: bool = True):
        self.root_dir = root_dir
        self.extensions = extensions
        self.ignore_patterns = set()
        
        # Load ignore patterns
        self.load_default_ignores()
        if use_gitignore:
            self.load_gitignore()

    def load_default_ignores(self):
        self.ignore_patterns.update(DEFAULT_IGNORE_DIRS)
        self.ignore_patterns.update(DEFAULT_IGNORE_FILES)

    def load_gitignore(self):
        """Đọc file .gitignore nếu tồn tại."""
        gitignore_path = self.root_dir / '.gitignore'
        if gitignore_path.exists():
            try:
                with open(gitignore_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            self.ignore_patterns.add(line)
                            # Support directory specific patterns
                            if line.endswith('/'):
                                self.ignore_patterns.add(line[:-1])
            except Exception as e:
                print(f"[!] Warning: Could not read .gitignore: {e}")

    def should_ignore(self, path: Path) -> bool:
        """Kiểm tra xem path có matches với bất kỳ pattern nào không."""
        name = path.name
        rel_path = str(path.relative_to(self.root_dir))
        
        # Check hidden files/dirs
        if name.startswith('.'):
            return True
            
        for pattern in self.ignore_patterns:
            if fnmatch.fnmatch(name, pattern) or fnmatch.fnmatch(rel_path, pattern):
                return True
            if path.is_dir() and fnmatch.fnmatch(name + '/', pattern):
                return True
        return False

    def generate_tree(self) -> list[str]:
        """Tạo cấu trúc cây thư mục."""
        tree_lines = ["Directory Structure:", "."]
        
        def _add_to_tree(directory: Path, prefix: str = ""):
            try:
                # Lọc và sắp xếp: thư mục trước, file sau
                items = sorted(list(directory.iterdir()), key=lambda x: (not x.is_dir(), x.name.lower()))
                items = [x for x in items if not self.should_ignore(x)]
                
                count = len(items)
                for i, item in enumerate(items):
                    is_last = (i == count - 1)
                    connector = "└── " if is_last else "├── "
                    
                    tree_lines.append(f"{prefix}{connector}{item.name}")
                    
                    if item.is_dir():
                        extension = "    " if is_last else "│   "
                        _add_to_tree(item, prefix + extension)
            except PermissionError:
                pass

        _add_to_tree(self.root_dir)
        return tree_lines

    def estimate_tokens(self, text: str) -> int:
        """Ước lượng số token (quy tắc: 1 token ~ 4 chars)."""
        return len(text) // 4

    def merge(self, output_file: Path, include_line_numbers: bool = False, tree_only: bool = False):
        stats = {
            'files_processed': 0,
            'files_skipped': 0,
            'total_lines': 0,
            'total_tokens': 0,
            'tree_str': ""
        }
        
        separator = "=" * 80
        content_buffer = []

        # 1. Generate Tree
        print("[*] Generating directory tree...")
        tree_lines = self.generate_tree()
        stats['tree_str'] = "\n".join(tree_lines)
        
        if tree_only:
            with open(output_file, 'w', encoding='utf-8') as out:
                out.write(stats['tree_str'])
            return stats

        # 2. Header Content
        head_info = [
            separator,
            f"PROJECT CONTEXT - {self.root_dir.name}",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Extensions: {', '.join(sorted(self.extensions))}",
            separator,
            "",
            stats['tree_str'],
            "",
            separator,
            ""
        ]
        content_buffer.extend(head_info)

        # 3. Process Files
        print("[*] Processing files...")
        for dirpath, dirnames, filenames in os.walk(self.root_dir):
            # Lọc thư mục (in-place modification)
            dirnames[:] = [d for d in dirnames 
                          if not self.should_ignore(Path(dirpath) / d)]
            
            for filename in sorted(filenames):
                filepath = Path(dirpath) / filename
                
                if self.should_ignore(filepath):
                    continue

                if filepath.suffix.lower() not in self.extensions:
                    continue

                rel_path = filepath.relative_to(self.root_dir)
                
                try:
                    file_content = filepath.read_text(encoding='utf-8', errors='replace')
                    lines = file_content.splitlines()
                    
                    # File Header
                    content_buffer.append(f"\n{separator}")
                    content_buffer.append(f"FILE PATH: {rel_path}")
                    content_buffer.append(f"LINES: {len(lines)}")
                    content_buffer.append(f"{separator}\n")
                    
                    # File Content
                    if include_line_numbers:
                        # Dùng list comprehension nhanh hơn vòng lặp
                        numbered_lines = [f"{i:4d}: {line}" for i, line in enumerate(lines, 1)]
                        content_buffer.extend(numbered_lines)
                    else:
                        content_buffer.append(file_content)
                    
                    stats['files_processed'] += 1
                    stats['total_lines'] += len(lines)
                    
                except Exception as e:
                    print(f"[!] Error reading {rel_path}: {e}")
                    stats['files_skipped'] += 1

        # 4. Footer
        content_buffer.append(f"\n{separator}")
        content_buffer.append("END OF PROJECT CONTEXT")
        
        # 5. Token Estimation & Final Write
        full_text = "\n".join(content_buffer)
        stats['total_tokens'] = self.estimate_tokens(full_text)
        
        content_buffer.append(f"Total files: {stats['files_processed']}")
        content_buffer.append(f"Total lines: {stats['total_lines']}")
        content_buffer.append(f"Estimated tokens: ~{stats['total_tokens']:,}")
        content_buffer.append(separator)
        
        # Write to file
        final_output = "\n".join(content_buffer)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(final_output)

        return stats

def main():
    parser = argparse.ArgumentParser(description='Advanced Project Context Merger')
    parser.add_argument('--root', '-r', type=Path, default=Path('.'), help='Root directory')
    parser.add_argument('--output', '-o', type=Path, default=None, help='Output file (default: project_context.txt in script dir)')
    parser.add_argument('--extensions', '-e', nargs='+', default=['.py'], help='File extensions to include')
    parser.add_argument('--line-numbers', '-n', action='store_true', help='Add line numbers')
    parser.add_argument('--all-code', action='store_true', help='Include all common code files')
    parser.add_argument('--tree-only', action='store_true', help='Only generate directory tree')
    parser.add_argument('--clipboard', '-c', action='store_true', help='Copy output to clipboard')
    parser.add_argument('--no-ignore', action='store_true', help='Disable .gitignore parsing')

    args = parser.parse_args()

    # Setup extensions
    if args.all_code:
        extensions = {'.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.go', '.rs', '.cpp', '.c', '.h', '.cs', '.php', '.html', '.css', '.json', '.yaml', '.yml', '.md'}
    else:
        extensions = {ext if ext.startswith('.') else f'.{ext}' for ext in args.extensions}

    merger = ProjectMerger(
        root_dir=args.root.resolve(),
        extensions=extensions,
        use_gitignore=not args.no_ignore
    )

    # Determine output file path
    if args.output:
        output_file = args.output.resolve()
    else:
        # Default to script directory
        output_file = Path(__file__).resolve().parent / 'project_context.txt'

    print(f"[*] Starting merge for: {merger.root_dir}")
    
    start_time = datetime.now()
    stats = merger.merge(
        output_file=output_file,
        include_line_numbers=args.line_numbers,
        tree_only=args.tree_only
    )
    duration = datetime.now() - start_time

    # Report
    print(f"\n[OK] Completed in {duration.total_seconds():.2f}s")
    if not args.tree_only:
        print(f"   Files: {stats['files_processed']}")
        print(f"   Lines: {stats['total_lines']:,}")
        print(f"   Tokens: ~{stats['total_tokens']:,}")
        print(f"   Output: {output_file}")
    else:
        print("   Tree generated successfully.")

    # Clipboard handling
    if args.clipboard:
        if HAS_CLIPBOARD:
            try:
                # Đọc lại file để copy
                content = output_file.read_text(encoding='utf-8')
                pyperclip.copy(content)
                print("   [+] Copied to clipboard!")
            except Exception as e:
                print(f"   [!] Clipboard error: {e}")
        else:
            print("   [!] 'pyperclip' module not found. Install it with: pip install pyperclip")

if __name__ == '__main__':
    main()
