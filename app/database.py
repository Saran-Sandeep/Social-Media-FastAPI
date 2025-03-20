import urllib.parse

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from .config import get_settings

settings = get_settings()
encoded_password = urllib.parse.quote_plus(settings.DB_PASSWORD)

DATABASE_URL = f"mysql://{settings.DB_USERNAME}:{encoded_password}@{settings.DB_HOST}/{settings.DB_NAME}"

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# `Base` is the base class for all our ORM models.
# It is created using `declarative_base()` and
# serves as the foundation for defining database tables.
# By inheriting from `Base`, our models gain ORM capabilities,
# allowing us to define table structures with columns and relationships.
Base = declarative_base()


def get_db():
    """
    Generator function that yields a database session.

    The function initializes a database session and closes it after it has been used.
    The session is yielded so that it can be used in a with statement, ensuring that
    the session is always closed after it has been used.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
