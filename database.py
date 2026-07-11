"""
AgroEdge AI - Database Module
Local SQLite storage only. Keeps a rolling window of the most
recent readings (no large datasets, no data warehouse).
"""

import sqlite3
import json
import config

DB_PATH = config.DB_PATH


def _get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Creates the readings table if it doesn't already exist."""
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            soil_moisture REAL,
            temperature REAL,
            humidity REAL,
            light_intensity REAL,
            wind_speed REAL,
            battery_level REAL,
            solar_charging INTEGER,
            health_score INTEGER,
            alerts TEXT,
            recommendations TEXT
        )
    """)
    conn.commit()
    conn.close()


def save_reading(readings, analysis):
    """
    Inserts one reading + its analysis, then trims the table so
    only the most recent MAX_STORED_RECORDS rows are kept.
    """
    conn = _get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO readings (
            timestamp, soil_moisture, temperature, humidity,
            light_intensity, wind_speed, battery_level, solar_charging,
            health_score, alerts, recommendations
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        readings["timestamp"],
        readings["soil_moisture"],
        readings["temperature"],
        readings["humidity"],
        readings["light_intensity"],
        readings["wind_speed"],
        readings["battery_level"],
        int(readings["solar_charging"]),
        analysis["health_score"],
        json.dumps(analysis["alerts"]),
        json.dumps(analysis["recommendations"])
    ))

    # Trim old rows beyond the configured limit (keeps storage lightweight)
    cursor.execute("""
        DELETE FROM readings
        WHERE id NOT IN (
            SELECT id FROM readings
            ORDER BY id DESC
            LIMIT ?
        )
    """, (config.MAX_STORED_RECORDS,))

    conn.commit()
    conn.close()


def get_recent_readings(limit=None):
    """Returns the most recent readings, oldest first (good for charts)."""
    if limit is None:
        limit = config.MAX_STORED_RECORDS

    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM readings
        ORDER BY id DESC
        LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()

    results = []
    for row in reversed(rows):  # oldest first for charting
        results.append({
            "id": row["id"],
            "timestamp": row["timestamp"],
            "soil_moisture": row["soil_moisture"],
            "temperature": row["temperature"],
            "humidity": row["humidity"],
            "light_intensity": row["light_intensity"],
            "wind_speed": row["wind_speed"],
            "battery_level": row["battery_level"],
            "solar_charging": bool(row["solar_charging"]),
            "health_score": row["health_score"],
            "alerts": json.loads(row["alerts"]),
            "recommendations": json.loads(row["recommendations"])
        })
    return results