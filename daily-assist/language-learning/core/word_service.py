from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func

from db.models import ExampleSentence, Word

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


def search_words(db: Session, query: str, limit: int = 20):
    normalized_query = query.strip()
    if not normalized_query:
        return []

    rows = (
        db.query(
            Word,
            func.count(ExampleSentence.id).label("example_count"),
        )
        .outerjoin(ExampleSentence, ExampleSentence.word_id == Word.id)
        .filter(Word.german_word.ilike(f"%{normalized_query}%"))
        .group_by(Word.id)
        .order_by(Word.german_word.asc())
        .limit(limit)
        .all()
    )

    return [
        {
            "id": word.id,
            "german_word": word.german_word,
            "meaning": word.meaning,
            "notes": word.notes,
            "enrichment_status": word.enrichment_status,
            "created_at": word.created_at,
            "example_count": example_count,
            "has_examples": example_count > 0,
        }
        for word, example_count in rows
    ]
