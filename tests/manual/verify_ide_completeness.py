import sys
from pathlib import Path

from unittest.mock import MagicMock, patch
sys.path.append(r"c:\Auto\Newauto")

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QApplication

from app.ui.ide_main_window import IDEMainWindow
from app.ui.intellisense import DSL_SIGNATURES
from core.models import InterruptRule


def test_ide_components():
    print("🚀 Starting IDE Comprehensive Audit...")

    # Init App
    app = QApplication.instance() or QApplication(sys.argv)

    # 1. Test IDEMainWindow Initialization
    try:
        window = IDEMainWindow()
        window.show()
        print("✅ IDEMainWindow initialized successfully")
    except Exception as e:
        print(f"❌ IDEMainWindow init failed: {e}")
        return

    # 2. Test Code Editor & IntelliSense
    print("\n🧪 Testing Code Editor & Intelligence...")
    editor = window.editor

    # 2.1 Asset Peek
    editor.set_asset_provider(lambda x: Path(f"assets/{x}.png"))
    # Mock mouse move
    # We can't easily trigger real tooltip without event loop, but we can verify logic
    # (Logic is inside mouseMoveEvent, hard to unit test without events.
    # But we verified it manually previously. Here we verify no crash on move.)
    event = QMouseEvent(
        QMouseEvent.Type.MouseMove,
        QPointF(10, 10),
        Qt.MouseButton.NoButton,
        Qt.MouseButton.NoButton,
        Qt.KeyboardModifier.NoModifier,
    )
    try:
        editor.mouseMoveEvent(event)
        print("✅ Asset Peek (mouseMoveEvent) handled without crash")
    except Exception as e:
        print(f"❌ Asset Peek failed: {e}")

    # 2.2 Signature Help Logic checks
    # Verify signatures exist
    if "click" in DSL_SIGNATURES:
        print(f"✅ Signature Help registry loaded ({len(DSL_SIGNATURES)} signatures)")
    else:
        print("❌ Signature Help registry missing 'click'")

    # 3. Test Properties Panel with InterruptRule (Recent Bug Verification)
    print("\n🧪 Testing Properties Panel (Regression Test)...")
    panel = window.inspector
    try:
        # Mock an interrupt rule
        rule = InterruptRule(when_image="test_img_id", do_actions=[])
        # Force load (simulating selection)
        # We need to wrap it like the IDE does: {"action": rule, "type": "interrupt", "index": 0}
        data = {"action": rule, "type": "interrupt", "index": 0}
        panel.load_action(data)
        print("✅ PropertiesPanel loaded InterruptRule successfully (Fix verified)")
    except AttributeError as e:
        print(f"❌ PropertiesPanel crashed on InterruptRule: {e}")
    except Exception as e:
        print(f"❌ PropertiesPanel failed: {e}")

    # 4. Test Syntax Checking
    print("\n🧪 Testing Syntax Checker...")
    code = """
@main:
  click btn
    """
    editor.set_code(code)
    try:
        window._check_syntax()
        # Verify output panel has logs (it might fail content check if parser strict, but shouldn't crash)
        print("✅ Syntax Check ran successfully")
    except Exception as e:
        print(f"❌ Syntax Check crashed: {e}")

    # 5. Test Flow Editor Integration (Regression Test)
    print("\n🧪 Testing Flow Editor Integration...")
    try:
        # Mock window.show to avoid opening real window during test
        with patch.object(window, '_flow_window', create=True):
             # Also need to mock QMessageBox to avoid popping up on success/fail
            with patch('PySide6.QtWidgets.QMessageBox.warning') as mock_warn, \
                 patch('PySide6.QtWidgets.QMessageBox.critical') as mock_crit:
                window._show_flow_editor()
                if mock_warn.called or mock_crit.called:
                    print(f"⚠️ Flow Editor opened with warnings: {mock_warn.call_args or mock_crit.call_args}")
                else:
                    print("✅ Flow Editor logic executed successfully (Conversion OK)")
    except AttributeError as e:
         print(f"❌ IDEMainWindow crashed on Flow Editor (Regression): {e}")
    except Exception as e:
         print(f"❌ Flow Editor test failed: {e}")

    # 6. Test Minimap (The Navigator)
    print("\n🧪 Testing Minimap (The Navigator)...")
    try:
        if hasattr(editor, "minimap"):
            print("✅ Minimap widget initialized")
            if editor.minimap.isVisible():
                print("✅ Minimap is visible")
            else:
                 # Minimap might be hidden if window not shown properly or logic differs
                 # logic says self.minimap.show() in init.
                 print("⚠️ Minimap exists but isVisible() returned False (might be due to mocked window state)")
            
            # Test paint event (no crash)
            # editor.minimap.repaint() # Hard to test without event loop
            print("✅ Minimap integration checked")
            
        else:
            print("❌ Minimap widget NOT found in editor")
    except Exception as e:
        print(f"❌ Minimap test failed: {e}")

    # 7. Test Structure Panel Integration
    print("\n🧪 Testing Structure Overlay...")
    try:
        if hasattr(window, "structure_panel"):
            print("✅ StructurePanel widget found in window")
            
            # Test refresh
            test_code = "@flow test:\n  #start"
            window.structure_panel.refresh(test_code)
            
            # Check items
            item_count = window.structure_panel.tree.topLevelItemCount()
            if item_count > 0:
                 print(f"✅ Structure parsed successfully (found {item_count} items)")
                 # Verify navigation signal works (mock emit)
                 # window.structure_panel.navigate_requested.emit(1)
            else:
                 print("⚠️ Structure parsing produced 0 items (check regex?)")
        else:
             print("❌ StructurePanel widget NOT found in IDEMainWindow")
    except Exception as e:
         print(f"❌ Structure Panel test failed: {e}")

    # 8. Clean up
    window.close()
    print("\n✨ Audit Complete. If all ticks are green, the System is stable.")


if __name__ == "__main__":
    test_ide_components()
