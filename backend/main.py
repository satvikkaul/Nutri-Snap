from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import List, Dict
import uvicorn

app = FastAPI(title="NutriSnap API")

# -----------------------
# Models
# -----------------------

class NutritionResponse(BaseModel):
    food: str
    calories: int
    protein: float
    carbs: float
    fat: float

class HistoryItem(BaseModel):
    food: str
    calories: int
    timestamp: str

# -----------------------
# Endpoints
# -----------------------

@app.post("/analyze")
async def analyze_food(file: UploadFile = File(...)):
    """
    Takes an uploaded food image, runs through ML model,
    and returns predicted food + calories.
    """
    return {"food": "pizza", "calories": 285}  # mock for now

@app.get("/nutrition", response_model=NutritionResponse)
async def get_nutrition(food: str):
    """
    Returns nutritional info for a given food.
    """
    return {"food": food, "calories": 285, "protein": 12, "carbs": 36, "fat": 10}

@app.get("/history", response_model=List[HistoryItem])
async def get_history(user_id: str):
    """
    Returns last meals logged by a user.
    """
    return [
        {"food": "pizza", "calories": 285, "timestamp": "2025-08-29T12:00:00"},
        {"food": "salad", "calories": 150, "timestamp": "2025-08-28T18:30:00"}
    ]

@app.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    """
    Upload endpoint (future: store to S3/DB).
    """
    return {"filename": file.filename, "status": "uploaded"}

# -----------------------
# Entry
# -----------------------
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
