from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.database import get_db_session
from core.word_service import create_word
from api import schemas

router = APIRouter()

# Dependency to get the DB session
def get_db():
    with get_db_session() as session:
        yield session

@router.post("/", response_model=schemas.WordInDB, status_code=201)
def add_new_word(word: schemas.WordCreate, db: Session = Depends(get_db)):
    """Add a new word to the database for nightly enrichment."""
    new_word = create_word(
        db=db,
        german_word=word.german_word,
        meaning=word.meaning,
        notes=word.notes
    )
    if not new_word:
        raise HTTPException(status_code=409, detail="Word already exists")
    return new_word