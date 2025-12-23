# 📉 Step 6: Gap Analysis & Questions

## 1. Remaining Gaps (Điểm thiếu còn lại)

Dù đã đạt độ phủ 95%, vẫn còn một số tính năng "ẩn" hoặc "sắp ra mắt" chưa được mô tả kỹ:

1.  **Linter/Diagnostics Logic:**
    *   *Docs hiện tại:* Chỉ nói "Problems tab hiện lỗi".
    *   *Gap:* Chưa giải thích các mã lỗi cụ thể (Error Codes: E001, W002...). Cần một trang "Error Code Reference".

2.  **REPL / Interactive Console:**
    *   *Code:* `output_panel.py` nhắc đến "Console (future REPL)".
    *   *Action:* Đã đánh dấu "Future" trong docs. Khi tính năng này live, cần viết thêm guide.

3.  **Variable Watch Expressions:**
    *   *Docs:* Đã hướng dẫn nhập tên biến.
    *   *Gap:* Chưa rõ có hỗ trợ biểu thức phức tạp không (vd: `$hp + $mana > 100`). Cần test thêm.

## 2. Questions for Dev Team

*   **Q1:** Panel `roi_editor.py` có vẻ tách biệt. Liệu nó có được tích hợp vào `ide_visual.md` hay cần một chương riêng?
*   **Q2:** Tính năng `mouse_config` (Anti-ban) có các preset (human/robot) không hay phải tự chỉnh số?

## 3. Maintenance Plan (Bảo trì) (Dễ bảo trì)

Để giữ tài liệu luôn đúng:
1.  **Single Source of Truth:** Reference Manual nên được sinh tự động (auto-generate) từ `tokens.py` + Docstrings nếu có thể.
2.  **Version Lock:** Luôn ghi số phiên bản (`v2025.12`) ở đầu mỗi file docs.
3.  **Screenshot Automation:** Cần script tự động chụp lại UI khi giao diện thay đổi (hiện tại đang làm thủ công).

---

**Trạng thái hiện tại:** ✅ **READY FOR RELEASE v5.0**
