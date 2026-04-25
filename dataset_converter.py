#!/usr/bin/env python3
"""Convert external disease/symptom datasets to the app's JSON format.

Supported inputs:
- JSON array of objects with disease/symptoms
- JSON object with a `diseases` map
- CSV/TSV with `disease` and `symptoms` columns
- CSV/TSV with disease in first column and symptom columns after

The converter normalizes symptom text to snake_case and writes:
- app/api/diseases_db.json
- app/api/symptoms.json
"""

import argparse
import csv
import json
import re
from pathlib import Path

DEFAULT_README = (
    "HOW TO ADD A DISEASE: Add a new entry under 'diseases'. "
    "Give it a name, a list of symptom IDs (use snake_case), "
    "a severity (mild/moderate/severe/critical), and advice text. "
    "Any new symptom ID you use is automatically added to the model — "
    "run 'python train.py' afterwards."
)

SPLIT_PATTERN = re.compile(r"\s*[;,|/]\s*")
NORMALIZE_PATTERN = re.compile(r"[^a-z0-9_]+")


def normalize_symptom_id(text):
    text = str(text or '').strip().lower()
    if not text:
        return ''
    text = text.replace('-', ' ').replace('.', ' ').replace('(', ' ').replace(')', ' ')
    text = re.sub(r"\s+", '_', text)
    text = NORMALIZE_PATTERN.sub('', text)
    text = re.sub(r"_+", '_', text).strip('_')
    return text


def split_symptoms(value):
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    if isinstance(value, str):
        if value.strip() == '':
            return []
        return [piece.strip() for piece in SPLIT_PATTERN.split(value.strip()) if piece.strip()]
    return [str(value).strip()]


def parse_csv(path):
    path = Path(path)
    delimiter = '\t' if path.suffix.lower() == '.tsv' else ','
    with path.open(newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        rows = list(reader)
    if not rows:
        raise ValueError(f'No rows found in {path}')

    entries = []
    for row in rows:
        row = {k.strip(): v for k, v in row.items() if k is not None}
        disease = row.get('disease') or row.get('Disease') or row.get('name') or row.get('Name')
        if not disease:
            disease = next(iter(row.values()), None)
        if not disease:
            continue

        raw_symptoms = []
        if 'symptoms' in row:
            raw_symptoms = split_symptoms(row['symptoms'])
        elif 'Symptom' in row:
            raw_symptoms = split_symptoms(row['Symptom'])
        else:
            columns = list(row.keys())
            if len(columns) > 1:
                raw_symptoms = [row[col] for col in columns[1:] if str(row[col]).strip()]

        entries.append({
            'disease': disease,
            'symptoms': raw_symptoms,
            'severity': row.get('severity') or row.get('Severity'),
            'advice': row.get('advice') or row.get('Advice')
        })
    return entries


def parse_json(path):
    with open(path, encoding='utf-8') as f:
        source = json.load(f)

    if isinstance(source, dict):
        if 'diseases' in source and isinstance(source['diseases'], dict):
            entries = []
            for disease, info in source['diseases'].items():
                entries.append({
                    'disease': disease,
                    'symptoms': info.get('symptoms', []),
                    'severity': info.get('severity'),
                    'advice': info.get('advice')
                })
            return entries
        if all(isinstance(v, list) for v in source.values()):
            return [
                {'disease': disease, 'symptoms': symptoms}
                for disease, symptoms in source.items()
            ]
        if 'disease' in source and 'symptoms' in source:
            return [source]
        raise ValueError('Unsupported JSON structure. Expected array or disease map.')
    if isinstance(source, list):
        entries = []
        for item in source:
            if isinstance(item, dict):
                entries.append({
                    'disease': item.get('disease') or item.get('name'),
                    'symptoms': item.get('symptoms') or item.get('symptom') or [],
                    'severity': item.get('severity'),
                    'advice': item.get('advice')
                })
        return entries
    raise ValueError('Unsupported JSON data type. Expected object or array.')


def build_dataset(entries, default_severity='moderate', default_advice=None):
    diseases = {}
    symptoms_set = set()

    for entry in entries:
        disease = str(entry.get('disease') or '').strip()
        if not disease:
            continue

        symptoms = [normalize_symptom_id(s) for s in split_symptoms(entry.get('symptoms'))]
        symptoms = [s for s in symptoms if s]
        symptoms_set.update(symptoms)

        severity = str(entry.get('severity') or default_severity).strip().lower()
        if severity not in {'mild', 'moderate', 'severe', 'critical'}:
            severity = default_severity

        advice = str(entry.get('advice') or default_advice or 'Please consult a qualified healthcare professional.').strip()

        diseases[disease] = {
            'symptoms': sorted(set(symptoms)),
            'severity': severity,
            'advice': advice
        }

    return diseases, sorted(symptoms_set)


def load_existing_diseases(path):
    path = Path(path)
    if not path.exists():
        return {'diseases': {}}, []
    with path.open(encoding='utf-8') as f:
        data = json.load(f)
    symptoms_path = path.parent / 'symptoms.json'
    symptoms = []
    if symptoms_path.exists():
        with symptoms_path.open(encoding='utf-8') as f:
            symptoms = json.load(f)
    return data, symptoms


def merge_datasets(existing, new):
    merged = existing.copy()
    merged.update(new)
    return merged


def write_dataset(diseases, symptoms, output_path, symptoms_path):
    output_path = Path(output_path)
    symptoms_path = Path(symptoms_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    symptoms_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open('w', encoding='utf-8') as f:
        json.dump({'_readme': DEFAULT_README, 'diseases': diseases}, f, indent=2, ensure_ascii=False)

    with symptoms_path.open('w', encoding='utf-8') as f:
        json.dump(sorted(symptoms), f, indent=2, ensure_ascii=False)


def main():
    parser = argparse.ArgumentParser(description='Convert external disease/symptom datasets to app/api/diseases_db.json')
    parser.add_argument('--input', '-i', required=True, help='External dataset file path (JSON, CSV, TSV)')
    parser.add_argument('--output', '-o', default='app/api/diseases_db.json', help='Target diseases DB JSON path')
    parser.add_argument('--symptoms-output', default='app/api/symptoms.json', help='Target symptoms JSON path')
    parser.add_argument('--merge', action='store_true', help='Merge with existing disease entries instead of replacing')
    parser.add_argument('--default-severity', default='moderate', help='Default severity when missing')
    parser.add_argument('--default-advice', default='Please consult a qualified healthcare professional.', help='Default advice when missing')

    args = parser.parse_args()
    input_path = Path(args.input)
    if not input_path.exists():
        raise FileNotFoundError(f'Input file not found: {input_path}')

    suffix = input_path.suffix.lower()
    if suffix in {'.json'}:
        entries = parse_json(input_path)
    elif suffix in {'.csv', '.tsv'}:
        entries = parse_csv(input_path)
    else:
        raise ValueError('Unsupported file type. Use JSON, CSV, or TSV.')

    diseases, symptoms = build_dataset(entries, args.default_severity, args.default_advice)

    if args.merge:
        existing_data, existing_symptoms = load_existing_diseases(args.output)
        merged_diseases = merge_datasets(existing_data.get('diseases', {}), diseases)
        symptoms = sorted(set(existing_symptoms).union(symptoms))
        diseases = merged_diseases

    write_dataset(diseases, symptoms, args.output, args.symptoms_output)
    print(f'Wrote {len(diseases)} diseases and {len(symptoms)} symptoms to {args.output}')


if __name__ == '__main__':
    main()
