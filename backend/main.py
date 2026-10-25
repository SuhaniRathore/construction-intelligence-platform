"""Multimodal Construction Intelligence Platform - FastAPI backend.
Every endpoint returns a strict JSON contract so the React frontend stays stable.
If GEMINI_API_KEY is missing, a deterministic fallback keeps the demo working."""
import io, json, os, re
from typing import Optional

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
model = None
if API_KEY:
    import google.generativeai as genai
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")

app = FastAPI(title="Multimodal Construction Intelligence Platform")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


def ask_llm(prompt: str, image: Optional[Image.Image], fallback: dict) -> dict:
    """Call the multimodal LLM and force a JSON answer; fall back on any failure."""
    if model is None:
        return {**fallback, "source": "fallback (no API key)"}
    try:
        parts = [prompt + "\nRespond with ONLY valid JSON, no markdown."]
        if image is not None:
            parts.append(image)
        text = model.generate_content(parts).text
        match = re.search(r"\{.*\}", text, re.S)
        return {**json.loads(match.group(0)), "source": "gemini"}
    except Exception as e:  # keep the API stable for the frontend
        return {**fallback, "source": f"fallback ({type(e).__name__})"}


async def load_image(file: Optional[UploadFile]) -> Optional[Image.Image]:
    if file is None:
        return None
    return Image.open(io.BytesIO(await file.read())).convert("RGB")


@app.get("/api/health")
def health():
    return {"status": "ok", "llm_enabled": model is not None}


# Epic 2 - image based analysis
@app.post("/api/safety")
async def safety(image: UploadFile = File(...), notes: str = Form("")):
    img = await load_image(image)
    prompt = f"""You are a construction site safety inspector. Analyse this site image. Notes: {notes}
Return JSON: {{"risk_level":"Low|Medium|High","violations":[str],"ppe_detected":[str],"recommendations":[str],"summary":str}}"""
    fb = {"risk_level": "Medium", "violations": ["Workers may be missing helmets or harnesses"],
          "ppe_detected": ["Unable to verify without LLM"],
          "recommendations": ["Enforce PPE checks", "Install edge protection", "Daily toolbox talk"],
          "summary": "Fallback analysis. Add GEMINI_API_KEY for real image analysis."}
    return ask_llm(prompt, img, fb)


@app.post("/api/cracks")
async def cracks(image: UploadFile = File(...)):
    img = await load_image(image)
    prompt = """You are a structural engineer. Inspect this surface for cracks.
Return JSON: {"crack_found":bool,"type":"hairline|shrinkage|structural|none","severity":"Low|Medium|High","probable_cause":str,"repair_steps":[str],"urgency":str}"""
    fb = {"crack_found": True, "type": "hairline", "severity": "Low",
          "probable_cause": "Plastic shrinkage during curing",
          "repair_steps": ["Clean the crack", "Apply epoxy or polymer filler", "Monitor for 30 days"],
          "urgency": "Within 2-4 weeks"}
    return ask_llm(prompt, img, fb)


# Epic 3 - planning and valuation
@app.post("/api/valuation")
async def valuation(location: str = Form(...), area_sqft: float = Form(...),
                    property_type: str = Form("Residential"), age_years: int = Form(0),
                    image: Optional[UploadFile] = File(None)):
    img = await load_image(image)
    prompt = f"""You are a real estate valuer in India. Property: {property_type}, {area_sqft} sqft, {location}, {age_years} years old.
Return JSON: {{"estimated_value_inr":number,"price_per_sqft_inr":number,"range_low_inr":number,"range_high_inr":number,"factors":[str],"summary":str}}"""
    base = {"Residential": 4500, "Commercial": 7500, "Plot": 3000}.get(property_type, 4500)
    rate = base * max(0.6, 1 - 0.01 * age_years)
    val = round(rate * area_sqft)
    fb = {"estimated_value_inr": val, "price_per_sqft_inr": round(rate),
          "range_low_inr": round(val * 0.9), "range_high_inr": round(val * 1.1),
          "factors": ["Location demand", "Property age depreciation", "Property type"],
          "summary": f"Rule-based estimate for {location}."}
    return ask_llm(prompt, img, fb)


@app.post("/api/planning")
async def planning(project_type: str = Form(...), budget_inr: float = Form(...),
                   duration_months: int = Form(...), description: str = Form("")):
    prompt = f"""You are a construction project planner. Project: {project_type}, budget INR {budget_inr}, {duration_months} months. {description}
Return JSON: {{"phases":[{{"name":str,"duration_weeks":int,"budget_share_percent":int,"key_tasks":[str]}}],"risks":[str],"summary":str}}"""
    fb = {"phases": [
        {"name": "Design & Approvals", "duration_weeks": 4, "budget_share_percent": 8, "key_tasks": ["Architect drawings", "Permits"]},
        {"name": "Foundation", "duration_weeks": 6, "budget_share_percent": 22, "key_tasks": ["Excavation", "Footing", "Plinth"]},
        {"name": "Structure", "duration_weeks": 12, "budget_share_percent": 35, "key_tasks": ["Columns", "Slabs", "Brickwork"]},
        {"name": "Finishing", "duration_weeks": 10, "budget_share_percent": 30, "key_tasks": ["Plaster", "Flooring", "Paint"]},
        {"name": "Handover", "duration_weeks": 2, "budget_share_percent": 5, "key_tasks": ["Inspection", "Snag list"]}],
        "risks": ["Material price rise", "Monsoon delay", "Labour shortage"],
        "summary": "Standard 5-phase plan (fallback)."}
    return ask_llm(prompt, None, fb)


# Epic 5 - assistant and advisory
@app.get("/api/weather")
async def weather(lat: float = 22.7196, lon: float = 75.8577):
    """Weather-aware advisory (defaults to Indore). Uses free Open-Meteo, no key."""
    try:
        async with httpx.AsyncClient(timeout=8) as c:
            r = await c.get("https://api.open-meteo.com/v1/forecast", params={
                "latitude": lat, "longitude": lon, "current": "temperature_2m,wind_speed_10m,precipitation"})
        cur = r.json()["current"]
    except Exception:
        cur = {"temperature_2m": 30, "wind_speed_10m": 10, "precipitation": 0}
    t, w, p = cur["temperature_2m"], cur["wind_speed_10m"], cur["precipitation"]
    advice = []
    if p > 0.5: advice.append("Rain: postpone concreting and electrical work; cover materials.")
    if w > 30: advice.append("High wind: stop crane and scaffold work.")
    if t > 38: advice.append("Heat: give rest breaks, water, and shift work to mornings.")
    if not advice: advice.append("Conditions are good for normal site activity.")
    return {"temperature_c": t, "wind_kmh": w, "precipitation_mm": p, "advisory": advice}


@app.post("/api/assistant")
async def assistant(question: str = Form(...), image: Optional[UploadFile] = File(None)):
    img = await load_image(image)
    prompt = f"""You are a construction knowledge assistant (IS codes, materials, methods, safety). Question: {question}
Return JSON: {{"answer":str,"key_points":[str],"related_topics":[str]}}"""
    fb = {"answer": "Add GEMINI_API_KEY to enable the assistant. General tip: always follow IS 456 for RCC work.",
          "key_points": ["Check mix design", "Cure concrete 7-14 days"], "related_topics": ["IS 456", "Curing", "Formwork"]}
    return ask_llm(prompt, img, fb)
