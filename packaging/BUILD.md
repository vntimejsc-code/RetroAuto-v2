# Building RetroAuto v2

## Prerequisites

```bash
pip install pyinstaller
```

## One-Folder Build (Recommended)

```bash
cd c:\Auto\Newauto
pyinstaller packaging/pyinstaller_spec.py
```

Output: `dist/RetroAuto/`

## Run from Distribution

```bash
dist\RetroAuto\RetroAuto.exe
```

## One-File Build

Edit `pyinstaller_spec.py`, change EXE to:

```python
exe = EXE(
    pyz, a.scripts, a.binaries, a.zipfiles, a.datas,
    name='RetroAuto',
    debug=False,
    console=False,
    onefile=True,
)
```

Then remove the COLLECT section.

## Troubleshooting

### Missing modules
Add to `hiddenimports` in spec file.

### DLL not found
Add to `binaries` in spec file:
```python
binaries=[('path/to/dll', '.')],
```

### Large output size
Add more items to `excludes` list.
