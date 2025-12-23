# Part 2: Visual IDE Manual (Giao Diện Đồ Họa)
> *Dành cho Operator & Non-Coder: Kéo thả để tự động hóa.*

---

## 2.1 The Workbench (Bàn Làm Việc)

Giao diện RetroAuto chia làm 3 cột chính:

### 1. Assets Panel (Kho Tài Nguyên) - Cột Trái
Quản lý "đôi mắt" của bot.
*   **Import:** Kéo file ảnh `.png` vào đây.
*   **Capture Tool (F2):** Cắt ảnh trực tiếp từ game.
*   **Chuột phải:** Rename, Delete, Copy Path.

### 2. Actions Panel (Kịch Bản) - Cột Giữa
Danh sách lệnh thực thi tuần tự.
*   **Kéo thả:** Thay đổi thứ tự lệnh.
*   **Disable:** Tắt tạm thời một lệnh (Chuột phải -> Disable).
*   **Group:** (Sắp ra mắt) Gom nhóm lệnh.

### 3. Properties Panel (Chi Tiết) - Cột Phải
Chỉnh sửa tham số từng lệnh.
*   **Click Action:** Tọa độ `x, y`, nút `left/right`.
*   **Wait Action:** `Asset ID`, `Timeout` (ms).
*   **Logic:** `Condition`, `Jump Label`.

---

## 2.2 Common Workflows

### Tạo Script mới
1. Mở App -> File -> New Script.
2. Bấm `F2` để cắt ảnh các nút trong game (Button Start, Button Login).
3. Đặt tên gợi nhớ cho ảnh (vd: `btn_start`, `btn_login`).
4. Kéo lệnh `ClickImage` từ toolbar vào Actions Panel.
5. Chọn `btn_start` trong Properties.
6. Bấm `F5` chạy thử.

### Chỉnh sửa tọa độ
Nếu không muốn tìm ảnh, bạn có thể click theo tọa độ cứng (không khuyến khích).
1. Dùng Action `Click`.
2. Bấm nút "Pick" (hình ống hút) trong Properties.
3. Click vào điểm trên màn hình để lấy tọa độ `x, y`.
