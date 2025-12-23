# RetroAuto v2 - IDE Tự Động Hóa Windows Đỉnh Cao
> **Version:** 2025.12 | **Build:** 20251223.021

![RetroAuto Banner](https://via.placeholder.com/800x200?text=RetroAuto+v2+-+Visual+Automation+IDE)

**RetroAuto** là bộ công cụ automation chuyên nghiệp cho Windows, sở hữu **Visual IDE** kéo thả, công nghệ **Anti-Ban** mạnh mẽ (Human Mouse), và ngôn ngữ **RetroScript** (Python-like) được thiết kế cho sự ổn định và dễ sử dụng.

---

## 📚 Tài Liệu (Bách Khoa Toàn Thư v5.0)

Bộ User Guide v5.0 đầy đủ đã có sẵn:
# 👉 **[ĐỌC FULL USER GUIDE TẠI ĐÂY](./docs/user_guide/01_start.md)**

- **[Phần 1: Bệ Phóng (The Launchpad)](./docs/user_guide/01_start.md)** (Cài đặt & Giao diện)
- **[Phần 2: Visual IDE Manual](./docs/user_guide/02_ide_visual.md)** (Hướng dẫn công cụ Kéo-Thả)
- **[Phần 3: Code & Debug Manual](./docs/user_guide/03_ide_code.md)** (Lập trình & Gỡ lỗi)
- **[Phần 5: The Cookbook](./docs/user_guide/05_cookbook.md)** (Bài mẫu: Auto-Login, Farm quái)
- **[Phần 7: Reference Manual](./docs/user_guide/07_reference.md)** (Từ điển Lệnh)

> 🖨️ **Bản In:** [Tải file HTML (Save as PDF)](./docs/RetroAuto_UserGuide_v5.html)
> 🤖 **Cho AI Agents:** Dùng file `[docs/llms.txt](./docs/llms.txt)` hoặc `[docs/full_user_guide.md](./docs/full_user_guide.md)`.

---

## ✨ Tính Năng Nổi Bật

### 🖱️ Human Mouse (Anti-Ban)
Thay thế click chuột robot bằng đường cong Bezier, gia tốc Fitts' Law và rung ngẫu nhiên (micro-jitter).
- `click_random(ROI)`: Không bao giờ click vào cùng 1 tọa độ pixel 2 lần.
- `drag(x1, y1, x2, y2)`: Thao tác vuốt/kéo thả như người thật.

### 🧠 Smart Vision (Hawk Eye)
- **Template Matching:** Nhận diện ảnh ổn định với chế độ xám/màu.
- **Tích hợp OCR:** Đọc chỉ số (HP, MP, Vàng) dùng Tesseract.
- **Global Interrupts:** Logic sự kiện (vd: Tự đăng nhập lại) chạy song song ngầm.

### 🎨 Visual IDE
- **Dual Mode:** Chuyển đổi tức thì giữa GUI Kéo-Thả và Code Editor.
- **Intellisense:** Gợi ý lệnh và Asset ID thông minh.
- **Visual Extensions:** Minimap, Structure Panel, và ROI Editor.

---

## 🛠️ Bắt Đầu Nhanh

### 1. Yêu cầu
- Windows 10/11
- Python 3.11+
- [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki) (Tùy chọn)

### 2. Cài đặt
```powershell
git clone https://github.com/vntimejsc-code/RetroAuto-v2.git
cd RetroAuto-v2
pip install -r requirements.txt
```

### 3. Chạy IDE
```powershell
python -m app.main
```

---

## 💻 Code Example (RetroScript)

**Old syntax (Deprecated):** `{ click(10,10); }`
**New Syntax (v2 - Python-like):**

```retroscript
@main:
    # Human-like interaction
    if_image("login_btn"):
        delay_random(500, 1000)
        click_image("login_btn")

    # Logic Loop
    loop 10:
        run_flow("AttackPattern")

        # Check HP using OCR
        read_text("$hp", region=[10, 10, 50, 20])
        if_text("$hp", "<", "30"):
            hotkey("F1") # Heal
            notify("Low HP! Healing...", method="telegram")
```

---

## 🤝 Contributing

We welcome contributions! Please see the `docs/` folder for architectural details (`core_concepts.md`) before submitting PRs.

**License:** MIT
**Maintainer:** VNTimeJSC Code Team
