# Part 1: The Launchpad (Bệ phóng) 🚀
> *Từ Zero đến Hero trong 30 phút*

---

## 1.1 Prerequisites & Environment (Tiền điều kiện)

Trước khi cài đặt RetroAuto, hãy đảm bảo môi trường Windows của bạn đã được cấu hình đúng. **60% lỗi "Image not found"** đến từ việc bỏ qua bước này.

### ✅ Checklist Bắt buộc

| # | Mục | Cách kiểm tra | Tại sao quan trọng? |
|---|-----|---------------|---------------------|
| 1 | **DPI Scaling = 100%** | Settings → Display → Scale = 100% | Pixel coordinates bị lệch nếu scale khác 100% |
| 2 | **Admin Rights** | Chuột phải → "Run as Administrator" | Một số game chặn input từ app không có quyền Admin |
| 3 | **Borderless Windowed** | Trong game: Settings → Display → Borderless | Fullscreen chặn screenshot/input từ bên ngoài |
| 4 | **Night Light OFF** | Settings → Display → Night Light = Off | Màu sắc bị biến đổi làm hỏng image matching |

### 🖥️ Multi-Monitor Setup

Nếu bạn có nhiều màn hình:
- **Tọa độ (0, 0):** Luôn ở góc trên-trái của màn hình CHÍNH (Primary).
- **Màn hình phụ:** Có thể có tọa độ âm (ví dụ: `-1920, 0` nếu nằm bên trái).
- **Khuyến nghị:** Chạy game trên màn hình chính để tránh rắc rối.

### ⚡ Power Settings

Nếu bạn chạy bot qua đêm:
```
Settings → Power & Sleep → Screen: Never | Sleep: Never
```
Hoặc: Download công cụ "Caffeine" để giữ máy tỉnh.

---

## 1.2 Quickstart: "The 5-Minute Bot" ⏱️

> **Goal:** Viết bot tự động search Google trong 5 phút.
> **Yêu cầu:** Đã cài Python 3.11+, pip.

### Bước 1: Cài đặt (2 phút)

```powershell
# Clone hoặc download RetroAuto
cd C:\Auto\Newauto

# Cài dependencies
pip install -r requirements.txt
```

### Bước 2: Chạy App (30 giây)

```powershell
python -m app.main
```

Cửa sổ RetroAuto sẽ hiện ra với 3 panel: **Assets | Actions | Properties**.

### Bước 3: Tạo Script đầu tiên (2 phút)

1. **Thêm Action "Click":**
   - Bấm nút `+ Click` trên Quick Add Bar.
   - Trong Properties: Nhập `x=500, y=300` (vị trí search box của Google, bạn tự điều chỉnh).

2. **Thêm Action "TypeText":**
   - Bấm `+ Type`.
   - Trong Properties: `text="Hello RetroAuto"`, `enter=true`.

3. **Save & Run:**
   - `Ctrl+S` để lưu.
   - `F5` để chạy.

### 🎉 Kết quả

Nếu bạn đang mở trình duyệt với Google, con trỏ sẽ click vào ô search và gõ "Hello RetroAuto" + Enter.

**Chúc mừng! Bạn đã viết bot đầu tiên.** 🎊

---

## 1.3 Installation & Dependencies

### Yêu cầu hệ thống

| Component | Version | Ghi chú |
|-----------|---------|---------|
| OS | Windows 10/11 | Chưa hỗ trợ Linux/macOS |
| Python | 3.11+ | Khuyến nghị 3.12 |
| RAM | 4GB+ | 8GB nếu dùng OCR nặng |
| Tesseract | 5.x (Optional) | Cho tính năng OCR |

### Cài đặt chi tiết

```powershell
# 1. Clone repo
git clone https://github.com/your-repo/retroauto.git
cd retroauto

# 2. Tạo virtual environment (khuyến nghị)
python -m venv .venv
.venv\Scripts\activate

# 3. Cài dependencies
pip install -r requirements.txt

# 4. (Optional) Cài Tesseract cho OCR
# Download từ: https://github.com/UB-Mannheim/tesseract/wiki
# Cài vào: C:\Program Files\Tesseract-OCR
```

### Cấu trúc thư mục

```
retroauto/
├── app/            # UI code (PySide6)
├── core/           # Engine, DSL parser, Runner
├── infra/          # Logging, Crash handler
├── assets/         # Image templates (bạn lưu ở đây)
├── scripts/        # Saved scripts (.retro files)
└── docs/           # Tài liệu này
```

---

## 1.4 Interface Tour (Khám phá giao diện)

### Main Window (Cửa sổ chính)

```
┌─────────────────────────────────────────────────────────┐
│  [Toolbar: Run | Pause | Stop | Capture | IDE | Save]   │
├──────────┬─────────────────────────┬────────────────────┤
│  Assets  │       Actions           │    Properties      │
│  Panel   │       Panel             │    Panel           │
│          │                         │                    │
│ 📷 img1  │ 1. Click(100, 200)      │ Action: Click      │
│ 📷 img2  │ 2. WaitImage("img1")    │ x: [100]           │
│          │ 3. TypeText("Hello")    │ y: [200]           │
│          │                         │ button: [left ▼]   │
└──────────┴─────────────────────────┴────────────────────┘
```

- **Assets Panel (Trái):** Quản lý hình ảnh mẫu.
- **Actions Panel (Giữa):** Danh sách hành động (Flow).
- **Properties Panel (Phải):** Chỉnh sửa tham số action đang chọn.

### IDE Window (Cửa sổ Code)

Bấm nút **IDE** trên toolbar để mở chế độ viết code:

```
┌─────────────────────────────────────────────────────────┐
│  [Toolbar: Run | Save | Format]                         │
├──────────┬─────────────────────────────────────┬────────┤
│ Structure│         Code Editor                 │Minimap │
│ Panel    │                                     │        │
│          │ @main:                              │ ░░░░░░ │
│ ▶ @main  │     click(100, 200)                 │ ░░░    │
│ ▶ @heal  │     wait_image("btn_ok")            │ ░░░░   │
│          │     run_flow("heal")                │        │
└──────────┴─────────────────────────────────────┴────────┘
```

- **Structure Panel (Trái):** Outline của flows và labels.
- **Code Editor (Giữa):** Viết DSL với Intellisense.
- **Minimap (Phải):** Nhìn tổng quan code, click để nhảy.

---

> 👉 **Tiếp theo:** [Part 3: The Cookbook](./cookbook.md) - Học qua các bài thực hành thực tế.
