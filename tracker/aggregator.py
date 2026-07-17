"""
Feature Aggregator
==================
Aggregates 1-second windows of raw keyboard and mouse events
into the 24+ feature vector used by the ML model.

All computations happen locally before any data is transmitted.
"""

import math
import queue
import time
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import numpy as np


@dataclass
class FeatureWindow:
    """A 1-second window of aggregated behavioral metrics."""

    # Window metadata
    window_start: float = 0.0
    window_end: float = 0.0
    session_elapsed_s: int = 0

    # ── Keyboard Features ─────────────────────────────────
    typing_speed_wpm: float = 0.0
    typing_speed_cpm: float = 0.0
    key_hold_time_ms: float = 0.0
    flight_time_ms: float = 0.0
    backspace_count: int = 0
    error_rate: float = 0.0
    idle_time_keyboard_s: float = 0.0
    typing_burst_score: float = 0.0
    typing_rhythm_variance: float = 0.0
    total_keystrokes: int = 0

    # ── Mouse Features ────────────────────────────────────
    mouse_speed_px_s: float = 0.0
    mouse_acceleration: float = 0.0
    mouse_distance_px: float = 0.0
    click_frequency: float = 0.0
    double_click_count: int = 0
    drag_count: int = 0
    scroll_speed: float = 0.0
    scroll_distance: float = 0.0
    idle_time_mouse_s: float = 0.0
    direction_changes: int = 0
    hover_duration_ms: float = 0.0

    # ── Combined ──────────────────────────────────────────
    total_idle_time_s: float = 0.0
    time_of_day_hour: float = 0.0

    def to_dict(self) -> dict:
        """Convert to dict for API transmission."""
        return {
            "typing_speed_wpm": round(self.typing_speed_wpm, 3),
            "typing_speed_cpm": round(self.typing_speed_cpm, 3),
            "key_hold_time_ms": round(self.key_hold_time_ms, 3),
            "flight_time_ms": round(self.flight_time_ms, 3),
            "backspace_count": self.backspace_count,
            "error_rate": round(self.error_rate, 4),
            "idle_time_keyboard_s": round(self.idle_time_keyboard_s, 3),
            "typing_burst_score": round(self.typing_burst_score, 4),
            "typing_rhythm_variance": round(self.typing_rhythm_variance, 4),
            "total_keystrokes": self.total_keystrokes,
            "mouse_speed_px_s": round(self.mouse_speed_px_s, 3),
            "mouse_acceleration": round(self.mouse_acceleration, 3),
            "mouse_distance_px": round(self.mouse_distance_px, 3),
            "click_frequency": round(self.click_frequency, 3),
            "double_click_count": self.double_click_count,
            "drag_count": self.drag_count,
            "scroll_speed": round(self.scroll_speed, 3),
            "scroll_distance": round(self.scroll_distance, 3),
            "idle_time_mouse_s": round(self.idle_time_mouse_s, 3),
            "direction_changes": self.direction_changes,
            "hover_duration_ms": round(self.hover_duration_ms, 3),
            "total_idle_time_s": round(self.total_idle_time_s, 3),
            "session_elapsed_s": self.session_elapsed_s,
            "time_of_day_hour": round(self.time_of_day_hour, 3),
        }


class FeatureAggregator:
    """
    Processes raw event queues over 1-second windows
    and produces a FeatureWindow.
    """

    def __init__(self, window_seconds: float = 1.0):
        self.window_seconds = window_seconds
        self._session_start = time.time()

        # Sliding state for inter-event calculations
        self._last_key_press_time: Optional[float] = None
        self._last_key_release_time: Optional[float] = None
        self._press_release_pairs: List[Tuple[float, float]] = []  # (press, release) tuples
        self._flight_times: List[float] = []
        self._prev_mouse_pos: Optional[Tuple[float, float]] = None
        self._prev_mouse_time: Optional[float] = None
        self._prev_mouse_speed: float = 0.0

    def aggregate(
        self,
        key_events: list,
        move_events: list,
        click_events: list,
        scroll_events: list,
        window_start: float,
        window_end: float,
    ) -> FeatureWindow:
        """Compute all features from raw events in the window."""
        fw = FeatureWindow()
        fw.window_start = window_start
        fw.window_end = window_end
        fw.session_elapsed_s = int(window_start - self._session_start)
        fw.time_of_day_hour = self._get_time_of_day_hour()

        # Keyboard features
        self._compute_keyboard_features(key_events, fw, window_start, window_end)

        # Mouse features
        self._compute_mouse_features(move_events, click_events, scroll_events, fw)

        # Combined
        fw.total_idle_time_s = max(fw.idle_time_keyboard_s, fw.idle_time_mouse_s)

        return fw

    def _compute_keyboard_features(self, events: list, fw: FeatureWindow, ws: float, we: float):
        """Compute all keyboard-derived features."""
        if not events:
            fw.idle_time_keyboard_s = self.window_seconds
            return

        press_events = [e for e in events if e.event_type == "press"]
        release_events = [e for e in events if e.event_type == "release"]

        fw.total_keystrokes = len(press_events)
        fw.backspace_count = sum(1 for e in press_events if e.is_backspace)

        # Error rate
        if fw.total_keystrokes > 0:
            fw.error_rate = min(fw.backspace_count / fw.total_keystrokes, 1.0)

        # Typing speed
        fw.typing_speed_cpm = fw.total_keystrokes * 60.0 / self.window_seconds
        fw.typing_speed_wpm = fw.typing_speed_cpm / 5.0

        # Flight time (time between consecutive key presses)
        press_times = sorted([e.timestamp for e in press_events])
        if len(press_times) >= 2:
            flights = [
                (press_times[i + 1] - press_times[i]) * 1000  # Convert to ms
                for i in range(len(press_times) - 1)
            ]
            valid_flights = [f for f in flights if 10 < f < 2000]
            if valid_flights:
                fw.flight_time_ms = float(np.mean(valid_flights))
                fw.typing_rhythm_variance = float(np.var(valid_flights))

        # Key hold time (press to release)
        hold_times = []
        for press in press_events:
            for release in release_events:
                dt = (release.timestamp - press.timestamp) * 1000
                if 10 < dt < 1000:
                    hold_times.append(dt)
                    break

        if hold_times:
            fw.key_hold_time_ms = float(np.mean(hold_times))

        # Idle time (time since last key press, if no press in this window)
        if press_events:
            last_press = max(e.timestamp for e in press_events)
            fw.idle_time_keyboard_s = max(0.0, we - last_press)
            if self._last_key_press_time is not None:
                first_press = min(e.timestamp for e in press_events)
                gap = first_press - self._last_key_press_time
                if gap > fw.idle_time_keyboard_s:
                    fw.idle_time_keyboard_s = min(gap, self.window_seconds)
            self._last_key_press_time = last_press
        else:
            fw.idle_time_keyboard_s = self.window_seconds

        # Burst score: ratio of time actively typing vs total window
        if press_times:
            active_span = press_times[-1] - press_times[0] if len(press_times) > 1 else 0
            fw.typing_burst_score = min(active_span / self.window_seconds, 1.0)

    def _compute_mouse_features(self, moves: list, clicks: list, scrolls: list, fw: FeatureWindow):
        """Compute all mouse-derived features."""
        # ── Movement ─────────────────────────────────────
        if moves:
            positions = [(e.x, e.y, e.timestamp) for e in sorted(moves, key=lambda m: m.timestamp)]
            speeds = []
            total_dist = 0.0
            direction_changes = 0
            prev_angle = None

            for i in range(1, len(positions)):
                dx = positions[i][0] - positions[i - 1][0]
                dy = positions[i][1] - positions[i - 1][1]
                dt = positions[i][2] - positions[i - 1][2]
                dist = math.sqrt(dx ** 2 + dy ** 2)
                total_dist += dist

                if dt > 0:
                    speed = dist / dt
                    speeds.append(speed)

                # Direction changes
                if dist > 0:
                    angle = math.atan2(dy, dx)
                    if prev_angle is not None:
                        angle_diff = abs(angle - prev_angle)
                        if angle_diff > math.pi / 4:  # 45-degree threshold
                            direction_changes += 1
                    prev_angle = angle

            fw.mouse_distance_px = total_dist
            fw.direction_changes = direction_changes

            if speeds:
                fw.mouse_speed_px_s = float(np.mean(speeds))
                # Acceleration = change in speed
                if len(speeds) >= 2:
                    fw.mouse_acceleration = float(np.mean(np.diff(speeds)))

            # Idle time: time since last mouse move
            last_move_time = max(e.timestamp for e in moves)
            fw.idle_time_mouse_s = max(0.0, moves[-1].timestamp + self.window_seconds - last_move_time - self.window_seconds)
            fw.idle_time_mouse_s = 0.0  # Movement happened in this window

        else:
            fw.idle_time_mouse_s = self.window_seconds

        # ── Clicks ────────────────────────────────────────
        if clicks:
            presses = [c for c in clicks if c.pressed]
            fw.click_frequency = len(presses)
            fw.double_click_count = sum(1 for c in presses if c.is_double_click)

        # ── Scroll ────────────────────────────────────────
        if scrolls:
            scroll_dy = [abs(s.dy) for s in scrolls]
            fw.scroll_speed = float(np.mean(scroll_dy)) if scroll_dy else 0.0
            fw.scroll_distance = float(sum(scroll_dy))

        # ── Hover ─────────────────────────────────────────
        if not moves and not clicks:
            fw.hover_duration_ms = self.window_seconds * 1000.0

    @staticmethod
    def _get_time_of_day_hour() -> float:
        """Return current time as decimal hour (0-23.99)."""
        now = time.localtime()
        return now.tm_hour + now.tm_min / 60.0 + now.tm_sec / 3600.0
