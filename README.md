# Beyond · Adaptive Behavioral Risk Engine

A production-grade investor risk profiling system using adaptive psychometrics, behavioral finance principles, and AI-powered instrument analysis.

## Architecture

```
beyond-risk-engine/
├── backend/                  # FastAPI backend
│   ├── app/
│   │   ├── api/              # Route handlers
│   │   │   ├── questions.py  # Question engine endpoints
│   │   │   ├── scoring.py    # Scoring engine endpoints  
│   │   │   ├── products.py   # Product matching + instrument upload
│   │   │   ├── investors.py  # Investor CRUD + assessments
│   │   │   └── explain.py    # Explanation engine
│   │   ├── models/           # SQLAlchemy models
│   │   │   └── database.py   # All DB models
│   │   ├── services/         # Business logic
│   │   │   ├── adaptive.py   # Adaptive question selection (IRT)
│   │   │   ├── scoring.py    # Trait computation engine
│   │   │   ├── matching.py   # Product-investor fit scoring
│   │   │   ├── explain.py    # Insight & talking point generation
│   │   │   └── instrument_analyzer.py  # AI factsheet analysis
│   │   └── core/
│   │       ├── config.py     # Settings & env vars
│   │       └── seed.py       # Seed data (40 questions, 35 instruments)
│   ├── main.py               # FastAPI app entry
│   ├── requirements.txt
│   ├── Dockerfile
│   └── railway.toml
├── frontend/                 # React (Vite) frontend
│   ├── src/
│   │   ├── components/       # Reusable UI components
│   │   ├── pages/            # Page-level components
│   │   ├── hooks/            # Custom React hooks
│   │   ├── services/         # API client
│   │   └── data/             # Static trait definitions
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   ├── Dockerfile
│   └── railway.toml
└── README.md
```

## Tech Stack

- **Backend:** FastAPI + SQLAlchemy + PostgreSQL
- **Frontend:** React (Vite) + Tailwind CSS
- **AI Analysis:** Anthropic Claude API for factsheet parsing
- **Deployment:** Railway (2 services + PostgreSQL)

## Key Features

1. **Adaptive Questionnaire** — IRT-based 3-tier system (Anchor/Diagnostic/Calibration)
2. **10-Trait Investor Risk Blueprint** — Continuous 0-100 scores with confidence intervals
3. **AI Instrument Scoring** — Upload factsheets → auto-calculate risk vectors
4. **Product Matching** — Asymmetric behavioral fit scoring
5. **Advisor Toolkit** — Talking points, conversation style, stress predictions
6. **Question Bank Management** — CRUD + AI question generation

## Local Development

```bash
# Backend
cd backend
pip install -r requirements.txt
DATABASE_URL=postgresql://... uvicorn main:app --reload

# Frontend  
cd frontend
npm install
npm run dev
```

## Deployment

Push to GitHub → Railway auto-deploys both services.
