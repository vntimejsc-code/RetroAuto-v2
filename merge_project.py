"""
RetroAuto v2 - Project Context Merger

Gộp toàn bộ source code của dự án vào một file văn bản duy nhất.
Hữu ích để chia sẻ context với AI hoặc review code.

Usage:
    python merge_project.py
    python merge_project.py --output custom_output.txt
    python merge_project.py --extensions .py .js .ts
"""

import argparse
import os
from pathlib import Path
from datetime import datetime

# Các thư mục cần bỏ qua
IGNORE_DIRS = {
    '.git',
    '__pycache__',
    'venv',
    '.venv',
    'env',
    'node_modules',
    '.idea',
    '.vscode',
    '.mypy_cache',
    '.pytest_cache',
    '.ruff_cache',
    '.coverage',
    'dist',
    'build',
    'eggs',
    '*.egg-info',
    '.tox',
    '.nox',
    'htmlcov',
}

# Các đuôi file mặc định
DEFAULT_EXTENSIONS = {'.py'}

# Các file cần bỏ qua
IGNORE_FILES = {
    'project_context.txt',  # File output
    '.gitignore',
    '.pre-commit-config.yaml',
    'mypy.ini',
    'pyproject.toml',
    'setup.py',
    'setup.cfg',
}


def should_ignore_dir(dir_name: str) -> bool:
    """Kiểm tra xem thư mục có nên bỏ qua không."""
    return dir_name in IGNORE_DIRS or dir_name.startswith('.')


def should_ignore_file(file_name: str) -> bool:
    """Kiểm tra xem file có nên bỏ qua không."""
    return file_name in IGNORE_FILES


def merge_project(
    root_dir: Path,
    output_file: Path,
    extensions: set[str],
    include_line_numbers: bool = False,
) -> dict:
    """
    Gộp tất cả source code vào một file.
    
    Args:
        root_dir: Thư mục gốc của dự án
        output_file: File output
        extensions: Các đuôi file cần lấy
        include_line_numbers: Thêm số dòng vào mỗi dòng code
        
    Returns:
        Dict với thống kê
    """
    stats = {
        'files_processed': 0,
        'files_skipped': 0,
        'total_lines': 0,
        'total_chars': 0,
        'errors': [],
    }
    
    separator = "=" * 80
    
    with open(output_file, 'w', encoding='utf-8') as out:
        # Header
        out.write(f"{separator}\n")
        out.write(f"PROJECT CONTEXT - {root_dir.name}\n")
        out.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        out.write(f"Extensions: {', '.join(sorted(extensions))}\n")
        out.write(f"{separator}\n\n")
        
        # Duyệt đệ quy
        for dirpath, dirnames, filenames in os.walk(root_dir):
            # Loại bỏ các thư mục cần ignore (in-place để os.walk không đi vào)
            dirnames[:] = [d for d in dirnames if not should_ignore_dir(d)]
            
            for filename in sorted(filenames):
                # Kiểm tra extension
                file_ext = os.path.splitext(filename)[1].lower()
                if file_ext not in extensions:
                    continue
                    
                # Kiểm tra file ignore
                if should_ignore_file(filename):
                    stats['files_skipped'] += 1
                    continue
                
                filepath = Path(dirpath) / filename
                relative_path = filepath.relative_to(root_dir)
                
                try:
                    # Đọc file với xử lý encoding
                    content = filepath.read_text(encoding='utf-8', errors='replace')
                    lines = content.splitlines()
                    
                    # Ghi header cho file
                    out.write(f"\n{separator}\n")
                    out.write(f"FILE PATH: {relative_path}\n")
                    out.write(f"LINES: {len(lines)}\n")
                    out.write(f"{separator}\n\n")
                    
                    # Ghi nội dung
                    if include_line_numbers:
                        for i, line in enumerate(lines, 1):
                            out.write(f"{i:4d}: {line}\n")
                    else:
                        out.write(content)
                    
                    out.write("\n")
                    
                    # Cập nhật stats
                    stats['files_processed'] += 1
                    stats['total_lines'] += len(lines)
                    stats['total_chars'] += len(content)
                    
                except Exception as e:
                    stats['errors'].append(f"{relative_path}: {e}")
                    stats['files_skipped'] += 1
        
        # Footer
        out.write(f"\n{separator}\n")
        out.write("END OF PROJECT CONTEXT\n")
        out.write(f"Total files: {stats['files_processed']}\n")
        out.write(f"Total lines: {stats['total_lines']}\n")
        out.write(f"{separator}\n")
    
    return stats


def main():
    parser = argparse.ArgumentParser(
        description='Gộp source code dự án vào một file văn bản'
    )
    parser.add_argument(
        '--root', '-r',
        type=Path,
        default=Path('.'),
        help='Thư mục gốc (mặc định: thư mục hiện tại)'
    )
    parser.add_argument(
        '--output', '-o',
        type=Path,
        default=Path('project_context.txt'),
        help='File output (mặc định: project_context.txt)'
    )
    parser.add_argument(
        '--extensions', '-e',
        nargs='+',
        default=['.py'],
        help='Các đuôi file cần lấy (mặc định: .py)'
    )
    parser.add_argument(
        '--line-numbers', '-n',
        action='store_true',
        help='Thêm số dòng vào mỗi dòng code'
    )
    parser.add_argument(
        '--all-code',
        action='store_true',
        help='Lấy tất cả file code phổ biến (.py, .js, .ts, .java, .go, .rs, .cpp, .c, .h)'
    )
    
    args = parser.parse_args()
    
    # Xử lý extensions
    if args.all_code:
        extensions = {'.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.go', '.rs', '.cpp', '.c', '.h', '.hpp', '.cs', '.rb', '.php'}
    else:
        extensions = {ext if ext.startswith('.') else f'.{ext}' for ext in args.extensions}
    
    root_dir = args.root.resolve()
    output_file = args.output.resolve()
    
    print(f"[*] Scanning: {root_dir}")
    print(f"[>] Output: {output_file}")
    print(f"[#] Extensions: {', '.join(sorted(extensions))}")
    print()
    
    stats = merge_project(
        root_dir=root_dir,
        output_file=output_file,
        extensions=extensions,
        include_line_numbers=args.line_numbers,
    )
    
    print(f"[OK] Done!")
    print(f"   Files processed: {stats['files_processed']}")
    print(f"   Files skipped: {stats['files_skipped']}")
    print(f"   Total lines: {stats['total_lines']:,}")
    print(f"   Total chars: {stats['total_chars']:,}")
    
    if stats['errors']:
        print(f"\n[!] Errors ({len(stats['errors'])}):")
        for err in stats['errors'][:5]:
            print(f"   - {err}")
        if len(stats['errors']) > 5:
            print(f"   ... and {len(stats['errors']) - 5} more")
    
    # Hiển thị kích thước file
    size_kb = output_file.stat().st_size / 1024
    if size_kb > 1024:
        print(f"\n[=] Output size: {size_kb/1024:.2f} MB")
    else:
        print(f"\n[=] Output size: {size_kb:.2f} KB")


if __name__ == '__main__':
    main()
