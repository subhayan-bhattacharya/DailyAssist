from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from db.models import Prompt


def get_default_prompt(db: Session):
    return db.query(Prompt).filter(Prompt.is_default.is_(True)).first()


def create_default_prompt_version(db: Session, name: str, template: str):
    try:
        db.query(Prompt).filter(Prompt.is_default.is_(True)).update(
            {Prompt.is_default: False},
            synchronize_session=False,
        )
        new_prompt = Prompt(name=name, template=template, is_default=True)
        db.add(new_prompt)
        db.commit()
        db.refresh(new_prompt)
        return new_prompt
    except IntegrityError:
        db.rollback()
        return None
