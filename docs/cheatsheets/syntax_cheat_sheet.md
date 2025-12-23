# 📜 RetroScript Cheat Sheet
> **Quick Reference v2025.12** | *Print this out!*

## 🟢 Basic Syntax
```retroscript
# This is a comment
@flow_name:              # Define a Flow
    action(arg1, arg2)   # Call Action
    if_image("id"):      # Condition
        action()         # Indent 2 spaces/4 spaces
```

## 🖱️ Actions (Command Reference)

| Category | Command | Example |
|---|---|---|
| **Mouse** | `click(x, y)` | `click(100, 200)` |
| | `click_image(id)` | `click_image("btn_ok")` |
| | `click_random(roi)` | `click_random(10, 10, 100, 100)` |
| | `drag(x1, y1, x2, y2)` | `drag(0, 0, 500, 500, duration=1s)` |
| **Keyboard** | `type_text(str)` | `type_text("hello", enter=true)` |
| | `hotkey(keys)` | `hotkey("Ctrl+C")` |
| **Wait** | `wait_image(id)` | `wait_image("loading", timeout=10s)` |
| | `sleep(ms)` | `sleep(500ms)` or `delay(1s)` |
| | `delay_random(min, max)` | `delay_random(500, 1500)` |
| **Flow** | `run_flow(name)` | `run_flow("HealRoutine")` |
| | `goto(label)` | `goto #start_loop` |
| | `label(name)` | `#start_loop` (This is a marker) |
| **Logic** | `if_image(id)` | `if_image("hp_bar")` |
| | `loop n` | `loop 5:` ... `loop_end` |
| | `while_image(id)` | `while_image("enemy"):` ... |
| **OCR** | `read_text(var, roi)` | `read_text("$hp", box_roi)` |
| | `if_text(var, op, val)` | `if_text("$hp", "<", "50")` |
| **Notification**| `notify(msg)` | `notify("Done!", method=telegram)` |

## ⌨️ IDE Hotkeys
| Key | Action |
|---|---|
| **F5** | Run Script |
| **F6** | Pause / Resume |
| **F8** | **Stop Hard** (Emergency) |
| **Ctrl+S** | Save Script |
| **Ctrl+Space** | Auto-Complete / Hints |
| **Ctrl+/** | Toggle Comment |

## 🧩 Common Patterns

### 1. The Retry Loop
```retroscript
loop 3:
    if_image("target"):
        click_image("target")
        break  # Not yet impl, use goto or flag
    sleep(1s)
```

### 2. The Login Guard (Interrupt)
*Set in "Interrupts" Tab:*
*   **Trigger:** `login_screen.png`
*   **Action:** `run_flow("Login")`
*   **Priority:** `P10 (High)`

### 3. Safety Check
```retroscript
if_image("hp_low"):
    hotkey("F1")
    sleep(200ms)
```
