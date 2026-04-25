#!/usr/bin/env python3
"""Train a PyTorch model from the app's disease data."""

import json
from pathlib import Path

import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.preprocessing import LabelEncoder


class SymptomClassifier(nn.Module):
    def __init__(self, input_dim, output_dim):
        super().__init__()
        self.model = nn.Sequential(
            nn.Linear(input_dim, max(input_dim * 2, 64)),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(max(input_dim * 2, 64), output_dim)
        )

    def forward(self, x):
        return self.model(x)


def load_data():
    root = Path(__file__).resolve().parent
    with open(root / 'app' / 'api' / 'diseases_db.json', encoding='utf-8') as f:
        diseases_db = json.load(f)
    with open(root / 'app' / 'api' / 'symptoms.json', encoding='utf-8') as f:
        symptoms = json.load(f)

    diseases = diseases_db['diseases']
    X = []
    y = []
    labels = []

    for name, info in diseases.items():
        vector = [1.0 if symptom in info['symptoms'] else 0.0 for symptom in symptoms]
        X.append(vector)
        labels.append(name)
        y.append(name)

    le = LabelEncoder()
    y = le.fit_transform(y)

    X_tensor = torch.tensor(X, dtype=torch.float32)
    y_tensor = torch.tensor(y, dtype=torch.long)

    return X_tensor, y_tensor, le, symptoms


def train(model, X, y, epochs=100, lr=0.01):
    optimizer = optim.Adam(model.parameters(), lr=lr)
    criterion = nn.CrossEntropyLoss()

    for epoch in range(1, epochs + 1):
        model.train()
        optimizer.zero_grad()
        logits = model(X)
        loss = criterion(logits, y)
        loss.backward()
        optimizer.step()

        if epoch % 20 == 0 or epoch == 1 or epoch == epochs:
            print(f'Epoch {epoch}/{epochs}  loss={loss.item():.4f}')

    return model


def save_model(model, label_encoder, symptoms):
    path = Path('app/api/model_torch.pth')
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            'state_dict': model.state_dict(),
            'symptoms': symptoms,
            'classes': label_encoder.classes_.tolist(),
        },
        path,
    )
    print(f'Saved PyTorch model to {path}')


def main():
    X, y, label_encoder, symptoms = load_data()
    model = SymptomClassifier(input_dim=X.size(1), output_dim=len(label_encoder.classes_))
    model = train(model, X, y)
    save_model(model, label_encoder, symptoms)
    print(f'Trained PyTorch model on {len(label_encoder.classes_)} diseases with {len(symptoms)} symptoms')


if __name__ == '__main__':
    main()
