# Part 8: The Capstone (Dự Án Tổng Hợp) 🏆
> *Đây là bài kiểm tra cuối khóa. Xây dựng BOT HOÀN CHỈNH từ A-Z.*

---

## 🎯 Mục Tiêu

Xây dựng một bot tự động chơi game với 5 tính năng:
1.  **Auto-Login:** Xử lý disconnect.
2.  **Infinite Farm Loop:** Vòng lặp đánh quái.
3.  **HP Monitor:** Tự bơm máu khi thấp.
4.  **Error Recovery:** Xử lý popup lỗi bất ngờ.
5.  **Anti-Ban:** Hành vi "giống người".

**Yêu cầu:** Đọc phần 1-7 trước khi làm.

---

## 📐 Kiến Trúc Tổng Quan

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            MAIN SCRIPT (@main)                              │
│                                                                             │
│   loop 999999:                                                              │
│       run_flow("SafetyCheck")  ──► [HP Monitor + Error Popup Handler]       │
│       run_flow("FarmCore")     ──► [Đánh quái + Nhặt đồ + Anti-ban jitter]  │
│       delay_random(300, 800)                                                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                           ▲ (Bị ngắt bởi Interrupt nếu thấy Login Screen)
                           │
┌──────────────────────────┴──────────────────────────────────────────────────┐
│                        INTERRUPT LAYER (Song song)                          │
│                                                                             │
│   Rule 1 (P10): Trigger="screen_login" ──► run_flow("LoginFlow")            │
│   Rule 2 (P8):  Trigger="popup_error"  ──► run_flow("ClosePopup")           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🧑‍💻 Code Hoàn Chỉnh

### Bước 1: Chuẩn bị Assets
Chụp 6 ảnh sau và đặt vào thư mục `assets/`:
- `screen_login.png`: Màn hình đăng nhập.
- `btn_start.png`: Nút vào game.
- `monster.png`: Quái vật.
- `hp_low.png`: Thanh máu < 30%.
- `popup_error.png`: Popup lỗi bất kỳ.
- `btn_close.png`: Nút đóng popup.

### Bước 2: Viết Script

```retroscript
# ==== MAIN ENTRY ====
@main:
    notify("Bot started!", method=popup)
    loop 999999:
        run_flow("SafetyCheck")
        run_flow("FarmCore")
        delay_random(300, 800) # Anti-ban micro-pause

# ==== SAFETY MODULE ====
@SafetyCheck:
    # 1. Bơm máu
    if_image("hp_low", region=[50, 50, 100, 30]):
        hotkey("F1") # Phím bình thuốc
        delay(500ms)
    
    # 2. Đóng popup lỗi bất ngờ
    if_image("popup_error"):
        click_image("btn_close")
        delay(300ms)

# ==== CORE FARM LOOP ====
@FarmCore:
    if_image("monster"):
        # A. Tấn công
        click_image("monster")
        delay_random(100, 300) # Giả lập phản xạ
        
        # B. Chờ quái chết (tối đa 10s)
        wait_image("monster", appear=false, timeout=10s)
        
        # C. Nhặt đồ (spam phím Space)
        loop 3:
            hotkey("Space")
            delay(150ms)
    else:
        # Không thấy quái -> xoay camera
        hotkey("Tab")
        delay(1s)

# ==== AUTO-LOGIN (INTERRUPT) ====
@LoginFlow:
    notify("Reconnecting...", method=telegram)
    wait_image("btn_start", timeout=30s)
    click_image("btn_start")
    wait_image("screen_login", appear=false, timeout=60s)
    notify("Reconnected!", method=popup)

# ==== ERROR POPUP HANDLER (INTERRUPT) ====
@ClosePopup:
    click_image("btn_close")
    delay(500ms)
```

### Bước 3: Thiết lập Interrupts

Vào tab **⚡ Interrupts**:

| Rule | Trigger Image | Action | Priority | Cooldown |
|------|---------------|--------|----------|----------|
| Login | `screen_login` | `run_flow("LoginFlow")` | P10 (Cao nhất) | 60s |
| Error | `popup_error` | `run_flow("ClosePopup")` | P8 | 5s |

---

## ✅ Checklist Kiểm Tra Trước Khi Chạy

1.  [ ] **DPI = 100%?** (Settings → Display)
2.  [ ] **Game ở Borderless Windowed?**
3.  [ ] **Đủ 6 ảnh trong `assets/`?**
4.  [ ] **Phím F1 đúng là phím bình thuốc trong game?**
5.  [ ] **Đã cấu hình Telegram API cho Notify?** (Tùy chọn)

---

## 🧪 Kịch Bản Test

| Test Case | Hành động | Kỳ vọng |
|-----------|-----------|---------|
| TC1: Happy Path | Chạy script khi đang ở trong game | Bot tự tìm quái, đánh, nhặt đồ. |
| TC2: Low HP | Để nhân vật bị đánh máu < 30% | Bot tự bấm F1. |
| TC3: Disconnect | Rút dây mạng 10 giây, cắm lại | Bot phát hiện Login Screen, tự vào lại game, tiếp tục farm. |
| TC4: Error Popup | Mở một popup game bất kỳ | Bot tự đóng popup và tiếp tục. |

---

## 🎓 Kết Luận

Nếu bạn hoàn thành bài này, bạn đã nắm vững:
- Kiến trúc Main + Interrupt.
- Logic phân tầng (SafetyCheck → FarmCore).
- Anti-ban cơ bản (delay_random).

**Chúc mừng! Bạn đã tốt nghiệp khóa học RetroAuto.** 🎉
