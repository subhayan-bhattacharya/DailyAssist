from sqlalchemy.orm import Session
from db.models import ExampleSentence, Word
from uuid import UUID

def get_word_examples(db: Session, word_id: UUID):
    word = db.query(Word).filter(Word.id == word_id).first()
    if not word:
        return None
    
    sentences = db.query(ExampleSentence).filter(ExampleSentence.word_id == word_id).all()
    
    return {
        "word_id": word_id,
        "german_word": word.german_word,
        "sentences": sentences
    }
