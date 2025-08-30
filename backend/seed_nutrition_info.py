# backend/seed_nutrition_info.py

from __future__ import annotations
from sqlalchemy.orm import Session
from .db import SessionLocal, engine, Base
from .models import NutritionInfo

# Starter nutrition facts (can expand later)
SEED = [
    {
        "food_key": "pizza",
        "calories_per_100g": 266,
        "protein": 11.0,
        "carbs": 33.0,
        "fat": 10.0,
        "default_serving_g": 150,
    },
    {
        "food_key": "banana",
        "calories_per_100g": 89,
        "protein": 1.1,
        "carbs": 23.0,
        "fat": 0.3,
        "default_serving_g": 118,
    },
    {
        "food_key": "spaghetti",
        "calories_per_100g": 158,
        "protein": 5.8,
        "carbs": 30.9,
        "fat": 0.9,
        "default_serving_g": 200,
    },
    {
        "food_key": "salad",
        "calories_per_100g": 50,
        "protein": 2.0,
        "carbs": 6.0,
        "fat": 2.0,
        "default_serving_g": 180,
    },
]

def run():
    Base.metadata.create_all(bind=engine)  # ensures table exists
    db: Session = SessionLocal()
    try:
        for item in SEED:
            existing = db.query(NutritionInfo).filter_by(food_key=item["food_key"]).first()
            if existing:
                # update values if they changed
                for k, v in item.items():
                    setattr(existing, k, v)
            else:
                db.add(NutritionInfo(**item))
        db.commit()
        print(f"Seeded {len(SEED)} nutrition records.")
    finally:
        db.close()

if __name__ == "__main__":
    run()
