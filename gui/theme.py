"""Shared visual constants for the AquaSoil-AI desktop GUI."""

from __future__ import annotations

THEME_NAME = "litera"

COLOR_PRIMARY = "#1565C0"
COLOR_SOIL = "#2E7D32"
COLOR_WATER = "#0277BD"
COLOR_CRITICAL = "#C62828"
COLOR_WARNING = "#E65100"
COLOR_OK = "#2E7D32"
COLOR_BACKGROUND = "#F5F7FA"
COLOR_CARD_BG = "#FFFFFF"
COLOR_TEXT_PRIMARY = "#263238"
COLOR_TEXT_MUTED = "#546E7A"
COLOR_DIVIDER = "#BBDEFB"
COLOR_SHADOW = "#D8DEE5"
COLOR_ENTRY_BG = "#FFFFFF"
COLOR_HEADER_BG = "#E3F2FD"
COLOR_NEUTRAL_BG = "#ECEFF1"
COLOR_TABLE_ALT = "#FAFBFC"
COLOR_PRINT_BG = "#FFFFFF"
COLOR_BLACK = "#000000"
COLOR_TRANSPARENT = "#FFFFFF"

CLASS_BACKGROUNDS = {
    "POOR": "#FFEBEE",
    "MODERATE": "#FFF3E0",
    "GOOD": "#E8F5E9",
    "UNKNOWN": "#ECEFF1",
}

CLASS_ACCENTS = {
    "POOR": COLOR_CRITICAL,
    "MODERATE": COLOR_WARNING,
    "GOOD": COLOR_OK,
    "UNKNOWN": COLOR_TEXT_MUTED,
}

CLASS_BOOTSTYLES = {
    "POOR": "danger",
    "MODERATE": "warning",
    "GOOD": "success",
    "UNKNOWN": "secondary",
}

SEVERITY_STYLES = {
    "CRITICAL": {
        "icon": "⛔",
        "accent": COLOR_CRITICAL,
        "background": "#FFEBEE",
        "bootstyle": "danger",
    },
    "WARNING": {
        "icon": "⚠️",
        "accent": COLOR_WARNING,
        "background": "#FFF3E0",
        "bootstyle": "warning",
    },
    "OK": {
        "icon": "✅",
        "accent": COLOR_OK,
        "background": "#E8F5E9",
        "bootstyle": "success",
    },
}

ROW_BACKGROUNDS = {
    "poor": "#FFEBEE",
    "good": "#E8F5E9",
    "mixed": "#FFF3E0",
}

FONT_TITLE = ("Arial", 22, "bold")
FONT_SUBTITLE = ("Arial", 11)
FONT_TAB = ("Arial", 11, "bold")
FONT_SECTION = ("Arial", 13, "bold")
FONT_BODY = ("Arial", 11)
FONT_BODY_BOLD = ("Arial", 11, "bold")
FONT_HINT = ("Arial", 9)
FONT_CARD_CLASS = ("Arial", 28, "bold")
FONT_CARD_LABEL = ("Arial", 12, "bold")
FONT_SMALL_BOLD = ("Arial", 9, "bold")
FONT_MONO = ("Consolas", 10)

PADDING_SMALL = 6
PADDING_MEDIUM = 12
PADDING_LARGE = 18

PARAMETER_ORDER = [
    "Soil pH",
    "Nitrogen (N)",
    "Phosphorus (P)",
    "Potassium (K)",
    "Soil Moisture",
    "Electrical Conductivity (EC)",
    "Water Turbidity",
    "Dissolved Oxygen (DO)",
    "Total Dissolved Solids",
]

PARAMETER_LABELS = {
    "Soil pH": "Soil pH",
    "Nitrogen (N)": "Nitrogen N (mg/kg)",
    "Phosphorus (P)": "Phosphorus P (mg/kg)",
    "Potassium (K)": "Potassium K (mg/kg)",
    "Soil Moisture": "Soil Moisture (%)",
    "Electrical Conductivity (EC)": "Elect. Conductivity",
    "Water Turbidity": "Turbidity (NTU)",
    "Dissolved Oxygen (DO)": "Dissolved Oxygen",
    "Total Dissolved Solids": "Total Dissolved Solids (mg/L)",
}

PARAMETER_SHORT_LABELS = {
    "Soil pH": "pH",
    "Nitrogen (N)": "N",
    "Phosphorus (P)": "P",
    "Potassium (K)": "K",
    "Soil Moisture": "Moisture",
    "Electrical Conductivity (EC)": "EC",
    "Water Turbidity": "Turbidity",
    "Dissolved Oxygen (DO)": "DO",
    "Total Dissolved Solids": "TDS",
}

OPTIMAL_RANGES = {
    "Soil pH": (6.0, 7.5),
    "Nitrogen (N)": (20.0, 500.0),
    "Phosphorus (P)": (10.0, 200.0),
    "Potassium (K)": (80.0, 1000.0),
    "Soil Moisture": (30.0, 80.0),
    "Electrical Conductivity (EC)": (0.0, 4.0),
    "Water Turbidity": (0.0, 50.0),
    "Dissolved Oxygen (DO)": (5.0, 20.0),
    "Total Dissolved Solids": (0.0, 1000.0),
}

TEAM_MEMBERS = [
    "Babagonio, Philip Neel",
    "Sabando, Nelann Llyod",
    "Demillo, Adrian Michael",
]

STATUS_READY = "Ready"
STATUS_ANALYZING = "Analyzing..."
STATUS_COMPLETE = "✅ Analysis complete"
