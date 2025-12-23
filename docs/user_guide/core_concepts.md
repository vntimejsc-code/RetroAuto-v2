# Part 2: The Core (Nguyên Lý Cốt Lõi) 🧠
> *Hiểu sâu để làm chủ.*

Để viết được script ổn định, bạn cần hiểu cách RetroAuto "nhìn" và "nghĩ".

---

## 2.1 The Execution Model (Cơ chế hoạt động)

RetroAuto không chạy mọi thứ cùng lúc. Nó có một "nhịp tim" (Event Loop) xử lý công việc theo thứ tự.

### Synchronous vs Asynchronous (Tuần tự vs Song song)

#### 1. Main Thread (Tuần tự - Synchronous)
Đây là luồng chính nơi `script` của bạn chạy. Lệnh này xong mới đến lệnh kia.
- **Ví dụ:** `click`, `wait_image`, `sleep`.
- **Đặc điểm:** Nếu bạn dùng `wait_image(timeout=infinite)`, bot sẽ **đứng yên mãi mãi** cho đến khi ảnh xuất hiện. Đây là hành vi "Blocking".

#### 2. Interrupts (Song song - Asynchronous)
Đây là "giác quan thứ 6" của bot. Nó chạy song song với Main Thread.
- **Cơ chế:** Cứ mỗi `500ms` (mặc định), hệ thống sẽ quét màn hình một lần để tìm các ảnh trong danh sách Rules.
- **Priority (Độ ưu tiên):** Nếu tìm thấy ảnh Interrupt (ví dụ: màn hình Login), bot sẽ:
    1.  **PAUSE** script chính ngay lập tức.
    2.  Chạy Action/Flow của Interrupt (ví dụ: Đăng nhập lại).
    3.  **RESUME** script chính từ điểm bị dừng.

> 📐 **Diagram: Interrupt Cycle**
> ```
> [Main Script] ---> Click ---> Wait ---> [PAUSED] ................... [RESUME] ---> Click...
>                                           ⬇                             ⬆
> [Interrupt Monitor] ----------------> [Detect Login] --> [Run LoginFlow] ⤴
> ```

---

## 2.2 The Coordinate System (Hệ tọa độ) 🗺️

RetroAuto sử dụng hệ tọa độ pixel của màn hình Windows.

### Global Coordinates (Tọa độ toàn cục)
- **Gốc (0, 0):** Góc trên cùng bên trái của màn hình chính.
- **X:** Tăng dần sang phải.
- **Y:** Tăng dần xuống dưới.

> ⚠️ **Lưu ý Multi-monitor:** Màn hình phụ có thể có tọa độ âm. Hãy luôn dùng công cụ **Capture Tool** (F2) hoặc **Cursor Info** để lấy tọa độ chính xác.

### ROI (Region of Interest - Vùng quan tâm)
Tìm kiếm trên toàn màn hình (1920x1080) rất chậm và dễ sai. Hãy dùng ROI để giới hạn vùng tìm kiếm.

- **Ví dụ:** Chỉ tìm thanh máu ở góc trái trên.
- **Lợi ích:**
    1.  **Tốc độ:** Nhanh gấp 5-10 lần.
    2.  **Chính xác:** Tránh nhận diện nhầm icon giống nhau ở chỗ khác.

---

## 2.3 Assets & Recognition (Nhận diện hình ảnh) 👁️

### Template Matching (Khớp mẫu)
RetroAuto dùng thuật toán OpenCV để trượt ảnh mẫu (`template`) trên màn hình (`source`).

### Threshold (Độ tương đồng)
Kết quả khớp trả về một con số từ `0.0` đến `1.0`.
- **1.0:** Giống tuyệt đối.
- **0.9:** Rất giống (Chấp nhận được).
- **0.7:** Khá giống (Mặc định).
- **< 0.5:** Không giống.

> 💡 **Best Practice:**
> - Icon tĩnh, nét: `0.9`
> - Hình trong game 3D (ánh sáng đổi): `0.7 - 0.8`
> - Văn bản (nếu không dùng OCR): `0.8`

### Grayscale vs Color
- **Mặc định:** RetroAuto so sánh ở chế độ **Grayscale** (Đen trắng) để tối ưu tốc độ.
- **Use Color:** Nếu bạn cần phân biệt 2 bình máu giống hệt nhau về hình dạng nhưng khác màu (Đỏ vs Xanh), hãy bật `match_color=true` (Tính năng nâng cao).

---

> 👉 **Tiếp theo:** [Part 4: The Tools](./tools_mastery.md) - Làm chủ công cụ IDE và GUI.
