# Multimodal Construction Intelligence Platform

An AI-powered, full-stack decision-support system for construction professionals. It analyses **text, images and structured project data** using a multimodal LLM (Google Gemini) to give actionable, context-aware insights.

**Stack:** React.js (Vite) · FastAPI (Python) · Gemini multimodal LLM · Open-Meteo weather API

## Features (mapped to project Epics)
| Epic | Feature | Endpoint |
|---|---|---|
| 1 | Requirements + environment setup | this README, `.env.example` |
| 2 | Site safety monitoring, crack detection and analysis (image-based) | `POST /api/safety`, `POST /api/cracks` |
| 3 | Real estate valuation, construction project planning | `POST /api/valuation`, `POST /api/planning` |
| 4 | AI intelligence layer: prompt engineering + strict JSON contracts + fallback | `ask_llm()` in `backend/main.py` |
| 5 | Daily site assistant, weather-aware advisory, knowledge assistant | `GET /api/weather`, `POST /api/assistant` |
| 6 | Interface, testing, deployment | React UI, `/api/health`, deployment below |

## Architecture
React UI -> FastAPI (JSON contracts) -> Gemini multimodal model; weather via Open-Meteo. If no API key is set, deterministic fallbacks keep every endpoint working.

## Run locally
Backend:
```bash
cd backend
python -m venv venv && venv\Scripts\activate   # Linux/Mac: source venv/bin/activate
pip install -r requirements.txt
copy .env.example .env    # add your GEMINI_API_KEY (free at aistudio.google.com)
uvicorn main:app --reload
```
Frontend:
```bash
cd frontend
npm install
npm run dev
```
Open http://localhost:5173 (API docs at http://localhost:8000/docs).

## Deploy
- Backend: Render (build `pip install -r requirements.txt`, start `uvicorn main:app --host 0.0.0.0 --port $PORT`, root dir `backend`, env var `GEMINI_API_KEY`).
- Frontend: Vercel/Netlify (root dir `frontend`, env var `VITE_API_URL` = your Render URL).

## Author
Suhani Rathore
