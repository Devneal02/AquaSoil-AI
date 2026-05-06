"""
Knowledge Base for AquaSoil-AI
Contains the IF-THEN rules used by the Reasoning Engine.
"""

# Priorities: 1 = Critical, 2 = Warning, 3 = Informational/OK
RULES = [
    # Soil pH - Acidic (2 rules)
    {
        'id': 'R01',
        'priority': 1,
        'domain': 'soil',
        'condition': lambda f: f.get('soil_class', '').upper() == 'POOR' and f.get('Soil pH', 7.0) < 5.5,
        'recommendation': '[CRITICAL] Soil is highly acidic. Apply agricultural lime. Do not plant until pH reaches 6.0-7.0.',
        'source': 'DA-Philippines Crop Guidelines'
    },
    {
        'id': 'R02',
        'priority': 2,
        'domain': 'soil',
        'condition': lambda f: f.get('soil_class', '').upper() == 'MODERATE' and 5.5 <= f.get('Soil pH', 7.0) < 6.0,
        'recommendation': '[WARNING] Soil is slightly acidic. Consider applying a moderate amount of lime before the next planting season.',
        'source': 'DA-Philippines Crop Guidelines'
    },
    
    # Soil pH - Alkaline (1 rule)
    {
        'id': 'R03',
        'priority': 1,
        'domain': 'soil',
        'condition': lambda f: f.get('soil_class', '').upper() == 'POOR' and f.get('Soil pH', 7.0) > 8.0,
        'recommendation': '[CRITICAL] Soil is highly alkaline. Apply sulfur or acidifying agents to lower pH.',
        'source': 'FAO Soil Quality Guidelines'
    },
    
    # Low NPK (3 rules)
    {
        'id': 'R04',
        'priority': 2,
        'domain': 'soil',
        'condition': lambda f: f.get('Nitrogen (N)', 100) < 20,
        'recommendation': '[WARNING] Low nitrogen detected. Apply urea fertilizer. Reassess in 2 weeks.',
        'source': 'DA-Philippines Crop Guidelines'
    },
    {
        'id': 'R05',
        'priority': 2,
        'domain': 'soil',
        'condition': lambda f: f.get('Phosphorus (P)', 50) < 10,
        'recommendation': '[WARNING] Low phosphorus detected. Apply phosphate fertilizer.',
        'source': 'DA-Philippines Crop Guidelines'
    },
    {
        'id': 'R06',
        'priority': 2,
        'domain': 'soil',
        'condition': lambda f: f.get('Potassium (K)', 200) < 80,
        'recommendation': '[WARNING] Low potassium detected. Apply potash fertilizer.',
        'source': 'DA-Philippines Crop Guidelines'
    },
    
    # Soil Moisture Stress (2 rules)
    {
        'id': 'R07',
        'priority': 2,
        'domain': 'soil',
        'condition': lambda f: f.get('Soil Moisture', 50) < 20,
        'recommendation': '[WARNING] Soil moisture critically low. Increase irrigation immediately.',
        'source': 'FAO Soil Quality Guidelines'
    },
    {
        'id': 'R08',
        'priority': 2,
        'domain': 'soil',
        'condition': lambda f: f.get('Soil Moisture', 50) > 80,
        'recommendation': '[WARNING] Soil moisture excessively high. Improve drainage to prevent waterlogging.',
        'source': 'FAO Soil Quality Guidelines'
    },
    
    # High Electrical Conductivity (1 rule)
    {
        'id': 'R09',
        'priority': 1,
        'domain': 'soil',
        'condition': lambda f: f.get('Electrical Conductivity (EC)', 0) > 4,
        'recommendation': '[CRITICAL] High electrical conductivity indicates salinity stress. Flush soil with fresh water.',
        'source': 'FAO Soil Quality Guidelines'
    },
    
    # High Water Turbidity (2 rules)
    {
        'id': 'R10',
        'priority': 2,
        'domain': 'water',
        'condition': lambda f: 50 < f.get('Water Turbidity', 0) <= 100,
        'recommendation': '[WARNING] Water turbidity is elevated. Filter before use for irrigation.',
        'source': 'DA-Philippines Crop Guidelines'
    },
    {
        'id': 'R11',
        'priority': 1,
        'domain': 'water',
        'condition': lambda f: f.get('Water Turbidity', 0) > 100,
        'recommendation': '[CRITICAL] Water turbidity is dangerously high. Do not use for irrigation.',
        'source': 'DA-Philippines Crop Guidelines'
    },
    
    # Low Dissolved Oxygen (1 rule)
    {
        'id': 'R12',
        'priority': 2,
        'domain': 'water',
        'condition': lambda f: f.get('Dissolved Oxygen (DO)', 10) < 5,
        'recommendation': '[WARNING] Low dissolved oxygen in water. Aerate water source if possible.',
        'source': 'FAO Water Quality Guidelines'
    },
    
    # High TDS (1 rule)
    {
        'id': 'R13',
        'priority': 2,
        'domain': 'water',
        'condition': lambda f: f.get('Total Dissolved Solids', 0) > 1000,
        'recommendation': '[WARNING] High Total Dissolved Solids detected. Consider using an alternative water source.',
        'source': 'FAO Water Quality Guidelines'
    },
    
    # Optimal Conditions (1 rule)
    {
        'id': 'R14',
        'priority': 3,
        'domain': 'combined',
        'condition': lambda f: f.get('soil_class', '').upper() == 'GOOD' and f.get('water_class', '').upper() == 'GOOD',
        'recommendation': '[OK] Soil and water quality are both Good. Safe to plant and irrigate.',
        'source': 'General Agricultural Guidelines'
    },
    
    # Combined Advisories (2 rules)
    {
        'id': 'R15',
        'priority': 1,
        'domain': 'combined',
        'condition': lambda f: f.get('soil_class', '').upper() == 'POOR' and f.get('water_class', '').upper() == 'POOR',
        'recommendation': '[CRITICAL] Both soil and water quality are Poor. Urgent intervention needed before any farming activity.',
        'source': 'General Agricultural Guidelines'
    },
    {
        'id': 'R16',
        'priority': 2,
        'domain': 'combined',
        'condition': lambda f: f.get('Soil Moisture', 50) < 30 and f.get('water_class', '').upper() == 'GOOD',
        'recommendation': '[WARNING] Low moisture detected but water quality is Good. Increase irrigation frequency safely.',
        'source': 'General Agricultural Guidelines'
    }
]
