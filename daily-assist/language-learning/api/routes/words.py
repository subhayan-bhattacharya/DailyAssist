from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from core.database import get_db_session
from core.word_service import create_word, search_words
from api import schemas

router = APIRouter()

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
