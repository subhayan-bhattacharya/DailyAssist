"""
Fetches pending words from the DB, calls OpenAI to generate example sentences,
and saves the results back. Run after seed_words.py.

Usage:
    export DATABASE_URL=...
    export OPENAI_API_KEY=...
    export OPENAI_MODEL=gpt-4o-mini   # optional, defaults to gpt-4o-mini
    uv run python scripts/run_enrichment.py
"""
import json, os, sys, uuid
from datetime import datetime, timezone
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from openai import OpenAI
from sqlalchemy import create_engine, text

BATCH_LIMIT = 50


def get_engine():
    db_url = os.environ.get("DATABASE_URL", "").replace("postgres://", "postgresql://", 1)
    if not db_url:
        print("ERROR: DATABASE_URL is not set.")
        sys.exit(1)
    return create_engine(db_url)


def run_enrichment():
    engine = get_engine()
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    ok, fail = 0, 0

    with engine.connect() as conn:
        prompt_row = conn.execute(
            text("SELECT id, template FROM prompts WHERE is_default = TRUE LIMIT 1")
        ).fetchone()
        if not prompt_row:
            print("ERROR: No default prompt found. Run seed_prompt.py first.")
            sys.exit(1)

        words = conn.execute(
            text("""
                SELECT id, german_word, meaning FROM words
                WHERE enrichment_status IN ('pending', 'failed')
                  AND enrichment_attempts < 3
                ORDER BY created_at ASC
                LIMIT :limit
            """),
            {"limit": BATCH_LIMIT},
        ).fetchall()

    print(f"Found {len(words)} word(s) to enrich.\n")

    for word in words:
        print(f"  Enriching: {word.german_word} ...", end=" ", flush=True)
        rendered = prompt_row.template.replace("{{word}}", word.german_word)
        job_id = uuid.uuid4()
        now = datetime.now(timezone.utc)

        with engine.connect() as conn:
            conn.execute(
                text("UPDATE words SET enrichment_status='processing', enrichment_attempts=enrichment_attempts+1 WHERE id=:id"),
                {"id": word.id},
            )
            conn.execute(
                text("INSERT INTO enrichment_jobs (id, word_id, prompt_id, status, started_at) VALUES (:id, :wid, :pid, 'processing', :now)"),
                {"id": job_id, "wid": word.id, "pid": prompt_row.id, "now": now},
            )
            conn.commit()

        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": rendered}],
                response_format={"type": "json_object"},
                temperature=0.7,
                max_tokens=2000,
            )
            data = json.loads(response.choices[0].message.content)
            sentences = data.get("sentences", [])
            meaning = data.get("meaning")
            if len(sentences) != 10:
                raise ValueError(f"Expected 10 sentences, got {len(sentences)}")

            with engine.connect() as conn:
                for s in sentences:
                    conn.execute(
                        text("INSERT INTO example_sentences (id, word_id, sentence_de, sentence_en, source, prompt_id) VALUES (:id, :wid, :de, :en, 'gpt', :pid)"),
                        {"id": uuid.uuid4(), "wid": word.id, "de": s["sentence_de"], "en": s["sentence_en"], "pid": prompt_row.id},
                    )
                updates = {"id": word.id}
                meaning_sql = ", meaning = :meaning" if (meaning and not word.meaning) else ""
                if meaning and not word.meaning:
                    updates["meaning"] = meaning
                conn.execute(
                    text(f"UPDATE words SET enrichment_status='completed'{meaning_sql} WHERE id=:id"),
                    updates,
                )
                conn.execute(
                    text("UPDATE enrichment_jobs SET status='completed', completed_at=:now, raw_response=:raw WHERE id=:id"),
                    {"now": datetime.now(timezone.utc), "raw": response.choices[0].message.content, "id": job_id},
                )
                conn.commit()
            print("done")
            ok += 1

        except Exception as e:
            with engine.connect() as conn:
                conn.execute(
                    text("UPDATE words SET enrichment_status='failed', last_error=:e WHERE id=:id"),
                    {"e": str(e), "id": word.id},
                )
                conn.execute(
                    text("UPDATE enrichment_jobs SET status='failed', error_message=:e WHERE id=:id"),
                    {"e": str(e), "id": job_id},
                )
                conn.commit()
            print(f"FAILED: {e}")
            fail += 1

    print(f"\nCompleted: {ok}  Failed: {fail}")


if __name__ == "__main__":
    run_enrichment()
