---
description: Quy trình lưu thay đổi code với version và git
---

# Auto-Save Workflow

Mỗi khi thay đổi code, sử dụng một trong các cách sau:

## Quick Save (Lưu nhanh)

Cho các thay đổi nhỏ, không cần bump version:

```python
from infra.version import quick_save

quick_save("Sửa lỗi click button")
# -> Commit: [20241221_121500] Sửa lỗi click button
```

Hoặc chạy từ command line:
```bash
cd c:\Auto\Newauto
python -c "from infra.version import quick_save; quick_save('Mô tả thay đổi')"
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

- **Luôn quick_save() trước khi thử nghiệm code mới**
- Sử dụng `release()` khi hoàn thành feature
- Commit message nên rõ ràng, ngắn gọn
