# 📊 Step 1-3: Inventory & Coverage Report

## 1. Current Structure Summary (v4.0)
The current documentation (`docs/user_guide/`) consists of 7 parts:
1.  **Launchpad:** Setup & UI Tour.
2.  **Core:** Sync/Async, Coords.
3.  **Cookbook:** Recipes.
4.  **Tools:** GUI & IDE Manual (Missing Debugger).
5.  **Deep Dive:** OCR, Human Mouse.
6.  **Troubleshooting:** Errors.
7.  **Reference:** DSL API.

## 2. Feature Inventory (Bảng kiểm kê)

| Group | Feature | Source Code | Verified? |
|-------|---------|-------------|-----------|
| **UI Main** | Assets Panel (Import/Cap/Edit) | `assets_panel.py` | ✅ |
| | Actions Panel (List/Drag/Disable) | `actions_panel.py` | ✅ |
| | Properties Panel (Dynamic Fields) | `properties_panel.py` | ✅ |
| | Output Panel (Logs/Problems Tab) | `output_panel.py` | ✅ |
| **IDE Debug** | **Call Stack (Frames)** | `debug_panel.py` | ✅ |
| | **Variables (Watch/Local)** | `debug_panel.py` | ✅ |
| | **Breakpoints (Toggle/Cond)** | `debug_panel.py` | ✅ |
| | **Controls (Step Over/Into/Out)** | `debug_panel.py` | ✅ |
| **Execution** | Sync Runner (Main) | `runner.py` | ✅ |
| | Async Interrupts (Sentinel) | `async_manager.py` | ✅ |
| **Vision** | Template Matching (Gray/Color) | `matcher.py` | ✅ |
| | OCR (Tesseract) | `ocr.py` | ✅ |
| | Human Mouse (Bezier) | `input.py` | ✅ |

## 3. Coverage Report (Đối chiếu)

| Feature | Docs Status | Evaluation |
|---------|-------------|------------|
| UI: Main Panels | ✅ `tools_mastery.md` | Good coverage. |
| **UI: Debug Panel** | ❌ **MISSING** | **CRITICAL GAP.** Users don't know how to use Breakpoints/Stepping. |
| UI: Output Panel | ⚠️ Partial | Mentioned in Troubleshooting but UI features (Tabs/Filters) missing. |
| DSL Commands | ✅ `reference_manual.md` | 100% Coverage verified. |
| Logic/Interrupts | ✅ `core_concepts.md` | Good conceptual diagrams. |
| Anti-Ban | ✅ `deep_dive.md` | Algorithm explained well. |

> **Conclusion:** The "Encyclopedia" upgrade MUST add a dedicated **Debugging & Diagnostics** chapter.
