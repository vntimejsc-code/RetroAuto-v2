# RetroAuto v2 - Advanced Windows Automation Tool

## Overview
RetroAuto v2 is a comprehensive automation toolchain featuring a custom DSL (RetroScript), a Win95-styled IDE, and powerful runtime capabilities for Windows automation, game botting, and testing.

## 🤖 For AI Agents Analyzing This Repo
This repository is structured to be easily parseable and understandable. Here is your map:

### 1. Core Architecture (`core/`)
- **DSL (`core/dsl/`)**: The heart of the language.
  - `parser.py`: Recursive descent parser.
  - `lexer.py`: Tokenizer.
  - `ast.py`: Abstract Syntax Tree definitions.
  - `interpreter.py`: Runtime execution engine.
- **Engine (`core/engine/`)**: Execution context, scope management, and built-ins.
- **Vision (`core/vision/`)**: Computer vision capabilities (template matching, OCR stubs).
- **Game (`core/game/`)**: Game-specific features (Pixel detection, Anti-detect, Macros).
- **Network (`core/network/`)**: HTTP/WebSocket clients and Remote Control API.
- **Analytics (`core/analytics/`)**: Metrics and structured logging.
- **Package (`core/package/`)**: Dependency management (`retro.toml`).
- **LSP (`core/lsp/`)**: Language Server Protocol implementation.

### 2. Application Layer (`app/`)
- **UI (`app/ui/`)**: PySide6 (Qt) based GUI with custom Windows 95 styling.
  - `main.py`: Entry point.
  - `main_window.py`: The primary IDE window.
  - `visual_editor/`: Drag-and-drop flow editing components.
- **Tools (`app/tools/`)**: CLI utilities (`cli.py`), bundler, scaffolding.

### 3. Key Entry Points
- **Run App**: `python -m app.main`
- **CLI**: `python -m app.cli`
- **LSP**: `python -m core.lsp.server`
- **Verification**: `python verify_all.py`

### 4. Language Syntax (RetroScript)
RetroScript looks like a mix of Python and Rust/Go.
```retroscript
flow main {
    log("Starting automation...");
    
    # Visual matching
    if find("button.png") {
        click(match.x, match.y);
    }
    
    # Network
    let data = fetch("https://api.example.com/config");
    
    # Game loop
    while true {
        wait(1s);
    }
}
```

## Setup & Run
1. Install dependencies: `pip install -r requirements.txt` (or manually: `PySide6`, `mss`, `numpy`, `pillow`, `requests`, `websocket-client`, `tomli`, `tomli-w`)
2. Run IDE: `python -m app.main`
3. Verify: `python verify_all.py`

## Project Status
- ✅ **Core DSL**: Fully implemented.
- ✅ **IDE**: Complete with Debugger & LSP.
- ✅ **Runtime**: Stable with Hot-Reload.
- ✅ **Modules**: Network, Game, Vision, Analytics, Package Manager all active.
