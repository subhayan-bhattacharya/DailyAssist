import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from uuid import UUID

from core.database import get_db_session
from core.word_service import create_word, delete_word, search_words
from api import schemas

router = APIRouter()
logger = logging.getLogger(__name__)

# Dependency to get the DB session
def get_db():
    with get_db_session() as session:
        yield session


@router.get("/search", response_model=schemas.WordSearchResponse)
def search_word_list(
    q: str = Query(..., min_length=1, description="Full or partial German word/phrase to search for"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Search existing vocabulary by German word substring."""
    results = search_words(db=db, query=q, limit=limit)
    return {
        "query": q,
        "count": len(results),
        "words": results,
    }

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


@router.delete("/{word_id}", response_model=schemas.WordDeleteResponse)
def delete_existing_word(word_id: UUID, db: Session = Depends(get_db)):
    """Delete a word and its dependent flashcard data."""
    logger.info("Received delete word request: word_id=%s", word_id)
    deleted_word = delete_word(db=db, word_id=word_id)
    if not deleted_word:
        logger.warning("Delete word request failed because word was not found: word_id=%s", word_id)
        raise HTTPException(status_code=404, detail="Word not found")

    logger.info("Delete word request completed: word_id=%s", word_id)
    return {
        **deleted_word,
        "message": "Word successfully deleted",
    }
