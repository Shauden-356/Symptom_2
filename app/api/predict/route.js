import { predict } from '../_model.js';

export async function POST(request) {
  try {
    const { symptoms } = await request.json();

    if (!Array.isArray(symptoms)) {
      return Response.json(
        { error: 'symptoms must be an array' },
        { status: 400 }
      );
    }

    const predictions = predict(symptoms);

    return Response.json({
      predictions,
      symptom_count: symptoms.length,
      disclaimer: 'This is an AI-based tool for informational purposes only. Always consult a qualified healthcare professional for medical advice.'
    });
  } catch (error) {
    console.error('Prediction error:', error);
    return Response.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}