"""
System Watchdog Module
Pillar 1 of "Titan Light" Robustness Strategy.

This module provides the vital signs monitoring for the automation engine.
It checks:
1. Internet Connectivity
2. Game Process Existence
3. Game Window Visibility & Resolution
"""

import ctypes
import socket
import subprocess
import time

from infra import get_logger

logger = get_logger("SystemWatchdog")


class SystemWatchdog:
    def __init__(self):
        self.last_check = 0
        self.check_interval = 5.0  # Check every 5 seconds
        self._user32 = ctypes.windll.user32
        self._shcore = ctypes.windll.shcore
        self._shcore.SetProcessDpiAwareness(
            1
        )  # Enable DPI awareness for accurate resolution checks

    def check_health(self, config: dict) -> tuple[bool, str]:
        """
        Run all configured health checks.
        Returns: (is_healthy, error_message)
        """
        current_time = time.time()
        if current_time - self.last_check < self.check_interval:
            return True, ""

        self.last_check = current_time

        # 1. Check Internet
        if config.get("check_internet", False):
            if not self._check_internet():
                return False, "⚠️ No Internet Connection"

        # 2. Check Process
        process_name = config.get("process_name")
        if process_name:
            if not self._check_process(process_name):
                return False, f"⚠️ Process '{process_name}' not found"

        # 3. Check Window
        window_title = config.get("window_title")
        if window_title:
            is_found, msg = self._check_window(window_title)
            if not is_found:
                return False, msg

        return True, "OK"

    def _check_internet(self, host="8.8.8.8", port=53, timeout=3) -> bool:
        """
        Check internet connectivity by trying to connect to Google DNS.
        Better than ping because it doesn't require ICMP.
        """
        try:
            socket.setdefaulttimeout(timeout)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
            return True
        except OSError:
            return False

    def _check_process(self, process_name: str) -> bool:
        """
        Check if a process is running using tasklist.
        Robust fallback if psutil is not available.
        """
        try:
            # Usage of tasklist is fast enough for 5s interval
            output = subprocess.check_output(
                f'tasklist /FI "IMAGENAME eq {process_name}"', shell=True
            ).decode(errors="ignore")
            # If process is found, it appears in the list.
            # If not, tasklist usually says "INFO: No tasks are running..."
            return process_name.lower() in output.lower()
        except Exception as e:
            logger.error(f"Error checking process: {e}")
            return True  # Assume true on error to prevent blocking execution due to watchdog bug

    def _check_window(self, partial_title: str) -> tuple[bool, str]:
        """
        Check if a window with partial_title exists and is not minimized.
        """
        found_window = []

        def enum_window_callback(hwnd, _):
            length = self._user32.GetWindowTextLengthW(hwnd)
            buff = ctypes.create_unicode_buffer(length + 1)
            self._user32.GetWindowTextW(hwnd, buff, length + 1)
            title = buff.value

            if partial_title.lower() in title.lower() and self._user32.IsWindowVisible(hwnd):
                found_window.append(hwnd)
                return False  # Stop enumeration
            return True

        CMPFUNC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)
        self._user32.EnumWindows(CMPFUNC(enum_window_callback), 0)

        if not found_window:
            return False, f"⚠️ Window containing '{partial_title}' not found"

        hwnd = found_window[0]

        # Check if minimized
        if self._user32.IsIconic(hwnd):
            return False, f"⚠️ Window '{partial_title}' is minimized"

        return True, ""
