"""
Mental Fatigue Desktop Tracker
================================
Privacy-preserving background tracker that collects keyboard
and mouse behavioral metrics and sends them to the FastAPI backend.

Architecture:
  - keyboard_collector.py: pynput keyboard listener
  - mouse_collector.py: pynput mouse listener
  - aggregator.py: compute 1-second feature windows
  - sender.py: authenticated HTTPS API client
  - main.py: orchestrator with graceful shutdown

Privacy guarantees:
  - NO keystrokes are logged — only timing metrics
  - NO screenshots are taken
  - All data is aggregated BEFORE transmission
  - User can pause/stop tracking at any time
"""

import queue
import threading
import time
from dataclasses import dataclass, field
from typing import Optional

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class KeyEvent:
    """A single keyboard event (press or release)."""
    key: str        # Key identifier (obfuscated — we only store timing)
    event_type: str  # "press" or "release"
    timestamp: float = field(default_factory=time.time)
    is_backspace: bool = False
    is_modifier: bool = False


class KeyboardCollector:
    """
    Collects keyboard timing events using pynput.
    NO actual keystrokes are stored — only timing data.
    """

    def __init__(self, event_queue: queue.Queue):
        self._queue = event_queue
        self._listener = None
        self._last_press_time: Optional[float] = None
        self._is_running = False

    def start(self):
        """Start keyboard listening in background thread."""
        try:
            from pynput import keyboard as kb

            self._listener = kb.Listener(
                on_press=self._on_press,
                on_release=self._on_release,
                suppress=False,  # NEVER suppress — do NOT intercept keys
            )
            self._listener.start()
            self._is_running = True
            logger.info("Keyboard collector started")
        except ImportError:
            logger.error("pynput not installed. Run: pip install pynput")
            raise

    def stop(self):
        """Stop keyboard listener."""
        self._is_running = False
        if self._listener:
            self._listener.stop()
        logger.info("Keyboard collector stopped")

    def _on_press(self, key):
        """Handle key press event — extract timing only."""
        if not self._is_running:
            return

        try:
            from pynput import keyboard as kb

            # Detect backspace without storing the key value
            is_backspace = key == kb.Key.backspace
            is_modifier = key in {
                kb.Key.ctrl, kb.Key.ctrl_l, kb.Key.ctrl_r,
                kb.Key.alt, kb.Key.alt_l, kb.Key.alt_r,
                kb.Key.shift, kb.Key.shift_l, kb.Key.shift_r,
                kb.Key.cmd,
            }

            event = KeyEvent(
                key="[KEY]",  # Never store actual key content
                event_type="press",
                timestamp=time.time(),
                is_backspace=is_backspace,
                is_modifier=is_modifier,
            )
            self._queue.put_nowait(event)

        except Exception:
            pass  # Never let the collector crash

    def _on_release(self, key):
        """Handle key release — record hold time."""
        if not self._is_running:
            return

        try:
            event = KeyEvent(
                key="[KEY]",
                event_type="release",
                timestamp=time.time(),
            )
            self._queue.put_nowait(event)
        except Exception:
            pass
