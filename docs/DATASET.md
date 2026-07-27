# Dataset

This document describes the synthetic dataset used to train the MindGuard fatigue detection model — including the generation methodology, assumptions, limitations, and validation strategy.

---

**Navigation:** [← Back to README](../README.md) | [Model Details](MODEL_DETAILS.md)

---

## Table of Contents

- [Why Synthetic Data?](#why-synthetic-data)
- [Generation Methodology](#generation-methodology)
- [Dataset Schema](#dataset-schema)
- [Label Generation](#label-generation)
- [Class Distribution](#class-distribution)
- [Assumptions & Limitations](#assumptions--limitations)
- [Ethical Considerations](#ethical-considerations)
- [Validation Strategy](#validation-strategy)
- [Generating the Dataset](#generating-the-dataset)

---

## Why Synthetic Data?

Real-world psychomotor fatigue datasets — containing labeled keyboard/mouse behavioral measurements tied to verified cognitive fatigue states — are:

1. **Extremely scarce.** Collection requires controlled lab settings, participant consent, validated fatigue protocols (e.g., Karolinska Sleepiness Scale), and IRB approval.
2. **Heavily privacy-restricted.** HCI behavioral data contains implicit identifying information (typing rhythm is unique to individuals), making public sharing rare.
3. **Expensive to collect at scale.** Studies typically involve 20–100 participants over a few sessions. Millions of observations require years of data collection.

Synthetic data allows us to:
- Prototype the full ML pipeline and system architecture
- Validate that the inference API and WebSocket pipeline work end-to-end
- Demonstrate the ML methodology to technical reviewers
- Generate sufficient volume for statistical training

> **This does not mean the model is production-ready for real fatigue prediction without validation on real-world data.** See [Limitations](#assumptions--limitations).

---

## Generation Methodology

The `dataset/generator.py` uses a **multi-stage physiological simulation approach**:

### Stage 1: User Profiles
Up to 1,000 unique synthetic "employees" are simulated. Each has:
- A baseline typing speed (drawn from N(55, 20) WPM, clipped 10–130)
- A mouse precision coefficient (U(0.3, 1.0))

This simulates the real-world diversity between fast typists, casual users, and power users.

### Stage 2: Contextual Features
Each observation is assigned a contextual state representing the session environment:
- **Session length** — bimodal distribution (short bursts + long sessions)
- **Time of day** — N(13, 3) clipped to 0–24 (concentrated around work hours)
- **Day of week** — weighted toward weekdays (Mon–Fri)
- **Sleep hours** — N(7, 1.2), clipped 3–10
- **Stress index** — Beta(2, 3)
- **Workload** — Beta(3, 2)

### Stage 3: Behavioral Metrics
Keyboard and mouse metrics are **degraded proportionally to the contextual fatigue state**:

- Fatigue increases key hold time, flight time, error rate, and idle periods
- Fatigue decreases typing speed, mouse velocity, and click frequency
- Gaussian noise (configurable, default 10%) is added to simulate natural variation

Scientific references used to calibrate baseline distributions:
- Salthouse (1984): mean typing speed ~55 WPM, std ~20
- Gao et al. (2012): key hold time 70–150ms normal range
- Zheng et al. (2011): flight time 100–250ms
- Jansen et al. (2018): mouse speed 150–600 px/s

### Stage 4: Label Generation
Labels are not directly assigned based on contextual features — they are computed from the **resulting behavioral signals** using a weighted scoring function. See [Label Generation](#label-generation).

---

## Dataset Schema

| Column | Type | Description |
|:---|:---:|:---|
| `user_id` | int | Synthetic user ID (1–1000) |
| `session_length_minutes` | float | Session duration |
| `time_of_day_hour` | float | Decimal hour (0–24) |
| `day_of_week` | int | 0=Monday, 6=Sunday |
| `stress_index` | float | Simulated stress level (0–1) |
| `typing_speed_wpm` | float | Words per minute |
| `key_hold_time_ms` | float | Average key dwell time |
| `flight_time_ms` | float | Inter-keystroke interval |
| `error_rate` | float | Backspace / total keystrokes |
| `idle_time_keyboard_s` | float | Seconds without keypress |
| `mouse_speed_px_s` | float | Average cursor velocity |
| `direction_changes_per_min` | float | Mouse jitter |
| `idle_time_mouse_s` | float | Seconds without mouse movement |
| `fatigue_score` | float | Continuous score (0–1) |
| `fatigue_label` | int | Binary: 0=alert, 1=fatigued |
| `fatigue_level` | str | Multi-class: alert/mild/moderate/high/critical |

---

## Label Generation

**Labels are derived from behavioral signals, not injected from context.** The scoring function:

```python
fatigue_score = (
    0.25 * normalized_error_rate
  + 0.20 * normalized_idle_keyboard
  + 0.15 * normalized_idle_mouse
  + 0.15 * normalized_rhythm_variance
  + 0.10 * normalized_hold_time
  + 0.15 * normalized_direction_changes
)
```

Binary label (`fatigue_label`): `1` if `fatigue_score >= 0.50`, else `0`.

Multi-class label (`fatigue_level`): Bucketed into alert/mild/moderate/high/critical.

This approach ensures labels are **grounded in the observable behavioral signals**, not in unobservable contextual variables like sleep hours or stress index.

> **Important:** `previous_fatigue_score` appears in the raw dataset schema but was **excluded** from the training feature set. Including it would constitute direct target leakage.

---

## Class Distribution

At default settings (150,000 rows, noise=0.10):

| Class | Count | % |
|:---|:---:|:---:|
| Alert | ~75,000 | ~50% |
| Fatigued | ~75,000 | ~50% |

The generator is tuned to produce approximately balanced classes. Imbalance in the actual generated file may vary due to noise.

---

## Assumptions & Limitations

| Assumption | Impact if Wrong |
|:---|:---|
| Behavioral degradation patterns match real-world fatigue | Model may perform poorly on real data |
| Linear relationship between fatigue level and feature degradation | Non-linear real-world effects would not be captured |
| Static individual baselines | Real users adapt to fatigue; dynamic baselines would be more accurate |
| No physiological noise correlation | In reality, fatigue patterns are correlated across features in complex ways |

### What This Dataset Cannot Validate

- Real fatigue states (only simulated ones)
- Individual differences and adaptation
- Effects of medication, caffeine, or health conditions
- Long-term behavioral drift

---

## Ethical Considerations

- No real user data was collected or used
- The generator uses published scientific distributions as references only
- The system is designed for **wellness support, not surveillance**
- All generated user IDs are integers with no connection to real people
- The model should not be used for HR decisions without real-world validation and ethical review

---

## Validation Strategy

To responsibly deploy MindGuard with real users, the following validation steps are recommended:

1. **Ground truth collection:** Recruit participants, collect HCI data during controlled fatigue sessions, validate against subjective ratings (KSS, NASA-TLX) and objective measures (EEG, reaction time).
2. **Model retraining:** Fine-tune the LightGBM model on the collected real-world dataset.
3. **Cross-population validation:** Validate across different user groups (age, profession, typing skill).
4. **Temporal validation:** Test prediction accuracy over extended real-world monitoring sessions.

---

## Generating the Dataset

```bash
# Default: 150,000 rows, noise=10%, seed=42
python dataset/generator.py

# Custom settings
python dataset/generator.py \
  --rows 50000 \
  --noise 0.15 \
  --seed 123 \
  --output dataset/generated/fatigue_data.csv

# Output: dataset/generated/fatigue_data.csv (~80MB)
```
