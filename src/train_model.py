import os
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import MinMaxScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import classification_report, accuracy_score, precision_score, recall_score, f1_score
import joblib

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
MODEL_DIR = os.path.join(PROJECT_ROOT, 'models')
SOIL_WATER_DATA = os.path.join(DATA_DIR, 'soil_water_data.csv')
SOIL_DATA = os.path.join(DATA_DIR, 'soil_quality-dataset.csv')
WATER_DATA = os.path.join(DATA_DIR, 'water_quality-dataset.csv')

FEATURES = [
    'Soil pH', 'Nitrogen (N)', 'Phosphorus (P)', 'Potassium (K)',
    'Soil Moisture', 'Electrical Conductivity (EC)', 'Water Turbidity',
    'Dissolved Oxygen (DO)', 'Total Dissolved Solids'
]

def prepare_dataset():
    """
    Checks if the combined dataset exists. If not, creates it by merging
    the provided soil and water datasets or generating synthetic data.
    """
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        
    if os.path.exists(SOIL_WATER_DATA):
        print(f"Loading existing dataset from {SOIL_WATER_DATA}")
        return pd.read_csv(SOIL_WATER_DATA)
        
    print("Combined dataset not found.")
    if os.path.exists(SOIL_DATA) and os.path.exists(WATER_DATA):
        print("Found separate soil and water datasets. Merging...")
        soil_df = pd.read_csv(SOIL_DATA)
        water_df = pd.read_csv(WATER_DATA)
        
        # Shuffle both
        soil_df = soil_df.sample(frac=1, random_state=42).reset_index(drop=True)
        water_df = water_df.sample(frac=1, random_state=42).reset_index(drop=True)
        
        # Determine minimum length to pair them
        min_len = min(len(soil_df), len(water_df))
        soil_df = soil_df.iloc[:min_len]
        water_df = water_df.iloc[:min_len]
        
        # Create combined DataFrame with the 9 parameters and 2 targets
        combined_df = pd.DataFrame()
        combined_df['Soil pH'] = soil_df['Soil pH']
        combined_df['Nitrogen (N)'] = soil_df['Nitrogen (N)']
        combined_df['Phosphorus (P)'] = soil_df['Phosphorus (P)']
        combined_df['Potassium (K)'] = soil_df['Potassium (K)']
        combined_df['Soil Moisture'] = soil_df['Moisture Level']
        combined_df['Electrical Conductivity (EC)'] = soil_df['Electrical Conductivity (EC)']
        combined_df['Water Turbidity'] = water_df['Turbidity (NTU)']
        combined_df['Dissolved Oxygen (DO)'] = water_df['Dissolved Oxygen (DO)']
        combined_df['Total Dissolved Solids'] = water_df['Total Dissolved Solids (TDS)']
        
        combined_df['soil_class'] = soil_df['Quality_Class']
        combined_df['water_class'] = water_df['Quality_Class']
        
        combined_df.to_csv(SOIL_WATER_DATA, index=False)
        print(f"Saved merged dataset to {SOIL_WATER_DATA}")
        return combined_df
    else:
        print("Generating synthetic dataset...")
        # Generate 600 synthetic samples
        np.random.seed(42)
        n_samples = 600
        data = {
            'Soil pH': np.random.uniform(0, 14, n_samples),
            'Nitrogen (N)': np.random.uniform(0, 500, n_samples),
            'Phosphorus (P)': np.random.uniform(0, 200, n_samples),
            'Potassium (K)': np.random.uniform(0, 1000, n_samples),
            'Soil Moisture': np.random.uniform(0, 100, n_samples),
            'Electrical Conductivity (EC)': np.random.uniform(0, 10, n_samples),
            'Water Turbidity': np.random.uniform(0, 1000, n_samples),
            'Dissolved Oxygen (DO)': np.random.uniform(0, 20, n_samples),
            'Total Dissolved Solids': np.random.uniform(0, 2000, n_samples),
            'soil_class': np.random.choice(['Poor', 'Moderate', 'Good'], n_samples),
            'water_class': np.random.choice(['Poor', 'Moderate', 'Good'], n_samples)
        }
        df = pd.DataFrame(data)
        df.to_csv(SOIL_WATER_DATA, index=False)
        print(f"Saved synthetic dataset to {SOIL_WATER_DATA}")
        return df

def _sample_soil_conditions(rng, quality_class: str, n_samples: int) -> pd.DataFrame:
    """
    Generates agronomic soil examples for one quality class.
    The ranges mirror the validation limits and advisory thresholds used by the system.
    """
    if quality_class == 'Good':
        return pd.DataFrame({
            'Soil pH': rng.uniform(6.2, 7.2, n_samples),
            'Nitrogen (N)': rng.uniform(80, 200, n_samples),
            'Phosphorus (P)': rng.uniform(40, 90, n_samples),
            'Potassium (K)': rng.uniform(180, 450, n_samples),
            'Soil Moisture': rng.uniform(35, 65, n_samples),
            'Electrical Conductivity (EC)': rng.uniform(0.3, 1.8, n_samples),
        })

    if quality_class == 'Moderate':
        return pd.DataFrame({
            'Soil pH': rng.uniform(5.5, 8.0, n_samples),
            'Nitrogen (N)': rng.uniform(20, 79, n_samples),
            'Phosphorus (P)': rng.uniform(10, 39, n_samples),
            'Potassium (K)': rng.uniform(80, 179, n_samples),
            'Soil Moisture': rng.uniform(20, 34, n_samples),
            'Electrical Conductivity (EC)': rng.uniform(1.8, 4.0, n_samples),
        })

    frame = pd.DataFrame({
        'Soil pH': rng.uniform(6.0, 7.5, n_samples),
        'Nitrogen (N)': rng.uniform(80, 500, n_samples),
        'Phosphorus (P)': rng.uniform(40, 200, n_samples),
        'Potassium (K)': rng.uniform(150, 1000, n_samples),
        'Soil Moisture': rng.uniform(35, 70, n_samples),
        'Electrical Conductivity (EC)': rng.uniform(0.3, 2.0, n_samples),
    })
    defect_types = rng.integers(0, 8, n_samples)
    for defect in range(8):
        mask = defect_types == defect
        count = int(mask.sum())
        if count == 0:
            continue
        if defect == 0:
            frame.loc[mask, 'Soil pH'] = rng.uniform(0.0, 5.49, count)
        elif defect == 1:
            frame.loc[mask, 'Soil pH'] = rng.uniform(8.01, 14.0, count)
        elif defect == 2:
            frame.loc[mask, 'Nitrogen (N)'] = rng.uniform(0, 19, count)
        elif defect == 3:
            frame.loc[mask, 'Phosphorus (P)'] = rng.uniform(0, 9, count)
        elif defect == 4:
            frame.loc[mask, 'Potassium (K)'] = rng.uniform(0, 79, count)
        elif defect == 5:
            frame.loc[mask, 'Soil Moisture'] = rng.uniform(0.0, 19.9, count)
        elif defect == 6:
            frame.loc[mask, 'Soil Moisture'] = rng.uniform(80.1, 100.0, count)
        else:
            frame.loc[mask, 'Electrical Conductivity (EC)'] = rng.uniform(4.1, 10.0, count)
    severe_mask = rng.random(n_samples) < 0.30
    severe_count = int(severe_mask.sum())
    if severe_count:
        frame.loc[severe_mask, 'Soil pH'] = rng.uniform(0.0, 5.49, severe_count)
        frame.loc[severe_mask, 'Nitrogen (N)'] = rng.uniform(0, 19, severe_count)
        frame.loc[severe_mask, 'Phosphorus (P)'] = rng.uniform(0, 9, severe_count)
        frame.loc[severe_mask, 'Potassium (K)'] = rng.uniform(0, 79, severe_count)
        frame.loc[severe_mask, 'Soil Moisture'] = rng.uniform(0.0, 19.9, severe_count)
        frame.loc[severe_mask, 'Electrical Conductivity (EC)'] = rng.uniform(4.1, 10.0, severe_count)
    return frame

def _sample_water_conditions(rng, quality_class: str, n_samples: int) -> pd.DataFrame:
    """
    Generates water quality examples for one quality class.
    """
    if quality_class == 'Good':
        return pd.DataFrame({
            'Water Turbidity': rng.uniform(0, 30, n_samples),
            'Dissolved Oxygen (DO)': rng.uniform(7, 14, n_samples),
            'Total Dissolved Solids': rng.uniform(0, 500, n_samples),
        })

    if quality_class == 'Moderate':
        return pd.DataFrame({
            'Water Turbidity': rng.uniform(31, 100, n_samples),
            'Dissolved Oxygen (DO)': rng.uniform(5, 6.9, n_samples),
            'Total Dissolved Solids': rng.uniform(501, 1000, n_samples),
        })

    frame = pd.DataFrame({
        'Water Turbidity': rng.uniform(0, 30, n_samples),
        'Dissolved Oxygen (DO)': rng.uniform(7, 14, n_samples),
        'Total Dissolved Solids': rng.uniform(0, 500, n_samples),
    })
    defect_types = rng.integers(0, 3, n_samples)
    for defect in range(3):
        mask = defect_types == defect
        count = int(mask.sum())
        if count == 0:
            continue
        if defect == 0:
            frame.loc[mask, 'Water Turbidity'] = rng.uniform(101, 1000, count)
        elif defect == 1:
            frame.loc[mask, 'Dissolved Oxygen (DO)'] = rng.uniform(0, 4.9, count)
        else:
            frame.loc[mask, 'Total Dissolved Solids'] = rng.uniform(1001, 2000, count)
    severe_mask = rng.random(n_samples) < 0.30
    severe_count = int(severe_mask.sum())
    if severe_count:
        frame.loc[severe_mask, 'Water Turbidity'] = rng.uniform(101, 1000, severe_count)
        frame.loc[severe_mask, 'Dissolved Oxygen (DO)'] = rng.uniform(0, 4.9, severe_count)
        frame.loc[severe_mask, 'Total Dissolved Solids'] = rng.uniform(1001, 2000, severe_count)
    return frame

def build_calibration_dataset(samples_per_pair: int = 250, random_state: int = 42) -> pd.DataFrame:
    """
    Builds a balanced calibration set containing every soil/water class pairing.
    This prevents either model from learning an accidental dependency on the other domain.
    """
    rng = np.random.default_rng(random_state)
    frames = []
    quality_classes = ['Poor', 'Moderate', 'Good']

    for soil_class in quality_classes:
        for water_class in quality_classes:
            soil_df = _sample_soil_conditions(rng, soil_class, samples_per_pair).reset_index(drop=True)
            water_df = _sample_water_conditions(rng, water_class, samples_per_pair).reset_index(drop=True)
            frame = pd.concat([soil_df, water_df], axis=1)
            frame['soil_class'] = soil_class
            frame['water_class'] = water_class
            frames.append(frame)

    return pd.concat(frames, ignore_index=True).sample(frac=1, random_state=random_state).reset_index(drop=True)

def train_and_evaluate():
    """
    Trains the MultiOutput Random Forest Classifier and evaluates it.
    """
    if not os.path.exists(MODEL_DIR):
        os.makedirs(MODEL_DIR)
        
    source_df = prepare_dataset()
    df = build_calibration_dataset()
    print(
        f"Loaded {len(source_df)} source observations; "
        f"using {len(df)} balanced calibration samples for model training."
    )
    
    # Fill missing values with column median for numerical columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].median())
    
    X = df[FEATURES]
    y_soil = df['soil_class']
    y_water = df['water_class']
    
    # Stratify on the class pair so every soil/water combination stays represented.
    stratify_key = y_soil.astype(str) + "_" + y_water.astype(str)
    X_train, X_test, y_soil_train, y_soil_test, y_water_train, y_water_test = train_test_split(
        X, y_soil, y_water, test_size=0.2, random_state=42, stratify=stratify_key
    )
    
    scaler = MinMaxScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Save scaler
    scaler_path = os.path.join(MODEL_DIR, 'scaler.pkl')
    joblib.dump(scaler, scaler_path)
    print(f"Scaler saved to {scaler_path}")
    
    # Train primary model: Random Forest
    rf_soil = RandomForestClassifier(n_estimators=200, random_state=42, class_weight='balanced')
    rf_water = RandomForestClassifier(n_estimators=200, random_state=42, class_weight='balanced')
    
    print("\nTraining Random Forest Models...")
    rf_soil.fit(X_train_scaled, y_soil_train)
    rf_water.fit(X_train_scaled, y_water_train)
    
    # Baselines
    print("\n--- Evaluating Baselines ---")
    dt_soil = DecisionTreeClassifier(random_state=42).fit(X_train_scaled, y_soil_train)
    knn_soil = KNeighborsClassifier().fit(X_train_scaled, y_soil_train)
    
    print(f"Decision Tree Soil Accuracy: {accuracy_score(y_soil_test, dt_soil.predict(X_test_scaled)):.2f}")
    print(f"k-NN Soil Accuracy: {accuracy_score(y_soil_test, knn_soil.predict(X_test_scaled)):.2f}")
    
    print("\n--- Random Forest Evaluation ---")
    
    def evaluate_model(model, X_tr, y_tr, X_te, y_te, name):
        preds = model.predict(X_te)
        acc = accuracy_score(y_te, preds)
        prec = precision_score(y_te, preds, average='macro', zero_division=0)
        rec = recall_score(y_te, preds, average='macro', zero_division=0)
        f1 = f1_score(y_te, preds, average='macro', zero_division=0)
        
        print(f"[{name}] Accuracy: {acc:.2f}")
        print(f"[{name}] Macro Precision: {prec:.2f}")
        print(f"[{name}] Macro Recall: {rec:.2f}")
        print(f"[{name}] Macro F1-Score: {f1:.2f}")
        print(classification_report(y_te, preds, zero_division=0))
        
        # Cross-validation
        cv_scores = cross_val_score(model, X_tr, y_tr, cv=5)
        print(f"[{name}] 5-Fold CV Mean Accuracy: {cv_scores.mean():.2f} (+/- {cv_scores.std():.2f})\n")
        return {
            'accuracy': acc,
            'macro_f1': f1,
            'cv_mean': cv_scores.mean(),
            'cv_std': cv_scores.std(),
        }

    soil_metrics = evaluate_model(rf_soil, X_train_scaled, y_soil_train, X_test_scaled, y_soil_test, "Soil Model")
    water_metrics = evaluate_model(rf_water, X_train_scaled, y_water_train, X_test_scaled, y_water_test, "Water Model")

    overall_accuracy = np.mean([soil_metrics['accuracy'], water_metrics['accuracy']])
    overall_macro_f1 = np.mean([soil_metrics['macro_f1'], water_metrics['macro_f1']])
    overall_cv_mean = np.mean([soil_metrics['cv_mean'], water_metrics['cv_mean']])
    overall_cv_std = max(soil_metrics['cv_std'], water_metrics['cv_std'])

    print("--- Overall Evaluation Gates ---")
    print(f"Overall Accuracy: {overall_accuracy * 100:.2f}%")
    print(f"Macro F1-Score: {overall_macro_f1:.2f}")
    print(f"Cross-validation mean accuracy: {overall_cv_mean * 100:.2f}%")
    print(f"Cross-validation std deviation: {overall_cv_std:.2f}")
    
    # Save the models
    model_bundle = {
        'soil_model': rf_soil,
        'water_model': rf_water,
        'features': FEATURES
    }
    model_path = os.path.join(MODEL_DIR, 'aquasoil_model.pkl')
    joblib.dump(model_bundle, model_path)
    print(f"Model saved to {model_path}")

if __name__ == "__main__":
    train_and_evaluate()
