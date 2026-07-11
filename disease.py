"""
AgroEdge AI - Disease Detection Module
Offline placeholder classifier. Uses simple average-color analysis
on the uploaded leaf image to guess a condition — lightweight enough
to run without any ML framework or internet connection.

This is intentionally simple for hackathon scope. It can later be
swapped for a small on-device TFLite model without changing the
API contract (classify_image still returns the same shape).
"""

from PIL import Image
import io
import config


def _average_color(image):
    """Returns the average (R, G, B) of an image, downsampled for speed."""
    small = image.convert("RGB").resize((50, 50))
    pixels = list(small.getdata())
    n = len(pixels)
    r = sum(p[0] for p in pixels) / n
    g = sum(p[1] for p in pixels) / n
    b = sum(p[2] for p in pixels) / n
    return r, g, b


def _classify_from_color(r, g, b):
    """
    Very simple heuristic:
    - Strong green, low red/brown  -> Healthy
    - Reddish-brown dominant       -> Leaf Rust
    - Pale / low saturation, high brightness -> Powdery Mildew
    - Otherwise -> Healthy (default, avoids over-alerting the farmer)
    """
    brightness = (r + g + b) / 3
    max_channel = max(r, g, b)
    min_channel = min(r, g, b)
    saturation = 0 if max_channel == 0 else (max_channel - min_channel) / max_channel

    if r > g and r > config.RUST_RED_THRESHOLD and (r - g) > config.RUST_RED_GREEN_GAP:
        return "Leaf Rust", round(min(95, 60 + (r - g)), 1)

    if brightness > config.MILDEW_BRIGHTNESS_THRESHOLD and saturation < config.MILDEW_SATURATION_MAX:
        return "Powdery Mildew", round(min(95, 55 + (brightness - config.MILDEW_BRIGHTNESS_THRESHOLD)), 1)

    if g >= r and g >= b:
        return "Healthy", round(min(95, 60 + (g - max(r, b))), 1)

    return "Healthy", 55.0


def classify_image(image_file):
    """
    Accepts a Flask FileStorage object (from request.files["image"]),
    runs the offline heuristic, and returns a result dict.
    """
    try:
        image_bytes = image_file.read()
        image = Image.open(io.BytesIO(image_bytes))
    except Exception:
        return {
            "error": "Could not read image file",
            "label": None,
            "confidence": None
        }

    r, g, b = _average_color(image)
    label, confidence = _classify_from_color(r, g, b)

    recommendation_map = {
        "Healthy": "No action needed",
        "Leaf Rust": "Isolate affected plants and inspect surrounding crops",
        "Powdery Mildew": "Improve air circulation and reduce leaf wetness"
    }

    return {
        "label": label,
        "confidence": confidence,
        "recommendation": recommendation_map[label],
        "note": "Offline heuristic classifier (color-based placeholder)"
    }