from __future__ import annotations
from sqlalchemy.orm import Session
from .db import SessionLocal, engine
from .models import Base, ImageNetMap

# Starter mapping (expand later as needed)
SEED = {
    "pizza": "pizza",
    "hotdog": "hot_dog",
    "hamburger": "burger",
    "cheeseburger": "burger",
    "bagel": "bagel",
    "pretzel": "bagel",
    "french_loaf": "bread",
    "burrito": "pasta",
    "carbonara": "pasta",
    "spaghetti_squash": "pasta",
    "ice_cream": "ice_cream",
    "ice_lolly": "ice_cream",
    "orange": "orange",
    "lemon": "lemon",
    "banana": "banana",
    "strawberry": "strawberry",
    "pineapple": "pineapple",
    "broccoli": "broccoli",
    "cauliflower": "cauliflower",
    "cucumber": "cucumber",
    "carrot": "carrot",
    "mushroom": "mushroom",
    "eggplant": "eggplant",
}

def run():
    # Ensure tables exist (safety net; use Alembic for prod migrations)
    Base.metadata.create_all(bind=engine)

    db: Session = SessionLocal()
    try:
        for imagenet_label, food_key in SEED.items():
            imagenet_label = imagenet_label.lower().strip().replace(" ", "_")
            food_key = food_key.lower().strip().replace(" ", "_")

            # Upsert style: check if exists
            existing = db.query(ImageNetMap).filter_by(imagenet_label=imagenet_label).first()
            if existing:
                existing.food_key = food_key
            else:
                db.add(ImageNetMap(imagenet_label=imagenet_label, food_key=food_key))
        db.commit()
        print(f"Seeded {len(SEED)} mappings into imagenet_map.")
    finally:
        db.close()

if __name__ == "__main__":
    run()
