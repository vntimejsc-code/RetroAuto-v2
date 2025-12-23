#!/usr/bin/env python3
"""
RetroAuto v2 - Documentation Sync

Automatically updates user guide documentation from code docstrings.

Features:
- Extracts action signatures from core/models.py
- Extracts DSL commands from core/dsl/tokens.py
- Updates 07_reference.md with auto-generated sections
- Preserves manual content outside auto-generated blocks

Usage:
    python scripts/sync_docs.py           # Sync all docs
    python scripts/sync_docs.py --check   # Check if docs are up-to-date
    python scripts/sync_docs.py --verbose # Show extracted docstrings
"""

import argparse
import ast
import re
import sys
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
DOCS_DIR = PROJECT_ROOT / "docs" / "user_guide"
MODELS_FILE = PROJECT_ROOT / "core" / "models.py"
TOKENS_FILE = PROJECT_ROOT / "core" / "dsl" / "tokens.py"

# Markers for auto-generated sections
AUTO_START = "<!-- AUTO-GENERATED: START -->"
AUTO_END = "<!-- AUTO-GENERATED: END -->"


@dataclass
class ActionDoc:
    """Documentation for an action."""
    name: str
    signature: str
    docstring: str
    category: str


def extract_action_docs(file_path: Path) -> list[ActionDoc]:
    """Extract action class documentation from models.py."""
    actions = []
    
    if not file_path.exists():
        return actions
    
    try:
        tree = ast.parse(file_path.read_text(encoding="utf-8"))
    except SyntaxError:
        return actions
    
    # Categories based on class names
    categories = {
        "Click": "🎯 Mouse Actions",
        "Drag": "🎯 Mouse Actions",
        "Scroll": "🎯 Mouse Actions",
        "Wait": "👁️ Vision & Wait",
        "If": "🔀 Conditionals",
        "While": "🔁 Loops",
        "Type": "⌨️ Keyboard",
        "Hotkey": "⌨️ Keyboard",
        "Read": "📖 OCR",
        "Notify": "📢 Notifications",
        "Run": "🔧 Flow Control",
        "Goto": "🔧 Flow Control",
        "Label": "🔧 Flow Control",
        "Delay": "⏱️ Timing",
        "Loop": "🔁 Loops",
    }
    
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            # Skip non-action classes
            if not any(node.name.startswith(prefix) for prefix in categories.keys()):
                continue
            
            # Get docstring
            docstring = ast.get_docstring(node) or ""
            
            # Build signature from class fields
            fields = []
            for item in node.body:
                if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                    field_name = item.target.id
                    if field_name not in ["action", "comment"]:
                        fields.append(field_name)
            
            signature = f"{node.name}({', '.join(fields)})" if fields else node.name
            
            # Determine category
            category = "🔧 Other"
            for prefix, cat in categories.items():
                if node.name.startswith(prefix):
                    category = cat
                    break
            
            actions.append(ActionDoc(
                name=node.name,
                signature=signature,
                docstring=docstring.split("\n")[0] if docstring else "",
                category=category,
            ))
    
    return actions


def extract_dsl_commands(file_path: Path) -> list[tuple[str, str]]:
    """Extract DSL command tokens from tokens.py."""
    commands = []
    
    if not file_path.exists():
        return commands
    
    content = file_path.read_text(encoding="utf-8")
    
    # Find TokenType enum members
    pattern = r'(\w+)\s*=\s*auto\(\)\s*#\s*(.+)'
    for match in re.finditer(pattern, content):
        token_name = match.group(1)
        description = match.group(2).strip()
        
        # Filter to actual commands (not structural tokens)
        if token_name.isupper() and not token_name.startswith("_"):
            commands.append((token_name.lower(), description))
    
    return commands


def generate_reference_section(actions: list[ActionDoc]) -> str:
    """Generate markdown reference section from actions."""
    lines = [
        "## Auto-Generated Action Reference",
        "",
        "> *Tự động tạo từ `core/models.py`. Cập nhật lần cuối: " + 
        __import__("datetime").datetime.now().strftime("%Y-%m-%d %H:%M") + "*",
        "",
    ]
    
    # Group by category
    by_category: dict[str, list[ActionDoc]] = {}
    for action in actions:
        by_category.setdefault(action.category, []).append(action)
    
    for category, cat_actions in sorted(by_category.items()):
        lines.append(f"### {category}")
        lines.append("")
        for action in sorted(cat_actions, key=lambda a: a.name):
            lines.append(f"**`{action.signature}`**")
            if action.docstring:
                lines.append(f"  - {action.docstring}")
            lines.append("")
    
    return "\n".join(lines)


def update_reference_doc(reference_path: Path, new_content: str) -> bool:
    """Update reference.md with new auto-generated content."""
    if not reference_path.exists():
        return False
    
    content = reference_path.read_text(encoding="utf-8")
    
    # Find and replace auto-generated section
    if AUTO_START in content and AUTO_END in content:
        before = content.split(AUTO_START)[0]
        after = content.split(AUTO_END)[1]
        new_content_full = f"{before}{AUTO_START}\n{new_content}\n{AUTO_END}{after}"
    else:
        # Add auto-generated section at the end
        new_content_full = f"{content}\n\n---\n\n{AUTO_START}\n{new_content}\n{AUTO_END}\n"
    
    reference_path.write_text(new_content_full, encoding="utf-8")
    return True


def generate_features_list() -> str:
    """Generate a features list from the codebase."""
    features = []
    
    # Scan for feature markers in code
    for py_file in PROJECT_ROOT.rglob("*.py"):
        if "__pycache__" in str(py_file):
            continue
        try:
            content = py_file.read_text(encoding="utf-8", errors="ignore")
            # Look for feature docstrings
            if '"""' in content:
                match = re.search(r'"""([^"]+)"""', content)
                if match:
                    first_line = match.group(1).strip().split("\n")[0]
                    if len(first_line) < 100 and first_line:
                        rel_path = py_file.relative_to(PROJECT_ROOT)
                        features.append((str(rel_path), first_line))
        except Exception:
            continue
    
    return features


def main():
    parser = argparse.ArgumentParser(description="Sync documentation from code")
    parser.add_argument("--check", action="store_true", help="Check if docs need update")
    parser.add_argument("--verbose", action="store_true", help="Show extracted content")
    args = parser.parse_args()
    
    print("=" * 60)
    print("  RetroAuto v2 - Documentation Sync")
    print("=" * 60)
    
    # Extract action documentation
    print("\n📚 Extracting action documentation...")
    actions = extract_action_docs(MODELS_FILE)
    print(f"   Found {len(actions)} actions")
    
    if args.verbose:
        for action in actions:
            print(f"   - {action.name}: {action.docstring[:50]}...")
    
    # Extract DSL commands
    print("\n📝 Extracting DSL commands...")
    commands = extract_dsl_commands(TOKENS_FILE)
    print(f"   Found {len(commands)} commands")
    
    # Generate reference content
    print("\n🔄 Generating reference content...")
    reference_content = generate_reference_section(actions)
    
    # Update reference.md
    reference_path = DOCS_DIR / "07_reference.md"
    if reference_path.exists():
        if args.check:
            current = reference_path.read_text(encoding="utf-8")
            if AUTO_START in current:
                print("   ℹ️  Reference has auto-generated section")
            else:
                print("   ⚠️  Reference missing auto-generated section")
            return 0
        
        # Add auto-generated markers if missing
        content = reference_path.read_text(encoding="utf-8")
        if AUTO_START not in content:
            # Append at the end
            new_content = f"{content}\n\n---\n\n{AUTO_START}\n{reference_content}\n{AUTO_END}\n"
            reference_path.write_text(new_content, encoding="utf-8")
            print("   ✅ Added auto-generated section to 07_reference.md")
        else:
            update_reference_doc(reference_path, reference_content)
            print("   ✅ Updated auto-generated section in 07_reference.md")
    
    # Generate FEATURES.md
    features_path = PROJECT_ROOT / "docs" / "FEATURES.md"
    print("\n📋 Generating FEATURES.md...")
    
    features_content = [
        "# RetroAuto v2 - Feature List",
        "",
        "> *Auto-generated from codebase. Do not edit manually.*",
        "",
        "## Core Modules",
        "",
    ]
    
    for rel_path, desc in sorted(generate_features_list())[:30]:
        features_content.append(f"- **{rel_path}**: {desc}")
    
    features_path.write_text("\n".join(features_content), encoding="utf-8")
    print(f"   ✅ Generated FEATURES.md ({len(generate_features_list())} modules)")
    
    print("\n🎉 Documentation sync complete!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
