from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api import schemas
from core.database import get_db_session
from core.prompt_service import create_default_prompt_version, get_default_prompt

router = APIRouter()


def get_db():
    with get_db_session() as session:
        yield session


@router.get("/default", response_model=schemas.PromptInDB)
def read_default_prompt(db: Session = Depends(get_db)):
    """Returns the prompt currently used by enrichment jobs."""
    prompt = get_default_prompt(db)
    if not prompt:
        raise HTTPException(status_code=404, detail="No default prompt configured")
    return prompt


@router.post("/default", response_model=schemas.PromptInDB, status_code=201)
def create_new_default_prompt(prompt: schemas.PromptCreate, db: Session = Depends(get_db)):
    """
    Creates a new default prompt version.
    Existing prompts are retained for historical enrichment records.
    """
    new_prompt = create_default_prompt_version(
        db=db,
        name=prompt.name,
        template=prompt.template,
    )
    if not new_prompt:
        raise HTTPException(status_code=409, detail="Could not set default prompt")
    return new_prompt
