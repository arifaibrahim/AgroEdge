"""
AgroEdge AI - Configuration
Central place for every threshold, range, and setting used across
the backend. Change values here instead of hunting through files.
"""

import os

# ---------------------------------------------------------
# DATABASE
# ---------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")
MAX_STORED_RECORDS = 100  # keep storage lightweight, no data warehouse

# ---------------------------------------------------------
# REFRESH INTERVALS (used by frontend polling via /api/status)
# ---------------------------------------------------------
NORMAL_REFRESH_MS = 3000        # 3 seconds
POWER_SAVING_REFRESH_MS = 10000  # 10 seconds

# ---------------------------------------------------------
# SENSOR SIMULATION RANGES
# Format: (min_value, max_value, max_drift_per_step)
# ---------------------------------------------------------
SENSOR_RANGES = {
    "soil_moisture":   (10.0, 90.0, 2.0),
    "temperature":     (15.0, 45.0, 1.0),
    "humidity":        (20.0, 95.0, 2.0),
    "light_intensity": (0.0, 1200.0, 40.0),
    "wind_speed":      (0.0, 40.0, 1.5),
    "battery_level":   (0.0, 100.0, 0.0),  # battery drains separately, not drifted
}

SOLAR_CHARGE_THRESHOLD = 300.0  # light_intensity above this => solar panel charging

# ---------------------------------------------------------
# DECISION ENGINE - IDEAL RANGES (used for health score)
# ---------------------------------------------------------
IDEAL_SOIL_MOISTURE = (40.0, 60.0)
IDEAL_TEMPERATURE = (20.0, 30.0)
IDEAL_HUMIDITY = (40.0, 65.0)
IDEAL_LIGHT = (400.0, 900.0)

# ---------------------------------------------------------
# DECISION ENGINE - ALERT THRESHOLDS
# ---------------------------------------------------------
LOW_MOISTURE_THRESHOLD = 30.0
HIGH_MOISTURE_THRESHOLD = 75.0
HEAT_STRESS_THRESHOLD = 35.0
HIGH_HUMIDITY_THRESHOLD = 80.0
LOW_LIGHT_THRESHOLD = 150.0
HIGH_WIND_THRESHOLD = 30.0
LOW_BATTERY_THRESHOLD = 20.0

# ---------------------------------------------------------
# PREDICTION MODULE
# ---------------------------------------------------------
PREDICTION_WINDOW = 20          # how many recent records to use for trend fitting
PREDICTION_STEPS_AHEAD = 2      # steps ahead to extrapolate
PREDICTION_HORIZON_MINUTES = 10  # label shown to the farmer ("next 10 minutes")

# ---------------------------------------------------------
# DISEASE DETECTION - COLOR HEURISTIC THRESHOLDS
# ---------------------------------------------------------
RUST_RED_THRESHOLD = 120.0
RUST_RED_GREEN_GAP = 25.0
MILDEW_BRIGHTNESS_THRESHOLD = 180.0
MILDEW_SATURATION_MAX = 0.15