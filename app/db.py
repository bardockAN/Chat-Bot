import os
import tempfile
import shutil
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase


class Base(DeclarativeBase):
    pass


def _writable_dir(preferred: Path) -> Path:
    try:
        preferred.mkdir(parents=True, exist_ok=True)
        probe = preferred / ".write_test"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
        return preferred
    except Exception:
        tmp = Path(tempfile.gettempdir()) / "bookstore_data"
        tmp.mkdir(parents=True, exist_ok=True)
        return tmp


def get_database_url() -> str:
    """Return a SQLite URL that works both locally and on Streamlit Cloud.

    - Use repo `data/bookstore.db` if writable.
    - If the repo path is read-only (typical on Streamlit Cloud), copy the
      bundled database to a writable temp folder and use that file instead.
    """
    project_root = Path(__file__).resolve().parents[1]
    repo_data_dir = project_root / "data"
    repo_db = repo_data_dir / "bookstore.db"

    # Choose a writable directory for runtime DB
    runtime_dir = _writable_dir(repo_data_dir)
    db_path = runtime_dir / "bookstore.db"

    # If runtime DB doesn't exist but a bundled DB exists in the repo, copy it
    if not db_path.exists() and repo_db.exists():
        try:
            shutil.copy2(repo_db, db_path)
        except Exception:
            # Best effort; if copy fails, SQLite will create an empty DB
            pass

    return f"sqlite:///{db_path.as_posix()}"


engine = create_engine(get_database_url(), echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def init_db() -> None:
    # Imported inside to avoid circulars
    from . import models  # noqa: F401
    Base.metadata.create_all(bind=engine)


