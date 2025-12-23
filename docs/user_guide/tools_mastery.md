# Part 4: The Tools (Làm Chủ Công Cụ) 🛠️
> *Thợ giỏi nhờ đồ nghề. Hướng dẫn chi tiết 100% các bảng điều khiển.*

RetroAuto cung cấp 2 chế độ làm việc: **GUI Mode** (Kéo thả) và **IDE Mode** (Viết code).

---

## 4.1 GUI Mode Mastery (Chế Độ Đồ Họa)

### 1. The 3-Panel Layout (Bố cục 3 Bảng)

#### A. Assets Panel (Trái - Tài nguyên)
Nơi quản lý "đôi mắt" của bot - các hình ảnh mẫu.
- **Import:** Kéo thả file ảnh `.png` từ Windows Explorer vào đây.
- **Capture (F2):** Bấm nút máy ảnh hoặc `F2` để cắt ảnh trực tiếp từ màn hình.
- **Context Menu (Chuột phải):**
    - `Rename`: Đổi tên ID (Lưu ý: Tên ID dùng trong code).
    - `Delete`: Xóa ảnh (Cảnh báo: Nếu code đang dùng ảnh này sẽ bị lỗi).
    - `Copy Path`: Lấy đường dẫn file.

#### B. Actions Panel (Giữa - Kịch bản)
Trái tim của Automation. Chứa danh sách các bước thực hiện.

**Action Categories (Phân loại):**
1.  **🎯 Clicks & Mouse:** `Click`, `ClickImage`, `Drag`, `Scroll`...
2.  **👁️ Vision & Wait:** `WaitImage`, `IfImage`, `WhileImage`, `ReadText`...
3.  **⌨️ Keyboard:** `TypeText`, `Hotkey`.
4.  **⏱️ Timing:** `Delay`, `DelayRandom`.
5.  **🔄 Flow Control:** `Loop`, `Label`, `Goto`, `RunFlow`.
6.  **📡 Notify:** `Notify` (Popup/Telegram).

**Thao tác:**
- **Thêm Action:** Dùng **Quick Add Bar** ở trên cùng hoặc kéo thả từ menu.
- **Sắp xếp:** Kéo thả (Drag & Drop) để đổi thứ tự.
- **Disable:** Chuột phải -> `Disable` để tạm tắt 1 dòng lệnh (Sẽ hiện màu xám).
- **Clone:** Chuột phải -> `Duplicate` để nhân bản.

#### C. Properties Panel (Phải - Tham số)
Chỉnh sửa chi tiết cho Action đang chọn.
- **Dynamic Fields:** Ô nhập liệu thay đổi theo loại Action.
    - `Click`: Có ô `x`, `y`, `button`.
    - `WaitImage`: Có ô `asset_id`, `timeout`.
- **Validation:** Viền đỏ nếu nhập sai (ví dụ: nhập chữ vào ô số).

---

## 4.2 IDE Mode Mastery (Chế Độ Code)

Bấm nút **IDE** trên Toolbar để chuyển sang giao diện lập trình.

### 1. Structure Panel (Cấu trúc)
Cột bên trái hiển thị outline của script.
- **▶ @Flows:** Danh sách các hàm (Function).
- **🏷️ #Labels:** Các điểm neo (Marker) để `goto`.
- **Double-click:** Để nhảy ngay đến dòng code đó.

### 2. The Code Editor (Soạn thảo)
Trình soạn thảo RetroScript mạnh mẽ với hỗ trợ:

- **Intellisense (Gợi ý):**
    - Gõ `c` -> Gợi ý `click`, `click_image`.
    - Gõ `"` -> Gợi ý danh sách ảnh (`"btn_ok"`, `"icon_hp"`).
    - Phím tắt: `Ctrl+Space`.

- **Signature Help (Nhắc tham số):**
    - Gõ `click(` -> Tooltip hiện: `x: int, y: int, button: str`.

- **Syntax Highlighting:**
    - **Xanh dương:** Lệnh (Verb).
    - **Cam:** Chuỗi/ID.
    - **Tím:** Số.
    - **Xám:** Comment (`#`).

### 3. Minimap (Bản đồ)
Dải bên phải giúp nhìn tổng quan code dài.
- **Màu sắc:** Phân biệt các khối lệnh `Loop`, `If`.
- **Click:** Cuộn nhanh đến vị trí.

---

## 🛑 Keyboard Shortcuts (Phím Tắt Toàn Tập)

| Phím (Global) | Chức năng | Hành vi |
|---------------|-----------|---------|
| **F5** | Run Script | Chạy script hiện tại từ đầu (Main Flow) |
| **F6** | Pause/Resume | Tạm dừng bot để check, bấm lại để chạy tiếp |
| **F8** | **STOP (Khẩn cấp)** | Dừng mọi hoạt động ngay lập tức (Kill Switch) |
| **F2** | Capture Tool | Mở công cụ chụp màn hình |

| Phím (Editor) | Chức năng |
|---------------|-----------|
| **Ctrl+S** | Lưu Script |
| **Ctrl+Space** | Gợi ý code (Autocompletion) |
| **Ctrl+Shift+Space** | Xem tham số hàm (Signature Help) |
| **Ctrl+/** | Comment/Uncomment dòng |
| **Ctrl+Z** | Undo (Hoàn tác) |
| **Ctrl+Y** | Redo (Làm lại) |
