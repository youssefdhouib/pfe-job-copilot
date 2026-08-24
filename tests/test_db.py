import sqlite3
import tempfile
import unittest
from pathlib import Path

from pfe_job_copilot.db import init_db, query_jobs, upsert_job
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


if __name__ == "__main__":
    unittest.main()
