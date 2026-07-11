"""
AgroEdge AI - Sensor Module
Simulates local sensor readings. Designed so that swapping in
real ESP32 sensor data later only requires editing this file.
"""

import random
import time
import config

# Keeps track of the last reading so values drift realistically
# instead of jumping randomly every call (mimics real sensors).
_last_reading = {
    "soil_moisture": 45.0,
    "temperature": 27.0,
    "humidity": 55.0,
    "light_intensity": 600.0,
    "wind_speed": 5.0,
    "battery_level": 82.0
}


def _drift(current, min_val, max_val, max_step):
    """Moves a value slightly up or down within realistic bounds."""
    step = random.uniform(-max_step, max_step)
    new_val = current + step
    return round(max(min_val, min(max_val, new_val)), 2)


def read_sensors(power_mode="normal"):
    """
    Returns one simulated sensor reading.

    In power_saving mode, fewer sensors are actively refreshed
    each cycle (mimics duty-cycling real sensors to save energy) —
    the rest hold their last known value.
    """
    global _last_reading

    # Sensors always refreshed even in power saving mode
    # (critical for safety / irrigation decisions)
    always_refresh = ["soil_moisture", "battery_level"]

    # Sensors that only refresh every cycle in normal mode,
    # but are skipped some cycles in power saving mode
    optional_refresh = ["temperature", "humidity", "light_intensity", "wind_speed"]

    for key in always_refresh:
        min_v, max_v, step = config.SENSOR_RANGES[key]
        _last_reading[key] = _drift(_last_reading[key], min_v, max_v, step)

    for key in optional_refresh:
        if power_mode == "power_saving" and random.random() < 0.5:
            # Skip this cycle, reuse last value to save compute
            continue
        min_v, max_v, step = config.SENSOR_RANGES[key]
        _last_reading[key] = _drift(_last_reading[key], min_v, max_v, step)

    # Slowly drain battery over time, slower when power saving
    drain_rate = 0.02 if power_mode == "power_saving" else 0.05
    _last_reading["battery_level"] = round(
        max(0.0, _last_reading["battery_level"] - drain_rate), 2
    )

    return {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "soil_moisture": _last_reading["soil_moisture"],
        "temperature": _last_reading["temperature"],
        "humidity": _last_reading["humidity"],
        "light_intensity": _last_reading["light_intensity"],
        "wind_speed": _last_reading["wind_speed"],
        "battery_level": _last_reading["battery_level"],
        "solar_charging": _last_reading["light_intensity"] > config.SOLAR_CHARGE_THRESHOLD
    }