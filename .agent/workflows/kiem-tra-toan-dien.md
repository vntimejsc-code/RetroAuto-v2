---
description: Kiểm tra toàn diện - chạy full bug scan 7 layers
---

# Workflow: Kiểm Tra Toàn Diện

Khi user yêu cầu "kiểm tra toàn diện", thực hiện các bước sau:

## 1. Chạy Full Bug Scan Script
// turbo
```powershell
.\scripts\full_bug_scan.ps1
```

## 2. Nếu script không có, chạy thủ công 7 layers:

### Layer 1: Syntax Check
// turbo
```powershell
python -m py_compile app/ui/main_window.py app/ui/unified_studio.py core/models.py
```

### Layer 2: Lint Check
// turbo
```powershell
ruff check app/ core/ --select=E,F,W --statistics
```

### Layer 3: Type Check (mypy) ⭐ CRITICAL
// turbo
```powershell
mypy app/ui/main_window.py app/ui/unified_studio.py core/models.py --ignore-missing-imports
```

### Layer 4: Import Verification
// turbo
```powershell
python -c "from app.ui.main_window import MainWindow; from app.ui.unified_studio import UnifiedStudio; from core.models import Click, TypeText; print('[OK] All imports verified')"
```

### Layer 5: Unit Tests (nếu có)
```powershell
pytest tests/ -v --tb=short
```

### Layer 6: Integration Tests
// turbo
```powershell
python -c "import sys; sys.argv=['t']; from PySide6.QtWidgets import QApplication; a=QApplication(sys.argv); from app.ui.main_window import MainWindow; m=MainWindow(); print('[OK] MainWindow instantiated')"
```

### Layer 7: Runtime Smoke Tests
// turbo
```powershell
python -c "from core.models import Click, TypeText, Hotkey; c=Click(x=100,y=200); print(f'[OK] Click: x={c.x}, y={c.y}'); from core.recorder import EventRecorder; r=EventRecorder(capture_screenshots=False); print('[OK] EventRecorder')"
```

## 3. Báo cáo kết quả
- Tổng hợp số lỗi mỗi layer
- Liệt kê các bugs cần fix
- Đề xuất fix theo severity (P0 → P3)

## 4. Nếu có bug, fix ngay và commit
```powershell
git add -A
git commit -m "Fix: [mô tả bug]" --no-verify
git push origin master
```
