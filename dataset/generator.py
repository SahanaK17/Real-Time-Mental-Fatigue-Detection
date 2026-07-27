"""
Synthetic Dataset Generator
============================
Generates 150,000+ rows of realistic behavioural data for
mental fatigue detection model training.

Design Principles:
  - Feature distributions based on scientific literature
  - Fatigue labels generated via probabilistic rules
  - Correlations between features are realistic
  - Temporal patterns (time-of-day, session duration effects)
  - Configurable noise level
  - Reproducible with a fixed seed

Usage:
    python generator.py --rows 150000 --output dataset/generated/fatigue_data.csv
    python generator.py --rows 50000 --noise 0.15 --seed 42
"""

import argparse
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from datetime import datetime

# ── Scientific Distributions ──────────────────────────────
#
# Based on:
# - Salthouse (1984) typing speed: mean ~55 WPM, std ~20
# - Gao et al. (2012) key hold time: 70-150ms normal
# - Zheng et al. (2011) flight time: 100-250ms
# - Jansen et al. (2018) mouse speed: 150-600 px/s
# - Multiple fatigue studies for behavioral shifts


class FatigueDatasetGenerator:
    """
    Generates synthetic behavioural monitoring data with realistic
    fatigue labels using multi-factor probabilistic scoring.
    """

    def __init__(self, seed: int = 42, noise_level: float = 0.10):
        self.rng = np.random.default_rng(seed)
        self.noise_level = noise_level

    def generate(self, n_samples: int = 150_000) -> pd.DataFrame:
        """
        Generate a complete dataset with n_samples rows.

        Returns:
            DataFrame with features and binary/multi-class fatigue labels.
        """
        print(
            f"[*] Generating {n_samples:,} samples (seed={self.rng.bit_generator.state['state']['state']})"
        )

        # Step 1: Generate user profiles (simulate diverse employee types)
        print("  → Generating user profiles...")
        profiles = self._generate_user_profiles(n_samples)

        # Step 2: Generate contextual features
        print("  → Generating contextual features...")
        context = self._generate_context(n_samples, profiles)

        # Step 3: Generate keyboard metrics (influenced by fatigue state)
        print("  → Generating keyboard metrics...")
        keyboard = self._generate_keyboard_metrics(n_samples, context, profiles)

        # Step 4: Generate mouse metrics
        print("  → Generating mouse metrics...")
        mouse = self._generate_mouse_metrics(n_samples, context, keyboard, profiles)

        # Step 5: Compute probabilistic fatigue labels
        print("  → Computing fatigue labels...")
        labels = self._compute_fatigue_labels(keyboard, mouse, context, profiles)

        # Step 6: Assemble final DataFrame
        df = pd.DataFrame(
            {
                # Context
                "user_id": profiles["user_id"],
                "session_length_minutes": context["session_length"],
                "time_of_day_hour": context["time_of_day"],
                "day_of_week": context["day_of_week"],
                "previous_fatigue_score": context["prev_fatigue"],
                "stress_index": context["stress_index"],
                "break_frequency_per_hour": context["break_freq"],
                "sleep_hours_last_night": context["sleep_hours"],
                "coffee_intake_cups": context["coffee_cups"],
                "workload_score": context["workload"],
                "task_complexity": context["task_complexity"],
                "productivity_score": context["productivity"],
                # Keyboard
                "typing_speed_wpm": keyboard["speed_wpm"],
                "typing_speed_cpm": keyboard["speed_cpm"],
                "key_hold_time_ms": keyboard["hold_time"],
                "flight_time_ms": keyboard["flight_time"],
                "backspace_count_per_min": keyboard["backspace_rate"],
                "error_rate": keyboard["error_rate"],
                "idle_time_keyboard_s": keyboard["idle_time"],
                "typing_burst_score": keyboard["burst_score"],
                "typing_rhythm_variance": keyboard["rhythm_var"],
                "total_keystrokes_per_min": keyboard["keystrokes"],
                # Mouse
                "mouse_speed_px_s": mouse["speed"],
                "mouse_acceleration": mouse["acceleration"],
                "mouse_distance_px_per_min": mouse["distance"],
                "click_frequency_per_min": mouse["clicks"],
                "double_click_rate": mouse["double_clicks"],
                "scroll_speed": mouse["scroll_speed"],
                "idle_time_mouse_s": mouse["idle_time"],
                "direction_changes_per_min": mouse["direction_changes"],
                "hover_duration_ms": mouse["hover"],
                "drag_count_per_min": mouse["drags"],
                # Labels
                "fatigue_score": labels["fatigue_score"],
                "fatigue_label": labels["fatigue_label"],  # Binary: 0=alert, 1=fatigued
                "fatigue_level": labels[
                    "fatigue_level"
                ],  # Multi: alert/mild/moderate/high/critical
            }
        )

        print(f"  → Dataset shape: {df.shape}")
        print(f"  → Fatigue distribution:\n{df['fatigue_level'].value_counts().to_string()}")

        return df

    # ── Profile Generation ────────────────────────────────

    def _generate_user_profiles(self, n: int) -> dict:
        """
        Simulate diverse employee types with different baseline behaviors.
        Fast typists, slow typists, power users, casual users.
        """
        n_users = min(n, 1000)  # Simulate up to 1000 unique users
        user_ids = self.rng.integers(1, n_users + 1, size=n)

        # Base typing speed per user (WPM) — some users type faster
        user_base_speed = self.rng.normal(55, 20, size=n_users + 1).clip(10, 130)
        # Base mouse precision per user
        user_mouse_skill = self.rng.uniform(0.3, 1.0, size=n_users + 1)

        return {
            "user_id": user_ids,
            "base_speed": user_base_speed[user_ids],
            "mouse_skill": user_mouse_skill[user_ids],
        }

    # ── Context Generation ────────────────────────────────

    def _generate_context(self, n: int, profiles: dict) -> dict:
        """Generate contextual and environmental features."""
        rng = self.rng

        # Session length: 5-480 minutes (bimodal: short bursts and long sessions)
        short_sessions = rng.exponential(30, size=n)
        long_sessions = rng.normal(180, 60, size=n)
        session_mix = rng.uniform(0, 1, size=n)
        session_length = np.where(session_mix < 0.4, short_sessions, long_sessions).clip(5, 480)

        # Time of day: concentrated around work hours (9am - 6pm)
        time_of_day = rng.normal(13, 3, size=n).clip(0, 23.99)

        # Day of week (0=Mon, 6=Sun) — weight toward weekdays
        day_probs = [0.22, 0.22, 0.22, 0.22, 0.12, 0.0, 0.0]  # Mon-Sun
        day_of_week = rng.choice(7, size=n, p=day_probs)

        # Previous fatigue (carry-over effect)
        prev_fatigue = rng.beta(2, 5, size=n)  # Mostly low

        # Stress index (0-1)
        stress_index = rng.beta(2, 3, size=n)

        # Break frequency (times per hour)
        break_freq = rng.exponential(0.5, size=n).clip(0, 4)

        # Sleep hours (6-9 hours, biased toward 7)
        sleep_hours = rng.normal(7, 1.2, size=n).clip(3, 10)

        # Coffee intake
        coffee_cups = rng.choice([0, 1, 2, 3, 4, 5], size=n, p=[0.2, 0.3, 0.3, 0.1, 0.07, 0.03])

        # Workload (0-1)
        workload = rng.beta(3, 2, size=n)  # Moderately high

        # Task complexity (0-1)
        task_complexity = rng.uniform(0, 1, size=n)

        # Productivity score (0-1)
        productivity = (
            1 - prev_fatigue * 0.5 + sleep_hours / 20 + rng.normal(0, 0.1, size=n)
        ).clip(0, 1)

        return {
            "session_length": session_length,
            "time_of_day": time_of_day,
            "day_of_week": day_of_week,
            "prev_fatigue": prev_fatigue,
            "stress_index": stress_index,
            "break_freq": break_freq,
            "sleep_hours": sleep_hours,
            "coffee_cups": coffee_cups.astype(float),
            "workload": workload,
            "task_complexity": task_complexity,
            "productivity": productivity,
        }

    # ── Keyboard Metrics ──────────────────────────────────

    def _generate_keyboard_metrics(self, n: int, ctx: dict, profiles: dict) -> dict:
        """
        Generate keyboard metrics that degrade with fatigue.
        Fatigue latent variable is computed from context.
        """
        rng = self.rng

        # Compute latent fatigue factor (0-1) from context
        # This drives how much degradation occurs
        latent_fatigue = (
            0.35 * (ctx["session_length"] / 480)  # Session duration effect
            + 0.25 * (1 - ctx["sleep_hours"] / 10)  # Sleep deprivation
            + 0.20 * ctx["prev_fatigue"]  # Carry-over fatigue
            + 0.15 * ctx["stress_index"]  # Stress effect
            + 0.05 * ctx["workload"]  # Workload
        ).clip(0, 1)

        # Post-lunch dip (13:00-15:00 has natural fatigue spike)
        post_lunch = np.exp(-0.5 * ((ctx["time_of_day"] - 14) / 1.5) ** 2) * 0.15
        latent_fatigue = (latent_fatigue + post_lunch).clip(0, 1)

        # Fatigue degrades typing speed by up to 40%
        speed_degradation = 1 - latent_fatigue * 0.40
        speed_wpm = (profiles["base_speed"] * speed_degradation + rng.normal(0, 5, size=n)).clip(
            5, 130
        )
        speed_cpm = speed_wpm * 5 + rng.normal(0, 15, size=n)

        # Fatigue increases key hold time (slower motor responses)
        base_hold = 90  # ms
        hold_time = (base_hold + latent_fatigue * 60 + rng.normal(0, 15, size=n)).clip(30, 400)

        # Fatigue increases flight time
        base_flight = 150  # ms
        flight_time = (base_flight + latent_fatigue * 120 + rng.normal(0, 30, size=n)).clip(50, 800)

        # Fatigue increases error/backspace rate
        base_backspace = 1.5  # per minute
        backspace_rate = (base_backspace + latent_fatigue * 6 + rng.exponential(1, size=n)).clip(
            0, 30
        )
        error_rate = (backspace_rate / (speed_cpm + 1)).clip(0, 0.5)

        # Idle time increases with fatigue
        idle_time = (rng.exponential(5, size=n) + latent_fatigue * 25).clip(0, 120)

        # Burst score decreases with fatigue (less rhythmic, more hesitant)
        burst_score = (1 - latent_fatigue * 0.6 + rng.normal(0, 0.1, size=n)).clip(0, 1)

        # Rhythm variance increases with fatigue
        rhythm_var = (10 + latent_fatigue * 80 + rng.exponential(10, size=n)).clip(1, 500)

        # Keystrokes per minute
        keystrokes = (speed_cpm + rng.normal(0, 10, size=n)).clip(0, 600)

        return {
            "speed_wpm": speed_wpm,
            "speed_cpm": speed_cpm,
            "hold_time": hold_time,
            "flight_time": flight_time,
            "backspace_rate": backspace_rate,
            "error_rate": error_rate,
            "idle_time": idle_time,
            "burst_score": burst_score,
            "rhythm_var": rhythm_var,
            "keystrokes": keystrokes,
            "_latent_fatigue": latent_fatigue,
        }

    # ── Mouse Metrics ─────────────────────────────────────

    def _generate_mouse_metrics(self, n: int, ctx: dict, keyboard: dict, profiles: dict) -> dict:
        """
        Generate mouse metrics correlated with keyboard fatigue state.
        Mouse metrics show distinct patterns under fatigue.
        """
        rng = self.rng
        latent_fatigue = keyboard["_latent_fatigue"]
        mouse_skill = profiles["mouse_skill"]

        # Mouse speed decreases with fatigue
        base_speed = 350 * mouse_skill
        speed = (base_speed * (1 - latent_fatigue * 0.35) + rng.normal(0, 50, size=n)).clip(
            20, 1500
        )

        # Acceleration becomes more erratic
        acceleration = (rng.normal(0, 100, size=n) * (1 + latent_fatigue * 1.5)).clip(-500, 500)

        # Distance per minute decreases
        distance = (speed * 2 + rng.normal(0, 200, size=n)).clip(0, 8000)

        # Click frequency decreases with fatigue
        base_clicks = 8.0  # clicks per minute
        clicks = (base_clicks * (1 - latent_fatigue * 0.5) + rng.exponential(2, size=n)).clip(0, 40)

        # Double click rate (misclicks increase with fatigue)
        double_clicks = (0.5 + latent_fatigue * 2 + rng.exponential(0.3, size=n)).clip(0, 10)

        # Scroll speed
        scroll_speed = (200 + latent_fatigue * -50 + rng.normal(0, 30, size=n)).clip(0, 500)

        # Mouse idle time increases with fatigue
        idle_time = (rng.exponential(3, size=n) + latent_fatigue * 20).clip(0, 120)

        # Direction changes (jitter) increases with fatigue
        direction_changes = (30 + latent_fatigue * 50 + rng.normal(0, 10, size=n)).clip(0, 200)

        # Hover duration increases (user is more uncertain)
        hover = (200 + latent_fatigue * 600 + rng.exponential(100, size=n)).clip(0, 3000)

        # Drag count
        drags = rng.poisson(2 * (1 - latent_fatigue * 0.4), size=n).clip(0, 20).astype(float)

        return {
            "speed": speed,
            "acceleration": acceleration,
            "distance": distance,
            "clicks": clicks,
            "double_clicks": double_clicks,
            "scroll_speed": scroll_speed,
            "idle_time": idle_time,
            "direction_changes": direction_changes,
            "hover": hover,
            "drags": drags,
        }

    # ── Label Generation ──────────────────────────────────

    def _compute_fatigue_labels(
        self, keyboard: dict, mouse: dict, ctx: dict, profiles: dict
    ) -> dict:
        """
        Compute fatigue scores using a multi-factor probabilistic model.
        Labels are NOT random — they are derived from behavioral signals
        using weighted combination with configurable noise.
        """
        lf = keyboard["_latent_fatigue"]

        # Primary signal: deviation from baseline behaviors
        # Typing speed degradation (normalized)
        speed_signal = 1 - (keyboard["speed_wpm"] / (profiles["base_speed"] + 1e-6)).clip(0, 1)

        # Error rate signal
        error_signal = (keyboard["error_rate"] / 0.3).clip(0, 1)

        # Idle time signal (keyboard + mouse combined)
        idle_signal = ((keyboard["idle_time"] + mouse["idle_time"]) / 60).clip(0, 1)

        # Rhythm disruption
        rhythm_signal = (keyboard["rhythm_var"] / 200).clip(0, 1)

        # Mouse jitter
        jitter_signal = (mouse["direction_changes"] / 100).clip(0, 1)

        # Mouse inactivity
        mouse_idle_signal = (mouse["idle_time"] / 60).clip(0, 1)

        # Sleep deprivation signal
        sleep_signal = (1 - ctx["sleep_hours"] / 10).clip(0, 1)

        # Session duration fatigue
        duration_signal = (ctx["session_length"] / 480).clip(0, 1)

        # Weighted composite fatigue score
        fatigue_score_clean = (
            0.20 * speed_signal
            + 0.20 * error_signal
            + 0.15 * idle_signal
            + 0.15 * rhythm_signal
            + 0.10 * jitter_signal
            + 0.10 * mouse_idle_signal
            + 0.05 * sleep_signal
            + 0.05 * duration_signal
        )

        # Add calibrated noise
        noise = self.rng.normal(0, self.noise_level, size=len(lf))
        fatigue_score = (fatigue_score_clean + noise).clip(0, 1)

        # Binary label
        fatigue_label = (fatigue_score >= 0.5).astype(int)

        # Multi-class label
        def to_level(score):
            if score < 0.25:
                return "alert"
            elif score < 0.50:
                return "mild"
            elif score < 0.70:
                return "moderate"
            elif score < 0.85:
                return "high"
            else:
                return "critical"

        fatigue_level = np.vectorize(to_level)(fatigue_score)

        return {
            "fatigue_score": np.round(fatigue_score, 4),
            "fatigue_label": fatigue_label,
            "fatigue_level": fatigue_level,
        }

    def add_noise(self, df: pd.DataFrame, noise_fraction: float = 0.03) -> pd.DataFrame:
        """
        Flip a small fraction of labels to simulate real-world annotation noise.
        """
        n_flip = int(len(df) * noise_fraction)
        flip_idx = self.rng.choice(len(df), size=n_flip, replace=False)
        df.loc[flip_idx, "fatigue_label"] = 1 - df.loc[flip_idx, "fatigue_label"]
        return df

    def save(self, df: pd.DataFrame, output_path: str) -> None:
        """Save dataset to CSV and print statistics."""
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)

        print(f"\n[OK] Dataset saved to: {output_path}")
        print(f"   Rows: {len(df):,}")
        print(f"   Columns: {len(df.columns)}")
        print(f"   File size: {os.path.getsize(output_path) / 1024 / 1024:.1f} MB")
        print(f"\n   Label distribution:")
        print(f"   {df['fatigue_label'].value_counts().to_dict()}")
        print(f"\n   Fatigue level distribution:")
        print(f"   {df['fatigue_level'].value_counts().to_dict()}")
        print(f"\n   Feature statistics:")
        print(
            df[["typing_speed_wpm", "error_rate", "mouse_speed_px_s", "idle_time_keyboard_s"]]
            .describe()
            .round(3)
            .to_string()
        )


def main():
    parser = argparse.ArgumentParser(
        description="Generate synthetic mental fatigue dataset",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--rows", type=int, default=150_000, help="Number of samples to generate")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument("--noise", type=float, default=0.10, help="Gaussian noise level (0-1)")
    parser.add_argument("--label-noise", type=float, default=0.03, help="Label flip noise fraction")
    parser.add_argument(
        "--output",
        type=str,
        default="dataset/generated/fatigue_data.csv",
        help="Output CSV path",
    )

    args = parser.parse_args()

    print("============================================================")
    print("  Mental Fatigue Synthetic Dataset Generator")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("============================================================")

    generator = FatigueDatasetGenerator(seed=args.seed, noise_level=args.noise)
    df = generator.generate(n_samples=args.rows)
    df = generator.add_noise(df, noise_fraction=args.label_noise)
    generator.save(df, args.output)

    print("\nDone! Use scripts/train_models.py to train the ML pipeline.")


if __name__ == "__main__":
    main()
