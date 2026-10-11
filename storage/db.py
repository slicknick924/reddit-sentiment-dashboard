"""SQLite storage for raw mentions and aggregated per-ticker sentiment.

Schema:
  mentions         one row per (reddit item, ticker) pair, with sentiment.
  ticker_snapshots one row per (ticker, pipeline run) aggregate, used by
                   the dashboard to show attention/sentiment over time.
"""
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from config.settings import ensure_data_dir

DB_FILENAME = "sentiment.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS mentions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    reddit_item_id TEXT NOT NULL,
    kind TEXT NOT NULL,
    subreddit TEXT NOT NULL,
    ticker TEXT NOT NULL,
    sentiment_label TEXT NOT NULL,
    sentiment_score REAL NOT NULL,
    signed_score REAL NOT NULL,
    item_score INTEGER NOT NULL,
    permalink TEXT NOT NULL,
    created_utc TEXT NOT NULL,
    fetched_at TEXT NOT NULL,
    UNIQUE(reddit_item_id, ticker)
);

CREATE INDEX IF NOT EXISTS idx_mentions_ticker ON mentions(ticker);
CREATE INDEX IF NOT EXISTS idx_mentions_created ON mentions(created_utc);

CREATE TABLE IF NOT EXISTS ticker_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,
    run_at TEXT NOT NULL,
    mention_count INTEGER NOT NULL,
    avg_signed_score REAL NOT NULL,
    positive_count INTEGER NOT NULL,
    negative_count INTEGER NOT NULL,
    neutral_count INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_snapshots_ticker ON ticker_snapshots(ticker);
CREATE INDEX IF NOT EXISTS idx_snapshots_run_at ON ticker_snapshots(run_at);
"""


def get_db_path() -> Path:
    return ensure_data_dir() / DB_FILENAME


@contextmanager
def get_connection():
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with get_connection() as conn:
        conn.executescript(SCHEMA)


def insert_mention(
    conn: sqlite3.Connection,
    reddit_item_id: str,
    kind: str,
    subreddit: str,
    ticker: str,
    sentiment_label: str,
    sentiment_score: float,
    signed_score: float,
    item_score: int,
    permalink: str,
    created_utc: datetime,
) -> None:
    conn.execute(
        """
        INSERT OR IGNORE INTO mentions (
            reddit_item_id, kind, subreddit, ticker,
            sentiment_label, sentiment_score, signed_score,
            item_score, permalink, created_utc, fetched_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            reddit_item_id,
            kind,
            subreddit,
            ticker,
            sentiment_label,
            sentiment_score,
            signed_score,
            item_score,
            permalink,
            created_utc.isoformat(),
            datetime.utcnow().isoformat(),
        ),
    )


def insert_snapshot(
    conn: sqlite3.Connection,
    ticker: str,
    run_at: datetime,
    mention_count: int,
    avg_signed_score: float,
    positive_count: int,
    negative_count: int,
    neutral_count: int,
) -> None:
    conn.execute(
        """
        INSERT INTO ticker_snapshots (
            ticker, run_at, mention_count, avg_signed_score,
            positive_count, negative_count, neutral_count
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            ticker,
            run_at.isoformat(),
            mention_count,
            avg_signed_score,
            positive_count,
            negative_count,
            neutral_count,
        ),
    )
