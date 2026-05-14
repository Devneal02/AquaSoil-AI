"""Farmer-focused explanations and assistant responses for AquaSoil-AI."""

from __future__ import annotations

import re
from typing import Any

from gui.theme import OPTIMAL_RANGES, PARAMETER_LABELS, PARAMETER_ORDER
from src.preprocess import PARAMETER_RANGES


ACTION_GROUPS = ("Urgent", "This Week", "Monitor")

PARAMETER_ALIASES = {
    "Soil pH": ("soil ph", "ph", "acidic", "alkaline", "lime"),
    "Nitrogen (N)": ("nitrogen", " n ", "urea"),
    "Phosphorus (P)": ("phosphorus", " p ", "phosphate"),
    "Potassium (K)": ("potassium", " k ", "potash"),
    "Soil Moisture": ("soil moisture", "moisture", "irrigation", "waterlogging", "dry"),
    "Electrical Conductivity (EC)": ("electrical conductivity", "ec", "salinity", "salty"),
    "Water Turbidity": ("water turbidity", "turbidity", "muddy", "dirty water"),
    "Dissolved Oxygen (DO)": ("dissolved oxygen", "oxygen", "aerate"),
    "Total Dissolved Solids": ("total dissolved solids", "tds", "dissolved solids"),
}

PARAMETER_NOTES = {
    "Soil pH": "Soil pH shows if soil is acidic or alkaline. Most crops grow better near neutral soil.",
    "Nitrogen (N)": "Nitrogen supports leafy growth. Low nitrogen can make crops pale or slow-growing.",
    "Phosphorus (P)": "Phosphorus supports root growth, flowering, and early crop strength.",
    "Potassium (K)": "Potassium helps crops handle stress and supports fruit or grain quality.",
    "Soil Moisture": "Soil moisture shows if the field is too dry, balanced, or at risk of waterlogging.",
    "Electrical Conductivity (EC)": "Electrical conductivity estimates soil salinity. High EC can stress roots.",
    "Water Turbidity": "Turbidity shows how cloudy or muddy the water is. High turbidity can clog systems and carry sediment.",
    "Dissolved Oxygen (DO)": "Dissolved oxygen shows how much oxygen is in the water. Very low oxygen can signal poor water quality.",
    "Total Dissolved Solids": "TDS estimates dissolved minerals and salts in water. High TDS may make irrigation risky.",
}


def severity_from_recommendation(recommendation: str) -> str:
    """Return CRITICAL, WARNING, or OK from a recommendation string."""
    upper_text = recommendation.upper()
    if "[CRITICAL]" in upper_text:
        return "CRITICAL"
    if "[WARNING]" in upper_text:
        return "WARNING"
    return "OK"


def clean_recommendation(recommendation: str) -> str:
    """Remove a leading severity tag from an advisory sentence."""
    return re.sub(r"^\s*\[[^\]]+\]\s*", "", recommendation).strip()


def build_action_plan(result: dict[str, Any] | None) -> dict[str, list[str]]:
    """Group recommendations into farmer-readable priority buckets."""
    plan = {group: [] for group in ACTION_GROUPS}
    if not result:
        plan["Monitor"].append("Run an analysis to create a field action plan.")
        return plan

    for recommendation in result.get("recommendations", []):
        text = clean_recommendation(str(recommendation))
        severity = severity_from_recommendation(str(recommendation))
        if severity == "CRITICAL":
            plan["Urgent"].append(text)
        elif severity == "WARNING":
            plan["This Week"].append(text)
        else:
            plan["Monitor"].append(text)

    if not plan["Urgent"]:
        plan["Urgent"].append("No urgent issue detected from the latest analysis.")
    if not plan["This Week"]:
        plan["This Week"].append("Keep normal field care and recheck if crop or water conditions change.")
    if not plan["Monitor"]:
        plan["Monitor"].append("Record this result and compare it with the next field reading.")

    return plan


def farmer_summary(result: dict[str, Any] | None) -> str:
    """Summarize the latest sample in plain farmer-facing language."""
    if not result:
        return "No sample has been analyzed yet. Enter measurements or load a CSV, then I can explain the result."

    sample = result.get("sample", "Unknown Field")
    soil_class = str(result.get("soil_class", "Unknown")).upper()
    water_class = str(result.get("water_class", "Unknown")).upper()
    recommendations = [str(item) for item in result.get("recommendations", [])]
    critical_count = sum(1 for item in recommendations if severity_from_recommendation(item) == "CRITICAL")
    warning_count = sum(1 for item in recommendations if severity_from_recommendation(item) == "WARNING")

    message = f"Latest sample: {sample}\nSoil quality: {soil_class}\nWater quality: {water_class}"
    if critical_count:
        message += f"\nFocus first on {critical_count} urgent issue(s), then handle the warnings."
    elif warning_count:
        message += f"\nThere are {warning_count} warning item(s). Conditions are manageable, but they need attention."
    else:
        message += "\nThe latest reading looks safe. Continue regular monitoring."
    return message


def generate_chat_response(
    question: str,
    latest_result: dict[str, Any] | None = None,
    history: list[dict[str, Any]] | None = None,
) -> str:
    """Generate an offline assistant response from app context and keyword intent."""
    text = question.strip()
    normalized = f" {text.lower()} "
    history = history or []

    if not text:
        return "Type a question about the app, your latest result, or a soil/water parameter."

    if _has_any(normalized, ("hello", "hi ", "hey ", "good morning", "good afternoon")):
        return "Hello. I can help explain AquaSoil-AI results, parameters, CSV use, reports, and next actions."

    matched_parameter = _match_parameter(normalized)
    if matched_parameter:
        return parameter_explanation(matched_parameter, latest_result)

    if _has_any(normalized, ("latest", "result", "summary", "explain", "status")):
        return farmer_summary(latest_result)

    if _has_any(normalized, ("first", "priority", "urgent", "action", "fix", "do next", "what should i do")):
        return _action_plan_response(latest_result)

    if _has_any(normalized, ("how to use", "start", "analyze", "sample", "measurements")):
        return (
            "Basic workflow:\n"
            "- Enter a field name.\n"
            "- Fill in the soil and water measurements.\n"
            "- Click Analyze Sample.\n"
            "- Open Results for the action plan and recommendations.\n"
            "- Save the report if you need a field record."
        )

    if _has_any(normalized, ("csv", "batch", "spreadsheet", "file")):
        return (
            "For CSV batch analysis, prepare one row per field sample. The file needs a Sample column plus all "
            "nine AquaSoil-AI parameter columns. Then use Load CSV from the Input tab."
        )

    if _has_any(normalized, ("report", "save", "print", "export")):
        return (
            "After an analysis, go to Results. You can save a text report, export the chart as PNG, or open "
            "the print preview."
        )

    if _has_any(normalized, ("history", "previous", "past", "old")):
        if not history:
            return "No saved history is available yet. Analyze a sample first, then History will list past results."
        return f"History currently has {len(history)} saved analysis record(s). Select a row to reopen its result."

    if _has_any(normalized, ("rule", "recommendation", "advice", "why")):
        return (
            "Recommendations come from the AquaSoil-AI knowledge base. Critical items are shown first, warnings "
            "come next, and OK messages mean no specific issue was detected by the current rules."
        )

    return (
        "I can help with app steps, CSV files, reports, history, the latest result, action priorities, and "
        "parameters like pH, NPK, moisture, EC, turbidity, DO, and TDS."
    )


def parameter_explanation(parameter: str, latest_result: dict[str, Any] | None = None) -> str:
    """Explain one parameter, including ranges and latest value when available."""
    valid_minimum, valid_maximum = PARAMETER_RANGES[parameter]
    optimal_minimum, optimal_maximum = OPTIMAL_RANGES[parameter]
    label = PARAMETER_LABELS.get(parameter, parameter)
    lines = [
        label,
        PARAMETER_NOTES[parameter],
        f"Valid app range: {_format_number(valid_minimum)} to {_format_number(valid_maximum)}.",
        f"Target range: {_format_number(optimal_minimum)} to {_format_number(optimal_maximum)}.",
    ]

    if latest_result:
        values = latest_result.get("input_values", {})
        if parameter in values and values[parameter] is not None:
            value = float(values[parameter])
            status = _value_status(value, optimal_minimum, optimal_maximum)
            lines.append(f"Latest value: {_format_number(value)} ({status}).")

    return "\n".join(lines)


def _action_plan_response(result: dict[str, Any] | None) -> str:
    plan = build_action_plan(result)
    lines = [farmer_summary(result), "", "Recommended order:"]
    for group in ACTION_GROUPS:
        items = plan[group]
        lines.append(f"{group}:")
        for item in items[:3]:
            lines.append(f"- {item}")
    return "\n".join(lines)


def _match_parameter(normalized: str) -> str | None:
    for parameter in PARAMETER_ORDER:
        aliases = PARAMETER_ALIASES[parameter]
        for alias in aliases:
            alias_text = alias.strip()
            if len(alias_text) <= 3 and alias_text.isalnum():
                if re.search(rf"\b{re.escape(alias_text)}\b", normalized):
                    return parameter
            elif alias in normalized:
                return parameter
    return None


def _has_any(normalized: str, keywords: tuple[str, ...]) -> bool:
    return any(keyword in normalized for keyword in keywords)


def _value_status(value: float, minimum: float, maximum: float) -> str:
    if value < minimum:
        return "below target"
    if value > maximum:
        return "above target"
    return "within target"


def _format_number(value: float) -> str:
    numeric = float(value)
    if numeric.is_integer():
        return str(int(numeric))
    return f"{numeric:g}"
