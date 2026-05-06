import os
import joblib
import pandas as pd
import numpy as np

MODEL_PATH = os.path.join('models', 'aquasoil_model.pkl')
SCALER_PATH = os.path.join('models', 'scaler.pkl')

def _load_model_and_scaler():
    """
    Loads the trained models and scaler.
    Raises FileNotFoundError with clear instructions if missing.
    """
    if not os.path.exists(MODEL_PATH) or not os.path.exists(SCALER_PATH):
        raise FileNotFoundError(
            f"Model or scaler file missing.\n"
            f"Please run 'python src/train_model.py' to generate them.\n"
            f"Expected paths: {MODEL_PATH}, {SCALER_PATH}"
        )
    model_bundle = joblib.load(MODEL_PATH)
    scaler = joblib.load(SCALER_PATH)
    return model_bundle, scaler

def classify(input_values: dict) -> dict:
    """
    Classifies the input using the trained Random Forest models.
    Returns:
        {
            'soil_class': str,
            'soil_confidence': float,
            'water_class': str,
            'water_confidence': float
        }
    """
    model_bundle, scaler = _load_model_and_scaler()
    
    features = model_bundle['features']
    rf_soil = model_bundle['soil_model']
    rf_water = model_bundle['water_model']
    
    # Ensure order matches training
    data = [input_values[f] for f in features]
    
    # Scale data
    scaled_data = scaler.transform([data])
    
    # Predict soil
    soil_pred = rf_soil.predict(scaled_data)[0]
    soil_proba = rf_soil.predict_proba(scaled_data)[0]
    soil_conf = np.max(soil_proba) * 100
    
    # Predict water
    water_pred = rf_water.predict(scaled_data)[0]
    water_proba = rf_water.predict_proba(scaled_data)[0]
    water_conf = np.max(water_proba) * 100
    
    return {
        'soil_class': soil_pred,
        'soil_confidence': soil_conf,
        'water_class': water_pred,
        'water_confidence': water_conf
    }
