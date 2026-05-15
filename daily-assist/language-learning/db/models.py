from sqlalchemy import Column, Integer, DateTime, Text, ForeignKey, SmallInteger, func, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship
import uuid

Base = declarative_base()

class Word(Base):
    __tablename__ = "words"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    german_word = Column(Text, nullable=False, unique=True)
    meaning, notes = Column(Text), Column(Text)
    enrichment_status = Column(Text, nullable=False, default='pending')
    enrichment_attempts = Column(Integer, default=0)
    last_error = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class Prompt(Base):
    __tablename__ = "prompts"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name, template = Column(Text, nullable=False), Column(Text, nullable=False)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class EnrichmentJob(Base):
    __tablename__ = "enrichment_jobs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    word_id = Column(UUID(as_uuid=True), ForeignKey("words.id", ondelete="CASCADE"), nullable=False)
    prompt_id = Column(UUID(as_uuid=True), ForeignKey("prompts.id"))
    status, raw_response, error_message = Column(Text, nullable=False), Column(Text), Column(Text)
    started_at, completed_at = Column(DateTime(timezone=True)), Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ExampleSentence(Base):
    __tablename__ = "example_sentences"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    word_id = Column(UUID(as_uuid=True), ForeignKey("words.id", ondelete="CASCADE"), nullable=False)
    sentence_de, sentence_en = Column(Text, nullable=False), Column(Text)
    source = Column(Text, default='gpt')
    prompt_id = Column(UUID(as_uuid=True), ForeignKey("prompts.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class FlashcardView(Base):
    __tablename__ = "flashcard_views"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    word_id = Column(UUID(as_uuid=True), ForeignKey("words.id", ondelete="CASCADE"), nullable=False)
    viewed_at = Column(DateTime(timezone=True), server_default=func.now())
    confidence = Column(SmallInteger) # 1-5
