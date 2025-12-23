# Part 7: Reference Manual (Từ Điển Lệnh) 📚
> *Tra cứu mọi chức năng. Không bỏ sót bất kỳ lệnh nào.*

Tài liệu này liệt kê đầy đủ 100% các lệnh được hỗ trợ trong RetroAuto v2, tương ứng với mã nguồn `tokens.py` và `actions_panel.py`.

---

## 7.1 🎯 Clicks & Mouse (Thao tác Chuột)

### `click(x, y, button="left", double=False)`
Click vào một tọa độ màn hình cố định.
- **x, y:** Tọa độ pixel (số nguyên).
- **button:** `"left"`, `"right"`, `"middle"`.
- **double:** `True` để double-click.

### `click_image(asset_id, button="left", timeout=0, double=False)`
Tìm ảnh và click vào tâm ảnh đó.
- **asset_id:** ID của tài nguyên (ví dụ: `"btn_ok"`).
- **timeout:** Thời gian chờ ảnh xuất hiện (giây). 0 = không chờ.
- **Ex:** `click_image("btn_start", timeout=5s)`

### `click_random(x1, y1, x2, y2)`
Click ngẫu nhiên trong vùng hình chữ nhật (Chống ban).
- **x1, y1:** Góc trên-trái.
- **x2, y2:** Góc dưới-phải.
- **Ex:** `click_random(100, 100, 200, 200)`

### `click_until(target_id, stop_id, max_clicks=10)`
Click liên tục vào `target_id` cho đến khi `stop_id` xuất hiện.
- **Ex:** `click_until("btn_next", "screen_page2")` (Click Next cho đến khi sang trang 2).

### `drag(x1, y1, x2, y2, duration=500)`
Kéo chuột từ A đến B (Swipe/Drop).
- **duration:** Thời gian kéo (ms).

### `scroll(dx, dy)`
Cuộn chuột.
- **dx:** Cuộn ngang (thường là 0).
- **dy:** Cuộn dọc. Dương = Lên, Âm = Xuống.
- **Ex:** `scroll(0, -500)` (Cuộn xuống dưới).

---

## 7.2 👁️ Vision & Wait (Thị giác)

### `wait_image(asset_id, timeout=infinite, appear=True)`
Dừng script cho đến khi ảnh xuất hiện (hoặc biến mất).
- **appear:** `True` (chờ hiện), `False` (chờ mất).
- **Ex:** `wait_image("loading_spinner", appear=False)` (Chờ loading xong).

### `wait_pixel(x, y, color, tolerance=10)`
Chờ một điểm pixel có màu cụ thể.
- **color:** Mã màu Hex (`#FF0000`) hoặc RGB tuple.

### `if_image(asset_id, region=None)`
Trả về `True` nếu ảnh có trên màn hình. Dùng trong khối `if`.
- **region:** `[x, y, w, h]` để giới hạn vùng tìm kiếm (Tăng tốc độ).

### `while_image(asset_id)`
Lặp lại khối lệnh MIỄN LÀ ảnh còn trên màn hình.
- **Ex:** `while_image("enemy"): attack()`

### `if_pixel(x, y, color)`
Giống `if_image` nhưng kiểm tra màu của 1 pixel.

### `read_text(variable, region)`
Đọc văn bản từ màn hình (OCR) và lưu vào biến.
- **variable:** Tên biến (vd: `"$hp"`).
- **region:** Vùng cần đọc `[x, y, w, h]`.
- **Ex:** `read_text("$gold", [10, 10, 100, 20])`

---

## 7.3 ⌨️ Keyboard & Input (Bàn phím)

### `type_text(text, interval=0, enter=False)`
Gõ văn bản như người dùng.
- **interval:** Độ trễ giữa các phím (ms).
- **enter:** Nhấn Enter cuối cùng.

### `hotkey(sequence)`
Gửi tổ hợp phím.
- **Ex:** `"Ctrl+C"`, `"Alt+F4"`, `"Win+R"`.

---

## 7.4 ⏱️ Timing & Delays (Thời gian)

### `delay(amount, random=False)` / `sleep()`
Dừng script.
- **amount:** `1s`, `500ms`.

### `delay_random(min_ms, max_ms)`
Dừng ngẫu nhiên (Quan trọng cho Anti-ban).

---

## 7.5 🔄 Flow Control (Điều khiển luồng)

### `if`, `elif`, `else`, `endif`
Cấu trúc rẽ nhánh điều kiện.
```retroscript
if_image("A"):
    click("A")
else:
    click("B")
```

### `loop n` / `endloop`
Lặp số lần cố định. `loop 0` hoặc không tham số = Lặp vô hạn.

### `run_flow(name)`
Gọi một Flow khác (Sub-routine).

### `goto(label)` / `label(name)`
Nhảy đến vị trí được đánh dấu.

### `if_text(variable, operator, value)`
So sánh giá trị văn bản/số.
- **operator:** `"=="`, `"!="`, `">"`, `"<"`, `"contains"`.
- **Ex:** `if_text("$hp", "<", 50)`

---

## 7.6 📡 Remote & Notify

### `notify(message, method="popup")`
Gửi thông báo.
- **method:** `"popup"` (Mặc định), `"telegram"`, `"discord"`, `"sound"`.

---

## 🧱 Cấu trúc DSL (Internal)

### Data Types
- **Integer:** `123`
- **Float:** `12.5`
- **String:** `"Hello"` (Trong ngoặc kép)
- **Duration:** `10s`, `500ms`
- **Boolean:** `true`, `false`

### Operators
- Arithmetic: `+`, `-`, `*`, `/`
- Comparison: `==`, `!=`, `<`, `>`
- Logic: `and`, `or`, `not`

> 💡 **Pro Tip:** Bạn có thể dùng biểu thức toán học trong tham số:
> `click(x + 10, y * 2)`
