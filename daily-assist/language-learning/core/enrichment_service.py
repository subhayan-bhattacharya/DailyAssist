"""Shared enrichment job logic for local scripts and scheduled Lambda."""

import base64
import json
import logging
import os
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from openai import OpenAI
from sqlalchemy import create_engine, select, update
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from db.models import EnrichmentJob, ExampleSentence, Prompt, Word

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

DEFAULT_BATCH_LIMIT = 15
DEFAULT_OPENAI_MODEL = "gpt-4o-mini"


@dataclass(frozen=True)
class EnrichmentConfig:
    database_url: str
    openai_api_key: str
    openai_model: str = DEFAULT_OPENAI_MODEL
    batch_limit: int = DEFAULT_BATCH_LIMIT


@dataclass(frozen=True)
class PromptSnapshot:
    id: uuid.UUID
    template: str


@dataclass(frozen=True)
class CandidateWord:
    id: uuid.UUID
    german_word: str
    meaning: str | None


@dataclass(frozen=True)
class ClaimedWord:
    id: uuid.UUID
    german_word: str
    meaning: str | None
    job_id: uuid.UUID


def _normalize_database_url(database_url: str) -> str:
    return database_url.replace("postgres://", "postgresql://", 1)


def _get_secret_value(secret_id: str) -> str:
    import boto3

    client = boto3.client("secretsmanager")
    response = client.get_secret_value(SecretId=secret_id)
    if "SecretString" in response:
        return response["SecretString"]
    return base64.b64decode(response["SecretBinary"]).decode("utf-8")


def _get_config_value(name: str, secret_env_name: str) -> str | None:
    direct_value = os.environ.get(name)
    if direct_value:
        return direct_value

    secret_id = os.environ.get(secret_env_name)
    if secret_id:
        return _get_secret_value(secret_id)

    return None


def get_enrichment_config_from_env() -> EnrichmentConfig:
    database_url = _get_config_value("DATABASE_URL", "DATABASE_URL_SECRET_ARN")
    if not database_url:
        raise ValueError(
            "DATABASE_URL or DATABASE_URL_SECRET_ARN environment variable is required"
        )

    openai_api_key = _get_config_value("OPENAI_API_KEY", "OPENAI_API_KEY_SECRET_ARN")
    if not openai_api_key:
        raise ValueError(
            "OPENAI_API_KEY or OPENAI_API_KEY_SECRET_ARN environment variable is required"
        )

    batch_limit = int(os.environ.get("ENRICHMENT_BATCH_LIMIT", DEFAULT_BATCH_LIMIT))
    if batch_limit < 1:
        raise ValueError("ENRICHMENT_BATCH_LIMIT must be greater than zero")

    return EnrichmentConfig(
        database_url=database_url,
        openai_api_key=openai_api_key,
        openai_model=os.environ.get("OPENAI_MODEL", DEFAULT_OPENAI_MODEL),
        batch_limit=batch_limit,
    )


def get_enrichment_config(
    batch_limit: int | None = None,
    openai_model: str | None = None,
) -> EnrichmentConfig:
    config = get_enrichment_config_from_env()
    if batch_limit is not None and batch_limit < 1:
        raise ValueError("batch_limit must be greater than zero")

    return EnrichmentConfig(
        database_url=config.database_url,
        openai_api_key=config.openai_api_key,
        openai_model=openai_model or config.openai_model,
        batch_limit=batch_limit or config.batch_limit,
    )


def create_enrichment_engine(database_url: str) -> Engine:
    return create_engine(_normalize_database_url(database_url), poolclass=NullPool)


def create_enrichment_session_maker(database_url: str):
    engine = create_enrichment_engine(database_url)
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _get_prompt_and_candidates(
    SessionLocal, batch_limit: int
) -> tuple[PromptSnapshot, list[CandidateWord]]:
    with SessionLocal() as session:
        prompt = session.execute(
            select(Prompt).where(Prompt.is_default.is_(True)).limit(1)
        ).scalar_one_or_none()
        if not prompt:
            raise ValueError("No default prompt found. Run seed_prompt.py first.")

        words = session.execute(
            select(Word.id, Word.german_word, Word.meaning)
            .where(
                Word.enrichment_status.in_(["pending", "failed"]),
                Word.enrichment_attempts < 3,
            )
            .order_by(Word.created_at.asc())
            .limit(batch_limit)
        ).all()

        return PromptSnapshot(id=prompt.id, template=prompt.template), [
            CandidateWord(
                id=word.id,
                german_word=word.german_word,
                meaning=word.meaning,
            )
            for word in words
        ]


def _claim_word(
    SessionLocal, word: CandidateWord, prompt_id: uuid.UUID
) -> ClaimedWord | None:
    now = datetime.now(timezone.utc)
    job_id = uuid.uuid4()
    with SessionLocal() as session:
        claimed_row = session.execute(
            update(Word)
            .where(
                Word.id == word.id,
                Word.enrichment_status.in_(["pending", "failed"]),
                Word.enrichment_attempts < 3,
            )
            .values(
                enrichment_status="processing",
                enrichment_attempts=Word.enrichment_attempts + 1,
            )
            .returning(Word.id, Word.german_word, Word.meaning)
        ).fetchone()
        if not claimed_row:
            return None

        session.add(
            EnrichmentJob(
                id=job_id,
                word_id=claimed_row.id,
                prompt_id=prompt_id,
                status="processing",
                started_at=now,
            )
        )
        session.commit()

        return ClaimedWord(
            id=claimed_row.id,
            german_word=claimed_row.german_word,
            meaning=claimed_row.meaning,
            job_id=job_id,
        )


def _complete_word(
    SessionLocal,
    word: ClaimedWord,
    prompt_id: uuid.UUID,
    job_id: uuid.UUID,
    raw_response: str,
    sentences: list[dict[str, str]],
    meaning: str | None,
) -> None:
    with SessionLocal() as session:
        for sentence in sentences:
            session.add(
                ExampleSentence(
                    id=uuid.uuid4(),
                    word_id=word.id,
                    sentence_de=sentence["sentence_de"],
                    sentence_en=sentence["sentence_en"],
                    source="gpt",
                    prompt_id=prompt_id,
                )
            )

        db_word = session.get(Word, word.id)
        if db_word:
            db_word.enrichment_status = "completed"
            if meaning and not db_word.meaning:
                db_word.meaning = meaning

        job = session.get(EnrichmentJob, job_id)
        if job:
            job.status = "completed"
            job.completed_at = datetime.now(timezone.utc)
            job.raw_response = raw_response

        session.commit()


def _fail_word(
    SessionLocal, word_id: uuid.UUID, job_id: uuid.UUID, error: Exception
) -> None:
    error_message = str(error)
    with SessionLocal() as session:
        db_word = session.get(Word, word_id)
        if db_word:
            db_word.enrichment_status = "failed"
            db_word.last_error = error_message

        job = session.get(EnrichmentJob, job_id)
        if job:
            job.status = "failed"
            job.error_message = error_message

        session.commit()


def run_enrichment(config: EnrichmentConfig | None = None) -> dict[str, int]:
    config = config or get_enrichment_config_from_env()
    SessionLocal = create_enrichment_session_maker(config.database_url)
    client = OpenAI(api_key=config.openai_api_key)
    completed = 0
    failed = 0

    prompt_row, candidates = _get_prompt_and_candidates(SessionLocal, config.batch_limit)
    logger.info("Found %d candidate word(s) to enrich", len(candidates))

    claimed_count = 0
    for candidate in candidates:
        word = _claim_word(SessionLocal, candidate, prompt_row.id)
        if not word:
            logger.info("Skipping already-claimed word: %s", candidate.german_word)
            continue
        claimed_count += 1
        logger.info(
            "Claimed word for enrichment: %s (word_id=%s, job_id=%s)",
            word.german_word,
            word.id,
            word.job_id,
        )
        rendered = prompt_row.template.replace("{{word}}", word.german_word)
        logger.info("Refining word with OpenAI: %s", word.german_word)
        try:
            response = client.chat.completions.create(
                model=config.openai_model,
                messages=[{"role": "user", "content": rendered}],
                response_format={"type": "json_object"},
                temperature=0.7,
                max_tokens=2000,
            )
            raw_response = response.choices[0].message.content
            if not raw_response:
                raise ValueError("OpenAI response did not include message content")
            data = json.loads(raw_response)
            sentences = data.get("sentences", [])
            meaning = data.get("meaning")
            if len(sentences) != 10:
                raise ValueError(f"Expected 10 sentences, got {len(sentences)}")

            _complete_word(
                SessionLocal=SessionLocal,
                word=word,
                prompt_id=prompt_row.id,
                job_id=word.job_id,
                raw_response=raw_response,
                sentences=sentences,
                meaning=meaning,
            )
            completed += 1
            logger.info("Completed enrichment for word: %s", word.german_word)
        except Exception as exc:
            _fail_word(SessionLocal, word.id, word.job_id, exc)
            failed += 1
            logger.exception("Failed enrichment for word: %s", word.german_word)

    return {
        "found": len(candidates),
        "claimed": claimed_count,
        "completed": completed,
        "failed": failed,
    }
