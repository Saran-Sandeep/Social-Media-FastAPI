import os
import urllib.parse

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

load_dotenv()

DB_USERNAME = os.getenv("DB_USERNAME")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")

encoded_password = urllib.parse.quote_plus(DB_PASSWORD)

DATABASE_URL = f"mysql://{DB_USERNAME}:{encoded_password}@{DB_HOST}/{DB_NAME}"

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
