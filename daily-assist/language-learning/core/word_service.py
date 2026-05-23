import logging
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from uuid import UUID

from db.models import DailySelection, ExampleSentence, Word

logger = logging.getLogger(__name__)


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


def delete_word(db: Session, word_id: UUID):
    logger.info("Deleting word from vocabulary: word_id=%s", word_id)
    word = db.get(Word, word_id)
    if not word:
        logger.warning("Delete requested for missing word: word_id=%s", word_id)
        return None

    deleted_word = {
        "id": word.id,
        "german_word": word.german_word,
    }

    updated_selection_count = 0
    try:
        for selection in db.query(DailySelection).all():
            if word_id in selection.word_ids:
                selection.word_ids = [
                    selected_word_id
                    for selected_word_id in selection.word_ids
                    if selected_word_id != word_id
                ]
                updated_selection_count += 1

        db.delete(word)
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Failed to delete word: word_id=%s", word_id)
        raise

    logger.info(
        "Deleted word successfully: word_id=%s german_word=%s updated_daily_selections=%s",
        deleted_word["id"],
        deleted_word["german_word"],
        updated_selection_count,
    )

    return deleted_word
