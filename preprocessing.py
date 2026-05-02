import pandas as pd
import numpy as np
from imblearn.over_sampling import SMOTE
from collections import Counter

# ==========================================
# PART 1: CLASSIFICATION LOGIC
# ==========================================

def classify_water(row):
    ph = row['pH Level']
    tds = row['Total Dissolved Solids (TDS)']
    
    if (ph < 5.5 or ph > 8.5) or tds > 1500:
        return 'Poor'
    elif (6.5 <= ph <= 7.5) and tds < 500:
        return 'Good'
    else:
        return 'Moderate'

def classify_soil(row):
    ph = row['Soil pH']
    om = row['Organic Matter']
    moisture = row['Moisture Level']
    
    if ph < 5.0 or ph > 8.5 or om < 1.0 or moisture < 10:
        return 'Poor'
    elif (6.0 <= ph <= 7.5) and om >= 3.0 and (20 <= moisture <= 60):
        return 'Good'
    else:
        return 'Moderate'

# ==========================================
# PART 2: SYNTHESIZING MISSING PARAMETERS
# ==========================================

def prepare_water_data(water_df):
    print("--- Preparing Water Data ---")
    # 1. Rename columns
    water_df = water_df.rename(columns={
        'ph': 'pH Level',
        'Solids': 'Total Dissolved Solids (TDS)',
        'Conductivity': 'Electrical Conductivity (EC)',
        'Turbidity': 'Turbidity (NTU)'
    })
    
    np.random.seed(42) 
    
    # 2. SYNTHESIZE 'Dissolved Oxygen (DO)'
    water_df['Dissolved Oxygen (DO)'] = np.random.uniform(low=2.0, high=9.0, size=len(water_df))
    
    # 3. FIX TDS: Synthesize realistic agricultural TDS (100 to 2000 mg/L) instead of Kaggle's 20,000+
    water_df['Total Dissolved Solids (TDS)'] = np.random.uniform(low=100.0, high=2000.0, size=len(water_df))
    
    # 4. ROUND EVERYTHING TO 2 DECIMALS
    water_df = np.round(water_df, 2)
    
    # 5. APPLY CORRECT LABELS
    water_df['Quality_Class'] = water_df.apply(classify_water, axis=1)
    
    # 6. Keep only the needed columns 
    needed_water_cols = ['pH Level', 'Turbidity (NTU)', 'Electrical Conductivity (EC)', 'Total Dissolved Solids (TDS)', 'Dissolved Oxygen (DO)', 'Quality_Class']
    
    return water_df[needed_water_cols]

def prepare_soil_data(soil_df):
    print("--- Preparing Soil Data ---")
    soil_df = soil_df.rename(columns={
        'Nitrogen': 'Nitrogen (N)',
        'Phosphorous': 'Phosphorus (P)',
        'Potassium': 'Potassium (K)',
        'Moisture': 'Moisture Level'
    })
    
    np.random.seed(42)
    soil_df['Soil pH'] = np.round(np.random.uniform(low=4.5, high=8.5, size=len(soil_df)), 2)
    soil_df['Organic Matter'] = np.round(np.random.uniform(low=0.5, high=5.0, size=len(soil_df)), 2)
    soil_df['Electrical Conductivity (EC)'] = np.round(np.random.uniform(low=0.5, high=3.5, size=len(soil_df)), 2)
    soil_df['Quality_Class'] = soil_df.apply(classify_soil, axis=1)
    
    needed_soil_cols = ['Soil pH', 'Nitrogen (N)', 'Phosphorus (P)', 'Potassium (K)', 
                        'Organic Matter', 'Moisture Level', 'Electrical Conductivity (EC)', 'Quality_Class']
    
    return soil_df[needed_soil_cols]

# ==========================================
# PART 3: BALANCING DATASETS WITH SMOTE
# ==========================================

def handle_missing_values(df, target_column):
    """Drop rows where target is NaN, then fill remaining NaNs with column medians."""
    before = len(df)

    # Drop rows where the label itself is missing (can't classify them)
    df = df.dropna(subset=[target_column])

    # Fill missing feature values with each column's median
    feature_cols = [col for col in df.columns if col != target_column]
    df[feature_cols] = df[feature_cols].fillna(df[feature_cols].median())

    after = len(df)
    if before != after:
        print(f"  Dropped {before - after} rows with missing '{target_column}' labels.")
    
    remaining_nans = df[feature_cols].isnull().sum().sum()
    if remaining_nans == 0:
        print("  No remaining NaNs in features — ready for SMOTE.")
    else:
        # Fallback: drop any stubborn rows (e.g. all-NaN columns)
        df = df.dropna()
        print(f"  Warning: {remaining_nans} NaNs could not be filled; affected rows dropped.")

    return df

def balance_dataset_with_smote(df, target_column):
    print(f"Original class distribution: {Counter(df[target_column])}")
    
    # FIX 1: Handle NaN values before passing to SMOTE
    df = handle_missing_values(df, target_column)

    X = df.drop(columns=[target_column])
    y = df[target_column]

    # FIX 2: Set k_neighbors dynamically based on the smallest class size.
    # SMOTE default is k=6, but it crashes if any class has fewer samples than that.
    min_class_samples = min(Counter(y).values())
    k = min(6, min_class_samples - 1)  # Must be at least 1 less than the smallest class

    if k < 1:
        print(f"  WARNING: A class has only {min_class_samples} sample(s) — too few even for SMOTE with k=1.")
        print("  Skipping SMOTE for this dataset. Check your classification thresholds or source data.")
        return df  # Return as-is rather than crashing

    print(f"  Using k_neighbors={k} for SMOTE (smallest class has {min_class_samples} sample(s)).")
    smote = SMOTE(random_state=42, k_neighbors=k)
    X_balanced, y_balanced = smote.fit_resample(X, y)
    
    balanced_df = pd.concat(
        [pd.DataFrame(X_balanced, columns=X.columns), pd.Series(y_balanced, name=target_column)],
        axis=1
    )
    
    balanced_df = np.round(balanced_df, 2)
    balanced_df[target_column] = y_balanced

    print(f"Balanced class distribution: {Counter(balanced_df[target_column])}")
    return balanced_df

# ==========================================
# EXECUTION
# ==========================================

if __name__ == "__main__":
    try:
        water_raw = pd.read_csv('water_dataset-raw.csv')
        soil_raw = pd.read_csv('soil_dataset-raw.csv')
        print("MY SOIL COLUMNS ARE:", soil_raw.columns.tolist())
        print("Successfully loaded CSV files!")
    except FileNotFoundError:
        print("ERROR: Could not find the CSV files. Make sure they are in the same folder as this script and the names match!")
        exit()

    water_processed = prepare_water_data(water_raw)
    soil_processed = prepare_soil_data(soil_raw)
    
    print("\n--- Applying SMOTE to Water Data ---")
    water_balanced = balance_dataset_with_smote(water_processed, 'Quality_Class')
    
    print("\n--- Applying SMOTE to Soil Data ---")
    soil_balanced = balance_dataset_with_smote(soil_processed, 'Quality_Class')
    
    water_balanced.to_csv('water_quality-dataset.csv', index=False)
    soil_balanced.to_csv('soil_quality-dataset.csv', index=False)
    print("\nSuccess! Your datasets are now perfectly synthesized, labeled, balanced, and saved.")