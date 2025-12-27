# RetroAuto Bug Scan Script v2.0
# Usage: .\scripts\full_bug_scan.ps1 [-Quick] [-Strict]
#
# Improvements:
# - Dynamic file scanning (not hardcoded)
# - Timing metrics
# - JSON report generation
# - Fixed ruff select syntax

param(
    [switch]$Quick,
    [switch]$Strict
)

$errors = @()
$startTime = Get-Date
$report = @{
    timestamp = (Get-Date -Format "o")
    layers    = @{}
    errors    = @()
    duration  = 0
}

Write-Host "`n=== RETRO AUTO BUG SCAN v2.0 ===" -ForegroundColor Cyan
Write-Host "Started: $(Get-Date -Format 'HH:mm:ss')" -ForegroundColor DarkGray

# Dynamic file discovery
$appFiles = Get-ChildItem -Path app -Recurse -Filter "*.py" | Select-Object -ExpandProperty FullName
$coreFiles = Get-ChildItem -Path core -Recurse -Filter "*.py" | Select-Object -ExpandProperty FullName
$allFiles = $appFiles + $coreFiles
Write-Host "Files to scan: $($allFiles.Count)" -ForegroundColor DarkGray

# ──────────────────────────────────────────────────────────────
# Layer 1: Syntax Check
# ──────────────────────────────────────────────────────────────
Write-Host "`n[1/7] Syntax Check..."
$syntaxErrors = 0
foreach ($file in $allFiles) {
    $result = python -m py_compile $file 2>&1
    if ($LASTEXITCODE -ne 0) { $syntaxErrors++ }
}
if ($syntaxErrors -eq 0) { 
    Write-Host "  [OK] All $($allFiles.Count) files passed" -ForegroundColor Green 
    $report.layers["syntax"] = @{ status = "pass"; files = $allFiles.Count }
}
else { 
    $errors += "Syntax"
    Write-Host "  [FAIL] $syntaxErrors files with syntax errors" -ForegroundColor Red 
    $report.layers["syntax"] = @{ status = "fail"; errors = $syntaxErrors }
}

# ──────────────────────────────────────────────────────────────
# Layer 2: Lint Check (Fixed --select syntax)
# ──────────────────────────────────────────────────────────────
Write-Host "[2/7] Lint Check (ruff)..."
$ruffOutput = ruff check app/ core/ --select=F401, F821, F841 --statistics 2>&1 | Out-String
if ($ruffOutput -match "Found 0 errors") { 
    Write-Host "  [OK] No critical lint errors" -ForegroundColor Green
    $report.layers["lint"] = @{ status = "pass" }
}
elseif ($LASTEXITCODE -eq 0) { 
    Write-Host "  [OK] Lint passed" -ForegroundColor Green
    $report.layers["lint"] = @{ status = "pass" }
}
else { 
    Write-Host "  [WARN] Lint issues found (run: ruff check --fix)" -ForegroundColor Yellow
    $report.layers["lint"] = @{ status = "warn" }
}

# ──────────────────────────────────────────────────────────────
# Layer 3: Type Check (mypy) - All files
# ──────────────────────────────────────────────────────────────
Write-Host "[3/7] Type Check (mypy)..."
$mypyOutput = mypy app/ui/ core/ --ignore-missing-imports --no-error-summary 2>&1 | Out-String
$mypyErrors = ($mypyOutput | Select-String "error:" -AllMatches).Matches.Count
if ($mypyErrors -gt 0) { 
    $errors += "Mypy"
    Write-Host "  [FAIL] $mypyErrors type errors" -ForegroundColor Red
    $report.layers["mypy"] = @{ status = "fail"; errors = $mypyErrors }
}
else { 
    Write-Host "  [OK] Type check passed" -ForegroundColor Green
    $report.layers["mypy"] = @{ status = "pass" }
}

# ──────────────────────────────────────────────────────────────
# Layer 3.5: IQDS AST Scan
# ──────────────────────────────────────────────────────────────
Write-Host "[3.5/7] IQDS Semantic Scan..."
$iqdsArgs = "scripts/iqds_ast_scanner.py app/ core/"
if ($Strict) { $iqdsArgs += " --strict" }
$iqdsArgs += " --json .iqds_report.json"

$iqdsOutput = python $iqdsArgs.Split() 2>&1
if ($LASTEXITCODE -eq 0) { 
    Write-Host "  [OK] No critical semantic issues" -ForegroundColor Green
    $report.layers["iqds"] = @{ status = "pass" }
}
else { 
    $errors += "IQDS"
    Write-Host "  [FAIL] Critical semantic issues found" -ForegroundColor Red
    $report.layers["iqds"] = @{ status = "fail" }
}

# ──────────────────────────────────────────────────────────────
# Layer 4: Import Verification
# ──────────────────────────────────────────────────────────────
Write-Host "[4/7] Import Check..."
$importTest = @"
from app.ui.main_window import MainWindow
from app.ui.unified_studio import UnifiedStudio
from core.models import Click, TypeText, Hotkey, Action
from core.recorder import EventRecorder
print('OK')
"@
$result = python -c $importTest 2>&1
if ($result -match "OK") { 
    Write-Host "  [OK] Core imports verified" -ForegroundColor Green
    $report.layers["imports"] = @{ status = "pass" }
}
else { 
    $errors += "Import"
    Write-Host "  [FAIL] Import errors detected" -ForegroundColor Red
    $report.layers["imports"] = @{ status = "fail" }
}

# ──────────────────────────────────────────────────────────────
# Layer 5-6: Unit/Integration Tests
# ──────────────────────────────────────────────────────────────
if (-not $Quick) {
    Write-Host "[5/7] Unit Tests..."
    if (Test-Path "tests/") {
        $pytestOutput = pytest tests/ -v --tb=short 2>&1
        if ($LASTEXITCODE -eq 0) { 
            Write-Host "  [OK] Tests passed" -ForegroundColor Green
            $report.layers["tests"] = @{ status = "pass" }
        }
        else { 
            $errors += "Tests"
            Write-Host "  [FAIL] Tests failed" -ForegroundColor Red
            $report.layers["tests"] = @{ status = "fail" }
        }
    }
    else {
        Write-Host "  [SKIP] No tests/ directory" -ForegroundColor DarkGray
    }
    
    Write-Host "[6/7] Integration Tests..."
    Write-Host "  [SKIP] Manual verification required" -ForegroundColor DarkGray
}
else {
    Write-Host "[5-6/7] Tests..." 
    Write-Host "  [SKIP] Quick mode (-Quick)" -ForegroundColor DarkGray
}

# ──────────────────────────────────────────────────────────────
# Layer 7: Runtime Smoke Test
# ──────────────────────────────────────────────────────────────
Write-Host "[7/7] Smoke Test..."
$smokeTest = @"
import sys
sys.argv = ['test']
from PySide6.QtWidgets import QApplication
app = QApplication.instance() or QApplication(sys.argv)

# Test widget instantiation
from app.ui.main_window import MainWindow
mw = MainWindow()

# Test action models
from core.models import Click, TypeText
c = Click(x=100, y=200)
t = TypeText(text='test')

# Test recorder
from core.recorder import EventRecorder
r = EventRecorder(capture_screenshots=False)

print('OK')
"@
$result = python -c $smokeTest 2>&1
if ($result -match "OK") { 
    Write-Host "  [OK] Runtime smoke passed" -ForegroundColor Green
    $report.layers["smoke"] = @{ status = "pass" }
}
else { 
    $errors += "Smoke"
    Write-Host "  [FAIL] Runtime crash detected" -ForegroundColor Red
    $report.layers["smoke"] = @{ status = "fail" }
}

# ──────────────────────────────────────────────────────────────
# Summary
# ──────────────────────────────────────────────────────────────
$duration = (Get-Date) - $startTime
$report.duration = $duration.TotalSeconds
$report.errors = $errors

Write-Host "`n=== SUMMARY ===" -ForegroundColor Cyan
Write-Host "Duration: $($duration.TotalSeconds.ToString('0.00'))s | Files: $($allFiles.Count)" -ForegroundColor DarkGray

if ($errors.Count -eq 0) {
    Write-Host "[OK] ALL CHECKS PASSED" -ForegroundColor Green
    $exitCode = 0
}
else {
    Write-Host "[X] FAILED: $($errors -join ', ')" -ForegroundColor Red
    $exitCode = 1
}

# Save JSON report
$report | ConvertTo-Json -Depth 4 | Out-File ".bug_scan_report.json" -Encoding UTF8
Write-Host "Report saved: .bug_scan_report.json" -ForegroundColor DarkGray

exit $exitCode
