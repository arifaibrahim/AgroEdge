"""
AgroEdge AI - Decision Engine
Pure rule-based, runs entirely locally. No ML, no internet.
Takes one sensor reading and returns health score, alerts,
and actionable recommendations.
"""

import config


def _score_soil_moisture(value):
    """Ideal range scores highest; too dry or too wet loses points."""
    low, high = config.IDEAL_SOIL_MOISTURE
    if low <= value <= high:
        return 100
    distance = min(abs(value - low), abs(value - high))
    return max(0, 100 - distance * 2)


def _score_temperature(value):
    low, high = config.IDEAL_TEMPERATURE
    if low <= value <= high:
        return 100
    distance = min(abs(value - low), abs(value - high))
    return max(0, 100 - distance * 4)


def _score_humidity(value):
    low, high = config.IDEAL_HUMIDITY
    if low <= value <= high:
        return 100
    distance = min(abs(value - low), abs(value - high))
    return max(0, 100 - distance * 2)


def _score_light(value):
    low, high = config.IDEAL_LIGHT
    if low <= value <= high:
        return 100
    distance = min(abs(value - low), abs(value - high))
    return max(0, 100 - distance * 0.1)


def analyze(readings):
    """
    Runs all local rules against a single sensor reading.
    Returns: health_score (0-100), list of alerts, list of recommendations.
    """
    alerts = []
    recommendations = []

    moisture = readings["soil_moisture"]
    temperature = readings["temperature"]
    humidity = readings["humidity"]
    light = readings["light_intensity"]
    wind = readings["wind_speed"]
    battery = readings["battery_level"]

    # ---------------- Soil Moisture ----------------
    if moisture < config.LOW_MOISTURE_THRESHOLD:
        alerts.append("Low Moisture")
        recommendations.append("Turn ON irrigation")
    elif moisture > config.HIGH_MOISTURE_THRESHOLD:
        recommendations.append("Reduce watering")
    else:
        recommendations.append("No irrigation required")

    # ---------------- Temperature (Heat Stress) ----------------
    if temperature > config.HEAT_STRESS_THRESHOLD:
        alerts.append("Heat Stress")
        recommendations.append("Provide shade or increase irrigation frequency")

    # ---------------- Humidity (Fungal Disease Risk) ----------------
    if humidity > config.HIGH_HUMIDITY_THRESHOLD:
        alerts.append("High Humidity")
        recommendations.append("Disease inspection recommended")

    # ---------------- Light ----------------
    if light < config.LOW_LIGHT_THRESHOLD:
        alerts.append("Low Light")

    # ---------------- Wind ----------------
    if wind > config.HIGH_WIND_THRESHOLD:
        alerts.append("High Wind")

    # ---------------- Battery ----------------
    if battery < config.LOW_BATTERY_THRESHOLD:
        alerts.append("Low Battery")

    # ---------------- Overall Health Score ----------------
    score = (
        _score_soil_moisture(moisture) * 0.35 +
        _score_temperature(temperature) * 0.25 +
        _score_humidity(humidity) * 0.20 +
        _score_light(light) * 0.20
    )
    health_score = round(max(0, min(100, score)))

    if not alerts:
        recommendations.append("Crop conditions healthy")

    return {
        "health_score": health_score,
        "alerts": alerts,
        "recommendations": recommendations
    }