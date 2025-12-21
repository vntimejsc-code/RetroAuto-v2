# RetroAuto v2

**Windows automation tool with image recognition - Win95/98 style**

## Features

- 🖼️ Image-based automation using template matching
- 🖱️ Mouse & keyboard control (click, hotkey, type)
- 📝 YAML script format with validation
- 🔄 Label/Goto flow control + nested flows
- ⚡ Interrupt rules for reactive automation
- 🎨 Classic Windows 95/98 style GUI

## Requirements

- Python 3.11+
- Windows 10/11

## Installation

```bash
# Clone the repository
git clone https://github.com/your/retroauto.git
cd retroauto

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate

# Install with dev dependencies
pip install -e ".[dev]"

# Setup pre-commit hooks
pre-commit install
```

## Quick Start

```bash
# Run the application
python -m app.main

# Or after installation
retroauto
```

## Project Structure

```
retroauto/
├── app/                    # Application layer
│   ├── main.py            # Entry point
│   └── ui/                # PySide6 UI components
│       ├── main_window.py
│       ├── assets_panel.py
│       ├── actions_panel.py
│       ├── properties_panel.py
│       ├── log_panel.py
│       └── capture_tool.py
├── core/                   # Core logic
│   ├── models.py          # Pydantic data models
│   ├── templates.py       # Template store
│   ├── script/            # Script IO
│   │   └── io.py
│   └── engine/            # Execution engine
│       ├── runner.py
│       ├── context.py
│       └── interrupts.py
├── vision/                 # Vision subsystem
│   ├── capture.py         # Screen capture (mss)
│   └── matcher.py         # Template matching (OpenCV)
├── input/                  # Input subsystem
│   ├── mouse.py           # Mouse control (pywin32)
│   └── keyboard.py        # Keyboard control (pywin32)
├── infra/                  # Infrastructure
│   ├── logging.py         # Logging setup
│   ├── config.py          # Configuration
│   └── hotkeys.py         # Global hotkeys
└── tests/                  # Test suite
```

## Development

```bash
# Run linting
ruff check .

# Run formatting
black .

# Run type checking
mypy app core vision input infra

# Run tests
pytest

# Run all checks
pre-commit run --all-files
```

## License

MIT
