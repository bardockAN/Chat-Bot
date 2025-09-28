# app/db.py
import tempfile
import shutil
from pathlib import Path
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase


class Base(DeclarativeBase):
    pass


def _writable_dir(preferred: Path) -> Path:
    """Đảm bảo có thư mục ghi được (ưu tiên repo/data, nếu không thì %TEMP%)."""
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
    """Trả về SQLite URL, tự copy DB mẫu sang nơi ghi được nếu cần."""
    project_root = Path(__file__).resolve().parents[1]
    repo_data_dir = project_root / "data"
    repo_db = repo_data_dir / "bookstore.db"

    runtime_dir = _writable_dir(repo_data_dir)
    db_path = runtime_dir / "bookstore.db"

    if not db_path.exists() and repo_db.exists():
        try:
            shutil.copy2(repo_db, db_path)
        except Exception:
            # Nếu copy fail thì SQLite sẽ tự tạo DB rỗng.
            pass

    return f"sqlite:///{db_path.as_posix()}"


engine = create_engine(get_database_url(), echo=False, future=True)

# Quan trọng: không expire object sau commit để tránh DetachedInstanceError
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    future=True,
    expire_on_commit=False,
)


@contextmanager
def get_db_session():
    """Context manager session: tự commit/rollback/close."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db() -> None:
    # Import trong hàm để tránh vòng lặp import
    from . import models  # noqa: F401
    Base.metadata.create_all(bind=engine)
