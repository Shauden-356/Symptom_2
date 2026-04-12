import json
import joblib

# Load model and data
model = joblib.load('app/api/model.pkl')
le = joblib.load('app/api/label_encoder.pkl')
symptoms = joblib.load('app/api/symptoms.pkl')

# Load disease info
with open('app/api/diseases_db.json') as f:
    diseases_db = json.load(f)

def predict_symptoms(selected_symptoms):
    # Create input vector
    input_vector = [1 if s in selected_symptoms else 0 for s in symptoms]

    # Predict probabilities
    probs = model.predict_proba([input_vector])[0]

    # Get top predictions
    predictions = []
    for i, prob in enumerate(probs):
        if prob > 0.01:  # threshold
            disease = le.inverse_transform([i])[0]
            info = diseases_db['diseases'][disease]
            predictions.append({
                'disease': disease,
                'confidence': round(prob * 100, 1),
                'severity': info['severity'],
                'advice': info['advice']
            })

    # Sort by confidence
    predictions.sort(key=lambda x: x['confidence'], reverse=True)

    return predictions[:5]  # top 5

def handler(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            selected_symptoms = data.get('symptoms', [])

            predictions = predict_symptoms(selected_symptoms)

            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'predictions': predictions,
                    'symptom_count': len(selected_symptoms),
                    'disclaimer': 'This is an AI-based tool for informational purposes only. Always consult a qualified healthcare professional for medical advice.'
                })
            }
        except Exception as e:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': str(e)})
            }
    else:
        return {
            'statusCode': 405,
            'body': 'Method not allowed'
        }