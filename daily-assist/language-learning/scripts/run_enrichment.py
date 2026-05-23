"""
Fetches pending words from the DB, calls OpenAI to generate example sentences,
and saves the results back. Run after seed_words.py.

Usage:
    export DATABASE_URL=...
    export OPENAI_API_KEY=...
    export OPENAI_MODEL=gpt-4o-mini   # optional, defaults to gpt-4o-mini
    export ENRICHMENT_BATCH_LIMIT=15  # optional, defaults to 15
    uv run python scripts/run_enrichment.py
"""

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.enrichment_service import run_enrichment


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    result = run_enrichment()
    print(
        "Completed enrichment run: "
        f"found={result['found']} "
        f"completed={result['completed']} "
        f"failed={result['failed']}"
    )


if __name__ == "__main__":
    main()
