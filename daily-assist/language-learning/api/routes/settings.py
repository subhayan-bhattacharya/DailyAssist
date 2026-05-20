from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.database import get_db_session
from core.settings_service import get_settings, update_settings
from api import schemas

router = APIRouter()

# Dependency to get the DB session
def get_db():
    with get_db_session() as session:
        yield session

@router.get("/", response_model=schemas.AppSettings)
def read_settings(db: Session = Depends(get_db)):
    """Returns all configurable app settings."""
    settings_dict = get_settings(db)
    return schemas.AppSettings(**settings_dict)


@router.patch("/", response_model=schemas.AppSettings)
def patch_settings(settings: schemas.AppSettings, db: Session = Depends(get_db)):
    """
    Updates one or more settings.
    Note: Changing daily_word_count takes effect the next day.
    """
    settings_dict = settings.model_dump(exclude_unset=True)
    if 'daily_word_count' in settings_dict:
        val = settings_dict['daily_word_count']
        if not isinstance(val, int) or val <= 0:
            raise HTTPException(status_code=422, detail="daily_word_count must be a positive integer")
            
    updated_settings = update_settings(db, settings_dict)
    return schemas.AppSettings(**updated_settings)
