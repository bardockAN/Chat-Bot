import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase


class Base(DeclarativeBase):
    pass


def get_database_url() -> str:
    project_root = Path(__file__).resolve().parents[1]
    data_dir = project_root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    db_path = data_dir / "bookstore.db"
    return f"sqlite:///{db_path.as_posix()}"


engine = create_engine(get_database_url(), echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def init_db() -> None:
    # Imported inside to avoid circulars
    from . import models  # noqa: F401
    Base.metadata.create_all(bind=engine)


