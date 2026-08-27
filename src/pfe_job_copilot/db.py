from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

from pfe_job_copilot.models import Job
from pfe_job_copilot.deadlines import extract_application_deadline
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
    stable_key TEXT,
    source TEXT NOT NULL,
    source_job_id TEXT NOT NULL DEFAULT '',
    description TEXT NOT NULL DEFAULT '',
    score INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'new',
    published_at TEXT,
    application_deadline TEXT,
    first_seen_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_seen_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_active INTEGER NOT NULL DEFAULT 1,
    missing_runs INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_jobs_score ON jobs(score DESC);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);

CREATE TABLE IF NOT EXISTS source_health (
    source TEXT PRIMARY KEY,
    last_success_at TEXT,
    last_error_at TEXT,
    last_error TEXT,
    jobs_seen INTEGER NOT NULL DEFAULT 0,
    jobs_saved INTEGER NOT NULL DEFAULT 0,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""

JOB_COLUMNS: dict[str, str] = {
    "stable_key": "TEXT",
    "source_job_id": "TEXT NOT NULL DEFAULT ''",
    "published_at": "TEXT",
    "application_deadline": "TEXT",
    "first_seen_at": "TEXT",
    "last_seen_at": "TEXT",
    "is_active": "INTEGER NOT NULL DEFAULT 1",
    "missing_runs": "INTEGER NOT NULL DEFAULT 0",
}


def connect(db_path: Path = DEFAULT_DB) -> sqlite3.Connection:
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    return connection


def init_db(db_path: Path = DEFAULT_DB) -> None:
    with closing(connect(db_path)) as connection:
        connection.executescript(SCHEMA)
        existing = {row[1] for row in connection.execute("PRAGMA table_info(jobs)")}
        for name, definition in JOB_COLUMNS.items():
            if name not in existing:
                connection.execute(f"ALTER TABLE jobs ADD COLUMN {name} {definition}")
        connection.execute(
            "UPDATE jobs SET stable_key = normalized_url WHERE stable_key IS NULL OR stable_key = ''"
        )
        connection.execute("UPDATE jobs SET first_seen_at = created_at WHERE first_seen_at IS NULL")
        connection.execute("UPDATE jobs SET last_seen_at = updated_at WHERE last_seen_at IS NULL")
        connection.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_jobs_stable_key ON jobs(stable_key)"
        )
        connection.execute("UPDATE jobs SET score = MIN(100, MAX(0, score)) WHERE score < 0 OR score > 100")
        connection.commit()


def upsert_job(job: Job, db_path: Path = DEFAULT_DB) -> bool:
    init_db(db_path)
    normalized_url = normalize_url(job.url)
    stable_key = f"{job.source}:{job.source_job_id}" if job.source_job_id else normalized_url
    title = clean_text(job.title)
    company = clean_text(job.company)
    location = clean_text(job.location)
    description = clean_text(job.description)
    application_deadline = job.application_deadline or extract_application_deadline(description)
    raw_score = job.score or score_job(title, company, location, description)
    score = min(100, max(0, raw_score))

    with closing(connect(db_path)) as connection:
        existing = connection.execute(
            "SELECT id FROM jobs WHERE stable_key = ? OR normalized_url = ? LIMIT 1",
            (stable_key, normalized_url),
        ).fetchone()
        if existing:
            cursor = connection.execute(
                """
                UPDATE jobs SET title = ?, company = ?, location = ?, url = ?,
                    normalized_url = ?, stable_key = ?, source = ?, source_job_id = ?,
                    description = ?, score = ?, published_at = COALESCE(?, published_at),
                    application_deadline = COALESCE(?, application_deadline),
                    last_seen_at = CURRENT_TIMESTAMP, is_active = 1, missing_runs = 0,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (title, company, location, job.url, normalized_url, stable_key, job.source,
                 job.source_job_id, description, score, job.published_at,
                 application_deadline, existing["id"]),
            )
        else:
            cursor = connection.execute(
                """
                INSERT INTO jobs (
                    title, company, location, url, normalized_url, stable_key, source,
                    source_job_id, description, score, published_at, application_deadline
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (title, company, location, job.url, normalized_url, stable_key, job.source,
                 job.source_job_id, description, score, job.published_at,
                 application_deadline),
            )
        connection.commit()
        return cursor.rowcount > 0


def rescore_jobs(db_path: Path = DEFAULT_DB) -> int:
    """Recompute stored scores after the deterministic scoring rules change."""
    init_db(db_path)
    with closing(connect(db_path)) as connection:
        rows = connection.execute("SELECT id, title, company, location, description FROM jobs")
        updates = [
            (score_job(row["title"], row["company"], row["location"], row["description"]), row["id"])
            for row in rows
        ]
        connection.executemany("UPDATE jobs SET score = ? WHERE id = ?", updates)
        connection.commit()
        return len(updates)


def list_jobs(db_path: Path = DEFAULT_DB, limit: int = 25) -> list[sqlite3.Row]:
    with closing(connect(db_path)) as connection:
        return list(
            connection.execute(
                """
                SELECT id, score, status, title, company, location, source, url,
                       application_deadline, is_active
                FROM jobs
                WHERE is_active = 1
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
        SELECT id, title, company, location, url, source, source_job_id, description,
               score, status, published_at, application_deadline, first_seen_at,
               last_seen_at, is_active, created_at, updated_at
        FROM jobs
        WHERE score >= ? AND is_active = 1
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


def record_source_health(
    source: str,
    *,
    succeeded: bool,
    jobs_seen: int = 0,
    jobs_saved: int = 0,
    error: str | None = None,
    db_path: Path = DEFAULT_DB,
) -> None:
    init_db(db_path)
    with closing(connect(db_path)) as connection:
        connection.execute(
            """
            INSERT INTO source_health (
                source, last_success_at, last_error_at, last_error,
                jobs_seen, jobs_saved, updated_at
            ) VALUES (
                ?, CASE WHEN ? THEN CURRENT_TIMESTAMP END,
                CASE WHEN ? THEN NULL ELSE CURRENT_TIMESTAMP END,
                ?, ?, ?, CURRENT_TIMESTAMP
            )
            ON CONFLICT(source) DO UPDATE SET
                last_success_at = CASE WHEN ? THEN CURRENT_TIMESTAMP ELSE source_health.last_success_at END,
                last_error_at = CASE WHEN ? THEN source_health.last_error_at ELSE CURRENT_TIMESTAMP END,
                last_error = CASE WHEN ? THEN NULL ELSE excluded.last_error END,
                jobs_seen = excluded.jobs_seen,
                jobs_saved = excluded.jobs_saved,
                updated_at = CURRENT_TIMESTAMP
            """,
            (source, succeeded, succeeded, error, jobs_seen, jobs_saved,
             succeeded, succeeded, succeeded),
        )
        connection.commit()


def source_health(db_path: Path = DEFAULT_DB) -> list[sqlite3.Row]:
    init_db(db_path)
    with closing(connect(db_path)) as connection:
        return list(connection.execute("SELECT * FROM source_health ORDER BY source"))


def reconcile_source_snapshot(
    source: str,
    seen_stable_keys: set[str],
    db_path: Path = DEFAULT_DB,
    deactivate_after: int = 3,
) -> int:
    """Deactivate jobs only after repeated absence from a complete source snapshot."""
    if deactivate_after < 1:
        raise ValueError("deactivate_after must be at least 1")
    init_db(db_path)
    with closing(connect(db_path)) as connection:
        rows = connection.execute(
            "SELECT id, stable_key FROM jobs WHERE source = ? AND is_active = 1", (source,)
        )
        missing_ids = [row["id"] for row in rows if row["stable_key"] not in seen_stable_keys]
        if not missing_ids:
            return 0
        placeholders = ",".join("?" for _ in missing_ids)
        connection.execute(
            f"UPDATE jobs SET missing_runs = missing_runs + 1 WHERE id IN ({placeholders})",
            missing_ids,
        )
        cursor = connection.execute(
            f"""UPDATE jobs SET is_active = 0, updated_at = CURRENT_TIMESTAMP
                WHERE id IN ({placeholders}) AND missing_runs >= ?""",
            [*missing_ids, deactivate_after],
        )
        connection.commit()
        return cursor.rowcount
