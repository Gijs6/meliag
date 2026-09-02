import json
import os
import sqlite3
from datetime import datetime, timedelta

from utils.paths import DATA_DIR

DB_PATH = os.path.join(DATA_DIR, "cache.sqlite3")


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS train_stock (
                train_number TEXT PRIMARY KEY,
                data TEXT NOT NULL,
                cached_at TEXT NOT NULL
            )
            """
        )


def is_cache_valid(cached_at):
    now = datetime.now()
    if cached_at.date() != now.date():
        return False
    return now - cached_at < timedelta(hours=3)


def get_train_stock(train_number):
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            "SELECT data, cached_at FROM train_stock WHERE train_number = ?",
            (train_number,),
        ).fetchone()

    if not row:
        return None

    data, cached_at = row
    if not is_cache_valid(datetime.fromisoformat(cached_at)):
        return None

    return json.loads(data)


def set_train_stock(train_number, data):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO train_stock (train_number, data, cached_at)
            VALUES (?, ?, ?)
            ON CONFLICT(train_number) DO UPDATE SET
                data = excluded.data,
                cached_at = excluded.cached_at
            """,
            (train_number, json.dumps(data), datetime.now().isoformat()),
        )
