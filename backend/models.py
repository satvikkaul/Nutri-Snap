# backend/models.py
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Integer, String, Text, Float,
    ForeignKey, Numeric,
    TIMESTAMP, func,
    Column 
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), unique=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=func.now())

    uploads: Mapped[list["Upload"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class Upload(Base):
    __tablename__ = "uploads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE")
    )
    file_name: Mapped[Optional[str]] = mapped_column(String(255))
    file_path: Mapped[Optional[str]] = mapped_column(Text)
    uploaded_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=func.now())

    user: Mapped[Optional["User"]] = relationship(back_populates="uploads")
    nutrition: Mapped[list["NutritionRecord"]] = relationship(
        back_populates="upload", cascade="all, delete-orphan"
    )


class NutritionRecord(Base):
    __tablename__ = "nutrition_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    upload_id: Mapped[int] = mapped_column(
        ForeignKey("uploads.id", ondelete="CASCADE")
    )
    food_label: Mapped[str] = mapped_column(String(100))
    confidence: Mapped[float] = mapped_column(Numeric(5, 4))  # 0.0000–9.9999
    calories: Mapped[int] = mapped_column(Integer)
    proteins: Mapped[float] = mapped_column(Numeric(6, 2))
    carbs: Mapped[float] = mapped_column(Numeric(6, 2))
    fats: Mapped[float] = mapped_column(Numeric(6, 2))
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=func.now())

    upload: Mapped["Upload"] = relationship(back_populates="nutrition")


class ImageNetMap(Base):
    __tablename__ = "imagenet_map"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    imagenet_label: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    food_key: Mapped[str] = mapped_column(String(100), index=True)


class NutritionInfo(Base):
    __tablename__ = "nutrition_info"

    id = Column(Integer, primary_key=True, index=True)
    food_key = Column(String(100), unique=True, index=True, nullable=False)
    calories_per_100g = Column(Integer, nullable=False)
    protein = Column(Float, nullable=False)
    carbs = Column(Float, nullable=False)
    fat = Column(Float, nullable=False)
    default_serving_g = Column(Integer, nullable=False)