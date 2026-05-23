import base64
import json
import os
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

# Initialize engine globally so it is reused across Lambda invocations
_engine = None


def _resolve_database_url() -> str:
    """Return DATABASE_URL, resolving from Secrets Manager if only the ARN is set."""
    db_url = os.environ.get("DATABASE_URL")
    if db_url:
        return db_url

    secret_arn = os.environ.get("DATABASE_URL_SECRET_ARN")
    if secret_arn:
        import boto3
        client = boto3.client("secretsmanager")
        response = client.get_secret_value(SecretId=secret_arn)
        if "SecretString" in response:
            return response["SecretString"]
        return base64.b64decode(response["SecretBinary"]).decode("utf-8")

    raise ValueError("DATABASE_URL or DATABASE_URL_SECRET_ARN environment variable is required")


def get_engine():
    global _engine
    if _engine is None:
        db_url = _resolve_database_url()
        if not db_url:
            raise ValueError("DATABASE_URL environment variable is not set")
        
        # SQLAlchemy 2.0 style requires postgresql:// instead of postgres://
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)
            
        _engine = create_engine(db_url, poolclass=NullPool)
    return _engine

def get_session_maker():
    engine = get_engine()
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)

@contextmanager
def get_db_session():
    SessionLocal = get_session_maker()
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
