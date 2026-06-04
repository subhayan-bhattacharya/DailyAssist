from sqlalchemy import Column, Integer, DateTime, Date, Text, ForeignKey, SmallInteger, func, Boolean, text, Index
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import declarative_base
import uuid

Base = declarative_base()

class Word(Base):
    __tablename__ = "words"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()"))
    german_word = Column(Text, nullable=False, unique=True)
    meaning, notes = Column(Text), Column(Text)
    enrichment_status = Column(Text, nullable=False, default='pending')
    enrichment_attempts = Column(Integer, default=0)
    last_error = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class Prompt(Base):
    __tablename__ = "prompts"
    __table_args__ = (
        Index(
            "uq_prompts_single_default",
            "is_default",
            unique=True,
            postgresql_where=text("is_default = TRUE"),
        ),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()"))
    name, template = Column(Text, nullable=False), Column(Text, nullable=False)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class EnrichmentJob(Base):
    __tablename__ = "enrichment_jobs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()"))
    word_id = Column(UUID(as_uuid=True), ForeignKey("words.id", ondelete="CASCADE"), nullable=False)
    prompt_id = Column(UUID(as_uuid=True), ForeignKey("prompts.id"))
    status, raw_response, error_message = Column(Text, nullable=False), Column(Text), Column(Text)
    started_at, completed_at = Column(DateTime(timezone=True)), Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ExampleSentence(Base):
    __tablename__ = "example_sentences"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()"))
    word_id = Column(UUID(as_uuid=True), ForeignKey("words.id", ondelete="CASCADE"), nullable=False)
    sentence_de, sentence_en = Column(Text, nullable=False), Column(Text)
    source = Column(Text, default='gpt')
    prompt_id = Column(UUID(as_uuid=True), ForeignKey("prompts.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class FlashcardView(Base):
    __tablename__ = "flashcard_views"
    __table_args__ = (
        Index("idx_flashcard_views_word_viewed_at", "word_id", text("viewed_at DESC")),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()"))
    word_id = Column(UUID(as_uuid=True), ForeignKey("words.id", ondelete="CASCADE"), nullable=False)
    viewed_at = Column(DateTime(timezone=True), server_default=func.now())
    confidence = Column(SmallInteger)  # 1-5

class DailySelection(Base):
    __tablename__ = "daily_selections"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()"))
    selected_on = Column(Date, nullable=False, unique=True)
    word_ids = Column(ARRAY(UUID(as_uuid=True)), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class AppSetting(Base):
    __tablename__ = "app_settings"
    key = Column(Text, primary_key=True)
    value = Column(Text, nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
