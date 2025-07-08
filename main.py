from typing import Optional, List
from datetime import datetime

import sqlite3
from fastapi import FastAPI, HTTPException, Query

from database.database import init_db
from models.models import ReviewResponse, ReviewRequest
from config.config import Config


app = FastAPI(
    title="Reviews Sentiment Service",
    description="Сервис для анализа настроения отзывов в реальном времени",
    version="1.0.0"
)


def analyze_sentiment(text: str) -> str:
    text_lower = text.lower()
    
    # Позитивные слова и фразы
    positive_words = [
        "хорош", "отлично", "прекрасно", "замечательно", "люблю", "нравится",
        "супер", "класс", "круто", "восхитительно", "великолепно", "идеально",
        "потрясающе", "превосходно", "шикарно", "браво", "молодцы"
    ]
    
    # Негативные слова и фразы
    negative_words = [
        "плохо", "ужасно", "отвратительно", "ненавижу", "не нравится", "кошмар",
        "провал", "разочарование", "бред", "ерунда", "глупо", "тупо", "дрянь",
        "мусор", "гадость", "безобразие", "позор"
    ]
    
    # Подсчет позитивных и негативных слов
    positive_count = sum(1 for word in positive_words if word in text_lower)
    negative_count = sum(1 for word in negative_words if word in text_lower)
    
    if positive_count > negative_count:
        return "positive"
    elif negative_count > positive_count:
        return "negative"
    else:
        return "neutral"


@app.on_event("startup")
async def startup_event():
    init_db()


@app.get("/")
async def root():
    return {"message": "Reviews Sentiment Service API", "version": "1.0.0"}


@app.post("/reviews", response_model=ReviewResponse)
async def create_review(review: ReviewRequest):
    try:
        sentiment = analyze_sentiment(review.text)
        created_at = datetime.utcnow().isoformat()

        conn = sqlite3.connect(Config.DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO reviews (text, sentiment, created_at) VALUES (?, ?, ?)",
            (review.text, sentiment, created_at)
        )
        
        review_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return ReviewResponse(
            id=review_id,
            text=review.text,
            sentiment=sentiment,
            created_at=created_at
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при создании отзыва: {str(e)}")


@app.get("/reviews", response_model=List[ReviewResponse])
async def get_reviews(sentiment: Optional[str] = Query(None, description="Фильтр по настроению: positive, negative, neutral")):
    try:
        conn = sqlite3.connect(Config.DB_PATH)
        cursor = conn.cursor()
        
        if sentiment:
            cursor.execute(
                "SELECT id, text, sentiment, created_at FROM reviews WHERE sentiment = ? ORDER BY created_at DESC",
                (sentiment,)
            )
        else:
            cursor.execute(
                "SELECT id, text, sentiment, created_at FROM reviews ORDER BY created_at DESC"
            )
        
        reviews = cursor.fetchall()
        conn.close()
        
        return [
            ReviewResponse(
                id=review[0],
                text=review[1],
                sentiment=review[2],
                created_at=review[3]
            )
            for review in reviews
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при получении отзывов: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

