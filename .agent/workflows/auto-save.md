---
description: Auto-save code changes with version bump and git commit
---

# Auto-Save Workflow (Dành cho AI Agent)

**QUAN TRỌNG:** Sau mỗi khi hoàn thành thay đổi code, AI Agent PHẢI thực hiện các bước sau:

## Bước 1: Check Code
```powershell
// turbo
python check_code.py
```

## Bước 2: Bump Build Version  
```powershell
// turbo
python -c "from infra.version import bump_build; bump_build()"
```

## Bước 3: Commit với Mô tả
```powershell
// turbo
git add -A; git commit -m "[$(Get-Date -Format 'yyyyMMdd_HHmmss')] Mô tả thay đổi" --no-verify
```

## Quick Save (One-liner cho PowerShell)
```powershell
// turbo-all
python -c "from infra.version import bump_build; bump_build()"; git add -A; git commit -m "[$(Get-Date -Format 'yyyyMMdd_HHmmss')] Mô tả thay đổi" --no-verify
```

## Rollback
```powershell
git log --oneline -10    # Xem lịch sử
git reset --hard <hash>  # Rollback về commit cũ
```

## Lưu ý cho AI Agent
- **SAU MỖI LẦN EDIT CODE**: Chạy workflow này trước khi kết thúc task
- **COMMIT MESSAGE**: Phải mô tả rõ ràng thay đổi (tiếng Việt hoặc tiếng Anh)
- **BUILD VERSION**: Tự động tăng theo format: YYYYMMDD.NNN
