"""
Tracker Main Entry Point
=========================
Orchestrates keyboard/mouse collection, aggregation, and API transmission.

Usage:
    python tracker/main.py --api-url http://localhost:8002 --token <JWT>
    python tracker/main.py --api-url http://localhost:8002 --email user@example.com --password MyPass123
"""

import argparse
import asyncio
import queue
import signal
import sys
import time
from pathlib import Path
from threading import Thread, Event

import requests
import structlog
import json
import random

# Add tracker dir to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tracker.keyboard_collector import KeyboardCollector
from tracker.mouse_collector import MouseCollector
from tracker.aggregator import FeatureAggregator

logger = structlog.get_logger(__name__)


class TrackerApp:
    """Main tracker orchestrator."""

    def __init__(self, api_url: str, token: str, session_id: str, interval: float = 1.0):
        self.api_url = api_url.rstrip("/")
        self.token = token
        self.session_id = session_id
        self.interval = interval

        # Event queues
        self._key_queue = queue.Queue(maxsize=10000)
        self._move_queue = queue.Queue(maxsize=50000)
        self._click_queue = queue.Queue(maxsize=1000)
        self._scroll_queue = queue.Queue(maxsize=5000)

        # Collectors
        self._keyboard = KeyboardCollector(self._key_queue)
        self._mouse = MouseCollector(self._move_queue, self._click_queue, self._scroll_queue)
        self._aggregator = FeatureAggregator(window_seconds=interval)

        # Control
        self._stop_event = Event()
        self._is_running = False

        # Stats
        self._windows_sent = 0
        self._errors = 0

        # Websocket Thread
        self._ws_thread = Thread(target=self._run_ws_listener, daemon=True)

    def _run_ws_listener(self):
        """Run asyncio event loop for websocket listener in a separate thread."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self._notification_loop())

    async def _notification_loop(self):
        """Listen to backend via WebSockets for high fatigue alerts to trigger popups."""
        try:
            import websockets
            from plyer import notification
        except ImportError:
            logger.warning("websockets or plyer not installed. Native notifications disabled.")
            return

        # Extract user_id from token payload without verifying sig
        try:
            import base64
            payload = self.token.split(".")[1]
            padded = payload + "=" * (-len(payload) % 4)
            user_id = json.loads(base64.b64decode(padded).decode())["sub"]
        except Exception:
            logger.error("Failed to decode token for websocket")
            return

        ws_url = self.api_url.replace("http://", "ws://").replace("https://", "wss://")
        ws_url = f"{ws_url}/ws/{user_id}?token={self.token}"

        TIPS = [
            "Time to hydrate! Drink a glass of water.",
            "Take a 5-minute stretch break.",
            "Rest your eyes: Look 20 feet away for 20 seconds.",
            "Stand up and take a quick walk.",
            "Do some deep breathing for a minute."
        ]
        
        last_notified = 0

        while self._is_running:
            try:
                async with websockets.connect(ws_url) as ws:
                    logger.info("Native Notification listener connected to WebSocket.")
                    while self._is_running:
                        msg = await ws.recv()
                        data = json.loads(msg)
                        if data.get("type") == "fatigue_alert":
                            level = data.get("level")
                            if level in ["high", "critical"]:
                                # Rate limit popups to once every 5 minutes
                                now = time.time()
                                if now - last_notified > 300:
                                    last_notified = now
                                    tip = random.choice(TIPS)
                                    notification.notify(
                                        title="MindGuard Fatigue Alert",
                                        message=f"Fatigue level is {level.upper()}. {tip}",
                                        app_name="MindGuard Tracker",
                                        timeout=10
                                    )
                                    logger.info("Desktop popup triggered", level=level, tip=tip)
            except Exception as e:
                if self._is_running:
                    logger.debug("Websocket disconnected, reconnecting in 5s...", error=str(e))
                    await asyncio.sleep(5)

    def start(self):
        """Start all collectors and the aggregation loop."""
        logger.info("Starting Mental Fatigue Tracker", api_url=self.api_url, session_id=self.session_id)

        # Start collectors in background threads
        self._keyboard.start()
        self._mouse.start()
        self._is_running = True
        self._ws_thread.start()

        logger.info("Collectors started. Monitoring keyboard and mouse activity...")
        logger.info("Press Ctrl+C to stop tracking.")

        # Run aggregation loop in main thread
        try:
            self._aggregation_loop()
        except KeyboardInterrupt:
            logger.info("Stop signal received")
        finally:
            self.stop()

    def stop(self):
        """Gracefully stop all components."""
        self._is_running = False
        self._stop_event.set()
        self._keyboard.stop()
        self._mouse.stop()

        # End session on backend
        try:
            self._end_session()
        except Exception:
            pass

        logger.info(
            "Tracker stopped",
            windows_sent=self._windows_sent,
            errors=self._errors,
        )

    def _aggregation_loop(self):
        """Main loop: every interval seconds, aggregate events and send."""
        while self._is_running:
            window_start = time.time()
            time.sleep(self.interval)
            window_end = time.time()

            # Drain queues
            key_events = self._drain_queue(self._key_queue)
            move_events = self._drain_queue(self._move_queue)
            click_events = self._drain_queue(self._click_queue)
            scroll_events = self._drain_queue(self._scroll_queue)

            # Aggregate features
            window = self._aggregator.aggregate(
                key_events=key_events,
                move_events=move_events,
                click_events=click_events,
                scroll_events=scroll_events,
                window_start=window_start,
                window_end=window_end,
            )

            # Send to API
            payload = window.to_dict()
            payload["session_id"] = self.session_id

            success = self._send_snapshot(payload)
            if success:
                self._windows_sent += 1
                if self._windows_sent % 60 == 0:  # Log every minute
                    logger.info(
                        "Tracker status",
                        windows_sent=self._windows_sent,
                        typing_wpm=round(window.typing_speed_wpm, 1),
                        mouse_speed=round(window.mouse_speed_px_s, 0),
                        errors=self._errors,
                    )
            else:
                self._errors += 1

    @staticmethod
    def _drain_queue(q: queue.Queue) -> list:
        """Extract all current items from a queue without blocking."""
        items = []
        while True:
            try:
                items.append(q.get_nowait())
            except queue.Empty:
                break
        return items

    def _send_snapshot(self, payload: dict) -> bool:
        """Send a behaviour snapshot to the API."""
        try:
            response = requests.post(
                f"{self.api_url}/api/v1/behaviour/snapshot",
                json=payload,
                headers={
                    "Authorization": f"Bearer {self.token}",
                    "Content-Type": "application/json",
                },
                timeout=5,
            )
            return response.status_code in {200, 201}
        except requests.exceptions.ConnectionError:
            logger.warning("API connection failed — will retry")
            return False
        except Exception as e:
            logger.error("Send error", error=str(e))
            return False

    def _end_session(self):
        """End the session on the backend."""
        try:
            requests.post(
                f"{self.api_url}/api/v1/sessions/end",
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=5,
            )
        except Exception:
            pass


def login(api_url: str, email: str, password: str) -> str:
    """Authenticate and return JWT token."""
    response = requests.post(
        f"{api_url}/api/v1/auth/login",
        data={"username": email, "password": password},
        timeout=10,
    )
    response.raise_for_status()
    return response.json()["access_token"]


def start_session(api_url: str, token: str) -> str:
    """Start a new tracking session and return session ID."""
    import platform
    response = requests.post(
        f"{api_url}/api/v1/sessions/start",
        json={
            "hostname": platform.node(),
            "os_platform": platform.system(),
            "tracker_version": "1.0.0",
        },
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )
    response.raise_for_status()
    return response.json()["id"]


def main():
    parser = argparse.ArgumentParser(
        description="Mental Fatigue Desktop Tracker",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--api-url", default="http://localhost:8002", help="Backend API URL")
    parser.add_argument("--token", default=None, help="JWT access token (skip login)")
    parser.add_argument("--email", default=None, help="Login email")
    parser.add_argument("--password", default=None, help="Login password")
    parser.add_argument("--interval", type=float, default=1.0, help="Aggregation interval (seconds)")
    parser.add_argument("--session-id", default=None, help="Existing session ID (skip session creation)")

    args = parser.parse_args()

    # Authenticate
    token = args.token
    if not token:
        if not args.email or not args.password:
            parser.error("Provide either --token or both --email and --password")
        print(f"Authenticating as {args.email}...")
        token = login(args.api_url, args.email, args.password)
        print("Authentication successful")

    # Start session
    session_id = args.session_id
    if not session_id:
        print("Starting new tracking session...")
        session_id = start_session(args.api_url, token)
        print(f"Session started: {session_id}")

    # Start tracker
    tracker = TrackerApp(
        api_url=args.api_url,
        token=token,
        session_id=session_id,
        interval=args.interval,
    )

    # Handle SIGTERM for graceful shutdown in production
    signal.signal(signal.SIGTERM, lambda s, f: tracker.stop())

    tracker.start()


if __name__ == "__main__":
    main()
