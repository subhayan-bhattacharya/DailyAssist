from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime

from core.database import get_db_session
from core.flashcard_service import get_daily_flashcards
from db.models import FlashcardView
from api import schemas

router = APIRouter()

# Dependency to get the DB session
def get_db():
    with get_db_session() as session:
        yield session

@router.get("/", response_model=schemas.FlashcardResponse)
def get_flashcards(db: Session = Depends(get_db)):
    """Get the 10 words for today's review session."""
    return get_daily_flashcards(db)

@router.post("/view", response_model=schemas.FlashcardViewResponse, status_code=201)
def record_flashcard_view(view_data: schemas.FlashcardViewCreate, db: Session = Depends(get_db)):
    """Record that a user viewed a flashcard and their confidence score."""
    new_view = FlashcardView(
        word_id=view_data.word_id,
        confidence=view_data.confidence,
        viewed_at=datetime.utcnow()
    )
    db.add(new_view)
    db.commit()
    db.refresh(new_view)
    
    return {
        "word_id": new_view.word_id,
        "viewed_at": new_view.viewed_at
    }
