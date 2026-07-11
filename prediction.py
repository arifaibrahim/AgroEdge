"""
AgroEdge AI - Prediction Module
Generates short-term trend predictions using simple linear
extrapolation over recent readings. No ML, no cloud inference —
cheap enough to run on constrained edge hardware.
"""

import config


def _linear_trend(values):
    """
    Fits a simple least-squares line through the values and
    returns (slope, intercept). x-axis is just the reading index.
    """
    n = len(values)
    if n < 2:
        return 0.0, values[0] if values else 0.0

    x_vals = list(range(n))
    x_mean = sum(x_vals) / n
    y_mean = sum(values) / n

    numerator = sum((x_vals[i] - x_mean) * (values[i] - y_mean) for i in range(n))
    denominator = sum((x_vals[i] - x_mean) ** 2 for i in range(n))

    slope = numerator / denominator if denominator != 0 else 0.0
    intercept = y_mean - slope * x_mean
    return slope, intercept


def _predict_next(values, steps_ahead):
    """Extrapolates `steps_ahead` points beyond the last known value."""
    slope, intercept = _linear_trend(values)
    n = len(values)
    predicted = intercept + slope * (n - 1 + steps_ahead)
    return round(predicted, 2)


def _trend_label(slope, flat_threshold):
    """Turns a numeric slope into a human-readable direction."""
    if slope > flat_threshold:
        return "rising"
    elif slope < -flat_threshold:
        return "falling"
    return "stable"


def predict_trends(recent_readings):
    """
    Takes a list of recent readings (oldest first, as returned by
    database.get_recent_readings) and returns short-term predictions
    for the metrics that matter most to a farmer.
    """
    if not recent_readings or len(recent_readings) < 2:
        return {
            "available": False,
            "message": "Not enough data yet to predict trends"
        }

    steps = config.PREDICTION_STEPS_AHEAD  # e.g. represents ~10 minutes ahead

    moisture_vals = [r["soil_moisture"] for r in recent_readings]
    temp_vals = [r["temperature"] for r in recent_readings]
    humidity_vals = [r["humidity"] for r in recent_readings]

    moisture_slope, _ = _linear_trend(moisture_vals)
    temp_slope, _ = _linear_trend(temp_vals)
    humidity_slope, _ = _linear_trend(humidity_vals)

    return {
        "available": True,
        "horizon_minutes": config.PREDICTION_HORIZON_MINUTES,
        "soil_moisture": {
            "predicted_value": _predict_next(moisture_vals, steps),
            "trend": _trend_label(moisture_slope, flat_threshold=0.2)
        },
        "temperature": {
            "predicted_value": _predict_next(temp_vals, steps),
            "trend": _trend_label(temp_slope, flat_threshold=0.1)
        },
        "humidity": {
            "predicted_value": _predict_next(humidity_vals, steps),
            "trend": _trend_label(humidity_slope, flat_threshold=0.2)
        }
    }