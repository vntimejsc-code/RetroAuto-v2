"""
RetroAuto v2 - Interrupt Scanner

Background thread that monitors screen for interrupt triggers.
When an interrupt image is detected, it pauses main flow and executes interrupt actions.
"""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import TYPE_CHECKING

from core.models import Action, InterruptRule, ROI
from infra import get_logger

if TYPE_CHECKING:
    from core.engine.context import ExecutionContext
    from vision import TemplateMatcher

logger = get_logger("InterruptScanner")


class InterruptState(Enum):
    """Interrupt scanner state."""
    IDLE = auto()
    SCANNING = auto()
    EXECUTING = auto()
    STOPPED = auto()


@dataclass
class InterruptMatch:
    """Result of an interrupt trigger."""
    rule: InterruptRule
    match_x: int
    match_y: int
    match_w: int
    match_h: int
    confidence: float
    timestamp: float = field(default_factory=time.time)


class InterruptScanner:
    """
    Background scanner for interrupt triggers.
    
    Features:
    - Scans screen at configurable interval
    - Checks interrupts by priority order
    - Pauses main flow when interrupt triggered
    - Executes interrupt actions
    - Resumes main flow after interrupt
    
    Usage:
        scanner = InterruptScanner(ctx, matcher)
        scanner.on_interrupt(callback)  # Register handler
        scanner.start()
        # ... main script runs ...
        scanner.stop()
    """
    
    def __init__(
        self,
        ctx: ExecutionContext,
        matcher: TemplateMatcher,
        scan_interval_ms: int = 200,
    ) -> None:
        """
        Initialize interrupt scanner.
        
        Args:
            ctx: Execution context with script and state
            matcher: Template matcher for image detection
            scan_interval_ms: Time between scans in milliseconds
        """
        self._ctx = ctx
        self._matcher = matcher
        self._scan_interval = scan_interval_ms / 1000.0
        
        self._state = InterruptState.IDLE
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        self._pause_event.set()  # Not paused initially
        
        # Callbacks
        self._on_interrupt_callbacks: list[Callable[[InterruptMatch], None]] = []
        self._on_interrupt_complete_callbacks: list[Callable[[InterruptMatch, bool], None]] = []
        
        # Current interrupt being executed
        self._current_interrupt: InterruptMatch | None = None
        
        # Cooldown to avoid re-triggering same interrupt
        self._cooldown: dict[str, float] = {}
        self._cooldown_duration = 2.0  # seconds
    
    @property
    def state(self) -> InterruptState:
        """Get current scanner state."""
        return self._state
    
    @property
    def is_running(self) -> bool:
        """Check if scanner is running."""
        return self._state in (InterruptState.SCANNING, InterruptState.EXECUTING)
    
    def on_interrupt(self, callback: Callable[[InterruptMatch], None]) -> None:
        """Register callback for when interrupt is triggered."""
        self._on_interrupt_callbacks.append(callback)
    
    def on_interrupt_complete(self, callback: Callable[[InterruptMatch, bool], None]) -> None:
        """Register callback for when interrupt execution completes."""
        self._on_interrupt_complete_callbacks.append(callback)
    
    def start(self) -> None:
        """Start the interrupt scanner thread."""
        if self._thread is not None and self._thread.is_alive():
            logger.warning("Scanner already running")
            return
        
        self._stop_event.clear()
        self._pause_event.set()
        self._state = InterruptState.SCANNING
        
        self._thread = threading.Thread(target=self._scan_loop, daemon=True)
        self._thread.start()
        logger.info("Interrupt scanner started (interval: %.0fms)", self._scan_interval * 1000)
    
    def stop(self) -> None:
        """Stop the interrupt scanner thread."""
        self._stop_event.set()
        self._state = InterruptState.STOPPED
        
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None
        
        logger.info("Interrupt scanner stopped")
    
    def pause(self) -> None:
        """Pause scanning (e.g., while executing interrupt)."""
        self._pause_event.clear()
        logger.debug("Scanner paused")
    
    def resume(self) -> None:
        """Resume scanning after pause."""
        self._pause_event.set()
        logger.debug("Scanner resumed")
    
    def _scan_loop(self) -> None:
        """Main scanning loop - runs in background thread."""
        while not self._stop_event.is_set():
            # Wait for resume if paused
            self._pause_event.wait()
            
            if self._stop_event.is_set():
                break
            
            # Scan for interrupts
            try:
                match = self._check_interrupts()
                if match is not None:
                    self._handle_interrupt(match)
            except Exception as e:
                logger.error("Error in interrupt scan: %s", e)
            
            # Wait before next scan
            time.sleep(self._scan_interval)
        
        self._state = InterruptState.STOPPED
    
    def _check_interrupts(self) -> InterruptMatch | None:
        """
        Check all interrupts in priority order.
        
        Returns:
            InterruptMatch if an interrupt is triggered, None otherwise
        """
        # Get interrupts sorted by priority (high first)
        interrupts = sorted(
            self._ctx.script.interrupts,
            key=lambda r: r.priority,
            reverse=True
        )
        
        current_time = time.time()
        
        for rule in interrupts:
            # Skip if in cooldown
            cooldown_key = rule.when_image
            if cooldown_key in self._cooldown:
                if current_time - self._cooldown[cooldown_key] < self._cooldown_duration:
                    continue
            
            # Get asset for this interrupt
            asset = self._ctx.script.get_asset(rule.when_image)
            if asset is None:
                continue
            
            # Determine ROI
            roi = rule.roi_override or asset.roi
            roi_tuple = (roi.x, roi.y, roi.w, roi.h) if roi else None
            
            # Try to match
            result = self._matcher.find(
                asset_id=asset.id,
                threshold=asset.threshold,
                roi=roi_tuple,
            )
            
            if result is not None:
                # Found a match!
                logger.info("Interrupt triggered: %s (priority %d)", rule.when_image, rule.priority)
                
                # Set cooldown
                self._cooldown[cooldown_key] = current_time
                
                return InterruptMatch(
                    rule=rule,
                    match_x=result.x,
                    match_y=result.y,
                    match_w=result.w,
                    match_h=result.h,
                    confidence=result.confidence,
                )
        
        return None
    
    def _handle_interrupt(self, match: InterruptMatch) -> None:
        """Handle a triggered interrupt."""
        self._state = InterruptState.EXECUTING
        self._current_interrupt = match
        
        # Notify callbacks
        for callback in self._on_interrupt_callbacks:
            try:
                callback(match)
            except Exception as e:
                logger.error("Error in interrupt callback: %s", e)
        
        # Execute interrupt actions
        success = True
        try:
            if match.rule.do_actions:
                # Execute inline actions
                success = self._execute_actions(match.rule.do_actions)
            elif match.rule.run_flow:
                # Run a flow
                # This would need integration with Runner
                logger.info("Would run flow: %s", match.rule.run_flow)
        except Exception as e:
            logger.error("Error executing interrupt: %s", e)
            success = False
        
        # Notify completion
        for callback in self._on_interrupt_complete_callbacks:
            try:
                callback(match, success)
            except Exception as e:
                logger.error("Error in completion callback: %s", e)
        
        self._current_interrupt = None
        self._state = InterruptState.SCANNING
    
    def _execute_actions(self, actions: list[Action]) -> bool:
        """
        Execute a list of actions.
        
        For now, this is a simple implementation.
        In production, this should integrate with Runner.
        """
        from input.mouse import MouseController
        from input.keyboard import KeyboardController
        from core.models import Click, Delay, Hotkey, TypeText
        
        mouse = MouseController()
        keyboard = KeyboardController()
        
        for action in actions:
            if self._stop_event.is_set():
                return False
            
            if isinstance(action, Click):
                x = action.x or self._current_interrupt.match_x + self._current_interrupt.match_w // 2
                y = action.y or self._current_interrupt.match_y + self._current_interrupt.match_h // 2
                mouse.click(x, y, action.button, action.clicks)
                
            elif isinstance(action, Delay):
                time.sleep(action.ms / 1000.0)
                
            elif isinstance(action, Hotkey):
                keyboard.hotkey(action.keys)
                
            elif isinstance(action, TypeText):
                keyboard.type_text(action.text, paste=action.paste_mode)
        
        return True
    
    def clear_cooldowns(self) -> None:
        """Clear all interrupt cooldowns."""
        self._cooldown.clear()
        logger.debug("Interrupt cooldowns cleared")
