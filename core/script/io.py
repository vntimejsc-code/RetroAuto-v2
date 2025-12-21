"""
RetroAuto v2 - Script YAML IO

Load and save scripts with validation and clear error messages.
"""

from pathlib import Path
from typing import Any

from pydantic import ValidationError
from ruamel.yaml import YAML

from core.models import Script
from infra import get_logger

logger = get_logger("ScriptIO")

# Configure ruamel.yaml for round-trip preservation
yaml = YAML()
yaml.preserve_quotes = True
yaml.default_flow_style = False


class ScriptLoadError(Exception):
    """Error loading script."""

    def __init__(self, message: str, errors: list[str] | None = None) -> None:
        super().__init__(message)
        self.errors = errors or []


class ScriptSaveError(Exception):
    """Error saving script."""

    pass


def load_script(path: Path | str) -> Script:
    """
    Load and validate a script from YAML file.

    Args:
        path: Path to script.yaml

    Returns:
        Validated Script object

    Raises:
        ScriptLoadError: If file not found, invalid YAML, or validation fails
    """
    path = Path(path)

    if not path.exists():
        raise ScriptLoadError(f"File not found: {path}")

    try:
        with open(path, encoding="utf-8") as f:
            data = yaml.load(f)
    except Exception as e:
        raise ScriptLoadError(f"Invalid YAML: {e}")

    if data is None:
        data = {}

    try:
        script = Script.model_validate(data)
    except ValidationError as e:
        errors = []
        for err in e.errors():
            loc = ".".join(str(x) for x in err["loc"])
            msg = err["msg"]
            errors.append(f"{loc}: {msg}")
        raise ScriptLoadError("Validation failed", errors)

    # Validate references
    ref_errors = script.validate_references()
    if ref_errors:
        raise ScriptLoadError("Invalid references", ref_errors)

    logger.info(
        "Loaded script: %s (%d assets, %d flows)", path.name, len(script.assets), len(script.flows)
    )
    return script


def save_script(script: Script, path: Path | str) -> None:
    """
    Save script to YAML file.

    Args:
        script: Script to save
        path: Destination path

    Raises:
        ScriptSaveError: If write fails
    """
    path = Path(path)

    # Ensure parent directory exists
    path.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Convert to dict - don't exclude defaults to preserve discriminator 'action' field
        data = script.model_dump(mode="json")

        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(data, f)

        logger.info("Saved script: %s", path)
    except Exception as e:
        raise ScriptSaveError(f"Failed to save: {e}")


def create_empty_script(name: str = "Untitled") -> Script:
    """Create a new empty script with default flow."""
    from core.models import Flow

    return Script(
        name=name,
        flows=[Flow(name="main", actions=[])],
        main_flow="main",
    )


def load_script_dict(data: dict[str, Any]) -> Script:
    """
    Load script from dictionary (for programmatic creation).

    Args:
        data: Script data dictionary

    Returns:
        Validated Script object
    """
    try:
        script = Script.model_validate(data)
    except ValidationError as e:
        errors = [f"{'.'.join(str(x) for x in err['loc'])}: {err['msg']}" for err in e.errors()]
        raise ScriptLoadError("Validation failed", errors)

    ref_errors = script.validate_references()
    if ref_errors:
        raise ScriptLoadError("Invalid references", ref_errors)

    return script


def script_to_yaml_string(script: Script) -> str:
    """Convert script to YAML string."""
    import io

    data = script.model_dump(mode="json")
    stream = io.StringIO()
    yaml.dump(data, stream)
    return stream.getvalue()
