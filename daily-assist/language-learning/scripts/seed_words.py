"""
Inserts the initial German words into the words table.
Skips any word that already exists (ON CONFLICT DO NOTHING).

Usage:
    export DATABASE_URL=...
    uv run python scripts/seed_words.py
"""
import os, sys, uuid
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text

WORDS = [
    {"german_word": "der Hinterhalt",               "meaning": "ambush",                   "notes": "noun"},
    {"german_word": "Bist du ausgeruht?",            "meaning": "Are you well rested?",     "notes": "common phrase"},
    {"german_word": "sich ausruhen",                 "meaning": "to rest",                  "notes": "reflexive verb"},
    {"german_word": "hinterhältig",                  "meaning": "malicious",                "notes": "adjective, e.g. hinterhältige Fragen"},
    {"german_word": "schmeicheln",                   "meaning": "to flatter",               "notes": "verb, takes dative"},
    {"german_word": "Ich fühle mich geschmeichelt",  "meaning": "I feel flattered",         "notes": "common expression"},
    {"german_word": "Ich muss ihm schmeicheln",      "meaning": "I must flatter him",       "notes": "dative usage example"},
    {"german_word": "außergewöhnlich",               "meaning": "exceptional/extraordinary","notes": "adjective"},
    {"german_word": "die Plauderei",                 "meaning": "the chat",                 "notes": "noun"},
    {"german_word": "das Geplauder",                 "meaning": "small talk",               "notes": "noun"},
]


def main():
    db_url = os.environ.get("DATABASE_URL", "")
    if not db_url:
        print("ERROR: DATABASE_URL is not set.")
        sys.exit(1)
    db_url = db_url.replace("postgres://", "postgresql://", 1)
    engine = create_engine(db_url)

    inserted = 0
    skipped = 0
    with engine.connect() as conn:
        for w in WORDS:
            result = conn.execute(
                text("""
                    INSERT INTO words (id, german_word, meaning, notes, enrichment_status, enrichment_attempts)
                    VALUES (:id, :german_word, :meaning, :notes, 'pending', 0)
                    ON CONFLICT (german_word) DO NOTHING
                """),
                {"id": uuid.uuid4(), **w},
            )
            if result.rowcount:
                print(f"  Inserted: {w['german_word']}")
                inserted += 1
            else:
                print(f"  Skipped (exists): {w['german_word']}")
                skipped += 1
        conn.commit()

    print(f"\nDone — inserted: {inserted}, skipped: {skipped}")


if __name__ == "__main__":
    main()
