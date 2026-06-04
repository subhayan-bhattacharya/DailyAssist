from datetime import date
import logging

from sqlalchemy import text
from sqlalchemy.orm import Session
from db.models import Word, DailySelection, AppSetting

logger = logging.getLogger(__name__)


def _get_daily_word_count(db: Session) -> int:
    daily_word_count_setting = db.query(AppSetting).filter(AppSetting.key == 'daily_word_count').first()
    daily_word_count = int(daily_word_count_setting.value) if daily_word_count_setting else 10
    logger.info("Loaded daily flashcard word count: %s", daily_word_count)
    return daily_word_count


def _select_flashcard_word_ids(db: Session, limit: int, target_date: date, excluded_word_ids=None):
    excluded_word_ids = set(excluded_word_ids or [])
    if limit <= 0:
        logger.info("Skipping flashcard selection because requested limit is %s", limit)
        return []

    selection_query = text("""
        WITH latest_view AS (
            SELECT DISTINCT ON (word_id)
                word_id,
                viewed_at,
                confidence
            FROM flashcard_views
            ORDER BY word_id, viewed_at DESC
        ),
        past_selections AS (
            SELECT DISTINCT unnest(word_ids) as word_id
            FROM daily_selections
            WHERE selected_on < :target_date
        ),
        word_schedule AS (
            SELECT
                w.id,
                lv.viewed_at,
                lv.confidence,
                CASE lv.confidence
                    WHEN 1 THEN lv.viewed_at + INTERVAL '1 day'
                    WHEN 2 THEN lv.viewed_at + INTERVAL '2 days'
                    WHEN 3 THEN lv.viewed_at + INTERVAL '4 days'
                    WHEN 4 THEN lv.viewed_at + INTERVAL '7 days'
                    WHEN 5 THEN lv.viewed_at + INTERVAL '14 days'
                    ELSE NULL
                END AS next_review_at,
                CASE
                    WHEN ps.word_id IS NOT NULL AND lv.confidence IS NULL THEN 1
                    ELSE 2
                END AS priority
            FROM words w
            LEFT JOIN latest_view lv ON lv.word_id = w.id
            LEFT JOIN past_selections ps ON ps.word_id = w.id
            WHERE w.enrichment_status = 'completed'
        )
        SELECT id FROM word_schedule
        ORDER BY
            priority ASC,
            next_review_at ASC NULLS FIRST,
            viewed_at ASC NULLS FIRST
        LIMIT :candidate_limit;
    """)

    candidate_limit = limit + len(excluded_word_ids)
    logger.info(
        "Selecting flashcard word IDs: limit=%s excluded_count=%s candidate_limit=%s target_date=%s",
        limit,
        len(excluded_word_ids),
        candidate_limit,
        target_date,
    )
    result = db.execute(selection_query, {"candidate_limit": candidate_limit, "target_date": target_date})

    selected_word_ids = []
    for row in result:
        word_id = row[0]
        if word_id in excluded_word_ids:
            continue
        selected_word_ids.append(word_id)
        if len(selected_word_ids) == limit:
            break

    logger.info("Selected %s flashcard word ID(s)", len(selected_word_ids))
    return selected_word_ids


def _get_words_in_selection_order(db: Session, word_ids):
    if not word_ids:
        logger.info("No flashcard word IDs supplied for ordered lookup")
        return []

    words = db.query(Word).filter(Word.id.in_(word_ids)).all()
    words_by_id = {word.id: word for word in words}
    missing_word_ids = [word_id for word_id in word_ids if word_id not in words_by_id]
    if missing_word_ids:
        logger.warning(
            "Daily selection contains %s stale/deleted word ID(s): %s",
            len(missing_word_ids),
            [str(word_id) for word_id in missing_word_ids],
        )

    return [words_by_id[word_id] for word_id in word_ids if word_id in words_by_id]


def get_daily_flashcards(db: Session):
    # 1. Get daily word count from settings
    daily_word_count = _get_daily_word_count(db)

    # 2. Check for today's selection
    today = date.today()
    todays_selection = db.query(DailySelection).filter(DailySelection.selected_on == today).first()

    if todays_selection:
        logger.info(
            "Found cached daily flashcard selection for %s with %s word ID(s)",
            today,
            len(todays_selection.word_ids),
        )
        # 4. If found, fetch words for the stored IDs and refill stale/deleted entries.
        words = _get_words_in_selection_order(db, todays_selection.word_ids)
        word_ids = [word.id for word in words]
        missing_count = daily_word_count - len(word_ids)
        if missing_count > 0:
            logger.info(
                "Refilling cached daily selection for %s: current_count=%s target_count=%s missing_count=%s",
                today,
                len(word_ids),
                daily_word_count,
                missing_count,
            )
            replacement_word_ids = _select_flashcard_word_ids(
                db,
                limit=missing_count,
                target_date=today,
                excluded_word_ids=word_ids,
            )
            word_ids = word_ids + replacement_word_ids
            todays_selection.word_ids = word_ids
            db.commit()
            logger.info(
                "Updated cached daily selection for %s with %s replacement word ID(s); final_count=%s",
                today,
                len(replacement_word_ids),
                len(word_ids),
            )
            words = _get_words_in_selection_order(db, word_ids)

        logger.info("Returning %s flashcard word(s) for cached selection on %s", len(words), today)
        return {"date": today, "words": words}

    # 3. If missing, run selection query
    logger.info("No cached daily flashcard selection found for %s; creating a new selection", today)
    selected_word_ids = _select_flashcard_word_ids(db, limit=daily_word_count, target_date=today)

    # Cache the new selection
    new_selection = DailySelection(
        selected_on=today,
        word_ids=selected_word_ids
    )
    db.add(new_selection)
    db.commit()
    logger.info(
        "Created cached daily flashcard selection for %s with %s word ID(s)",
        today,
        len(selected_word_ids),
    )

    words = _get_words_in_selection_order(db, selected_word_ids)
    logger.info("Returning %s flashcard word(s) for new selection on %s", len(words), today)
    return {"date": today, "words": words}
