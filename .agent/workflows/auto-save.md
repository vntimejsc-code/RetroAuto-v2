---
description: Auto-save code changes with version bump and git commit
---

# Auto-Save Workflow (Cho AI Agent)

**QUAN TRỌNG:** Sau mỗi khi hoàn thành thay đổi code, AI Agent PHẢI thực hiện các bước sau:

## Bước 1: Check Code
```bash
// turbo
python check_code.py
```

## Bước 2: Bump Build Version
```bash
// turbo
python -c "from infra.version import bump_build; bump_build()"
```

## Bước 3: Commit với Mô tả
```bash
// turbo
git add -A && git commit -m "[$(Get-Date -Format 'yyyyMMdd_HHmmss')] Mô tả thay đổi"
```

## Quick Save (One-liner)
```bash
// turbo-all
python check_code.py; if ($?) { python -c "from infra.version import bump_build; bump_build()"; git add -A; git commit -m "[$(Get-Date -Format 'yyyyMMdd_HHmmss')] Mô tả thay đổi" }
```

## Rollback
```bash
git log --oneline -10    # Xem lịch sử
git reset --hard <hash>  # Rollback về commit cũ
```

## Lưu ý cho AI Agent
- **SAU MỖI LẦN EDIT CODE**: Chạy workflow này
- **SAU MỖI LẦN THÊM FILE MỚI**: git add -A trước
- **COMMIT MESSAGE**: Phải mô tả rõ ràng thay đổi
