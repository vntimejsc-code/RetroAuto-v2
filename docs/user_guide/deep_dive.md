# Part 5: Deep Dive (Chuyên Sâu) 🔬
> *Vượt qua giới hạn cơ bản.*

---

## 5.1 Hawk Eye OCR System (Hệ thống đọc chữ)
Ngoài việc nhìn hình ảnh, RetroAuto có thể "đọc" chữ số (máu, vàng, tên nhân vật).

### Cấu hình Tesseract
Để dùng OCR, bạn cần chỉ định đường dẫn Tesseract trong `Settings` hoặc code:
```retroscript
# Cấu hình OCR engine
ocr_config(lang="eng", psm=7, whitelist="0123456789/")
```
- **psm (Page Segmentation Mode):**
    - `7`: Coi ảnh là một dòng văn bản đơn (Tốt nhất cho thanh máu/tên).
    - `3`: Tự động nhận diện (Mặc định).
- **whitelist:** Chỉ cho phép đọc các ký tự này (Giúp tránh đọc nhầm `O` thành `0`).

### Text Logic
```retroscript
# Đọc % máu tại vùng [100, 100, 50, 20]
read_text("$hp_str", region=[100, 100, 50, 20])

# So sánh logic
if_text("$hp_str", "<", "50"):
    hotkey("F1")
```

---

## 5.2 Human Mouse (Anti-Ban Tech) 🕵️
Game Master (GM) phát hiện bot bằng cách nào? Họ xem log di chuyển chuột.
- ❌ **Robotic:** Di chuyển thẳng tắp, tốc độ không đổi -> **BAN**.
- ✅ **Human:** Đường cong Bezier, tốc độ thay đổi (nhanh ở giữa, chậm dần khi đến đích), run tay (jitter).

### Cách sử dụng
RetroAuto mặc định kích hoạt Human Mouse cho lệnh `move()` và `drag()`.
```retroscript
# Tự động sinh đường cong ngẫu nhiên
click(500, 500) 

# Tùy chỉnh độ "người"
mouse_config(speed_min=0.5, speed_max=1.0, deviation=5)
```

---

## 5.3 Global Interrupts Architecture
Một script RetroAuto thực chất chạy **2 luồng song song**:

1.  **Main Flow:** Logic chính (Farm quái). Chạy tuần tự.
2.  **Interrupt Sentinel:** Lính canh. Chạy ngầm mỗi 500ms.

### Priority System (Hệ thống ưu tiên)
Điều gì xảy ra nếu vừa thấy "Máu thấp" (P10) vừa thấy "Túi đầy" (P5)?
-> **P10 thắng.** Script sẽ chạy Flow bơm máu trước.

### Cooldown (Hồi chiêu)
Để tránh việc bot bấm hồi máu liên tục 100 lần/giây, mỗi Interrupt Rule có `cooldown`.
- Ví dụ: `Reconnect` có cooldown `60s`. Nếu vừa reconnect xong mà lại thấy nút login, bot sẽ đợi hết 60s mới bấm tiếp.

---

> 👉 **Tiếp theo:** [Part 6: Troubleshooting](./troubleshooting.md) - Sơ đồ chẩn đoán lỗi.
