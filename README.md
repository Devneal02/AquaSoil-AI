# AquaSoil-AI

Intelligent Soil & Water Quality Monitoring and Advisory System.

## Setup Instructions

1. Ensure Python 3.9+ is installed.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Folder structure is initialized on the first run of the training script.

## How to Train the Model

To build the combined dataset and train the ML models, run:
```bash
python src/train_model.py
```
This will generate `aquasoil_model.pkl` and `scaler.pkl` in the `models/` directory.

## How to Run the System

### Single Sample Mode
To process a single sample interactively, run:
```bash
python src/main.py
```
or 
```bash
python gui/app.py
```
to run it with GUI
You will be prompted to enter a sample label and values for the 9 parameters.

### Batch Mode
To process multiple samples from a CSV file:
```bash
python src/main.py --batch path/to/your_batch.csv
```
The CSV file must contain a `Sample` column and exactly match the parameter names:
`Soil pH`, `Nitrogen (N)`, `Phosphorus (P)`, `Potassium (K)`, `Soil Moisture`, `Electrical Conductivity (EC)`, `Water Turbidity`, `Dissolved Oxygen (DO)`, `Total Dissolved Solids`.

### Debug Mode
Add `--debug` to see detailed logs of rule firings.

## How to Add New Rules to the Knowledge Base

1. Open `src/knowledge_base.py`.
2. Append a new dictionary to the `RULES` list.
3. Ensure you follow the structure:
   - `id`: Unique string (e.g., 'R17')
   - `priority`: 1 (Critical), 2 (Warning), or 3 (Informational/OK)
   - `domain`: 'soil', 'water', or 'combined'
   - `condition`: A lambda function taking a `facts` dictionary and returning a boolean. Use `facts.get('Parameter Name', default)` to handle missing values gracefully.
   - `recommendation`: The text to output, prefixed with [CRITICAL], [WARNING], or [OK].
   - `source`: Citation of the agricultural standard.
