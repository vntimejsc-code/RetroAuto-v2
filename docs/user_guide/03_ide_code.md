# Part 3: Code & Debugging Manual (Lập Trình & Gỡ Lỗi)
> *Dành cho Developer: Viết code nhanh, sửa lỗi siêu tốc.*

---

## 3.1 The Code Editor (Trình Soạn Thảo)

### Intellisense (Gợi ý thông minh)
- **Kích hoạt:** `Ctrl + Space`
- **Chức năng:**
  - Gợi ý lệnh: Gõ `cl` => `click`, `click_image`.
  - Gợi ý Asset: Gõ `"` => Danh sách ID từ Assets Panel.
  - Signature Help: Gõ `(` => Hiện tham số `(x, y, button, ...)`

### Minimap (Bản đồ Code)
Dải bên phải hiển thị tổng quan logic.
- **Màu Xanh:** Flow definitions (`@main`).
- **Màu Tím:** Logic loops (`loop`, `if`).
- **Thao tác:** Click để cuộn nhanh.

---

## 3.2 The Debugger (Trình Gỡ Lỗi) 🐞
*Tính năng cao cấp giúp bạn "soi" từng dòng code.*

### Giao diện Debug Panel
Nằm ở dưới cùng (hoặc tab bên phải):

| Tab | Chức năng |
|-----|-----------|
| **Call Stack** | Xem bot đang chạy ở Flow nào, dòng nào. |
| **Variables** | Xem giá trị biến (`$hp`, `$count`) theo thời gian thực. |
| **Breakpoints** | Quản lý các điểm dừng. |

### Các Lệnh Điều Khiển (Debug Controls)

| Icon | Lệnh | Phím tắt | Mô tả |
| :---: | :--- | :--- | :--- |
| ▶ | **Continue** | F5 | Chạy tiếp cho đến breakpoint tiếp theo. |
| ⏸ | **Pause** | F6 | Tạm dừng bot ngay lập tức. |
| ⤵ | **Step Over** | F10 | Chạy 1 dòng lệnh tiếp theo (Không chui vào Flow con). |
| ↴ | **Step Into** | F11 | Chui vào bên trong Flow/Hàm đang gọi. |
| ↱ | **Step Out** | Shift+F11 | Chạy cho đến khi thoát khỏi Flow hiện tại. |
| ■ | **Stop** | F8 | Dừng hẳn chương trình. |

### Cách Debug Hiệu Quả

#### 1. Đặt Breakpoint (Điểm dừng)
- **Cách làm:** Click vào lề trái (số dòng) trong Code Editor -> Xuất hiện chấm đỏ 🔴.
- **Tác dụng:** Khi chạy đến dòng này, bot sẽ tự động Pause.

#### 2. Soi Biến (Variables Watch)
- Khi bot đang Pause, chuyển sang tab **Variables**.
- Bạn sẽ thấy giá trị hiện tại của mọi biến.
- **Watch:** Nhập tên biến (vd: `$hp`) vào ô Watch để theo dõi riêng nó.

#### 3. Stack Trace
- Khi bot Pause trong một Flow con, **Call Stack** cho biết ai đã gọi nó.
- **Ví dụ:** `Main > Loop > AttackFlow > UseSkill`.

---

## 3.3 Output & Diagnostics (Nhật ký & Chẩn đoán)

### Output Log
Hiển thị lịch sử chạy của bot.
- **Màu sắc:**
  - ⚫ Info: Sự kiện thường.
  - 🟡 Warning: Tìm ảnh độ khớp thấp.
  - 🔴 Error: Lỗi logic.

### Problems Tab
Danh sách lỗi cú pháp (Syntax Errors) và cảnh báo (Warnings).
- Click đúp vào lỗi để nhảy đến dòng code bị sai.
