import os
import sqlite3

from .config import DB_PATH


def _is_sqlite_file(db_path: str) -> bool:
    try:
        with open(db_path, "rb") as handle:
            header = handle.read(16)
        return header == b"SQLite format 3\x00"
    except OSError:
        return False

def init_db(db_path: str = DB_PATH) -> None:
    dir_name = os.path.dirname(db_path)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)

    if os.path.exists(db_path):
        if os.path.isdir(db_path):
            raise sqlite3.DatabaseError(f"DB path is a directory: {db_path}")
        if not _is_sqlite_file(db_path):
            os.remove(db_path)

    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS images (
            id TEXT PRIMARY KEY,
            original_filename TEXT,
            uploaded_at TIMESTAMP,
            original_width INTEGER,
            original_height INTEGER,
            file_sizes TEXT,
            keywords TEXT
        )
        """
    )
    conn.commit()
    conn.close()


def get_db(db_path: str = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn
