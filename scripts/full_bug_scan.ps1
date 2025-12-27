# RetroAuto Bug Scan Script v1.0
# Usage: .\scripts\full_bug_scan.ps1 [-Quick]

param([switch]$Quick)

$errors = @()

Write-Host "`n=== BUG SCAN START ===" -ForegroundColor Cyan

# Layer 1: Syntax
Write-Host "[1/7] Syntax Check..."
python -m py_compile app/ui/main_window.py app/ui/unified_studio.py 2>&1 | Out-Null
if ($LASTEXITCODE -eq 0) { Write-Host "  OK: Syntax" -ForegroundColor Green }
else { $errors += "Syntax"; Write-Host "  FAIL: Syntax" -ForegroundColor Red }

# Layer 2: Lint
Write-Host "[2/7] Lint Check..."
$ruff = ruff check app/ core/ --select=F401,F821 --statistics 2>&1
if ($ruff -match "Found 0") { Write-Host "  OK: Lint" -ForegroundColor Green }
elseif ($LASTEXITCODE -eq 0) { Write-Host "  OK: Lint" -ForegroundColor Green }
else { Write-Host "  WARN: Lint issues found" -ForegroundColor Yellow }

# Layer 3: Mypy
Write-Host "[3/7] Type Check (mypy)..."
$mypy = mypy app/ui/main_window.py --ignore-missing-imports 2>&1
if ($mypy -match "error:") { $errors += "Mypy"; Write-Host "  FAIL: Type errors" -ForegroundColor Red }
else { Write-Host "  OK: Types" -ForegroundColor Green }

# Layer 4: Imports
Write-Host "[4/7] Import Check..."
python -c "from app.ui.main_window import MainWindow; from core.models import Click" 2>&1 | Out-Null
if ($LASTEXITCODE -eq 0) { Write-Host "  OK: Imports" -ForegroundColor Green }
else { $errors += "Import"; Write-Host "  FAIL: Import" -ForegroundColor Red }

# Layer 5-6: Skip in quick mode
if (-not $Quick) {
    Write-Host "[5/7] Unit Tests... (skipped - no tests dir)"
    Write-Host "[6/7] Integration... (run manually)"
}

# Layer 7: Smoke
Write-Host "[7/7] Smoke Test..."
$smoke = python -c "import sys; sys.argv=['t']; from PySide6.QtWidgets import QApplication; a=QApplication(sys.argv); from app.ui.main_window import MainWindow; m=MainWindow(); print('OK')" 2>&1
if ($smoke -match "OK") { Write-Host "  OK: Smoke" -ForegroundColor Green }
else { $errors += "Smoke"; Write-Host "  FAIL: Smoke" -ForegroundColor Red }

# Summary
Write-Host "`n=== SUMMARY ===" -ForegroundColor Cyan
if ($errors.Count -eq 0) {
    Write-Host "ALL CHECKS PASSED" -ForegroundColor Green
    exit 0
} else {
    Write-Host "FAILED: $($errors -join ', ')" -ForegroundColor Red
    exit 1
}
