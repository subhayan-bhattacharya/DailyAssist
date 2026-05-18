"""
Inserts (or updates) the default B2 German tutor prompt in the prompts table.
Run before seed_words.py and run_enrichment.py.

Usage:
    export DATABASE_URL=...
    uv run python scripts/seed_prompt.py
"""
import os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text

PROMPT_NAME = "b2_tutor_prompt"
PROMPT_TEMPLATE = (
    "You are my German tutor, your job is to help me with German words, verbs, nouns, "
    "adjectives, phrases and their meanings and grammatical structures etc. You are teaching "
    "someone who has already completed B1 so teach accordingly. Whenever I ask you to explain "
    "a word or teach me a grammatical structure always explain with examples and in those examples "
    "always use present perfect unless asked for something else. I will ask for past tense when I "
    "need it so by default try to avoid it. Remember B2 level and always present perfect unless "
    "asked otherwise. Make the sentences a bit long, lets say 10 to 15 words long and include the "
    "below grammatical structures wherever possible: Nebensätze, Relativsätze, Indirekte "
    "Fragesätze, Konjunktiv II, Vorgangspassiv Präteritum, Zustandspassiv, sich lassen, "
    "Nominalisierung, Infinitiv mit zu, reflexive and dative verbs, Partizip I & II as Adjectives, "
    "Vermutung etc. When asked about the meaning of a word, give me 10 sentences including the "
    "above grammar subjects.\n\n"
    "The word or phrase to explain is: {{word}}\n\n"
    "You MUST respond with valid JSON only, no other text. Use this exact format:\n"
    '{\"meaning\": \"English meaning of the word or phrase\", \"sentences\": '
    '[{\"sentence_de\": \"German sentence here\", \"sentence_en\": \"English translation here\"}]}\n'
    "The sentences array must contain exactly 10 items."
)


def main():
    db_url = os.environ.get("DATABASE_URL", "")
    if not db_url:
        print("ERROR: DATABASE_URL is not set.")
        sys.exit(1)
    db_url = db_url.replace("postgres://", "postgresql://", 1)
    engine = create_engine(db_url)

    with engine.connect() as conn:
        row = conn.execute(text("SELECT id FROM prompts WHERE is_default = TRUE LIMIT 1")).fetchone()
        if row:
            conn.execute(
                text("UPDATE prompts SET template = :t WHERE id = :id"),
                {"t": PROMPT_TEMPLATE, "id": row.id},
            )
            print(f"Updated existing default prompt: {row.id}")
        else:
            result = conn.execute(
                text("INSERT INTO prompts (name, template, is_default) VALUES (:n, :t, TRUE) RETURNING id"),
                {"n": PROMPT_NAME, "t": PROMPT_TEMPLATE},
            )
            print(f"Inserted new default prompt: {result.fetchone().id}")
        conn.commit()


if __name__ == "__main__":
    main()
