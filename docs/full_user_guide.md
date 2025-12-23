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
# Part 4: Core Concepts (Nguyên Lý Cốt Lõi) 🧠

---

## 4.1 Execution Model (Cơ chế Hoạt động)

RetroAuto sử dụng **Event Loop Hybrid**: Kết hợp giữa tuần tự (Main Thread) và song song (Interrupt Watchdog).

### 📐 The Runtime Loop ASCII Art

```
┌───────────────── MAIN THREAD (Synchronous) ─────────────────┐
│                                                             │
│   [Start]                                                   │
│      │                                                      │
│      ▼                                                      │
│   [Fetch Instruction] <───(Step Pointer)                    │
│      │                                                      │
│      ▼                                                      │
│   [Execute Action] (Click, Type, Wait...)                   │
│      │                                                      │
│      │  ⚠️ BLOCKED? (e.g. sleep 5s)                         │
│      │  (Main thread sleeps, but Background thread is ALIVE)│
│      │                                                      │
│      ▼                                                      │
│   [Check Events] (Stop? Pause?)                             │
│      │                                                      │
│      └───► Loop to Next Instruction                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
               ▲                 │
               │ (Pause Request) │ (Resume)
               │                 ▼
┌────────────── BACKGROUND THREAD (Asynchronous) ─────────────┐
│                                                             │
│   [Sentinel Timer (500ms)]                                  │
│      │                                                      │
│      ▼                                                      │
│   [Scan All Interrupt Rules]                                │
│      │                                                      │
│      ├──► Rule 1: Login Screen? (No)                        │
│      │                                                      │
│      ├──► Rule 2: Low HP? (YES!) ──┐                        │
│      │                             │                        │
│      └──► Rule 3: Error Popup?     │                        │
│                                    │                        │
│          ┌─────────────────────────┘                        │
│          ▼                                                  │
│   [PREEMPTION TRIGGERED]                                    │
│   1. Pause Main Thread                                      │
│   2. Save Context (Stack/Variables)                         │
│   3. Run "HealFlow"                                         │
│   4. Resume Main Thread                                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 4.2 Priority System (Hệ thống Ưu tiên)

Khi nhiều sự kiện xảy ra cùng lúc, ai thắng?

```
High Priority (P10) > Medium (P5) > Low (P1)
```

**Ví dụ xung đột:**
- **Sự kiện A:** Hết máu (P10, Flow: "Heal")
- **Sự kiện B:** Túi đầy (P5, Flow: "SellItems")

**Kịch bản:**
1. Bot thấy cả "Hết máu" và "Túi đầy".
2. **P10 (Heal)** chiến thắng -> Chạy `Heal` trước.
3. Sau khi `Heal` xong, nếu vẫn thấy "Túi đầy", chạy `SellItems`.

---

## 4.3 Coordinate Systems (Hệ Tọa Độ)

Cách RetroAuto định vị trên màn hình:

```
(0,0) Top-Left
  ┌──────────────────────────────────────────X (Width)
  │
  │      [Global Coordinate]
  │      Click(500, 300)
  │          Target
  │            ▼
  │            ✕
  │
  │
  Y
(Height)
```

**ROI (Region of Interest - Vùng quan tâm):**
Thay vì tìm trên cả màn hình, chỉ tìm trong một hộp nhỏ.

```
┌──────────────────────────────────────────────────┐
│ Screen (1920x1080)                               │
│                                                  │
│   ┌──────── ROI (Health Bar) ───────┐            │
│   │ [##########........] 50%        │            │
│   └─────────────────────────────────┘            │
│                                                  │
└──────────────────────────────────────────────────┘
```
**Lợi ích:** Tăng tốc độ tìm kiếm gấp 5-10 lần.
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
# Part 6: Troubleshooting & Diagnostics (Xử Lý Sự Cố) 🔧

---

## 6.1 Diagnostic Playbook (Quy trình Chẩn bệnh)

### 🌡️ Symptom: "Image Not Found" (Không tìm thấy ảnh)

**Mô tả:** Bot đứng yên, log báo `WARNING: WaitImage('xyz') timed out`.

**Decision Flow (Cây quyết định):**
```
[START]
   │
   ▼
[Check Screen] -> Is the image visible to YOUR eyes?
   │
   ├─ NO ──> [Game Logic Issue]
   │          Wait longer (increase timeout)
   │          or excessive lag?
   │
   └─ YES (I see it!)
        │
        ▼
   [Check Threshold]
        │
        ├─ > 0.9? ──> Too strict. Lower to 0.7.
        │
        └─ < 0.7? ──> [Check Rendering]
             │
             ├─ Different Resolution/DPI? (Check Settings)
             │
             ├─ Color changed? (Night mode? Hover effect?)
             │    └─ Capture NEW image.
             │
             └─ Obstructed? (Mouse cursor/Tooltip covering it?)
```

---

### 🌡️ Symptom: "Bot click trượt" (Click Accuracy)

**Mô tả:** Bot click vào chỗ không có gì, hoặc click lệch nút.

**Nguyên nhân & Fix:**
1.  **DPI Scaling:** Windows Scale != 100%.
    *   *Fix:* Set Display Scale về 100%.
2.  **Offset:** Ảnh mẫu có viền trong suốt (Transparent) quá lớn.
    *   *Fix:* Cắt ảnh (Crop) sát vào nội dung nút, bỏ viền.
3.  **Dynamic UI:** Nút di chuyển động.
    *   *Fix:* Dùng `wait_image` liên tục để cập nhật vị trí mới nhất ngay trước khi click.

---

## 6.2 Log Analysis (Phân tích Log)

Mở tab **Output** hoặc file `logs/retroauto.log`.

### Cấu trúc Log
```
[TIME]     [LEVEL]  [MODULE]    [MESSAGE]
14:05:01   INFO     Runner      Starting flow 'Farm'
14:05:02   DEBUG    Matcher     Found 'mob_slime' at (500, 200) | score=0.95
14:05:03   INFO     Input       Clicking at (505, 202)
```

### Các tín hiệu lạ
- **Spam "Found...":** Interrupt Rule của bạn không có cooldown hoặc action quá nhanh.
- **"FPS drop":** Quá trình tìm ảnh (Vision) tốn > 200ms. Hãy thu nhỏ ROI lại.

---

## 6.3 Reporting Bugs (Báo Lỗi)

Khi cần hỗ trợ, hãy cung cấp đủ **3 món ăn chơi**:
1.  **Screenshot:** Chụp màn hình lúc lỗi (cả game + cửa sổ RetroAuto).
2.  **Log File:** Copy 50 dòng cuối cùng.
3.  **Repro Steps:** "Chạy Flow A, đến bước B thì bị đơ".

---

## 6.4 Advanced Debugging (Gỡ Lỗi Nâng Cao)

### 🧠 Lỗi Logic (Bot chạy nhưng không làm gì)

**Symptom:** Script không báo lỗi, chạy qua các bước nhưng kết quả sai (vd: không click được nút).

**Decision Tree:**
```
[Bot chạy nhưng không click đúng]
   │
   ├─ [1] if_image luôn trả về FALSE?
   │      └─ Kiểm tra Threshold / DPI / ROI.
   │
   ├─ [2] if_image TRUE nhưng click không trúng?
   │      └─ Ảnh mẫu có viền trong suốt (offset sai).
   │
   └─ [3] Interrupt chạy liên tục chiếm quyền?
          └─ Xem log có "Interrupt triggered" spam không? Tăng Cooldown.
```

### 🔧 Lỗi Môi Trường

| Triệu chứng | Nguyên nhân | Giải pháp |
|-------------|-------------|-----------|
| Bot không điều khiển được game | Antivirus/Game Guard chặn input | Thêm RetroAuto vào Whitelist / Tắt GameGuard. |
| Screenshot trả về màn hình đen | Game chạy ở DirectX Fullscreen | Đổi game về **Borderless Windowed**. |
| Tọa độ click bị lệch | Windows DPI Scaling ≠ 100% | Set Display Scale về 100%. |
| OCR đọc sai chữ | Font game quá nhỏ/nghệ thuật | Tăng vùng ROI, dùng `psm=6` (block text). |

### 🔥 Race Condition (Xung đột Interrupt)

**Symptom:** Hai Interrupt P10 cùng kích hoạt, bot hành xử lạ.

**Giải pháp:**
1.  **Không nên đặt 2 rule cùng Priority cao.** Phân biệt rõ (Login=P10, Error=P8).
2.  **Đảm bảo mỗi Interrupt Flow kết thúc rõ ràng** (không để vòng lặp vô tận bên trong).

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

---

## 🔬 Under the Hood (Cơ Chế Bên Trong)

### 1. Biến & Phạm Vi (Variable Scope)

RetroAuto sử dụng **Global Scope** duy nhất cho toàn bộ script.

```
┌──────────────────────────────────────────────────┐
│                 GLOBAL SCOPE                     │
│                                                  │
│  $hp = 100                                       │
│  $gold = 5000                                    │
│                                                  │
│  ┌────────────────┐   ┌────────────────┐         │
│  │ @main:         │   │ @heal:         │         │
│  │   $hp = 50     │──▶│   if $hp < 30  │ ✅ OK   │
│  │   run_flow()   │   │     ...        │         │
│  └────────────────┘   └────────────────┘         │
│                                                  │
└──────────────────────────────────────────────────┘
```
**Kết luận:**
- Biến `$hp` khai báo ở `@main` **có thể đọc/ghi** từ `@heal`.
- **Không có Local Scope riêng biệt** cho mỗi Flow.
- **Gotcha:** Tên biến dễ bị ghi đè nếu trùng. Hãy đặt tên rõ ràng (`$main_hp` thay vì `$hp`).

### 2. Call Stack & Đệ Quy

Khi gọi `run_flow("A")`, hệ thống **push** một Frame vào Stack:

```
Stack: [Main] -> [A] -> [B] -> [C] ...
```
**Giới hạn:** Stack tối đa **100 levels** (Configurable).
**Gotcha:** Nếu Flow A gọi lại chính nó (đệ quy vô hạn), sẽ gặp `RecursionError`.

### 3. Hiệu Năng Vision (Performance)

| Tác vụ | Thời gian ước tính | Ghi chú |
|--------|-------------------:|---------|
| `if_image` (Full Screen 1080p) | 50-150 ms | Chậm, tránh dùng trong vòng lặp nhanh. |
| `if_image` (ROI 100x100 px) | 2-10 ms | **Nhanh gấp 10x.** |
| `wait_pixel` | < 1 ms | Cực nhanh, chỉ kiểm tra 1 điểm. |
| OCR `read_text` | 100-500 ms | Nặng, dùng tiết kiệm. |

**Best Practice:** Luôn dùng `region=[x, y, w, h]` để giới hạn vùng tìm kiếm.
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
