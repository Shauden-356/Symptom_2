#!/usr/bin/env python3
"""
train.py — Train the ML model from diseases_db.json

Run this script whenever you update diseases_db.json to regenerate model.pkl
"""

import json
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
import joblib

# Load data
with open('app/api/diseases_db.json') as f:
    diseases_db = json.load(f)

with open('app/api/symptoms.json') as f:
    symptoms = json.load(f)

# Create dataset
data = []
labels = []
for disease, info in diseases_db['diseases'].items():
    row = {symptom: 1 if symptom in info['symptoms'] else 0 for symptom in symptoms}
    data.append(row)
    labels.append(disease)

df = pd.DataFrame(data)
le = LabelEncoder()
y = le.fit_transform(labels)

# Train model
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(df, y)

# Save
joblib.dump(model, 'app/api/model.pkl')
joblib.dump(le, 'app/api/label_encoder.pkl')
joblib.dump(symptoms, 'app/api/symptoms.pkl')

print(f"Trained model on {len(df)} diseases with {len(symptoms)} symptoms")