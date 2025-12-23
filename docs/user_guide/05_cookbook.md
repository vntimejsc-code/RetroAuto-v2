# Part 3: The Cookbook (Món Ngon Thực Chiến) 🍳
> *Học qua hành động. Copy, Paste, và Chạy.*

Chào mừng bạn đến với "Căn bếp Automation". Tại đây, chúng ta sẽ không nói lý thuyết suông. Bạn sẽ học cách nấu những "món ăn" (script) phổ biến nhất mà bất kỳ pro-gamer hay operator nào cũng cần.

---

## 🥗 Recipe 1: The Login Guard (Hộ Vệ Đăng Nhập)
**Level:** 🟢 Dễ | **Time:** 5 phút | **Concept:** Interrupts (Sự kiện)

### Vấn đề
Game online hay bị disconnect (mất mạng) hoặc văng game khi treo máy đêm. Bạn muốn bot tự động đăng nhập lại khi thấy màn hình login.

### Nguyên liệu
1.  Ảnh `screen_login.png`: Màn hình đăng nhập.
2.  Ảnh `btn_start.png`: Nút "Vào game".
3.  Flow "LoginFlow": Chuỗi hành động để đăng nhập.

### Cách chế biến (Step-by-Step)

#### Bước 1: Tạo Flow Đăng Nhập (`LoginFlow`)
Vào `Flow Editor`, tạo một flow mới tên `LoginFlow`:

```retroscript
@LoginFlow:
    # 1. Chờ nút Start xuất hiện (phòng khi máy chậm)
    wait_image("btn_start", timeout=10s)

    # 2. Click vào nút Start
    click_image("btn_start")

    # 3. Chờ loading xong (Loading screen biến mất)
    wait_image("screen_loading", appear=false, timeout=60s)

    # 4. Thông báo đã vào lại game
    notify("Reconnected successfully!", method=popup)
```

#### Bước 2: Cài Đặt "Hộ Vệ" (Interrupt Rule)
Chúng ta không muốn viết lệnh `check_login` vào mọi nơi trong script chính (Farming). Hãy dùng tính năng **Interrupts** (Tương tự như phản xạ không điều kiện).

1.  Chuyển sang tab **⚡ Interrupts**.
2.  Bấm `Add Rule`.
3.  **Trigger Image:** Chọn `screen_login.png`.
4.  **Action:** Run Flow -> `LoginFlow`.
5.  **Priority:** `High (P10)` (Ưu tiên cao nhất, dừng mọi việc khác để login).
6.  **Cooldown:** `30s` (Để tránh spam login liên tục).

### 🎯 Kết quả
Bây giờ, dù bạn đang farm quái ở Flow nào, chỉ cần màn hình Login hiện ra, RetroAuto sẽ **ngay lập tức** tạm dừng việc farm, chạy `LoginFlow` để vào lại game, rồi tiếp tục farm.

---

## 🍲 Recipe 2: The Infinite Farming Loop (Vòng Lặp Vô Tận)
**Level:** 🟡 Trung Bình | **Time:** 10 phút | **Concept:** Logic & State

### Vấn đề
Bạn muốn nhân vật tự tìm quái, đánh quái, nhặt đồ. Khi máu thấp (< 50%) thì tự bơm máu. Khi túi đầy thì tự về thành bán đồ.

### Nguyên liệu
-   `monster.png`: Quái vật.
-   `hp_low.png`: Thanh máu khi cạn (màu đỏ nhạt).
-   `inventory_full.png`: Thông báo túi đầy.

### Cách chế biến

Hãy viết script dạng DSL (IDE Mode) để dễ quản lý logic phức tạp.

```retroscript
@main:
    # Vòng lặp chính vô tận
    loop 999999:

        # 1. Kiểm tra an toàn trước
        run_flow("SafetyCheck")

        # 2. Tìm quái
        if_image("monster"):
            # Tìm thấy quái -> Đánh
            click_image("monster")

            # Đợi đánh xong (Ví dụ: chờ thanh exp hiện lên hoặc quái biến mất)
            wait_image("monster", appear=false, timeout=10s)

            # Nhặt đồ (Loop nhặt 3 lần cho chắc)
            loop 3:
                hotkey("Space") # Phím nhặt đồ
                sleep(200ms)
        else:
            # Không thấy quái -> Tìm góc khác hoặc xoay camera
            hotkey("Tab")
            sleep(1s)

        # 3. Giả lập nghỉ ngơi (Anti-ban)
        delay_random(500, 1500)

@SafetyCheck:
    # 1. Bơm máu (Logic sinh tồn)
    if_image("hp_low"):
        hotkey("F1") # Phím bình máu
        sleep(500ms)

    # 2. Check túi đầy (Logic tài nguyên)
    if_image("inventory_full"):
        notify("Inventory full! Going home...", method=telegram)
        run_flow("GoHomeAndSell") # Flow về thành (bạn tự define nhé)
```

### 💡 Bí kíp của Đầu bếp (Chef's Tips)

1.  **Đừng check `hp_low` liên tục trong main loop:** Hãy tách ra thành `@SafetyCheck` để code gọn gàng.
2.  **Anti-Ban:** Luôn dùng `delay_random` thay vì `sleep` cố định. Game master rất ghét những ai bấm nút đều như vắt chanh (vd: đúng 1000ms mỗi lần).
3.  **Fail-safe:** Luôn có `timeout` cho `wait_image`. Đừng để bot chờ mãi mãi một hình ảnh có thể không bao giờ hiện (ví dụ: lag game làm mất hình quái).

---

> 👉 **Bài tập về nhà:** Hãy thử kết hợp Recipe 1 và Recipe 2. Chạy Farming Loop và rút dây mạng ra để test xem Login Guard có hoạt động không nhé!
