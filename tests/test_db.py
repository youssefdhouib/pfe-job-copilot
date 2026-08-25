import sqlite3
import tempfile
import unittest
from pathlib import Path

from pfe_job_copilot.db import (
    init_db,
    query_jobs,
    reconcile_source_snapshot,
    record_source_health,
    source_health,
    upsert_job,
)
from pfe_job_copilot.models import Job


class DatabaseTests(unittest.TestCase):
    def test_external_scores_are_capped_at_100(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "jobs.sqlite3"
            init_db(db)
            upsert_job(Job(title="AI internship", company="Example", url="https://example.com/1", source="test", score=148), db)

            self.assertEqual(query_jobs(db)[0]["score"], 100)

    def test_tracking_parameters_do_not_create_duplicate_jobs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / "jobs.sqlite3"
            init_db(db)
            upsert_job(
                Job(
                    title="Stage PFE IA",
                    company="Example",
                    url="https://example.com/jobs/42?utm_source=linkedin",
                    source="linkedin",
                ),
                db,
            )
            upsert_job(
                Job(
                    title="Stage PFE Intelligence Artificielle",
                    company="Example",
                    url="https://example.com/jobs/42?utm_source=alert",
                    source="email-alert",
                ),
                db,
            )

            connection = sqlite3.connect(db)
            try:
                count = connection.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
            finally:
                connection.close()
            self.assertEqual(count, 1)

    def test_existing_database_is_migrated_without_data_loss(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / "jobs.sqlite3"
            connection = sqlite3.connect(db)
            connection.execute(
                """CREATE TABLE jobs (
                    id INTEGER PRIMARY KEY, title TEXT NOT NULL, company TEXT NOT NULL DEFAULT '',
                    location TEXT NOT NULL DEFAULT '', url TEXT NOT NULL,
                    normalized_url TEXT NOT NULL UNIQUE, source TEXT NOT NULL,
                    description TEXT NOT NULL DEFAULT '', score INTEGER NOT NULL DEFAULT 0,
                    status TEXT NOT NULL DEFAULT 'new', created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )"""
            )
            connection.execute(
                "INSERT INTO jobs (title, url, normalized_url, source) VALUES (?, ?, ?, ?)",
                ("Stage IA", "https://example.com/1", "https://example.com/1", "test"),
            )
            connection.commit()
            connection.close()

            init_db(db)
            row = query_jobs(db)[0]
            self.assertEqual(row["title"], "Stage IA")
            self.assertEqual(row["is_active"], 1)
            self.assertIsNotNone(row["first_seen_at"])

    def test_source_id_deduplicates_changed_urls_and_preserves_deadline(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / "jobs.sqlite3"
            init_db(db)
            upsert_job(Job(title="Stage IA", company="A", url="https://a.test/old",
                           source="ashby:acme", source_job_id="ashby:42"), db)
            upsert_job(Job(title="Stage IA", company="A", url="https://a.test/new",
                           source="ashby:acme", source_job_id="ashby:42",
                           application_deadline="2027-03-01"), db)
            rows = query_jobs(db)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["url"], "https://a.test/new")
            self.assertEqual(rows[0]["application_deadline"], "2027-03-01")

    def test_snapshot_requires_three_misses_before_deactivation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / "jobs.sqlite3"
            init_db(db)
            upsert_job(Job(title="Stage IA", company="A", url="https://a.test/1",
                           source="snapshot", source_job_id="1"), db)
            self.assertEqual(reconcile_source_snapshot("snapshot", set(), db), 0)
            self.assertEqual(reconcile_source_snapshot("snapshot", set(), db), 0)
            self.assertEqual(reconcile_source_snapshot("snapshot", set(), db), 1)
            self.assertEqual(query_jobs(db), [])

    def test_source_health_clears_error_after_success(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / "jobs.sqlite3"
            record_source_health("test", succeeded=False, error="timeout", db_path=db)
            record_source_health("test", succeeded=True, jobs_seen=4, jobs_saved=3, db_path=db)
            row = source_health(db)[0]
            self.assertIsNone(row["last_error"])
            self.assertEqual(row["jobs_saved"], 3)


if __name__ == "__main__":
    unittest.main()
