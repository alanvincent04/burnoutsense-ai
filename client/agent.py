import time
import requests
import random
import os
from datetime import datetime
from threading import Thread

try:
    from pynput import keyboard, mouse
    PYNPUT_AVAILABLE = True
except Exception:
    PYNPUT_AVAILABLE = False
    print("WARNING - pynput not available, using simulated input data")


class BurnoutAgent:

    def __init__(self, employee_id, api_url, token, interval=30):
        self.employee_id = employee_id
        self.api_url = api_url
        self.token = token
        self.interval = interval

        # Session tracking
        self.session_start = time.time()
        self.last_activity = time.time()

        # Real typing tracking
        self.last_key_time = None
        self.typing_speeds = []
        self.total_keystrokes = 0

        # Real break tracking
        self.breaks = []
        self.last_break_start = None

        # Real mouse tracking
        self.mouse_moves = 0

        print(f"INFO - Agent initialized for employee: {employee_id}")
        print(f"INFO - Keyboard tracking: {'ON (Real Data)' if PYNPUT_AVAILABLE else 'OFF (Simulated)'}")

    # ── REAL KEYBOARD LISTENER ──────────────────────────────────────────
    def on_key_press(self, key):
        """Records TIMING only — never the key content."""
        now = time.time()
        self.total_keystrokes += 1
        self.last_activity = now

        if self.last_key_time is not None:
            gap = now - self.last_key_time

            if gap < 2.0:
                # Active typing — calculate WPM from gap
                wpm = min(200, 60.0 / (gap * 5.0))
                self.typing_speeds.append(wpm)

            elif gap > 300:
                # Gap over 5 minutes = break detected
                if self.last_break_start is None:
                    self.last_break_start = self.last_key_time
                break_duration = now - self.last_break_start
                self.breaks.append(break_duration)
                self.last_break_start = None

        self.last_key_time = now

    # ── REAL MOUSE LISTENER ─────────────────────────────────────────────
    def on_mouse_move(self, x, y):
        self.last_activity = time.time()
        self.mouse_moves += 1

    # ── FEATURE COMPUTATIONS ────────────────────────────────────────────
    def get_typing_speed_variation(self):
        """Real: max-min WPM spread. Higher = more cognitive fatigue."""
        recent = self.typing_speeds[-200:] if self.typing_speeds else []
        if len(recent) >= 5:
            return round(max(recent) - min(recent), 2)
        elif PYNPUT_AVAILABLE:
            return round(random.uniform(5, 20), 2)  # warm-up period
        else:
            return round(random.uniform(10, 45), 2)  # simulated

    def get_idle_time_pct(self):
        """Real: how much of the session has been inactive."""
        now = time.time()
        idle_seconds = now - self.last_activity
        session_seconds = now - self.session_start
        if session_seconds < 10:
            return 0.0
        pct = (idle_seconds / session_seconds) * 100
        return round(min(pct, 98.0), 1)

    def get_session_duration_hrs(self):
        """Real: actual time since agent started."""
        return round((time.time() - self.session_start) / 3600.0, 2)

    def get_break_irregularity(self):
        """Real: variance in break timing. 0=regular, 10=chaotic."""
        if len(self.breaks) >= 2:
            diffs = [abs(self.breaks[i] - self.breaks[i-1])
                     for i in range(1, len(self.breaks))]
            mean_diff = sum(diffs) / len(diffs)
            return round(min(10.0, mean_diff / 360.0), 2)
        elif len(self.breaks) == 0:
            # No breaks taken yet — irregularity grows with session time
            hrs = self.get_session_duration_hrs()
            return round(min(10.0, hrs * 0.8), 2)
        else:
            return 5.0  # only 1 break, neutral score

    def get_work_hour_deviation(self):
        """Real: how far your current hour is from 9AM baseline."""
        current_hour = datetime.now().hour
        return round(abs(current_hour - 9), 2)

    def get_task_completion_rate(self):
        """
        Simulated: decreases as session gets longer.
        To make this real, connect to Jira/Asana/Trello API here.
        """
        hrs = self.get_session_duration_hrs()
        noise = random.uniform(-8, 8)
        rate = 90 - (hrs * 6) + noise
        return round(max(10.0, min(100.0, rate)), 1)

    def compute_features(self):
        """Bundle all 6 features into one payload."""
        return {
            "employee_id": self.employee_id,
            "timestamp": datetime.utcnow().isoformat(),
            "typing_speed_variation": self.get_typing_speed_variation(),
            "idle_time_pct": self.get_idle_time_pct(),
            "session_duration_hrs": self.get_session_duration_hrs(),
            "break_irregularity_index": self.get_break_irregularity(),
            "work_hour_deviation": self.get_work_hour_deviation(),
            "task_completion_rate": self.get_task_completion_rate(),
        }

    # ── SEND DATA ────────────────────────────────────────────────────────
    def send_data(self):
        try:
            payload = self.compute_features()

            # Print what is being sent
            print(f"\n--- Sending Data [{datetime.now().strftime('%H:%M:%S')}] ---")
            print(f"  Typing Variation : {payload['typing_speed_variation']} WPM")
            print(f"  Idle Time        : {payload['idle_time_pct']}%")
            print(f"  Session Duration : {payload['session_duration_hrs']} hrs")
            print(f"  Break Irregularity: {payload['break_irregularity_index']}/10")
            print(f"  Work Hr Deviation: {payload['work_hour_deviation']} hrs")
            print(f"  Task Completion  : {payload['task_completion_rate']}%")

            response = requests.post(
                f"{self.api_url}/api/v1/activity/log",
                json=payload,
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=10
            )
            if response.status_code == 201:
                result = response.json()
                level = result["risk"]["level"]
                score = result["risk"]["score"]
                conf  = result["risk"]["confidence"]
                colors = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}
                print(f"  RESULT → {colors.get(level,'')} {level} Risk | Score: {score}/100 | Confidence: {conf*100:.1f}%")
            else:
                print(f"  WARNING - API returned {response.status_code}")

        except Exception as e:
            print(f"  ERROR - {e}")

    def _send_loop(self):
        while True:
            time.sleep(self.interval)
            self.send_data()

    # ── MAIN RUN ─────────────────────────────────────────────────────────
    def run(self):
        print("INFO - BurnoutSense Agent starting...")

        # Start background sender
        sender = Thread(target=self._send_loop, daemon=True)
        sender.start()

        if PYNPUT_AVAILABLE:
            # Start real keyboard and mouse listeners
            print("INFO - Real keyboard + mouse tracking active")
            print("INFO - Monitoring active. Press Ctrl+C to stop.\n")
            with keyboard.Listener(on_press=self.on_key_press), \
                 mouse.Listener(on_move=self.on_mouse_move):
                try:
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    print("\nINFO - Agent stopped.")
        else:
            # Fallback simulation mode
            print("INFO - Running in simulation mode")
            print("INFO - Monitoring active. Press Ctrl+C to stop.\n")
            try:
                while True:
                    time.sleep(1)
                    # Simulate occasional activity
                    if random.random() < 0.3:
                        self.last_activity = time.time()
            except KeyboardInterrupt:
                print("\nINFO - Agent stopped.")


if __name__ == "__main__":
    agent = BurnoutAgent(
        employee_id=os.getenv("EMPLOYEE_ID", "emp_001"),
        api_url=os.getenv("API_URL", "http://localhost:5000"),
        token=os.getenv("AGENT_TOKEN", "test-token"),
        interval=30
    )
    agent.run()