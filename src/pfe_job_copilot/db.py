from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

from pfe_job_copilot.models import Job
from pfe_job_copilot.normalize import clean_text, normalize_url
from pfe_job_copilot.scoring import score_job


DEFAULT_DB = Path("jobs.sqlite3")
JOB_STATUSES = {
    "new", "shortlisted", "preparing", "ready", "applied", "interview", "rejected", "offer", "ignored"
}


SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    company TEXT NOT NULL DEFAULT '',
    location TEXT NOT NULL DEFAULT '',
    url TEXT NOT NULL,
    normalized_url TEXT NOT NULL UNIQUE,
    source TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    score INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'new',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_jobs_score ON jobs(score DESC);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
"""


def connect(db_path: Path = DEFAULT_DB) -> sqlite3.Connection:
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    return connection


def init_db(db_path: Path = DEFAULT_DB) -> None:
    with closing(connect(db_path)) as connection:
        connection.executescript(SCHEMA)
        connection.execute("UPDATE jobs SET score = MIN(100, MAX(0, score)) WHERE score < 0 OR score > 100")
        connection.commit()


def upsert_job(job: Job, db_path: Path = DEFAULT_DB) -> bool:
    normalized_url = normalize_url(job.url)
    title = clean_text(job.title)
    company = clean_text(job.company)
    location = clean_text(job.location)
    description = clean_text(job.description)
    raw_score = job.score or score_job(title, company, location, description)
    score = min(100, max(0, raw_score))

    with closing(connect(db_path)) as connection:
        cursor = connection.execute(
            """
            INSERT INTO jobs (title, company, location, url, normalized_url, source, description, score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(normalized_url) DO UPDATE SET
                title = excluded.title,
                company = excluded.company,
                location = excluded.location,
                source = excluded.source,
                description = excluded.description,
                score = excluded.score,
                updated_at = CURRENT_TIMESTAMP
            WHERE jobs.status = 'new'
            """,
            (title, company, location, job.url, normalized_url, job.source, description, score),
        )
        connection.commit()
        return cursor.rowcount > 0


def list_jobs(db_path: Path = DEFAULT_DB, limit: int = 25) -> list[sqlite3.Row]:
    with closing(connect(db_path)) as connection:
        return list(
            connection.execute(
                """
                SELECT id, score, status, title, company, location, source, url
                FROM jobs
                ORDER BY score DESC, created_at DESC
                LIMIT ?
                """,
                (limit,),
            )
        )


def query_jobs(
    db_path: Path = DEFAULT_DB,
    limit: int = 25,
    min_score: int = 0,
    status: str | None = None,
) -> list[sqlite3.Row]:
    sql = """
        SELECT id, title, company, location, url, source, description, score, status,
               created_at, updated_at
        FROM jobs
        WHERE score >= ?
    """
    params: list[object] = [min_score]
    if status:
        sql += " AND status = ?"
        params.append(status)
    sql += " ORDER BY score DESC, created_at DESC LIMIT ?"
    params.append(limit)
    with closing(connect(db_path)) as connection:
        return list(connection.execute(sql, params))


def update_job_status(job_id: int, status: str, db_path: Path = DEFAULT_DB) -> bool:
    if status not in JOB_STATUSES:
        raise ValueError(f"Unknown status '{status}'")
    with closing(connect(db_path)) as connection:
        cursor = connection.execute(
            "UPDATE jobs SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (status, job_id),
        )
        connection.commit()
        return cursor.rowcount == 1


def job_stats(db_path: Path = DEFAULT_DB) -> dict[str, int]:
    with closing(connect(db_path)) as connection:
        rows = connection.execute("SELECT status, COUNT(*) AS count FROM jobs GROUP BY status")
        result = {row["status"]: row["count"] for row in rows}
        result["total"] = sum(result.values())
        return result
