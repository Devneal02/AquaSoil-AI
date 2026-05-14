"""Crop-specific suitability scoring and advisory helpers."""

from __future__ import annotations

from typing import Any


CROP_PROFILES: dict[str, dict[str, Any]] = {
    "General Field": {
        "description": "Balanced field use when no specific crop has been chosen.",
        "ranges": {
            "Soil pH": (6.0, 7.5),
            "Nitrogen (N)": (20.0, 500.0),
            "Phosphorus (P)": (10.0, 200.0),
            "Potassium (K)": (80.0, 1000.0),
            "Soil Moisture": (30.0, 80.0),
            "Electrical Conductivity (EC)": (0.0, 4.0),
            "Water Turbidity": (0.0, 50.0),
            "Dissolved Oxygen (DO)": (5.0, 20.0),
            "Total Dissolved Solids": (0.0, 1000.0),
        },
    },
    "Rice": {
        "description": "Rice favors moist fields, moderate acidity, and low salinity irrigation water.",
        "ranges": {
            "Soil pH": (5.5, 7.0),
            "Nitrogen (N)": (40.0, 250.0),
            "Phosphorus (P)": (10.0, 80.0),
            "Potassium (K)": (80.0, 300.0),
            "Soil Moisture": (60.0, 90.0),
            "Electrical Conductivity (EC)": (0.0, 3.0),
            "Water Turbidity": (0.0, 100.0),
            "Dissolved Oxygen (DO)": (4.0, 20.0),
            "Total Dissolved Solids": (0.0, 1000.0),
        },
    },
    "Corn": {
        "description": "Corn prefers well-drained soil, steady nutrients, and moderate moisture.",
        "ranges": {
            "Soil pH": (5.8, 7.5),
            "Nitrogen (N)": (60.0, 250.0),
            "Phosphorus (P)": (15.0, 90.0),
            "Potassium (K)": (100.0, 350.0),
            "Soil Moisture": (35.0, 70.0),
            "Electrical Conductivity (EC)": (0.0, 2.5),
            "Water Turbidity": (0.0, 50.0),
            "Dissolved Oxygen (DO)": (5.0, 20.0),
            "Total Dissolved Solids": (0.0, 900.0),
        },
    },
    "Vegetables": {
        "description": "Vegetables usually need balanced pH, clean water, and consistent but not excessive moisture.",
        "ranges": {
            "Soil pH": (6.0, 7.0),
            "Nitrogen (N)": (40.0, 220.0),
            "Phosphorus (P)": (20.0, 100.0),
            "Potassium (K)": (120.0, 400.0),
            "Soil Moisture": (40.0, 70.0),
            "Electrical Conductivity (EC)": (0.0, 2.0),
            "Water Turbidity": (0.0, 40.0),
            "Dissolved Oxygen (DO)": (5.0, 20.0),
            "Total Dissolved Solids": (0.0, 700.0),
        },
    },
    "Banana": {
        "description": "Banana favors warm, moist, well-drained soil with strong potassium supply.",
        "ranges": {
            "Soil pH": (5.5, 7.5),
            "Nitrogen (N)": (50.0, 250.0),
            "Phosphorus (P)": (15.0, 100.0),
            "Potassium (K)": (150.0, 500.0),
            "Soil Moisture": (50.0, 80.0),
            "Electrical Conductivity (EC)": (0.0, 2.0),
            "Water Turbidity": (0.0, 60.0),
            "Dissolved Oxygen (DO)": (5.0, 20.0),
            "Total Dissolved Solids": (0.0, 800.0),
        },
    },
}

CROP_OPTIONS = tuple(CROP_PROFILES.keys())

PARAMETER_WEIGHTS = {
    "Soil pH": 1.35,
    "Nitrogen (N)": 1.0,
    "Phosphorus (P)": 0.9,
    "Potassium (K)": 0.95,
    "Soil Moisture": 1.25,
    "Electrical Conductivity (EC)": 1.25,
    "Water Turbidity": 0.85,
    "Dissolved Oxygen (DO)": 0.75,
    "Total Dissolved Solids": 0.9,
}

LOW_ACTIONS = {
    "Soil pH": "Raise soil pH gradually with agricultural lime before planting.",
    "Nitrogen (N)": "Add nitrogen fertilizer or organic compost based on local fertilizer guidance.",
    "Phosphorus (P)": "Apply phosphate fertilizer or compost to support root growth.",
    "Potassium (K)": "Apply potash or potassium-rich organic material.",
    "Soil Moisture": "Increase irrigation or schedule watering before planting.",
    "Electrical Conductivity (EC)": "EC is already low enough for the selected crop.",
    "Water Turbidity": "Turbidity is already low enough for the selected crop.",
    "Dissolved Oxygen (DO)": "Aerate or refresh the water source before relying on it for irrigation.",
    "Total Dissolved Solids": "TDS is already low enough for the selected crop.",
}

HIGH_ACTIONS = {
    "Soil pH": "Lower soil pH gradually using organic matter or approved acidifying amendments.",
    "Nitrogen (N)": "Avoid adding more nitrogen for now and monitor crop leaf growth.",
    "Phosphorus (P)": "Avoid extra phosphorus and monitor for nutrient imbalance.",
    "Potassium (K)": "Avoid extra potassium until the field is retested.",
    "Soil Moisture": "Improve drainage and delay planting if the field is waterlogged.",
    "Electrical Conductivity (EC)": "Reduce salinity risk by flushing with cleaner water if available.",
    "Water Turbidity": "Let water settle or filter it before irrigation.",
    "Dissolved Oxygen (DO)": "Dissolved oxygen is above the selected crop minimum and is not a concern.",
    "Total Dissolved Solids": "Use a cleaner water source or dilute high-TDS water if possible.",
}


def normalize_crop(crop: str | None) -> str:
    """Return a supported crop name, defaulting to General Field."""
    if not crop:
        return "General Field"
    candidate = str(crop).strip()
    for option in CROP_OPTIONS:
        if candidate.lower() == option.lower():
            return option
    return "General Field"


def evaluate_crop(
    crop: str | None,
    input_values: dict[str, float],
    soil_class: str = "",
    water_class: str = "",
) -> dict[str, Any]:
    """Evaluate field suitability for one crop using measured soil and water values."""
    crop_name = normalize_crop(crop)
    profile = CROP_PROFILES[crop_name]
    ranges = profile["ranges"]
    weighted_score = 0.0
    total_weight = 0.0
    issues: list[dict[str, Any]] = []

    for parameter, (minimum, maximum) in ranges.items():
        if parameter not in input_values:
            continue
        value = float(input_values[parameter])
        weight = PARAMETER_WEIGHTS.get(parameter, 1.0)
        score = _parameter_score(value, minimum, maximum)
        weighted_score += score * weight
        total_weight += weight
        if value < minimum or value > maximum:
            direction = "low" if value < minimum else "high"
            issues.append(
                {
                    "parameter": parameter,
                    "value": value,
                    "target_min": minimum,
                    "target_max": maximum,
                    "direction": direction,
                    "action": _parameter_action(parameter, direction),
                }
            )

    score = weighted_score / total_weight if total_weight else 0.0
    score = _adjust_for_classes(score, soil_class, water_class)
    status = _status_from_score(score)
    next_steps = _next_steps(crop_name, issues, status)

    return {
        "crop": crop_name,
        "score": round(score, 1),
        "status": status,
        "summary": _summary(crop_name, score, issues),
        "description": profile["description"],
        "issues": issues,
        "next_steps": next_steps,
        "target_ranges": ranges,
    }


def crop_advisory_lines(crop_advisory: dict[str, Any] | None) -> list[str]:
    """Return compact text lines for reports and assistant responses."""
    if not crop_advisory:
        return ["No crop-specific advisory available."]
    lines = [
        f"Crop       : {crop_advisory.get('crop', 'General Field')}",
        f"Suitability: {crop_advisory.get('score', 0):.0f}% - {crop_advisory.get('status', 'Unknown')}",
        f"Summary    : {crop_advisory.get('summary', '')}",
    ]
    steps = crop_advisory.get("next_steps", [])
    if steps:
        lines.append("Next Steps :")
        lines.extend(f"- {step}" for step in steps)
    return lines


def _parameter_score(value: float, minimum: float, maximum: float) -> float:
    if minimum <= value <= maximum:
        return 100.0
    span = max(maximum - minimum, 1.0)
    distance = minimum - value if value < minimum else value - maximum
    penalty = min(75.0, (distance / span) * 100.0)
    return max(25.0, 100.0 - penalty)


def _parameter_action(parameter: str, direction: str) -> str:
    if direction == "low":
        return LOW_ACTIONS[parameter]
    return HIGH_ACTIONS[parameter]


def _adjust_for_classes(score: float, soil_class: str, water_class: str) -> float:
    soil = str(soil_class).upper()
    water = str(water_class).upper()
    if soil == "POOR":
        score -= 10.0
    elif soil == "MODERATE":
        score -= 4.0
    if water == "POOR":
        score -= 10.0
    elif water == "MODERATE":
        score -= 4.0
    return max(0.0, min(100.0, score))


def _status_from_score(score: float) -> str:
    if score >= 80.0:
        return "Suitable"
    if score >= 60.0:
        return "Needs attention"
    return "Delay planting"


def _summary(crop_name: str, score: float, issues: list[dict[str, Any]]) -> str:
    if score >= 80.0 and not issues:
        return f"{crop_name} looks suitable based on the current soil and water readings."
    if score >= 80.0:
        return f"{crop_name} is mostly suitable, but a few readings should still be monitored."
    if score >= 60.0:
        return f"{crop_name} can be considered after fixing the main limiting readings."
    return f"Delay {crop_name} planting until the field conditions improve."


def _next_steps(crop_name: str, issues: list[dict[str, Any]], status: str) -> list[str]:
    if not issues:
        return [
            f"Proceed with {crop_name} planning while continuing regular monitoring.",
            "Retest the field before major fertilizer or irrigation changes.",
        ]
    steps = [issue["action"] for issue in issues[:3]]
    if status == "Delay planting":
        steps.insert(0, f"Delay {crop_name} planting until urgent soil or water issues are corrected.")
    return steps
