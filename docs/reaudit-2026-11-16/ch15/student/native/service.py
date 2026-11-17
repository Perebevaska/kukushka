# uv add fastapi uvicorn scikit-learn pandas joblib
# файл service.py; запуск: uv run uvicorn service:app --port 8000
import json
from typing import Literal, Optional

import joblib
import pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel, ConfigDict, Field

model = joblib.load("models/churn/1.0/model.joblib")            # загружается один раз при старте
card = json.load(open("models/churn/1.0/card.json", encoding="utf-8"))

class Guest(BaseModel):                                          # контракт запроса
    model_config = ConfigDict(strict=True)
    city: Literal["Казань", "Пермь", "Тюмень", "Уфа"]
    fav_category: Literal["кофе", "не кофе", "еда"]
    tenure_months: int = Field(ge=1, le=120)
    app: int = Field(ge=0, le=1)
    visits_90d: int = Field(ge=0)
    days_since_last: int = Field(ge=0, le=3650)
    avg_check: Optional[float] = Field(ge=50, le=3000)          # Optional — может быть null
    delivery_share: float = Field(ge=0, le=1)
    promo_used: int = Field(ge=0)
    complaints: int = Field(ge=0)

app = FastAPI(title="Отток гостей «Зерна»")

@app.post("/predict")
def predict(guest: Guest):
    row = pd.DataFrame([guest.model_dump()])[card["features"]]
    p = float(model.predict_proba(row)[0, 1])
    return {"proba": round(p, 3), "in_campaign": p >= card["threshold"], "model_version": card["version"]}
