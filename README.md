# SymptomAI — Next.js + Vercel

AI-powered disease prediction. Everything — frontend and backend — runs on a **single Vercel deployment**.

## Stack

- **Frontend**: Next.js 15 (App Router) — React UI
- **Backend**: Python serverless functions in `/app/api` — scikit-learn ML model plus optional PyTorch training support
- **Auto-update**: GitHub Actions retrains the model when `diseases_db.json` changes
- **Deploy**: Vercel only

## Structure

```
symptom-ai/
├── app/
│   ├── layout.js       Root layout + fonts
│   ├── page.js         Main React UI
│   └── globals.css     All styles
│
├── app/api/            Python serverless functions → /api/*
│   ├── _model.js       Legacy JS model (not used)
│   ├── health/         GET  /api/health
│   ├── symptoms/       GET  /api/symptoms
│   ├── categories/     GET  /api/categories
│   ├── predict/        POST /api/predict (Python)
│   ├── questions/      POST /api/questions
│   ├── diseases_db.json ✏️ Add diseases here
│   ├── symptoms.json
│   ├── model.pkl       Auto-generated ML model
│   ├── label_encoder.pkl
│   └── symptoms.pkl
│
├── train.py            Script to manually retrain the model
├── requirements.txt    Python dependencies
├── .github/workflows/train.yml  Auto-retrain on data changes
├── package.json
├── next.config.js
├── vercel.json
└── .gitignore
```

## Adding Diseases

Edit `app/api/diseases_db.json` to add new diseases. Each disease needs:
- `symptoms`: array of symptom IDs (snake_case)
- `severity`: "mild", "moderate", "severe", "critical"
- `advice`: short medical advice text

After editing, push to GitHub. GitHub Actions will automatically retrain the ML model and update `model.pkl`.

For local development, run `python3 train.py` to retrain manually.

## Import external datasets

Use `dataset_converter.py` to convert external JSON, CSV, or TSV datasets into the app format. This script normalizes symptom text to snake_case and writes both:
- `app/api/diseases_db.json`
- `app/api/symptoms.json`

Example conversions:

```bash
python3 dataset_converter.py --input external-diseases.csv
python3 dataset_converter.py --input external-dataset.json --output app/api/diseases_db.json
python3 dataset_converter.py --input external-data.tsv --merge
```

If your external dataset does not contain severity or advice, `dataset_converter.py` fills missing values with defaults so the dataset is still usable.

## PyTorch training

A PyTorch training script is available at `train_torch.py`.

```bash
python3 train_torch.py
```

This produces `app/api/model_torch.pth` and uses the same disease/symptom schema as the rest of the app.

## Deploy (one command)

```bash
# 1. Push to GitHub
git init
git add .
git commit -m "initial commit"
git remote add origin https://github.com/YOUR_USERNAME/symptom-ai.git
git push -u origin main

# 2. Go to vercel.com → New Project → Import your repo
#    Framework: Next.js  (auto-detected)
#    Root Directory: . (the repo root, default)
#    No environment variables needed
#    Click Deploy
```

Done. Your app is live at `https://symptom-ai.vercel.app`.

## Local Development

```bash
npm install
npm run dev
# → http://localhost:3000
```

## Adding a New Disease

Edit `app/api/diseases_db.json`, commit and push. The model is pre-trained so you also need to retrain locally and commit the new `model.pkl`:

```bash
python3 train.py   # regenerates model.pkl, symptoms.json
python3 train_torch.py  # optionally train the PyTorch model too
git add .
git commit -m "add new disease"
git push
```
