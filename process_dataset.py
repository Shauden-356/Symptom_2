#!/usr/bin/env python3
"""Process the new dataset and integrate into the project."""

import csv
import json
import re
from collections import defaultdict
from pathlib import Path

def to_snake_case(s):
    # Convert to lowercase, replace spaces and special chars with underscores
    s = re.sub(r'[^\w\s-]', '', s)  # Remove special chars except spaces and hyphens
    s = re.sub(r'[\s-]+', '_', s)  # Replace spaces and hyphens with underscores
    return s.lower()

def process_csv():
    root = Path(__file__).resolve().parent
    csv_path = root / 'Final_Augmented_dataset_Diseases_and_Symptoms.csv'
    
    # Read existing data
    with open(root / 'app' / 'api' / 'symptoms.json', encoding='utf-8') as f:
        existing_symptoms = set(json.load(f))
    
    with open(root / 'app' / 'api' / 'diseases_db.json', encoding='utf-8') as f:
        diseases_db = json.load(f)
    
    # Symptom mapping: original -> snake_case
    symptom_map = {}
    disease_symptoms = defaultdict(set)
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            disease = row['diseases']
            for symptom, value in row.items():
                if symptom == 'diseases':
                    continue
                if value == '1':
                    snake_symptom = to_snake_case(symptom)
                    symptom_map[symptom] = snake_symptom
                    disease_symptoms[disease].add(snake_symptom)
    
    # Update symptoms.json
    all_symptoms = existing_symptoms.union(set(symptom_map.values()))
    with open(root / 'app' / 'api' / 'symptoms.json', 'w', encoding='utf-8') as f:
        json.dump(sorted(all_symptoms), f, indent=2)
    
    # Update diseases_db.json
    for disease, symptoms in disease_symptoms.items():
        if disease not in diseases_db['diseases']:
            diseases_db['diseases'][disease] = {
                "symptoms": list(symptoms),
                "severity": "moderate",  # Default
                "advice": "Consult a healthcare professional for proper diagnosis and treatment."
            }
    
    with open(root / 'app' / 'api' / 'diseases_db.json', 'w', encoding='utf-8') as f:
        json.dump(diseases_db, f, indent=2, ensure_ascii=False)
    
    print(f"Added {len(disease_symptoms)} new diseases and {len(set(symptom_map.values())) - len(existing_symptoms)} new symptoms.")

if __name__ == '__main__':
    process_csv()