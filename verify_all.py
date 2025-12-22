"""
RetroAuto v2 - Comprehensive Verification Script
Verifies all implemented phases (1-20).
"""

import sys
import unittest
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))


class TestRetroAutoIntegration(unittest.TestCase):

    def test_phase_01_11_core(self):
        """Verify Core DSL components."""
        print("\n[Phase 1-11] Core DSL...", end=" ")
        try:
            from core.dsl.parser import Parser

            code = "flow main { let x = 10; log(x); }"
            parser = Parser(code)
            program = parser.parse()

            if parser.errors:
                for err in parser.errors:
                    print(f"Parser Error: {err.message} at {err.span}")

            self.assertEqual(len(parser.errors), 0)
            self.assertIsNotNone(program)
            self.assertEqual(len(program.flows), 1)
            print("OK")
        except Exception as e:
            self.fail(f"Failed: {e}")

    def test_phase_12_lsp(self):
        """Verify LSP Server."""
        print("[Phase 12] LSP Server...", end=" ")
        try:
            from core.lsp.server import RetroScriptLanguageServer

            server = RetroScriptLanguageServer()
            self.assertIsNotNone(server)
            print("OK")
        except Exception as e:
            self.fail(f"Failed: {e}")

    def test_phase_13_packaging(self):
        """Verify Package Management."""
        print("[Phase 13] Packaging...", end=" ")
        try:
            from core.package.manifest import PackageMetadata
            from core.package.resolver import VersionReq

            meta = PackageMetadata("test-pkg", "1.0.0")
            self.assertEqual(meta.name, "test-pkg")

            req = VersionReq("^1.2.0")
            self.assertTrue(req.kind == "caret")
            print("OK")
        except Exception as e:
            self.fail(f"Failed: {e}")

    def test_phase_14_visual(self):
        """Verify Visual Components."""
        print("[Phase 14] Visual Editor...", end=" ")
        try:
            from PySide6.QtWidgets import QApplication

            from app.ui.roi_selector import ROISelector
            from app.ui.variable_watch import VariableWatch

            # App might be running, check if instance exists
            QApplication.instance() or QApplication([])

            roi = ROISelector()
            watch = VariableWatch()
            self.assertIsNotNone(roi)
            self.assertIsNotNone(watch)
            print("OK")
        except Exception as e:
            self.fail(f"Failed: {e}")

    def test_phase_16_network(self):
        """Verify Network Features (Mock/Local)."""
        print("[Phase 16] Network...", end=" ")
        try:
            from core.network.http_client import HttpClient
            from core.network.remote import RemoteController

            client = HttpClient()
            # P1 Fix: Don't connect to external echo server
            # ws = WebSocketClient("wss://echo.websocket.org")

            # Just verify class instantiation and interface
            remote = RemoteController(port=0, auth_token="test")

            self.assertIsNotNone(client)
            # self.assertIsNotNone(ws)
            self.assertIsNotNone(remote)

            # Verify Auth Check
            self.assertFalse(remote.check_auth(None))
            self.assertTrue(remote.check_auth("Bearer test"))

            print("OK")
        except Exception as e:
            self.fail(f"Failed: {e}")

    def test_phase_17_analytics(self):
        """Verify Analytics."""
        print("[Phase 17] Analytics...", end=" ")
        try:
            from core.analytics.metrics import MetricsRegistry, ScriptMetrics

            registry = MetricsRegistry()
            ctr = registry.counter("test_counter")
            ctr.inc()
            self.assertEqual(ctr.get(), 1)

            metrics = ScriptMetrics(registry)
            metrics.script_started("test")
            print("OK")
        except Exception as e:
            self.fail(f"Failed: {e}")

    def test_phase_20_game(self):
        """Verify Game Features."""
        print("[Phase 20] Game Features...", end=" ")
        try:
            from core.game.anti_detect import AntiDetection
            from core.game.macro import MacroRecorder
            from core.game.pixel_detect import Color

            color = Color(255, 0, 0)
            self.assertEqual(color.to_hex(), "#ff0000")

            anti = AntiDetection()
            recorder = MacroRecorder()

            self.assertIsNotNone(anti)
            self.assertIsNotNone(recorder)
            print("OK")
        except Exception as e:
            self.fail(f"Failed: {e}")


if __name__ == "__main__":
    unittest.main(verbosity=0)
