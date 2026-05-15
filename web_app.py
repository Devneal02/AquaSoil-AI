"""Modern Streamlit web app for AquaSoil-AI."""

from __future__ import annotations

from datetime import datetime
from html import escape
from textwrap import dedent
from typing import Any

import pandas as pd
import streamlit as st

from gui.database import delete_all, init_db, load_all, save_analysis
from gui.farmer_helper import (
    ACTION_GROUPS,
    build_action_plan,
    clean_recommendation,
    generate_chat_response,
    severity_from_recommendation,
)
from gui.theme import PARAMETER_LABELS, TEAM_MEMBERS
from src.crop_advisor import CROP_OPTIONS, CROP_PROFILES, crop_advisory_lines
from src.main import process_sample
from src.preprocess import PARAMETER_RANGES, validate_inputs


PARAMETER_COLUMNS = list(PARAMETER_RANGES.keys())
SOIL_PARAMETERS = PARAMETER_COLUMNS[:6]
WATER_PARAMETERS = PARAMETER_COLUMNS[6:]

DEFAULT_VALUES = {
    "Soil pH": 6.5,
    "Nitrogen (N)": 80.0,
    "Phosphorus (P)": 35.0,
    "Potassium (K)": 180.0,
    "Soil Moisture": 55.0,
    "Electrical Conductivity (EC)": 1.2,
    "Water Turbidity": 30.0,
    "Dissolved Oxygen (DO)": 6.5,
    "Total Dissolved Solids": 500.0,
}


def _html(markup: str) -> None:
    """Render custom HTML after removing Python indentation."""
    cleaned = "\n".join(line.strip() for line in dedent(markup).strip().splitlines())
    st.markdown(cleaned, unsafe_allow_html=True)


st.set_page_config(
    page_title="AquaSoil-AI",
    page_icon=":seedling:",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def main() -> None:
    """Render the AquaSoil-AI web application."""
    _inject_styles()
    _ensure_state()
    _refresh_history()
    _render_header()

    if st.session_state.get("db_error"):
        st.warning(f"History database is unavailable: {st.session_state['db_error']}")

    tabs = st.tabs(["Dashboard", "Analyze Field", "Batch CSV", "AquaBot", "History", "About & CSV"])
    with tabs[0]:
        _render_dashboard()
    with tabs[1]:
        _render_single_sample()
    with tabs[2]:
        _render_batch_upload()
    with tabs[3]:
        _render_chat()
    with tabs[4]:
        _render_history()
    with tabs[5]:
        _render_about_and_csv_help()


def _ensure_state() -> None:
    if "history" not in st.session_state:
        st.session_state["history"] = []
    if "latest_result" not in st.session_state:
        st.session_state["latest_result"] = None
    if "last_batch_results" not in st.session_state:
        st.session_state["last_batch_results"] = []
    if "db_error" not in st.session_state:
        st.session_state["db_error"] = ""
    if "chat_messages" not in st.session_state:
        st.session_state["chat_messages"] = [
            {
                "role": "assistant",
                "content": "Hello. I can explain the latest result, suggest what to do first, and help with CSV files.",
            }
        ]


def _refresh_history() -> None:
    try:
        init_db()
        history = load_all()
    except Exception as exc:
        st.session_state["db_error"] = str(exc)
        return

    st.session_state["history"] = history
    st.session_state["db_error"] = ""
    if history and st.session_state.get("latest_result") is None:
        st.session_state["latest_result"] = history[0]


def _save_result(result: dict[str, Any]) -> None:
    st.session_state["latest_result"] = result
    try:
        save_analysis(result)
    except Exception as exc:
        st.session_state["db_error"] = str(exc)
        st.session_state["history"] = [result, *st.session_state.get("history", [])]
        return
    _refresh_history()


def _save_results(results: list[dict[str, Any]]) -> None:
    if not results:
        return
    st.session_state["latest_result"] = results[-1]
    try:
        for result in results:
            save_analysis(result)
    except Exception as exc:
        st.session_state["db_error"] = str(exc)
        st.session_state["history"] = list(reversed(results)) + st.session_state.get("history", [])
        return
    _refresh_history()


def _render_header() -> None:
    history = st.session_state.get("history", [])
    urgent_count = sum(1 for result in history if _priority(result) == "Urgent")
    good_count = sum(1 for result in history if _is_good(result))
    latest_crop = history[0].get("crop", "None") if history else "None"

    _html(
        f"""
        <div class="app-hero">
            <div class="brand-lockup">
                <div class="brand-mark">AS</div>
                <div>
                    <div class="eyebrow">AquaSoil-AI Web</div>
                    <h1>Farmer field advisor</h1>
                    <p>Soil and water quality analysis with crop suitability, action planning, batch CSV review, and AquaBot guidance.</p>
                </div>
            </div>
            <div class="hero-stats">
                <div><span>{len(history)}</span><small>Analyses</small></div>
                <div><span>{urgent_count}</span><small>Urgent</small></div>
                <div><span>{good_count}</span><small>Good</small></div>
                <div><span>{escape(str(latest_crop))}</span><small>Latest crop</small></div>
            </div>
        </div>
        """
    )


def _render_dashboard() -> None:
    history = st.session_state.get("history", [])
    latest = history[0] if history else st.session_state.get("latest_result")

    urgent_count = sum(1 for result in history if _priority(result) == "Urgent")
    watch_count = sum(1 for result in history if _priority(result) == "Watch")
    good_count = sum(1 for result in history if _is_good(result))

    metric_columns = st.columns(4)
    _metric_card(metric_columns[0], "Total Analyses", str(len(history)), "Saved field records", "primary")
    _metric_card(metric_columns[1], "Urgent Fields", str(urgent_count), "Needs first attention", "danger")
    _metric_card(metric_columns[2], "Watch List", str(watch_count), "Review this week", "warning")
    _metric_card(metric_columns[3], "Good Fields", str(good_count), "Soil and water good", "success")

    left, right = st.columns([1.05, 0.95], gap="large")
    with left:
        _render_latest_field(latest)
    with right:
        _render_action_plan(latest, title="Today Action Focus")

    _html('<div class="section-title">Recent Fields</div>')
    if history:
        st.dataframe(_history_dataframe(history[:8]), use_container_width=True, hide_index=True)
    else:
        _empty_state("No saved analyses yet", "Use Analyze Field or Batch CSV to start building the dashboard.")


def _render_latest_field(result: dict[str, Any] | None) -> None:
    _html('<div class="section-title">Latest Field Reading</div>')
    if not result:
        _empty_state("No latest reading", "Run an analysis to show the newest field status here.")
        return

    advisory = result.get("crop_advisory", {}) if isinstance(result.get("crop_advisory"), dict) else {}
    score = float(advisory.get("score", 0))
    priority = _priority(result)
    first_issue = _first_recommendation(result)

    _html(
        f"""
        <div class="latest-card">
            <div class="latest-heading">
                <div>
                    <span class="eyebrow">Newest sample</span>
                    <h3>{escape(str(result.get("sample", "Unknown Field")))}</h3>
                </div>
                <span class="status-pill tone-{_tone_for_priority(priority)}">{priority}</span>
            </div>
            <div class="detail-grid">
                <div><small>Crop</small><strong>{escape(str(result.get("crop", "General Field")))}</strong></div>
                <div><small>Timestamp</small><strong>{escape(str(result.get("timestamp", "")))}</strong></div>
                <div><small>Soil</small><strong>{escape(str(result.get("soil_class", "")).upper())}</strong></div>
                <div><small>Water</small><strong>{escape(str(result.get("water_class", "")).upper())}</strong></div>
                <div><small>Crop Fit</small><strong>{score:.0f}% {escape(str(advisory.get("status", "")))}</strong></div>
            </div>
            <div class="callout">{escape(first_issue)}</div>
        </div>
        """
    )


def _render_single_sample() -> None:
    left, right = st.columns([0.44, 0.56], gap="large")

    with left:
        _html('<div class="section-title">Field Measurements</div>')
        with st.form("single_sample_form", clear_on_submit=False):
            sample = st.text_input("Sample / Field Name", value="Field A - Barangay Pisan")
            crop = st.selectbox("Target Crop", options=CROP_OPTIONS, index=0)

            values: dict[str, float] = {}
            st.markdown("#### Soil Parameters")
            soil_columns = st.columns(2)
            for index, parameter in enumerate(SOIL_PARAMETERS):
                with soil_columns[index % 2]:
                    values[parameter] = _number_input(parameter, "single")

            st.markdown("#### Water Parameters")
            water_columns = st.columns(2)
            for index, parameter in enumerate(WATER_PARAMETERS):
                with water_columns[index % 2]:
                    values[parameter] = _number_input(parameter, "single")

            submitted = st.form_submit_button("Analyze Sample", type="primary", use_container_width=True)

        if submitted:
            _handle_single_analysis(sample, crop, values)

    with right:
        _html('<div class="section-title">Result Workspace</div>')
        latest = st.session_state.get("latest_result")
        if latest:
            _render_result(latest, key_prefix="single")
        else:
            _empty_state("Waiting for measurements", "Analyze a field to see classifications, crop advice, action plan, and range indicators.")


def _number_input(parameter: str, key_prefix: str) -> float:
    minimum, maximum = PARAMETER_RANGES[parameter]
    return float(
        st.number_input(
            PARAMETER_LABELS.get(parameter, parameter),
            min_value=float(minimum),
            max_value=float(maximum),
            value=float(DEFAULT_VALUES[parameter]),
            step=_step_for(parameter),
            key=f"{key_prefix}_{parameter}",
        )
    )


def _handle_single_analysis(sample: str, crop: str, values: dict[str, float]) -> None:
    sample_label = sample.strip() or "Unknown Field"
    try:
        result = _analyze_sample(sample_label, crop, values)
    except Exception as exc:
        st.error(f"Could not analyze this sample: {exc}")
        return

    _save_result(result)
    st.success(f"Analysis complete for {sample_label}.")


def _render_batch_upload() -> None:
    _html('<div class="section-title">Analyze Multiple Fields</div>')
    setup_column, preview_column = st.columns([0.42, 0.58], gap="large")

    with setup_column:
        uploaded_file = st.file_uploader("Upload AquaSoil-AI CSV", type=["csv"])
        default_crop = st.selectbox("Default crop when CSV has no Crop column", options=CROP_OPTIONS, index=0)
        run_batch = st.button("Run Batch Analysis", type="primary", use_container_width=True)

    dataframe = None
    with preview_column:
        if uploaded_file is None:
            _empty_state("CSV not loaded", "Upload a file with one row per field sample.")
        else:
            try:
                dataframe = pd.read_csv(uploaded_file)
            except Exception as exc:
                st.error(f"Could not read CSV: {exc}")
                return
            _html('<div class="subtle-label">Preview</div>')
            st.dataframe(dataframe.head(12), use_container_width=True, hide_index=True)

    if run_batch:
        if dataframe is None:
            st.warning("Upload a CSV file first.")
            return
        missing = [column for column in PARAMETER_COLUMNS if column not in dataframe.columns]
        if missing:
            st.error("The CSV is missing required columns: " + ", ".join(missing))
            return
        if dataframe.empty:
            st.warning("The uploaded CSV has no rows.")
            return

        results, skipped = _analyze_dataframe(dataframe, default_crop)
        st.session_state["last_batch_results"] = results
        _save_results(results)
        if skipped:
            st.warning(f"Skipped {len(skipped)} invalid row(s).")
            with st.expander("Skipped rows"):
                st.write("\n".join(skipped))
        if results:
            st.success(f"Analyzed {len(results)} field sample(s).")
        else:
            st.error("No valid rows were analyzed.")

    results = st.session_state.get("last_batch_results", [])
    if results:
        _render_batch_results(results)


def _render_batch_results(results: list[dict[str, Any]]) -> None:
    _html('<div class="section-title">Batch Summary</div>')
    summary = _results_to_dataframe(results)
    st.dataframe(summary, use_container_width=True, hide_index=True)
    st.download_button(
        "Download Summary CSV",
        data=summary.to_csv(index=False).encode("utf-8"),
        file_name=f"aquasoil_batch_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
        use_container_width=True,
    )

    options = list(range(len(results)))
    selected_index = st.selectbox(
        "View detailed result",
        options=options,
        format_func=lambda index: f"{results[index].get('sample', 'Unknown Field')} - {results[index].get('crop', 'General Field')}",
    )
    _render_result(results[selected_index], key_prefix=f"batch_{selected_index}")


def _render_chat() -> None:
    _html('<div class="section-title">AquaBot Helper</div>')
    latest = st.session_state.get("latest_result") or _latest_history_result()
    if latest:
        _html(
            f"""
            <div class="context-strip">
                <span>Current context</span>
                <strong>{escape(str(latest.get("sample", "Unknown Field")))}</strong>
                <small>{escape(str(latest.get("crop", "General Field")))} | {_priority(latest)}</small>
            </div>
            """
        )

    quick_prompts = [
        "Explain latest result",
        "Explain crop suitability",
        "What should I do first?",
        "How do I use CSV?",
        "Explain pH",
    ]
    prompt_columns = st.columns(len(quick_prompts))
    for index, prompt in enumerate(quick_prompts):
        with prompt_columns[index]:
            if st.button(prompt, use_container_width=True, key=f"quick_prompt_{index}"):
                _submit_chat(prompt)
                st.rerun()

    for message in st.session_state["chat_messages"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    question = st.chat_input("Ask AquaBot about results, parameters, CSV, reports, or next actions")
    if question:
        _submit_chat(question)
        st.rerun()

    if st.button("Clear Chat", use_container_width=False):
        st.session_state["chat_messages"] = st.session_state["chat_messages"][:1]
        st.rerun()


def _submit_chat(question: str) -> None:
    latest = st.session_state.get("latest_result") or _latest_history_result()
    history = st.session_state.get("history", [])
    response = generate_chat_response(question, latest_result=latest, history=history)
    st.session_state["chat_messages"].append({"role": "user", "content": question})
    st.session_state["chat_messages"].append({"role": "assistant", "content": response})


def _render_history() -> None:
    history = st.session_state.get("history", [])
    _html('<div class="section-title">Session History</div>')

    filter_columns = st.columns([1.3, 0.8, 0.8])
    with filter_columns[0]:
        search_text = st.text_input("Search", placeholder="Sample, crop, class, recommendation")
    with filter_columns[1]:
        priority_filter = st.selectbox("Priority", options=("All", "Urgent", "Watch", "OK", "Good", "Poor"))
    with filter_columns[2]:
        crop_filter = st.selectbox("Crop", options=("All", *CROP_OPTIONS))

    filtered = [
        result
        for result in history
        if _matches_history_filters(result, search_text, priority_filter, crop_filter)
    ]

    metric_columns = st.columns(4)
    _metric_card(metric_columns[0], "Showing", f"{len(filtered)} / {len(history)}", "Filtered records", "primary")
    _metric_card(metric_columns[1], "Urgent", str(sum(1 for item in history if _priority(item) == "Urgent")), "Fix first", "danger")
    _metric_card(metric_columns[2], "Watch", str(sum(1 for item in history if _priority(item) == "Watch")), "Review soon", "warning")
    _metric_card(metric_columns[3], "OK", str(sum(1 for item in history if _priority(item) == "OK")), "Monitor", "success")

    if not filtered:
        _empty_state("No matching analyses", "Try another search or analyze a new field.")
    else:
        st.dataframe(_history_dataframe(filtered), use_container_width=True, hide_index=True)
        selected_index = st.selectbox(
            "Open saved result",
            options=list(range(len(filtered))),
            format_func=lambda index: f"{filtered[index].get('timestamp', '')} - {filtered[index].get('sample', 'Unknown Field')}",
        )
        _render_result(filtered[selected_index], key_prefix=f"history_{selected_index}")

    bottom_columns = st.columns([0.5, 0.5])
    with bottom_columns[0]:
        if history:
            history_csv = _history_dataframe(history).to_csv(index=False).encode("utf-8")
            st.download_button(
                "Download History CSV",
                data=history_csv,
                file_name=f"aquasoil_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True,
            )
    with bottom_columns[1]:
        confirm_clear = st.checkbox("Confirm clear saved history")
        if st.button("Clear Saved History", disabled=not confirm_clear, use_container_width=True):
            try:
                delete_all()
                st.session_state["history"] = []
                st.session_state["latest_result"] = None
                st.session_state["last_batch_results"] = []
                st.success("Saved history cleared.")
                st.rerun()
            except Exception as exc:
                st.error(f"Could not clear history: {exc}")


def _render_about_and_csv_help() -> None:
    about_column, csv_column = st.columns([0.48, 0.52], gap="large")
    with about_column:
        _html('<div class="section-title">About AquaSoil-AI</div>')
        _info_panel(
            "Project Context",
            [
                "Built for farmers in Kabacan, North Cotabato.",
                "Course: CS 17A - Introduction to Artificial Intelligence, 3-BSCS-A, A.Y. 2025-2026.",
                "Intelligent soil and water quality monitoring with farmer-focused advice.",
            ],
        )
        _info_panel("Team Members", TEAM_MEMBERS)
        _info_panel("Technology Stack", ["Python", "Scikit-Learn", "Streamlit", "SQLite", "Pandas"])

    with csv_column:
        _html('<div class="section-title">CSV Format</div>')
        st.write("Use these exact column names. `Crop` is optional but recommended.")
        template = _csv_template()
        st.dataframe(template, use_container_width=True, hide_index=True)
        st.download_button(
            "Download CSV Template",
            data=template.to_csv(index=False).encode("utf-8"),
            file_name="aquasoil_batch_template.csv",
            mime="text/csv",
            use_container_width=True,
        )


def _render_result(result: dict[str, Any], key_prefix: str) -> None:
    _html(
        f"""
        <div class="result-head">
            <div>
                <span class="eyebrow">Analysis result</span>
                <h3>{escape(str(result.get("sample", "Unknown Field")))}</h3>
                <p>{escape(str(result.get("timestamp", "")))} | {escape(str(result.get("crop", "General Field")))}</p>
            </div>
            <span class="status-pill tone-{_tone_for_priority(_priority(result))}">{_priority(result)}</span>
        </div>
        """
    )

    _render_summary_metrics(result)
    _render_crop_suitability(result)
    _render_recommendations(result)
    _render_action_plan(result, title="Farmer Action Plan")
    _render_range_indicators(result)
    _render_report_download(result, key_prefix)


def _render_summary_metrics(result: dict[str, Any]) -> None:
    advisory = result.get("crop_advisory", {}) if isinstance(result.get("crop_advisory"), dict) else {}
    score = float(advisory.get("score", 0))
    metric_columns = st.columns(4)
    _metric_card(
        metric_columns[0],
        "Soil Quality",
        str(result.get("soil_class", "")).upper(),
        f"{float(result.get('soil_confidence', 0)):.0f}% confidence",
        _tone_for_class(result.get("soil_class")),
    )
    _metric_card(
        metric_columns[1],
        "Water Quality",
        str(result.get("water_class", "")).upper(),
        f"{float(result.get('water_confidence', 0)):.0f}% confidence",
        _tone_for_class(result.get("water_class")),
    )
    _metric_card(metric_columns[2], "Crop Fit", f"{score:.0f}%", str(advisory.get("status", "Unknown")), _tone_for_score(score))
    _metric_card(metric_columns[3], "Recommendations", str(len(result.get("recommendations", []))), "Advisory rules matched", "primary")


def _render_crop_suitability(result: dict[str, Any]) -> None:
    advisory = result.get("crop_advisory", {}) if isinstance(result.get("crop_advisory"), dict) else {}
    _html('<div class="section-title">Crop Suitability</div>')
    if not advisory:
        _empty_state("No crop advice available", "Choose a target crop and analyze a sample.")
        return

    score = max(0.0, min(100.0, float(advisory.get("score", 0))))
    crop_name = str(advisory.get("crop", result.get("crop", "General Field")))
    description = CROP_PROFILES.get(crop_name, CROP_PROFILES["General Field"]).get("description", "")

    score_column, detail_column = st.columns([0.32, 0.68], gap="large")
    with score_column:
        _html(
            f"""
            <div class="score-card tone-{_tone_for_score(score)}">
                <small>{escape(crop_name)}</small>
                <strong>{score:.0f}%</strong>
                <span>{escape(str(advisory.get("status", "Unknown")))}</span>
            </div>
            """
        )
        st.progress(score / 100.0)
    with detail_column:
        _html(
            f"""
            <div class="detail-card">
                <p>{escape(str(advisory.get("summary", "")))}</p>
                <small>{escape(str(description))}</small>
            </div>
            """
        )
        steps = [str(step) for step in advisory.get("next_steps", [])]
        if steps:
            _numbered_panel("Next Steps", steps[:4])


def _render_recommendations(result: dict[str, Any]) -> None:
    _html('<div class="section-title">Advisory Recommendations</div>')
    recommendations = [str(item) for item in result.get("recommendations", [])]
    if not recommendations:
        _empty_state("No recommendations", "No rule-based recommendation was generated for this result.")
        return

    cards = []
    for recommendation in recommendations:
        severity = severity_from_recommendation(recommendation)
        cards.append(
            f"""
            <div class="rec-card tone-{_tone_for_severity(severity)}">
                <strong>{escape(severity.title())}</strong>
                <p>{escape(clean_recommendation(recommendation))}</p>
            </div>
            """
        )
    _html("".join(cards))


def _render_action_plan(result: dict[str, Any] | None, title: str) -> None:
    _html(f'<div class="section-title">{escape(title)}</div>')
    plan = build_action_plan(result)
    columns = st.columns(len(ACTION_GROUPS))
    tones = {"Urgent": "danger", "This Week": "warning", "Monitor": "success"}

    for column, group in zip(columns, ACTION_GROUPS):
        items = plan[group][:3]
        body = "".join(f"<li>{escape(str(item))}</li>" for item in items)
        with column:
            _html(
                f"""
                <div class="plan-card tone-{tones[group]}">
                    <strong>{escape(group)}</strong>
                    <ol>{body}</ol>
                </div>
                """
            )


def _render_range_indicators(result: dict[str, Any]) -> None:
    _html('<div class="section-title">Parameter Analysis</div>')
    values = result.get("input_values", {})
    target_ranges = result.get("crop_advisory", {}).get("target_ranges", {})
    cards = [_range_card(parameter, values, target_ranges) for parameter in PARAMETER_COLUMNS]
    _html(f'<div class="range-grid">{"".join(cards)}</div>')


def _range_card(parameter: str, values: dict[str, Any], target_ranges: dict[str, Any]) -> str:
    value = float(values.get(parameter, 0))
    valid_minimum, valid_maximum = PARAMETER_RANGES[parameter]
    target_minimum, target_maximum = target_ranges.get(parameter, PARAMETER_RANGES[parameter])
    target_minimum = float(target_minimum)
    target_maximum = float(target_maximum)
    valid_minimum = float(valid_minimum)
    valid_maximum = float(valid_maximum)

    if value < target_minimum:
        status = "Below crop target"
        tone = "warning"
    elif value > target_maximum:
        status = "Above crop target"
        tone = "warning"
    else:
        status = "Within crop target"
        tone = "success"

    target_left = _percent(target_minimum, valid_minimum, valid_maximum)
    target_right = _percent(target_maximum, valid_minimum, valid_maximum)
    target_width = max(2.0, target_right - target_left)
    marker_left = _percent(value, valid_minimum, valid_maximum)

    return (
        f'<div class="range-card tone-{tone}">'
        '<div class="range-head">'
        f"<strong>{escape(PARAMETER_LABELS.get(parameter, parameter))}</strong>"
        f"<span>{status}</span>"
        "</div>"
        '<div class="range-meta">'
        f"<span>Value {value:g}</span>"
        f"<span>Target {target_minimum:g} - {target_maximum:g}</span>"
        "</div>"
        '<div class="range-track">'
        f'<i class="range-target" style="left:{target_left:.2f}%; width:{target_width:.2f}%;"></i>'
        f'<i class="range-marker" style="left:{marker_left:.2f}%;"></i>'
        "</div>"
        '<div class="range-scale">'
        f"<span>{valid_minimum:g}</span>"
        f"<span>{valid_maximum:g}</span>"
        "</div>"
        "</div>"
    )


def _render_report_download(result: dict[str, Any], key_prefix: str) -> None:
    report_text = _format_report_text(result)
    st.download_button(
        "Download Text Report",
        data=report_text.encode("utf-8"),
        file_name=_safe_report_filename(result.get("sample", "Unknown_Field")),
        mime="text/plain",
        use_container_width=True,
        key=f"{key_prefix}_report_{_result_key(result)}",
    )


def _analyze_sample(sample: str, crop: str, values: dict[str, float]) -> dict[str, Any]:
    validate_inputs(values)
    result = process_sample(sample, values, crop_name=crop)
    if result is None:
        raise RuntimeError("analysis failed")
    result["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    result["input_values"] = values.copy()
    return result


def _analyze_dataframe(dataframe: pd.DataFrame, default_crop: str) -> tuple[list[dict[str, Any]], list[str]]:
    results: list[dict[str, Any]] = []
    skipped: list[str] = []
    for position, row in dataframe.iterrows():
        try:
            sample = str(row.get("Sample", f"Sample_{position + 1}")).strip() or f"Sample_{position + 1}"
            crop = default_crop
            if "Crop" in dataframe.columns and not pd.isna(row.get("Crop")):
                crop = str(row.get("Crop"))
            values = {parameter: float(row[parameter]) for parameter in PARAMETER_COLUMNS}
            results.append(_analyze_sample(sample, crop, values))
        except Exception as exc:
            skipped.append(f"Row {position + 1}: {exc}")
    return results, skipped


def _history_dataframe(results: list[dict[str, Any]]) -> pd.DataFrame:
    rows = []
    for result in results:
        advisory = result.get("crop_advisory", {}) if isinstance(result.get("crop_advisory"), dict) else {}
        rows.append(
            {
                "Timestamp": result.get("timestamp", ""),
                "Sample": result.get("sample", "Unknown Field"),
                "Crop": result.get("crop", "General Field"),
                "Fit": f"{float(advisory.get('score', result.get('crop_score') or 0)):.0f}%",
                "Status": advisory.get("status", result.get("crop_status", "")),
                "Soil": str(result.get("soil_class", "")).upper(),
                "Water": str(result.get("water_class", "")).upper(),
                "Priority": _priority(result),
                "Recs": len(result.get("recommendations", [])),
            }
        )
    return pd.DataFrame(rows)


def _results_to_dataframe(results: list[dict[str, Any]]) -> pd.DataFrame:
    rows = []
    for result in results:
        advisory = result.get("crop_advisory", {}) if isinstance(result.get("crop_advisory"), dict) else {}
        rows.append(
            {
                "Sample": result.get("sample", ""),
                "Crop": result.get("crop", "General Field"),
                "Crop Fit": f"{float(advisory.get('score', 0)):.0f}%",
                "Crop Status": advisory.get("status", ""),
                "Soil": str(result.get("soil_class", "")).upper(),
                "Water": str(result.get("water_class", "")).upper(),
                "Priority": _priority(result),
                "Recommendations": len(result.get("recommendations", [])),
            }
        )
    return pd.DataFrame(rows)


def _csv_template() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "Sample": "Field A - Rice Plot",
                "Crop": "Rice",
                "Soil pH": 6.2,
                "Nitrogen (N)": 80,
                "Phosphorus (P)": 35,
                "Potassium (K)": 180,
                "Soil Moisture": 72,
                "Electrical Conductivity (EC)": 1.2,
                "Water Turbidity": 35,
                "Dissolved Oxygen (DO)": 6.5,
                "Total Dissolved Solids": 480,
            }
        ]
    )


def _format_report_text(result: dict[str, Any]) -> str:
    lines = [
        "=== AquaSoil-AI Advisory Report ===",
        f"Timestamp    : {result.get('timestamp', '')}",
        f"Sample       : {result.get('sample', 'Unknown Field')}",
        f"Target Crop  : {result.get('crop', 'General Field')}",
        f"Soil Quality : {str(result.get('soil_class', '')).upper()} ({float(result.get('soil_confidence', 0)):.0f}% confidence)",
        f"Water Quality: {str(result.get('water_class', '')).upper()} ({float(result.get('water_confidence', 0)):.0f}% confidence)",
        "",
        "--- Input Parameters ---",
    ]
    for parameter in PARAMETER_COLUMNS:
        value = result.get("input_values", {}).get(parameter, "")
        lines.append(f"{parameter}: {value}")

    lines.append("")
    lines.append("--- Crop Suitability ---")
    lines.extend(crop_advisory_lines(result.get("crop_advisory")))

    lines.append("")
    lines.append("--- Recommendations ---")
    for recommendation in result.get("recommendations", []):
        lines.append(str(recommendation))
    return "\n".join(lines)


def _metric_card(container: Any, label: str, value: str, caption: str, tone: str) -> None:
    with container:
        _html(
            f"""
            <div class="metric-card tone-{tone}">
                <small>{escape(label)}</small>
                <strong>{escape(value)}</strong>
                <span>{escape(caption)}</span>
            </div>
            """
        )


def _numbered_panel(title: str, items: list[str]) -> None:
    body = "".join(f"<li>{escape(item)}</li>" for item in items)
    _html(
        f"""
        <div class="numbered-panel">
            <strong>{escape(title)}</strong>
            <ol>{body}</ol>
        </div>
        """
    )


def _info_panel(title: str, lines: list[str]) -> None:
    body = "".join(f"<li>{escape(line)}</li>" for line in lines)
    _html(
        f"""
        <div class="info-panel">
            <strong>{escape(title)}</strong>
            <ul>{body}</ul>
        </div>
        """
    )


def _empty_state(title: str, body: str) -> None:
    _html(
        f"""
        <div class="empty-state">
            <strong>{escape(title)}</strong>
            <span>{escape(body)}</span>
        </div>
        """
    )


def _matches_history_filters(result: dict[str, Any], search_text: str, priority_filter: str, crop_filter: str) -> bool:
    if priority_filter == "Good" and not _is_good(result):
        return False
    if priority_filter == "Poor":
        soil = str(result.get("soil_class", "")).upper()
        water = str(result.get("water_class", "")).upper()
        if soil != "POOR" and water != "POOR":
            return False
    if priority_filter in {"Urgent", "Watch", "OK"} and _priority(result) != priority_filter:
        return False
    if crop_filter != "All" and str(result.get("crop", "")) != crop_filter:
        return False
    if not search_text.strip():
        return True

    normalized = search_text.strip().lower()
    haystack = " ".join(
        [
            str(result.get("timestamp", "")),
            str(result.get("sample", "")),
            str(result.get("crop", "")),
            str(result.get("soil_class", "")),
            str(result.get("water_class", "")),
            " ".join(str(item) for item in result.get("recommendations", [])),
        ]
    ).lower()
    return normalized in haystack


def _first_recommendation(result: dict[str, Any]) -> str:
    recommendations = [str(item) for item in result.get("recommendations", [])]
    if recommendations:
        return clean_recommendation(recommendations[0])
    return "No urgent issue detected from the latest analysis."


def _priority(result: dict[str, Any]) -> str:
    severities = {severity_from_recommendation(str(item)) for item in result.get("recommendations", [])}
    if "CRITICAL" in severities:
        return "Urgent"
    if "WARNING" in severities:
        return "Watch"
    return "OK"


def _is_good(result: dict[str, Any]) -> bool:
    return (
        str(result.get("soil_class", "")).upper() == "GOOD"
        and str(result.get("water_class", "")).upper() == "GOOD"
    )


def _latest_history_result() -> dict[str, Any] | None:
    history = st.session_state.get("history", [])
    return history[0] if history else None


def _tone_for_priority(priority: str) -> str:
    return {"Urgent": "danger", "Watch": "warning", "OK": "success"}.get(priority, "primary")


def _tone_for_severity(severity: str) -> str:
    return {"CRITICAL": "danger", "WARNING": "warning", "OK": "success"}.get(severity, "primary")


def _tone_for_class(value: Any) -> str:
    normalized = str(value).upper()
    if normalized == "POOR":
        return "danger"
    if normalized == "MODERATE":
        return "warning"
    if normalized == "GOOD":
        return "success"
    return "primary"


def _tone_for_score(score: float) -> str:
    if score >= 80:
        return "success"
    if score >= 60:
        return "warning"
    return "danger"


def _percent(value: float, minimum: float, maximum: float) -> float:
    span = max(maximum - minimum, 0.0001)
    return max(0.0, min(100.0, ((value - minimum) / span) * 100.0))


def _step_for(parameter: str) -> float:
    return 0.1 if parameter in {"Soil pH", "Electrical Conductivity (EC)", "Dissolved Oxygen (DO)"} else 1.0


def _safe_report_filename(sample_label: Any) -> str:
    safe_label = "".join(character if character.isalnum() else "_" for character in str(sample_label)).strip("_")
    if not safe_label:
        safe_label = "Unknown_Field"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"report_{safe_label}_{timestamp}.txt"


def _result_key(result: dict[str, Any]) -> str:
    raw_key = f"{result.get('sample', '')}_{result.get('timestamp', '')}_{result.get('crop', '')}"
    safe_key = "".join(character if character.isalnum() else "_" for character in raw_key)
    return safe_key[:80] or "result"


def _inject_styles() -> None:
    _html(
        """
        <style>
        :root {
            --primary: #1565c0;
            --soil: #2e7d32;
            --water: #0277bd;
            --danger: #c62828;
            --warning: #e65100;
            --success: #2e7d32;
            --ink: #263238;
            --muted: #607d8b;
            --line: #d9e4ec;
            --surface: #ffffff;
            --page: #f4f7fb;
        }

        .stApp {
            background: var(--page);
            color: var(--ink);
        }

        .block-container {
            max-width: 1280px;
            padding-top: 1.05rem;
            padding-bottom: 2rem;
        }

        [data-testid="stHeader"] {
            background: rgba(244, 247, 251, 0.88);
        }

        .app-hero {
            display: flex;
            align-items: stretch;
            justify-content: space-between;
            gap: 1rem;
            background: var(--surface);
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: 1.15rem;
            box-shadow: 0 12px 28px rgba(38, 50, 56, 0.08);
            margin-bottom: 1rem;
        }

        .brand-lockup {
            display: flex;
            align-items: center;
            gap: 1rem;
            min-width: 0;
        }

        .brand-mark {
            width: 58px;
            height: 58px;
            display: grid;
            place-items: center;
            flex: 0 0 auto;
            border-radius: 8px;
            background: #e8f5e9;
            color: var(--soil);
            font-weight: 800;
            border: 1px solid #b9dfbd;
        }

        .eyebrow,
        .subtle-label {
            color: var(--primary);
            font-size: 0.78rem;
            font-weight: 800;
            letter-spacing: 0;
            text-transform: uppercase;
        }

        .app-hero h1,
        .latest-card h3,
        .result-head h3 {
            margin: 0.05rem 0;
            color: var(--ink);
            letter-spacing: 0;
        }

        .app-hero h1 {
            font-size: 2rem;
            line-height: 1.08;
        }

        .app-hero p,
        .result-head p {
            margin: 0.15rem 0 0;
            color: var(--muted);
            max-width: 720px;
        }

        .hero-stats {
            display: grid;
            grid-template-columns: repeat(4, minmax(92px, 1fr));
            gap: 0.6rem;
            min-width: 420px;
        }

        .hero-stats div,
        .metric-card,
        .latest-card,
        .plan-card,
        .rec-card,
        .range-card,
        .info-panel,
        .empty-state,
        .detail-card,
        .numbered-panel,
        .context-strip {
            background: var(--surface);
            border: 1px solid var(--line);
            border-radius: 8px;
        }

        .hero-stats div {
            padding: 0.75rem;
        }

        .hero-stats span {
            display: block;
            color: var(--ink);
            font-size: 1.15rem;
            font-weight: 800;
            overflow-wrap: anywhere;
        }

        .hero-stats small,
        .metric-card span,
        .detail-grid small,
        .score-card small,
        .score-card span,
        .detail-card small,
        .empty-state span,
        .context-strip small {
            color: var(--muted);
        }

        .section-title {
            margin: 1.05rem 0 0.55rem;
            color: var(--ink);
            font-size: 1.02rem;
            font-weight: 800;
            letter-spacing: 0;
        }

        .metric-card {
            position: relative;
            min-height: 112px;
            padding: 0.9rem;
            overflow: hidden;
            border-top: 4px solid var(--primary);
            box-shadow: 0 8px 20px rgba(38, 50, 56, 0.06);
        }

        .metric-card small {
            display: block;
            color: var(--muted);
            font-weight: 800;
        }

        .metric-card strong {
            display: block;
            margin: 0.35rem 0 0.2rem;
            color: var(--ink);
            font-size: 1.52rem;
            line-height: 1.1;
            overflow-wrap: anywhere;
        }

        .tone-danger { border-color: #efc7c7 !important; border-top-color: var(--danger) !important; }
        .tone-warning { border-color: #f2d5b9 !important; border-top-color: var(--warning) !important; }
        .tone-success { border-color: #c5e2c8 !important; border-top-color: var(--success) !important; }
        .tone-primary { border-color: #bdd5ea !important; border-top-color: var(--primary) !important; }

        .latest-card,
        .result-head {
            padding: 1rem;
            box-shadow: 0 8px 20px rgba(38, 50, 56, 0.06);
        }

        .latest-heading,
        .result-head {
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 1rem;
        }

        .status-pill {
            display: inline-flex;
            align-items: center;
            border-radius: 999px;
            padding: 0.28rem 0.65rem;
            font-size: 0.78rem;
            font-weight: 800;
            background: #eef5fb;
            color: var(--primary);
            white-space: nowrap;
            border: 1px solid #bdd5ea;
        }

        .status-pill.tone-danger { background: #ffebee; color: var(--danger); }
        .status-pill.tone-warning { background: #fff3e0; color: var(--warning); }
        .status-pill.tone-success { background: #e8f5e9; color: var(--success); }

        .detail-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 0.75rem;
            margin-top: 1rem;
        }

        .detail-grid strong {
            display: block;
            color: var(--ink);
            overflow-wrap: anywhere;
        }

        .callout {
            margin-top: 1rem;
            padding: 0.8rem;
            border-left: 4px solid var(--primary);
            background: #f4f9fd;
            color: var(--ink);
            border-radius: 6px;
        }

        .score-card,
        .detail-card,
        .numbered-panel,
        .plan-card,
        .rec-card,
        .range-card,
        .info-panel,
        .empty-state,
        .context-strip {
            padding: 0.9rem;
            box-shadow: 0 8px 20px rgba(38, 50, 56, 0.05);
        }

        .score-card {
            border-radius: 8px;
            border: 1px solid var(--line);
            background: var(--surface);
            border-top: 4px solid var(--primary);
        }

        .score-card strong {
            display: block;
            margin: 0.25rem 0;
            font-size: 2rem;
            color: var(--ink);
        }

        .detail-card p {
            margin: 0 0 0.55rem;
            color: var(--ink);
            font-weight: 650;
        }

        .numbered-panel ol,
        .plan-card ol,
        .info-panel ul {
            margin: 0.55rem 0 0;
            padding-left: 1.15rem;
        }

        .numbered-panel li,
        .plan-card li,
        .info-panel li {
            margin-bottom: 0.35rem;
            color: var(--ink);
        }

        .plan-card {
            min-height: 210px;
            border-top: 4px solid var(--primary);
        }

        .plan-card strong,
        .info-panel strong,
        .numbered-panel strong {
            color: var(--ink);
        }

        .rec-card {
            margin-bottom: 0.6rem;
            border-left: 5px solid var(--primary);
        }

        .rec-card.tone-danger { border-left-color: var(--danger) !important; }
        .rec-card.tone-warning { border-left-color: var(--warning) !important; }
        .rec-card.tone-success { border-left-color: var(--success) !important; }

        .rec-card p {
            margin: 0.3rem 0 0;
            color: var(--ink);
        }

        .range-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 0.75rem;
        }

        .range-card {
            border-top: 4px solid var(--primary);
        }

        .range-head,
        .range-meta,
        .range-scale {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 0.8rem;
        }

        .range-head strong {
            color: var(--ink);
            overflow-wrap: anywhere;
        }

        .range-head span {
            flex: 0 0 auto;
            color: var(--muted);
            font-size: 0.82rem;
            font-weight: 800;
        }

        .range-meta,
        .range-scale {
            margin-top: 0.3rem;
            color: var(--muted);
            font-size: 0.82rem;
        }

        .range-track {
            position: relative;
            height: 12px;
            margin-top: 0.7rem;
            border-radius: 999px;
            background: #e9eef3;
            overflow: visible;
        }

        .range-target {
            position: absolute;
            top: 3px;
            height: 6px;
            border-radius: 999px;
            background: var(--success);
        }

        .range-marker {
            position: absolute;
            top: 50%;
            width: 14px;
            height: 14px;
            border-radius: 999px;
            background: var(--primary);
            border: 2px solid white;
            box-shadow: 0 0 0 1px rgba(21, 101, 192, 0.45);
            transform: translate(-50%, -50%);
        }

        .empty-state {
            display: flex;
            flex-direction: column;
            gap: 0.3rem;
            padding: 1rem;
            min-height: 112px;
            justify-content: center;
        }

        .context-strip {
            display: flex;
            align-items: center;
            gap: 0.7rem;
            margin-bottom: 0.8rem;
        }

        .context-strip span {
            color: var(--muted);
            font-size: 0.82rem;
            font-weight: 800;
            text-transform: uppercase;
        }

        .stButton > button,
        [data-testid="stFormSubmitButton"] button,
        .stDownloadButton > button {
            border-radius: 7px;
            font-weight: 750;
            border: 1px solid var(--line);
        }

        div[data-testid="stDataFrame"] {
            border: 1px solid var(--line);
            border-radius: 8px;
            overflow: hidden;
        }

        @media (max-width: 980px) {
            .app-hero,
            .latest-heading,
            .result-head,
            .context-strip {
                flex-direction: column;
            }

            .hero-stats,
            .range-grid,
            .detail-grid {
                grid-template-columns: 1fr;
                min-width: 0;
            }
        }
        </style>
        """
    )


if __name__ == "__main__":
    main()
