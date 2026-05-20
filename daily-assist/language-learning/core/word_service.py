from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from db.models import Word

def create_word(db: Session, german_word: str, meaning: str = None, notes: str = None):
    try:
        new_word = Word(
            german_word=german_word,
            meaning=meaning,
            notes=notes,
            enrichment_status='pending'
        )
        db.add(new_word)
        db.commit()
        db.refresh(new_word)
        return new_word
    except IntegrityError:
        db.rollback()
        return None # Indicate duplicate