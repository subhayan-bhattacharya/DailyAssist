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

DEFAULT_FILE_PATH = os.path.expanduser("~/Downloads/Deutsch tough Words.txt")

def load_words_from_file(file_path):
    """
    Parses a file and extracts ONLY the German word/phrase
    (the part before the first colon on each relevant line).
    """
    words = []
    if not os.path.exists(file_path):
        print(f"ERROR: File not found at {file_path}")
        return []

    print(f"Reading words from: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if ":" in line:
                # Extract only the German word (before the colon)
                word = line.split(":", 1)[0].strip()
                if word and word.lower() != "new list":
                    words.append(word)
    
    return words


def main():
    db_url = os.environ.get("DATABASE_URL", "")
    if not db_url:
        print("ERROR: DATABASE_URL is not set.")
        sys.exit(1)
    
    words_to_seed = load_words_from_file(DEFAULT_FILE_PATH)
    if not words_to_seed:
        print("No words found to seed.")
        sys.exit(0)

    db_url = db_url.replace("postgres://", "postgresql://", 1)
    engine = create_engine(db_url)

    inserted = 0
    skipped = 0
    with engine.connect() as conn:
        for word in words_to_seed:
            result = conn.execute(
                text("""
                    INSERT INTO words (id, german_word, enrichment_status, enrichment_attempts)
                    VALUES (:id, :german_word, 'pending', 0)
                    ON CONFLICT (german_word) DO NOTHING
                """),
                {"id": uuid.uuid4(), "german_word": word},
            )
            if result.rowcount:
                print(f"  Inserted: {word}")
                inserted += 1
            else:
                print(f"  Skipped (exists): {word}")
                skipped += 1
        conn.commit()

    print(f"\nDone — inserted: {inserted}, skipped: {skipped}")


if __name__ == "__main__":
    main()
