"""
AgroEdge AI - Main Flask Application
Fully offline, edge-based crop monitoring backend.
Run: python app.py
Access: http://127.0.0.1:5000
"""

from flask import Flask, jsonify, request, render_template
import config
import database
import sensor
import rules
import prediction
import disease

app = Flask(__name__)

# Initialize SQLite database and tables on startup
database.init_db()

# Track current power mode in memory (simple, no need for DB overhead)
system_state = {
    "power_mode": "normal"  # "normal" or "power_saving"
}


# ---------------------------------------------------------
# FRONTEND ROUTE
# ---------------------------------------------------------
@app.route("/")
def index():
    """Serves the main dashboard page."""
    return render_template("index.html")


# ---------------------------------------------------------
# SENSOR + DECISION ENGINE ROUTE
# ---------------------------------------------------------
@app.route("/api/sensor-data", methods=["GET"])
def get_sensor_data():
    """
    Reads current (simulated) sensor values, runs them through
    the local decision engine, stores the reading, and returns
    everything the dashboard needs in one call.
    """
    readings = sensor.read_sensors(power_mode=system_state["power_mode"])

    analysis = rules.analyze(readings)

    database.save_reading(readings, analysis)

    return jsonify({
        "readings": readings,
        "health_score": analysis["health_score"],
        "recommendations": analysis["recommendations"],
        "alerts": analysis["alerts"],
        "power_mode": system_state["power_mode"]
    })


# ---------------------------------------------------------
# HISTORY ROUTE (for charts)
# ---------------------------------------------------------
@app.route("/api/history", methods=["GET"])
def get_history():
    """Returns the last N stored readings for Chart.js."""
    limit = int(request.args.get("limit", config.MAX_STORED_RECORDS))
    records = database.get_recent_readings(limit)
    return jsonify(records)


# ---------------------------------------------------------
# PREDICTION ROUTE
# ---------------------------------------------------------
@app.route("/api/prediction", methods=["GET"])
def get_prediction():
    """Returns lightweight short-term trend predictions."""
    recent = database.get_recent_readings(config.PREDICTION_WINDOW)
    result = prediction.predict_trends(recent)
    return jsonify(result)


# ---------------------------------------------------------
# DISEASE DETECTION ROUTE
# ---------------------------------------------------------
@app.route("/api/disease-check", methods=["POST"])
def check_disease():
    """
    Accepts an uploaded crop image and runs it through the
    offline placeholder classifier.
    """
    if "image" not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    image_file = request.files["image"]
    result = disease.classify_image(image_file)
    return jsonify(result)


# ---------------------------------------------------------
# POWER MODE TOGGLE ROUTE
# ---------------------------------------------------------
@app.route("/api/power-mode", methods=["POST"])
def set_power_mode():
    """Switches between 'normal' and 'power_saving' modes."""
    data = request.get_json(force=True)
    mode = data.get("mode")

    if mode not in ("normal", "power_saving"):
        return jsonify({"error": "Invalid mode"}), 400

    system_state["power_mode"] = mode
    return jsonify({"power_mode": system_state["power_mode"]})


# ---------------------------------------------------------
# SYSTEM STATUS ROUTE (battery, solar, refresh interval)
# ---------------------------------------------------------
@app.route("/api/status", methods=["GET"])
def get_status():
    """Returns general system status for the dashboard header."""
    refresh_interval = (
        config.POWER_SAVING_REFRESH_MS
        if system_state["power_mode"] == "power_saving"
        else config.NORMAL_REFRESH_MS
    )
    return jsonify({
        "power_mode": system_state["power_mode"],
        "refresh_interval_ms": refresh_interval
    })


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)