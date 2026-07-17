"""
Mouse Event Collector
======================
Collects mouse movement, clicks, and scroll events via pynput.
"""

import queue
import time
import math
from dataclasses import dataclass, field
from typing import Optional, Tuple


@dataclass
class MouseMoveEvent:
    x: float
    y: float
    timestamp: float = field(default_factory=time.time)


@dataclass
class MouseClickEvent:
    x: float
    y: float
    button: str
    pressed: bool
    timestamp: float = field(default_factory=time.time)
    is_double_click: bool = False


@dataclass
class MouseScrollEvent:
    x: float
    y: float
    dx: float
    dy: float
    timestamp: float = field(default_factory=time.time)


class MouseCollector:
    """
    Collects mouse behavioral metrics via pynput.
    Position data is used only for speed/distance calculations,
    never transmitted or stored long-term.
    """

    def __init__(self, move_queue: queue.Queue, click_queue: queue.Queue, scroll_queue: queue.Queue):
        self._move_queue = move_queue
        self._click_queue = click_queue
        self._scroll_queue = scroll_queue
        self._listener = None
        self._is_running = False
        self._last_click_time: Optional[float] = None
        self._last_click_pos: Optional[Tuple[float, float]] = None
        self._double_click_threshold = 0.3  # seconds

    def start(self):
        """Start mouse listening."""
        try:
            from pynput import mouse as m

            self._listener = m.Listener(
                on_move=self._on_move,
                on_click=self._on_click,
                on_scroll=self._on_scroll,
            )
            self._listener.start()
            self._is_running = True

        except ImportError:
            raise ImportError("pynput not installed. Run: pip install pynput")

    def stop(self):
        """Stop mouse listener."""
        self._is_running = False
        if self._listener:
            self._listener.stop()

    def _on_move(self, x: int, y: int):
        if not self._is_running:
            return
        try:
            self._move_queue.put_nowait(MouseMoveEvent(x=float(x), y=float(y)))
        except queue.Full:
            pass

    def _on_click(self, x: int, y: int, button, pressed: bool):
        if not self._is_running:
            return
        try:
            now = time.time()
            is_double = False

            if pressed and self._last_click_time is not None:
                time_diff = now - self._last_click_time
                if time_diff < self._double_click_threshold:
                    is_double = True

            if pressed:
                self._last_click_time = now
                self._last_click_pos = (x, y)

            self._click_queue.put_nowait(MouseClickEvent(
                x=float(x),
                y=float(y),
                button=str(button),
                pressed=pressed,
                is_double_click=is_double,
            ))
        except queue.Full:
            pass

    def _on_scroll(self, x: int, y: int, dx: int, dy: int):
        if not self._is_running:
            return
        try:
            self._scroll_queue.put_nowait(MouseScrollEvent(
                x=float(x), y=float(y), dx=float(dx), dy=float(dy),
            ))
        except queue.Full:
            pass
