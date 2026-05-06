import numpy as np

# Valid ranges as per SRS Section 6.1
PARAMETER_RANGES = {
    "Soil pH": (0.0, 14.0),
    "Nitrogen (N)": (0, 500),
    "Phosphorus (P)": (0, 200),
    "Potassium (K)": (0, 1000),
    "Soil Moisture": (0, 100),
    "Electrical Conductivity (EC)": (0, 10),
    "Water Turbidity": (0, 1000),
    "Dissolved Oxygen (DO)": (0, 20),
    "Total Dissolved Solids": (0, 2000)
}

def validate_inputs(input_values: dict):
    """
    Validates the input dictionary against the defined physical ranges.
    Raises ValueError if any parameter is missing or out of bounds.
    """
    for param, (min_val, max_val) in PARAMETER_RANGES.items():
        if param not in input_values:
            raise ValueError(f"Missing required parameter: {param}")
        
        val = input_values[param]
        if not isinstance(val, (int, float)):
            raise ValueError(f"Parameter '{param}' must be a number. Got: {type(val)}")
            
        if not (min_val <= val <= max_val):
            raise ValueError(f"Parameter '{param}' value {val} is out of bounds. Valid range: {min_val} to {max_val}.")

def fit_scaler(data, scaler):
    """
    Fits the MinMaxScaler on the provided training data.
    """
    return scaler.fit(data)

def transform_data(data, scaler):
    """
    Transforms data using the fitted MinMaxScaler.
    """
    return scaler.transform(data)
