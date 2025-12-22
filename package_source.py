import os
import zipfile
from pathlib import Path


def zip_project(output_filename="RetroAuto_v2_Source.zip", source_dir="."):
    source_path = Path(source_dir).resolve()

    # Exclude these patterns
    excludes = {
        "__pycache__",
        ".git",
        ".idea",
        ".vscode",
        ".DS_Store",
        "venv",
        "env",
        ".pytest_cache",
        "dist",
        "build",
        "retroauto.log",
    }

    with zipfile.ZipFile(output_filename, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(source_path):
            # Modify dirs in-place to skip excluded directories
            dirs[:] = [d for d in dirs if d not in excludes]

            for file in files:
                if file in excludes or file.endswith(".pyc") or file == output_filename:
                    continue

                file_path = Path(root) / file
                archive_name = file_path.relative_to(source_path)

                print(f"Adding: {archive_name}")
                zipf.write(file_path, archive_name)

    print(f"\nSuccessfully created: {output_filename}")
    print(f"Size: {os.path.getsize(output_filename) / 1024 / 1024:.2f} MB")


if __name__ == "__main__":
    zip_project()
