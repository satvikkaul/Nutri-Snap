# backend/main.py
from __future__ import annotations

import io
import time
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .db import get_db
from .models import Upload, NutritionRecord

# ---------- FastAPI ----------
app = FastAPI(title="NutriSnap API")

ALLOWED_ORIGINS = ["http://localhost:5173"]  # add your Netlify domain in prod
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MAX_IMAGE_BYTES = 5 * 1024 * 1024
ALLOWED_MIME = {"image/jpeg", "image/png", "image/webp"}

# --- simple nutrition mapping (placeholder; swap to DB table later) ---
NUTRITION_MAP = {
    "pizza":       {"calories_per_100g": 266, "protein": 11.0, "carbs": 33.0, "fat": 10.0, "default_serving_g": 150},
    "banana":      {"calories_per_100g":  89, "protein":  1.1, "carbs": 23.0, "fat":  0.3, "default_serving_g": 118},
    "spaghetti":   {"calories_per_100g": 158, "protein":  5.8, "carbs": 30.9, "fat":  0.9, "default_serving_g": 200},
    "salad":       {"calories_per_100g":  50, "protein":  2.0, "carbs":  6.0, "fat":  2.0, "default_serving_g": 180},
}

# ---------- Schemas ----------
class AnalyzeResponse(BaseModel):
    food: str
    confidence: float
    serving_g: int
    calories: int
    protein_g: float
    carbs_g: float
    fat_g: float
    inference_ms: int
    upload_id: int
    record_id: int
    timestamp: datetime

class HistoryItem(BaseModel):
    id: int
    food: str
    calories: int
    protein_g: float
    carbs_g: float
    fat_g: float
    confidence: float
    timestamp: datetime
    file_name: Optional[str] = None

class NutritionResponse(BaseModel):
    food: str
    calories_per_100g: int
    protein: float
    carbs: float
    fat: float
    default_serving_g: int

# ---------- Helpers ----------
def _validate_image(file: UploadFile) -> None:
    if file.content_type not in ALLOWED_MIME:
        raise HTTPException(status_code=415, detail="Unsupported image type")
    # size check
    # UploadFile doesn't expose size before read; enforce a cap by reading into memory.
    data = file.file.read(MAX_IMAGE_BYTES + 1)
    if len(data) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="Image too large (>5MB)")
    # reset pointer for any downstream use
    file.file = io.BytesIO(data)

def _mock_infer(file: UploadFile) -> tuple[str, float]:
    # Placeholder ML: choose a label by filename hint; otherwise default.
    name = (file.filename or "").lower()
    for k in NUTRITION_MAP:
        if k in name:
            return k, 0.85
    return "pizza", 0.80

def _calc_from_map(label: str) -> tuple[int, float, float, float, int]:
    info = NUTRITION_MAP.get(label)
    if not info:
        # fallback to pizza profile if unknown
        info = NUTRITION_MAP["pizza"]
    cal100 = int(info["calories_per_100g"])
    prot = float(info["protein"])
    carbs = float(info["carbs"])
    fat = float(info["fat"])
    serving = int(info["default_serving_g"])
    # compute for serving
    calories = round(cal100 * serving / 100)
    return calories, prot, carbs, fat, serving

# ---------- Routes ----------
@app.get("/health")
def health():
    return {"ok": True}

@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_food(
    image: UploadFile = File(...),
    user_id: Optional[str] = None,
    db: Session = Depends(get_db),
):
    # 1) validate image
    _validate_image(image)

    # 2) create Upload row
    up = Upload(user_id=None, file_name=image.filename, file_path=None)  # file_path: add persistence later
    db.add(up)
    db.flush()  # get up.id before commit

    # 3) run inference (mock now; replace with TF model later)
    t0 = time.perf_counter()
    label, conf = _mock_infer(image)
    calories, prot, carbs, fat, serving = _calc_from_map(label)
    infer_ms = int((time.perf_counter() - t0) * 1000)

    # 4) insert NutritionRecord
    rec = NutritionRecord(
        upload_id=up.id,
        food_label=label,
        confidence=round(conf, 4),
        calories=calories,
        proteins=prot,
        carbs=carbs,
        fats=fat,
    )
    db.add(rec)
    db.commit()
    db.refresh(up)
    db.refresh(rec)

    return AnalyzeResponse(
        food=label,
        confidence=float(rec.confidence),
        serving_g=serving,
        calories=rec.calories,
        protein_g=float(rec.proteins),
        carbs_g=float(rec.carbs),
        fat_g=float(rec.fats),
        inference_ms=infer_ms,
        upload_id=up.id,
        record_id=rec.id,
        timestamp=rec.created_at,
    )

@app.get("/history", response_model=list[HistoryItem])
def get_history(
    user_id: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    # No auth yet; return latest N records across uploads
    q = (
        db.query(NutritionRecord, Upload)
        .join(Upload, NutritionRecord.upload_id == Upload.id)
        .order_by(NutritionRecord.created_at.desc())
        .limit(min(limit, 200))
    )
    items: list[HistoryItem] = []
    for rec, up in q.all():
        items.append(
            HistoryItem(
                id=rec.id,
                food=rec.food_label,
                calories=rec.calories,
                protein_g=float(rec.proteins),
                carbs_g=float(rec.carbs),
                fat_g=float(rec.fats),
                confidence=float(rec.confidence),
                timestamp=rec.created_at,
                file_name=up.file_name,
            )
        )
    return items

@app.get("/nutrition", response_model=NutritionResponse)
def get_nutrition(food: str):
    info = NUTRITION_MAP.get(food.lower())
    if not info:
        raise HTTPException(status_code=404, detail="Food not found")
    return NutritionResponse(food=food.lower(), **info)
