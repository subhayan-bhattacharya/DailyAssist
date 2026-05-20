from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from datetime import date, datetime

# --- Word Schemas ---

class WordBase(BaseModel):
    german_word: str
    meaning: Optional[str] = None
    notes: Optional[str] = None

class WordCreate(WordBase):
    pass

class WordInDB(WordBase):
    id: UUID
    enrichment_status: str
    created_at: datetime

    class Config:
        from_attributes = True

# --- Flashcard Schemas ---

class FlashcardWord(BaseModel):
    word_id: UUID = Field(..., alias='id')
    german_word: str
    meaning: Optional[str] = None
    notes: Optional[str] = None

    class Config:
        from_attributes = True
        populate_by_name = True


class FlashcardResponse(BaseModel):
    date: date
    words: List[FlashcardWord]

class FlashcardViewCreate(BaseModel):
    word_id: UUID
    confidence: int = Field(..., ge=1, le=5)

class FlashcardViewResponse(BaseModel):
    word_id: UUID
    viewed_at: datetime

# --- Example Schemas ---

class ExampleSentence(BaseModel):
    sentence_de: str
    sentence_en: str

    class Config:
        from_attributes = True

class ExampleResponse(BaseModel):
    word_id: UUID
    german_word: str
    sentences: List[ExampleSentence]


# --- Settings Schemas ---

class AppSettings(BaseModel):
    daily_word_count: Optional[int] = None

    class Config:
        from_attributes = True
