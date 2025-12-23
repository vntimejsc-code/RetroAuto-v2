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

