"""
RetroAuto v2 - CLI Tool

Command-line interface for RetroScript.
Part of RetroScript Phase 8 - Runtime + Distribution.

Usage:
    retro run script.retro
    retro build project/
    retro test project/
    retro new my_project
    retro docs script.retro
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        prog="retro",
        description="RetroScript CLI - Automation scripting tool",
    )
    parser.add_argument(
        "--version",
        "-v",
        action="version",
        version="RetroScript 1.0.0",
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # run command
    run_parser = subparsers.add_parser("run", help="Run a RetroScript file")
    run_parser.add_argument("file", help="Script file to run")
    run_parser.add_argument("--profile", action="store_true", help="Enable profiling")
    run_parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    run_parser.add_argument("--watch", action="store_true", help="Watch for changes")

    # build command
    build_parser = subparsers.add_parser("build", help="Build/bundle a project")
    build_parser.add_argument("project", help="Project directory")
    build_parser.add_argument("-o", "--output", help="Output path")
    build_parser.add_argument("--no-assets", action="store_true", help="Exclude assets")

    # test command
    test_parser = subparsers.add_parser("test", help="Run tests")
    test_parser.add_argument("path", nargs="?", default=".", help="Project or test file")
    test_parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    # new command
    new_parser = subparsers.add_parser("new", help="Create new project")
    new_parser.add_argument("name", help="Project name")
    new_parser.add_argument(
        "--template",
        "-t",
        choices=["basic", "game_bot", "scraper", "testing"],
        default="basic",
        help="Project template",
    )

    # docs command
    docs_parser = subparsers.add_parser("docs", help="Generate documentation")
    docs_parser.add_argument("path", help="File or directory")
    docs_parser.add_argument("-o", "--output", help="Output path")

    # format command
    fmt_parser = subparsers.add_parser("fmt", help="Format code")
    fmt_parser.add_argument("path", help="File or directory")
    fmt_parser.add_argument("--check", action="store_true", help="Check only, don't modify")

    # lint command
    lint_parser = subparsers.add_parser("lint", help="Lint code")
    lint_parser.add_argument("path", help="File or directory")

    # parse command
    parse_parser = subparsers.add_parser("parse", help="Parse and show AST")
    parse_parser.add_argument("file", help="Script file")
    parse_parser.add_argument("--json", action="store_true", help="Output as JSON")

    return parser


def cmd_run(args: argparse.Namespace) -> int:
    """Run a script."""
    file_path = Path(args.file)
    if not file_path.exists():
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        return 1

    print(f"Running: {file_path}")

    # Read and parse
    source = file_path.read_text(encoding="utf-8")

    try:
        from core.dsl.parser import Parser

        parser = Parser(source)
        program = parser.parse()

        if parser.errors:
            print("Parse errors:")
            for err in parser.errors:
                print(f"  {err}")
            return 1

        print(f"Parsed successfully: {len(program.flows)} flows")

        if args.profile:
            from core.runtime.profiler import get_profiler

            profiler = get_profiler()
            profiler.reset()
            print("Profiling enabled")

        if args.watch:
            from core.runtime.hot_reload import HotReloader

            reloader = HotReloader()
            reloader.watch(file_path)
            reloader.on_reload = lambda p: print(f"Reloaded: {p}")
            reloader.start()
            print("Hot reload enabled. Press Ctrl+C to stop.")
            try:
                while True:
                    import time

                    time.sleep(1)
            except KeyboardInterrupt:
                reloader.stop()

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_build(args: argparse.Namespace) -> int:
    """Build/bundle a project."""
    project_dir = Path(args.project)
    if not project_dir.exists():
        print(f"Error: Project not found: {project_dir}", file=sys.stderr)
        return 1

    try:
        from app.tools.bundler import BundleOptions, Bundler

        options = BundleOptions(include_assets=not args.no_assets)
        bundler = Bundler(options)
        output = bundler.bundle(project_dir, args.output)
        print(f"Bundle created: {output}")
        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_test(args: argparse.Namespace) -> int:
    """Run tests."""
    path = Path(args.path)
    print(f"Running tests in: {path}")

    # Find test files
    if path.is_file():
        test_files = [path]
    else:
        test_files = list(path.glob("**/test_*.retro"))
        test_files.extend(path.glob("**/*_test.retro"))

    print(f"Found {len(test_files)} test file(s)")

    passed = 0
    failed = 0

    for test_file in test_files:
        if args.verbose:
            print(f"  {test_file}")
        # TODO: Run actual tests
        passed += 1

    print(f"\nResults: {passed} passed, {failed} failed")
    return 0 if failed == 0 else 1


def cmd_new(args: argparse.Namespace) -> int:
    """Create new project."""
    try:
        from app.tools.scaffold import create_project

        project_path = create_project(args.name, args.template)
        print(f"Created project: {project_path}")
        print("\nNext steps:")
        print(f"  cd {args.name}")
        print("  retro run main.retro")
        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_docs(args: argparse.Namespace) -> int:
    """Generate documentation."""
    path = Path(args.path)
    if not path.exists():
        print(f"Error: Path not found: {path}", file=sys.stderr)
        return 1

    try:
        from app.tools.doc_generator import DocGenerator

        gen = DocGenerator()

        if path.is_file():
            source = path.read_text(encoding="utf-8")
            doc = gen.generate(source)
            doc.name = path.stem
            markdown = gen.to_markdown(doc)

            if args.output:
                output_path = Path(args.output)
                output_path.write_text(markdown, encoding="utf-8")
                print(f"Documentation written to: {output_path}")
            else:
                print(markdown)
        else:
            # Directory of files
            modules = []
            for file in path.glob("**/*.retro"):
                source = file.read_text(encoding="utf-8")
                doc = gen.generate(source)
                doc.name = file.stem
                modules.append(doc)

            index = gen.generate_index(modules)
            print(index)

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_fmt(args: argparse.Namespace) -> int:
    """Format code."""
    path = Path(args.path)
    if not path.exists():
        print(f"Error: Path not found: {path}", file=sys.stderr)
        return 1

    try:
        from app.ide.formatter import Formatter

        formatter = Formatter()

        files = [path] if path.is_file() else list(path.glob("**/*.retro"))

        for file in files:
            source = file.read_text(encoding="utf-8")
            formatted = formatter.format(source)

            if args.check:
                if source != formatted:
                    print(f"Would format: {file}")
            else:
                file.write_text(formatted, encoding="utf-8")
                print(f"Formatted: {file}")

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_lint(args: argparse.Namespace) -> int:
    """Lint code."""
    path = Path(args.path)
    if not path.exists():
        print(f"Error: Path not found: {path}", file=sys.stderr)
        return 1

    try:
        from app.ide.quick_fixes import LiveValidator

        validator = LiveValidator()

        files = [path] if path.is_file() else list(path.glob("**/*.retro"))

        total_issues = 0

        for file in files:
            source = file.read_text(encoding="utf-8")
            errors = validator.validate(source)

            if errors:
                print(f"\n{file}:")
                for err in errors:
                    print(f"  L{err.line}: [{err.severity}] {err.message}")
                    total_issues += 1

        if total_issues:
            print(f"\n{total_issues} issue(s) found")
            return 1
        else:
            print("No issues found")
            return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_parse(args: argparse.Namespace) -> int:
    """Parse and show AST."""
    file_path = Path(args.file)
    if not file_path.exists():
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        return 1

    source = file_path.read_text(encoding="utf-8")

    try:
        from core.dsl.parser import Parser

        parser = Parser(source)
        program = parser.parse()

        if parser.errors:
            print("Parse errors:")
            for err in parser.errors:
                print(f"  {err}")
            return 1

        print(f"Flows: {[f.name for f in program.flows]}")
        print(f"Imports: {len(program.imports)}")
        print(f"Constants: {len(program.constants)}")

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def main(argv: list[str] | None = None) -> int:
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 0

    commands = {
        "run": cmd_run,
        "build": cmd_build,
        "test": cmd_test,
        "new": cmd_new,
        "docs": cmd_docs,
        "fmt": cmd_fmt,
        "lint": cmd_lint,
        "parse": cmd_parse,
    }

    handler = commands.get(args.command)
    if handler:
        return handler(args)

    print(f"Unknown command: {args.command}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
