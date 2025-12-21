# -*- mode: python ; coding: utf-8 -*-
"""
RetroAuto v2 - PyInstaller Spec File

Build: pyinstaller packaging/pyinstaller_spec.py
Output: dist/RetroAuto/
"""

import sys
from pathlib import Path

project_root = Path(SPECPATH).parent

a = Analysis(
    [str(project_root / 'app' / 'main.py')],
    pathex=[str(project_root)],
    binaries=[],
    datas=[],
    hiddenimports=[
        'PySide6.QtCore', 'PySide6.QtGui', 'PySide6.QtWidgets',
        'core', 'core.models', 'core.templates',
        'core.script', 'core.script.io',
        'core.engine', 'core.engine.runner',
        'core.engine.context', 'core.engine.interrupts',
        'vision', 'vision.capture', 'vision.matcher', 'vision.waiter',
        'input', 'input.mouse', 'input.keyboard',
        'infra', 'infra.logging', 'infra.config', 'infra.hotkeys',
        'app.ui', 'app.ui.main_window', 'app.ui.assets_panel',
        'app.ui.actions_panel', 'app.ui.properties_panel',
        'app.ui.log_panel', 'app.ui.capture_tool',
        'app.ui.roi_editor', 'app.ui.engine_worker',
        'pydantic', 'pydantic_core', 'ruamel.yaml',
        'cv2', 'numpy', 'mss',
        'win32api', 'win32con', 'win32clipboard',
    ],
    excludes=['tkinter', 'matplotlib', 'scipy', 'pandas'],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name='RetroAuto',
    debug=False,
    console=False,
    icon=None,
)

coll = COLLECT(
    exe, a.binaries, a.zipfiles, a.datas,
    strip=False, upx=True,
    name='RetroAuto',
)
