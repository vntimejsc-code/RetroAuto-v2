#!/usr/bin/env python3
"""
RetroAuto Studio - Entry Point

Launch the Unified Studio with mode tabs (Visual/Code/Debug).

Usage:
    python run_studio.py
    python run_studio.py --project path/to/project
    python run_studio.py --file script.dsl
"""

import sys
import argparse
from pathlib import Path


def main() -> int:
    """Main entry point for RetroAuto Studio."""
    parser = argparse.ArgumentParser(
        description="RetroAuto Studio - Unified Scripting Environment"
    )
    parser.add_argument(
        "--project", "-p",
        type=str,
        help="Path to project folder to open"
    )
    parser.add_argument(
        "--file", "-f",
        type=str,
        help="Path to script file to open"
    )
    parser.add_argument(
        "--mode", "-m",
        choices=["visual", "code", "debug"],
        default="visual",
        help="Initial mode (default: visual)"
    )
    
    args = parser.parse_args()
    
    # Import here to avoid slow startup for --help
    from PySide6.QtWidgets import QApplication
    from app.ui.unified_studio import UnifiedStudio
    from app.ui.theme_engine import get_theme_manager
    from app.ui.onboarding_wizard import show_onboarding_if_needed
    
    # Create app
    app = QApplication.instance() or QApplication(sys.argv)
    
    # Apply theme
    get_theme_manager().apply_theme()
    
    # Create studio
    studio = UnifiedStudio()
    
    # Show onboarding for first-run (unless file/project specified)
    if not args.file and not args.project:
        selected_mode = show_onboarding_if_needed(studio)
        if selected_mode:
            args.mode = selected_mode
    
    # Set initial mode
    if args.mode == "code":
        studio.mode_bar.set_code_mode()
    elif args.mode == "debug":
        studio.mode_bar.set_debug_mode()
    elif args.mode == "tutorial":
        # Tutorial mode: open visual with demo
        studio.mode_bar.set_visual_mode()
        studio.output.log_info("Welcome! Try clicking the nodes in Visual Mode to learn.")
    # else visual is default
    
    # Open project or file
    if args.project:
        project_path = Path(args.project)
        if project_path.exists() and project_path.is_dir():
            studio.explorer.load_project(project_path)
    
    if args.file:
        file_path = Path(args.file)
        if file_path.exists() and file_path.is_file():
            studio._load_file(file_path)
            studio.mode_bar.set_code_mode()
    
    studio.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
