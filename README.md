# SymptomAI — Next.js + Vercel

AI-powered disease prediction. Everything — frontend and backend — runs on a **single Vercel deployment**. No Render, no Railway, no separate backend needed.

## Stack

- **Frontend**: Next.js 14 (App Router) — React UI
- **Backend**: Python serverless functions in `/api` — scikit-learn ML model
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

Edit `api/data/diseases_db.json`, commit and push. The model is pre-trained so you also need to retrain locally and commit the new `model.pkl`:

```bash
cd api
python train.py   # regenerates model.pkl, symptoms.json, diseases.json
cd ..
git add .
git commit -m "add new disease"
git push
```
