# backend/main.py
from __future__ import annotations

import io, os, time
from datetime import datetime
from typing import Optional

import numpy as np
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from functools import lru_cache

from .db import get_db, SessionLocal
from .models import Upload, NutritionRecord, ImageNetMap, NutritionInfo

# ---------- FastAPI ----------
app = FastAPI(title="NutriSnap API")

# TF globals (lazy-loaded)
TF_MODEL = None
TF_DECODE = None
IMG_SIZE = 224

ALLOWED_ORIGINS = ["http://localhost:5173"]  # add your deployed UI origin later
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MAX_IMAGE_BYTES = 5 * 1024 * 1024
ALLOWED_MIME = {"image/jpeg", "image/png", "image/webp"}

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
    data = file.file.read(MAX_IMAGE_BYTES + 1)
    if len(data) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="Image too large (>5MB)")
    file.file = io.BytesIO(data)

def _load_imagenet_model_if_needed():
    """Lazy-load MobileNetV2(pretrained). First call may download weights."""
    global TF_MODEL, TF_DECODE
    if TF_MODEL is not None:
        return
    try:
        import tensorflow as tf  # type: ignore
        from tensorflow.keras.applications import mobilenet_v2  # type: ignore
        TF_MODEL = mobilenet_v2.MobileNetV2(weights="imagenet", include_top=True)
        TF_DECODE = mobilenet_v2.decode_predictions
        TF_MODEL._ns_preprocess = mobilenet_v2.preprocess_input  # type: ignore[attr-defined]
    except Exception:
        TF_MODEL, TF_DECODE = None, None

def _tf_preprocess_image_bytes(image_bytes: bytes) -> np.ndarray:
    import tensorflow as tf  # type: ignore
    img = tf.io.decode_image(image_bytes, channels=3, expand_animations=False)
    img = tf.image.resize(img, [IMG_SIZE, IMG_SIZE])
    x = tf.cast(img, tf.float32).numpy()
    x = TF_MODEL._ns_preprocess(x)  # type: ignore[attr-defined]
    return x[None, ...]

@lru_cache(maxsize=1)
def _label_map_snapshot(db_hash: int = 0) -> dict[str, str]:
    """Load imagenet→food mapping from DB and cache in memory."""
    d: dict[str, str] = {}
    s = SessionLocal()
    try:
        for row in s.query(ImageNetMap).all():
            d[row.imagenet_label] = row.food_key
    finally:
        s.close()
    return d

def _map_imagenet_label(lbl: str) -> str | None:
    key = lbl.replace(" ", "_").lower()
    return _label_map_snapshot().get(key)

def _infer_label(image: UploadFile) -> tuple[str, float]:
    """Try ImageNet MobileNetV2; if unavailable or unmapped, fall back to filename heuristic."""
    image.file.seek(0)
    data = image.file.read()
    image.file.seek(0)

    _load_imagenet_model_if_needed()
    if TF_MODEL is not None and TF_DECODE is not None:
        try:
            x = _tf_preprocess_image_bytes(data)
            probs = TF_MODEL.predict(x, verbose=0)
            decoded = TF_DECODE(probs, top=5)[0]
            for (_, class_name, score) in decoded:
                mapped = _map_imagenet_label(class_name)
                if mapped:
                    return mapped, float(score)
            _, class_name, score = decoded[0]
            return class_name.replace(" ", "_").lower(), float(score)
        except Exception:
            pass

    # fallback: filename heuristic
    name = (image.filename or "").lower()
    for raw_label, mapped in _label_map_snapshot().items():
        if raw_label in name:
            return mapped, 0.85
    return "pizza", 0.80

def _calc_from_db(label: str, db: Session) -> tuple[int, float, float, float, int]:
    info = db.query(NutritionInfo).filter(NutritionInfo.food_key == label).first()
    if not info:
        info = db.query(NutritionInfo).filter(NutritionInfo.food_key == "pizza").first()
    cal100 = int(info.calories_per_100g) # type: ignore
    prot = float(info.protein) # type: ignore 
    carbs = float(info.carbs) # type: ignore 
    fat = float(info.fat) # type: ignore
    serving = int(info.default_serving_g) # type: ignore
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
    _validate_image(image)

    up = Upload(user_id=None, file_name=image.filename, file_path=None)
    db.add(up)
    db.flush()

    t0 = time.perf_counter()
    label, conf = _infer_label(image)
    calories, prot, carbs, fat, serving = _calc_from_db(label, db)
    infer_ms = int((time.perf_counter() - t0) * 1000)

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
def get_nutrition(food: str, db: Session = Depends(get_db)):
    info = db.query(NutritionInfo).filter(NutritionInfo.food_key == food.lower()).first()
    if not info:
        raise HTTPException(status_code=404, detail="Food not found")
    return NutritionResponse( # type: ignore
        food=info.food_key,# type: ignore
        calories_per_100g=info.calories_per_100g,# type: ignore
        protein=info.protein,# type: ignore
        carbs=info.carbs,# type: ignore
        fat=info.fat, # type: ignore
        default_serving_g=info.default_serving_g,# type: ignore
    )
