---
description: Quy trình lưu thay đổi code với version và git
---

# Auto-Save Workflow

Mỗi khi thay đổi code, sử dụng một trong các cách sau:

## Quick Save (Lưu nhanh + Check code)

Cho các thay đổi nhỏ, tự động check code và commit:

```bash
cd c:\Auto\Newauto

# 1. Check code trước
python check_code.py

# 2. Nếu pass, commit
git add -A
git commit -m "[YYYYMMDD_HHMMSS] Mô tả thay đổi"
```

Hoặc chạy tất cả:
```bash
# // turbo
python check_code.py; if ($?) { git add -A; git commit -m "[$(Get-Date -Format 'yyyyMMdd_HHmmss')] Quick save" }
```

## Quick Save với Auto-fix

```bash
# Fix lỗi ruff tự động
python check_code.py --fix

# Commit sau khi fix
git add -A
git commit -m "[$(Get-Date -Format 'yyyyMMdd_HHmmss')] Fixed: Mô tả"
```

## Release (Phát hành version mới)

Cho các thay đổi lớn, cần bump version:

```python
from infra.version import release

release(
    changes=[
        "Thêm chức năng OCR",
        "Sửa lỗi capture overlay",
    ],
    bump="minor",  # major, minor, patch
    category="Added",  # Added, Changed, Fixed, Removed
)
# -> v2.1.0, cập nhật CHANGELOG.md, commit và tag
```

## Check Code Options

```bash
python check_code.py           # Quick check (stop on first failure)
python check_code.py --full    # Full check (run all tests)
python check_code.py --fix     # Auto-fix ruff issues
```

## Rollback

```bash
# Xem lịch sử
git log --oneline -10

# Rollback về commit cũ
git reset --hard <commit_hash>

# Xem các version đã tag
git tag -l

# Checkout version cụ thể
git checkout v2.0.0
```

## Lưu ý

- **Luôn check_code.py trước khi commit**
- Sử dụng `release()` khi hoàn thành feature
- Commit message nên rõ ràng, ngắn gọn
