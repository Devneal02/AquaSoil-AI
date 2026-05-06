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

DATA_DIR = 'data'
MODEL_DIR = 'models'
SOIL_WATER_DATA = os.path.join(DATA_DIR, 'soil_water_data.csv')
SOIL_DATA = 'soil_quality-dataset.csv'
WATER_DATA = 'water_quality-dataset.csv'

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

def train_and_evaluate():
    """
    Trains the MultiOutput Random Forest Classifier and evaluates it.
    """
    if not os.path.exists(MODEL_DIR):
        os.makedirs(MODEL_DIR)
        
    df = prepare_dataset()
    
    # Fill missing values with column median for numerical columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].median())
    
    features = [
        'Soil pH', 'Nitrogen (N)', 'Phosphorus (P)', 'Potassium (K)', 
        'Soil Moisture', 'Electrical Conductivity (EC)', 'Water Turbidity', 
        'Dissolved Oxygen (DO)', 'Total Dissolved Solids'
    ]
    
    X = df[features]
    y_soil = df['soil_class']
    y_water = df['water_class']
    
    # 80/20 train/test split. 
    # Since we have two targets, we can just split randomly, or stratify on one. We'll stratify on soil_class for simplicity
    X_train, X_test, y_soil_train, y_soil_test, y_water_train, y_water_test = train_test_split(
        X, y_soil, y_water, test_size=0.2, random_state=42, stratify=y_soil
    )
    
    scaler = MinMaxScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Save scaler
    scaler_path = os.path.join(MODEL_DIR, 'scaler.pkl')
    joblib.dump(scaler, scaler_path)
    print(f"Scaler saved to {scaler_path}")
    
    # Train primary model: Random Forest
    rf_soil = RandomForestClassifier(n_estimators=100, random_state=42)
    rf_water = RandomForestClassifier(n_estimators=100, random_state=42)
    
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

    evaluate_model(rf_soil, X_train_scaled, y_soil_train, X_test_scaled, y_soil_test, "Soil Model")
    evaluate_model(rf_water, X_train_scaled, y_water_train, X_test_scaled, y_water_test, "Water Model")
    
    # Save the models
    model_bundle = {
        'soil_model': rf_soil,
        'water_model': rf_water,
        'features': features
    }
    model_path = os.path.join(MODEL_DIR, 'aquasoil_model.pkl')
    joblib.dump(model_bundle, model_path)
    print(f"Model saved to {model_path}")

if __name__ == "__main__":
    train_and_evaluate()
