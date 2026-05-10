import os
from datetime import datetime
import textwrap

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORTS_DIR = os.path.join(PROJECT_ROOT, 'reports')

def _ensure_report_dir():
    if not os.path.exists(REPORTS_DIR):
        os.makedirs(REPORTS_DIR)

def print_advisory(sample_label: str, classification_result: dict, recommendations: list[str]) -> None:
    """
    Formats and prints the advisory report to CLI, and saves it to a file.
    """
    _ensure_report_dir()
    
    soil_cls = classification_result['soil_class'].upper()
    soil_conf = classification_result['soil_confidence']
    water_cls = classification_result['water_class'].upper()
    water_conf = classification_result['water_confidence']
    generated_at = datetime.now()
    
    report_lines = []
    report_lines.append("=== AquaSoil-AI Advisory Report ===")
    report_lines.append(f"Sample      : {sample_label}")
    report_lines.append(f"Timestamp   : {generated_at.strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append(f"Soil Quality: {soil_cls:<6} (Confidence: {soil_conf:.0f}%)")
    report_lines.append(f"Water Quality: {water_cls:<5} (Confidence: {water_conf:.0f}%)")
    report_lines.append("\n--- Recommendations ---")
    
    for rec in recommendations:
        # We need to wrap text with an indent for subsequent lines.
        # Find where the severity tag ends, typically after ']'
        tag_end = rec.find(']') + 1
        if tag_end > 0:
            prefix = rec[:tag_end] + "  "
            content = rec[tag_end:].strip()
            # Wrap the content, subsequent lines should align with content start
            wrapper = textwrap.TextWrapper(initial_indent=prefix, subsequent_indent=" " * len(prefix), width=70)
            report_lines.append(wrapper.fill(content))
        else:
            report_lines.append(textwrap.fill(rec, width=70))
            
    report_text = "\n".join(report_lines)
    
    # Save report
    timestamp = generated_at.strftime("%Y%m%d_%H%M%S")
    # Clean label for filename if provided
    safe_label = "".join(c if c.isalnum() else "_" for c in sample_label.split(" - ")[0])
    filename = f"report_{timestamp}_{safe_label}.txt"
    filepath = os.path.join(REPORTS_DIR, filename)
    counter = 2
    while os.path.exists(filepath):
        filename = f"report_{timestamp}_{safe_label}_{counter}.txt"
        filepath = os.path.join(REPORTS_DIR, filename)
        counter += 1
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(report_text)
        
    display_path = os.path.relpath(filepath, PROJECT_ROOT)
    report_text += f"\n\nReport saved: {display_path}\n"
    
    print("\n" + report_text)

def print_batch_summary(results: list[dict]):
    """
    Prints a summary table of all samples processed in batch mode.
    """
    print("\n=== Batch Processing Summary ===")
    header = f"{'Sample':<25} | {'Soil Quality':<12} | {'Water Quality':<13} | {'Alerts'}"
    print(header)
    print("-" * len(header))
    
    for r in results:
        sample = textwrap.shorten(r['sample'], width=23, placeholder="..")
        soil = r['soil_class'].upper()
        water = r['water_class'].upper()
        alerts = len([rec for rec in r['recommendations'] if 'CRITICAL' in rec or 'WARNING' in rec])
        print(f"{sample:<25} | {soil:<12} | {water:<13} | {alerts} issue(s)")
    print("================================\n")
