import argparse
import os
import sys
import pandas as pd
import logging

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.preprocess import PARAMETER_RANGES, validate_inputs
from src.classifier import classify
from src.reasoning_engine import get_recommendations
from src.output import print_advisory, print_batch_summary

def get_interactive_inputs() -> tuple[str, dict]:
    """
    Prompts the user for a sample label and the 9 required parameters.
    Returns a tuple of (sample_label, input_dict).
    """
    print("\n=== AquaSoil-AI Parameter Input ===")
    sample_label = input("Enter Sample Label (e.g., 'Field A - Barangay Kilada'): ").strip()
    if not sample_label:
        sample_label = "Unknown Field"
        
    input_values = {}
    for param, (min_val, max_val) in PARAMETER_RANGES.items():
        while True:
            try:
                val_str = input(f"Enter {param} ({min_val} - {max_val}): ")
                val = float(val_str)
                # Validation handled by validate_inputs later, but we do basic bounds here for UX
                if not (min_val <= val <= max_val):
                    print(f"  [!] Value must be between {min_val} and {max_val}. Try again.")
                    continue
                input_values[param] = val
                break
            except ValueError:
                print("  [!] Invalid number format. Please enter a numeric value.")
                
    return sample_label, input_values

def process_sample(sample_label: str, input_values: dict, debug: bool = False) -> dict:
    """
    Processes a single sample through the pipeline.
    """
    try:
        # 1. Validate Input
        validate_inputs(input_values)
        
        # 2. Classify
        classification_result = classify(input_values)
        
        # 3. Reasoning
        # Combine input values and classification results into facts
        facts = input_values.copy()
        facts.update({
            'soil_class': classification_result['soil_class'],
            'water_class': classification_result['water_class']
        })
        recommendations = get_recommendations(facts, debug=debug)
        
        # Return bundled result for reporting
        return {
            'sample': sample_label,
            'soil_class': classification_result['soil_class'],
            'soil_confidence': classification_result['soil_confidence'],
            'water_class': classification_result['water_class'],
            'water_confidence': classification_result['water_confidence'],
            'recommendations': recommendations
        }
    except Exception as e:
        if debug:
            logging.exception("Error processing sample.")
        print(f"\n[ERROR] Failed to process sample '{sample_label}': {str(e)}")
        return None

def main():
    range_lines = "\n".join(
        f"  - {param}: {min_val} to {max_val}"
        for param, (min_val, max_val) in PARAMETER_RANGES.items()
    )
    parser = argparse.ArgumentParser(
        description="AquaSoil-AI: Intelligent Soil and Water Quality Advisory System",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=(
            "Required parameters and valid ranges:\n"
            f"{range_lines}\n\n"
            "Available flags:\n"
            "  --batch PATH   Process samples from a CSV file\n"
            "  --debug        Print fired rule IDs and diagnostic details"
        ),
    )
    parser.add_argument('--batch', type=str, help="Path to CSV file for batch processing")
    parser.add_argument('--debug', action='store_true', help="Enable debug logging for rule firing")
    args = parser.parse_args()
    
    if args.debug:
        logging.basicConfig(level=logging.DEBUG, format="[DEBUG] %(message)s")
        
    if args.batch:
        print(f"Starting batch mode processing for file: {args.batch}")
        try:
            df = pd.read_csv(args.batch)
            results = []
            
            for index, row in df.iterrows():
                # Extract sample label, default to row index if missing
                sample_label = str(row.get('Sample', f"Sample_{index+1}"))
                
                # Extract parameters mapping (case insensitive matching or exact depending on CSV)
                # We assume the CSV header exactly matches PARAMETER_RANGES keys
                input_values = {}
                for param in PARAMETER_RANGES.keys():
                    if param in row:
                        input_values[param] = float(row[param])
                    else:
                        raise KeyError(f"CSV missing required column: '{param}'")
                        
                result = process_sample(sample_label, input_values, debug=args.debug)
                if result:
                    print_advisory(result['sample'], result, result['recommendations'])
                    results.append(result)
                    
            if results:
                print_batch_summary(results)
                
        except FileNotFoundError:
            print(f"[ERROR] Batch file '{args.batch}' not found.")
            sys.exit(1)
        except Exception as e:
            print(f"[ERROR] Batch processing failed: {str(e)}")
            sys.exit(1)
            
    else:
        # Interactive mode
        try:
            sample_label, input_values = get_interactive_inputs()
            result = process_sample(sample_label, input_values, debug=args.debug)
            if result:
                print_advisory(result['sample'], result, result['recommendations'])
        except KeyboardInterrupt:
            print("\nOperation cancelled by user.")
            sys.exit(0)

if __name__ == "__main__":
    main()
