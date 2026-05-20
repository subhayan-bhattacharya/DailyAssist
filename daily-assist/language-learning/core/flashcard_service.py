from datetime import date
from sqlalchemy import text
from sqlalchemy.orm import Session
from db.models import Word, DailySelection, AppSetting

def get_daily_flashcards(db: Session):
    # 1. Get daily word count from settings
    daily_word_count_setting = db.query(AppSetting).filter(AppSetting.key == 'daily_word_count').first()
    daily_word_count = int(daily_word_count_setting.value) if daily_word_count_setting else 10

    # 2. Check for today's selection
    today = date.today()
    todays_selection = db.query(DailySelection).filter(DailySelection.selected_on == today).first()

    if todays_selection:
        # 4. If found, fetch words for the stored IDs
        word_ids = todays_selection.word_ids
        words = db.query(Word).filter(Word.id.in_(word_ids)).all()
        return {"date": today, "words": words}

    # 3. If missing, run selection query
    selection_query = text("""
        WITH latest_view AS (
            SELECT DISTINCT ON (word_id)
                word_id,
                viewed_at,
                confidence
            FROM flashcard_views
            ORDER BY word_id, viewed_at DESC
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
                END AS next_review_at
            FROM words w
            LEFT JOIN latest_view lv ON lv.word_id = w.id
            WHERE w.enrichment_status = 'completed'
        )
        SELECT id FROM word_schedule
        ORDER BY
            next_review_at ASC NULLS FIRST,
            viewed_at ASC NULLS FIRST
        LIMIT :daily_word_count;
    """)

    result = db.execute(selection_query, {"daily_word_count": daily_word_count})
    selected_word_ids = [row[0] for row in result]

    # Cache the new selection
    new_selection = DailySelection(
        selected_on=today,
        word_ids=selected_word_ids
    )
    db.add(new_selection)
    db.commit()

    words = db.query(Word).filter(Word.id.in_(selected_word_ids)).all()
    return {"date": today, "words": words}