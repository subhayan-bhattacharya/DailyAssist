from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from core.database import get_db_session
from core.example_service import get_word_examples
from api import schemas

router = APIRouter()

# Dependency to get the DB session
def get_db():
    with get_db_session() as session:
        yield session

@router.get("/{word_id}/examples", response_model=schemas.ExampleResponse)
def get_examples_for_word(word_id: UUID, db: Session = Depends(get_db)):
    """On-demand fetch of example sentences for a given word."""
    result = get_word_examples(db, word_id=word_id)
    if not result:
        raise HTTPException(status_code=404, detail="Word not found")
    return result