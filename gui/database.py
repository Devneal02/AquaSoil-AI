"""SQLite persistence helpers for AquaSoil-AI GUI analysis history."""

from __future__ import annotations

import csv
import json
import sqlite3
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "data" / "aquasoil_history.db"

PARAMETER_TO_COLUMN = {
    "Soil pH": "pH",
    "Nitrogen (N)": "N",
    "Phosphorus (P)": "P",
    "Potassium (K)": "K",
    "Soil Moisture": "moisture",
    "Electrical Conductivity (EC)": "EC",
    "Water Turbidity": "turbidity",
    "Dissolved Oxygen (DO)": "DO",
    "Total Dissolved Solids": "TDS",
}

CSV_COLUMNS = [
    "id",
    "timestamp",
    "sample_label",
    "soil_class",
    "water_class",
    "soil_confidence",
    "water_confidence",
    "pH",
    "N",
    "P",
    "K",
    "moisture",
    "EC",
    "turbidity",
    "DO",
    "TDS",
    "recommendations",
]


def _connect() -> sqlite3.Connection:
    """Open a connection to the AquaSoil history database."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db() -> None:
    """Create the analysis history table if it does not already exist."""
    with _connect() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS analyses (
              id               INTEGER PRIMARY KEY AUTOINCREMENT,
              timestamp        TEXT,
              sample_label     TEXT,
              soil_class       TEXT,
              water_class      TEXT,
              soil_confidence  REAL,
              water_confidence REAL,
              pH               REAL,
              N                REAL,
              P                REAL,
              K                REAL,
              moisture         REAL,
              EC               REAL,
              turbidity        REAL,
              DO               REAL,
              TDS              REAL,
              recommendations  TEXT
            );
            """
        )


def save_analysis(data: dict[str, Any]) -> None:
    """Insert one analysis result into persistent history."""
    init_db()
    input_values = data.get("input_values", {})
    recommendations = data.get("recommendations", [])
    if not isinstance(recommendations, list):
        recommendations = [str(recommendations)]

    row = {
        "timestamp": data.get("timestamp", ""),
        "sample_label": data.get("sample_label", data.get("sample", "Unknown Field")),
        "soil_class": data.get("soil_class", ""),
        "water_class": data.get("water_class", ""),
        "soil_confidence": float(data.get("soil_confidence", 0)),
        "water_confidence": float(data.get("water_confidence", 0)),
        "recommendations": json.dumps(recommendations, ensure_ascii=False),
    }
    for parameter, column in PARAMETER_TO_COLUMN.items():
        value = data.get(column, input_values.get(parameter))
        row[column] = None if value is None else float(value)

    placeholders = ", ".join("?" for _ in CSV_COLUMNS[1:])
    columns = ", ".join(CSV_COLUMNS[1:])
    values = [row[column] for column in CSV_COLUMNS[1:]]
    with _connect() as connection:
        connection.execute(f"INSERT INTO analyses ({columns}) VALUES ({placeholders})", values)


def load_all() -> list[dict[str, Any]]:
    """Return all analysis rows newest first."""
    init_db()
    with _connect() as connection:
        rows = connection.execute("SELECT * FROM analyses ORDER BY id DESC").fetchall()
    return [_row_to_dict(row) for row in rows]


def delete_all() -> None:
    """Clear all stored analysis history."""
    init_db()
    with _connect() as connection:
        connection.execute("DELETE FROM analyses")


def export_csv(path: str | Path) -> None:
    """Write all stored analysis rows to a CSV file."""
    init_db()
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with _connect() as connection:
        rows = connection.execute("SELECT * FROM analyses ORDER BY id DESC").fetchall()

    with destination.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row[column] for column in CSV_COLUMNS})


def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    """Convert a SQLite row into the GUI's analysis result shape."""
    raw_recommendations = row["recommendations"] or "[]"
    try:
        recommendations = json.loads(raw_recommendations)
    except json.JSONDecodeError:
        recommendations = [raw_recommendations]
    if not isinstance(recommendations, list):
        recommendations = [str(recommendations)]

    input_values = {
        parameter: row[column]
        for parameter, column in PARAMETER_TO_COLUMN.items()
    }
    record = {column: row[column] for column in CSV_COLUMNS}
    record.update(
        {
            "sample": row["sample_label"],
            "input_values": input_values,
            "recommendations": recommendations,
        }
    )
    return record
