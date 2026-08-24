import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from pfe_job_copilot import api
from pfe_job_copilot.models import Job


class FakeCollector:
    source = "fake"

    def search(self, query: str, location: str, limit: int):
        yield Job(
            title="Stage PFE AI Engineer",
            company="Example",
            location="Paris, France",
            url="https://example.com/jobs/ai-pfe",
            source=self.source,
            description="Six-month machine learning internship using Python and LLMs.",
        )


class MixedCollector:
    source = "fake"

    def search(self, query: str, location: str, limit: int):
        yield from FakeCollector().search(query, location, limit)
        yield Job(
            title="Enseignant chercheur informatique",
            company="Example University",
            location="France",
            url="https://example.com/jobs/teacher",
            source=self.source,
            description="Teach AI and supervise student internships and PFE projects.",
        )


class ApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.original_db = api.API_DB
        api.API_DB = Path(self.temp.name) / "api.sqlite3"
        self.client = TestClient(api.app)
        self.client.__enter__()

    def tearDown(self) -> None:
        self.client.__exit__(None, None, None)
        api.API_DB = self.original_db
        self.temp.cleanup()

    def test_health_collect_list_and_status_flow(self) -> None:
        self.assertEqual(self.client.get("/health").status_code, 200)

        with patch("pfe_job_copilot.api.get_collector", return_value=FakeCollector()):
            response = self.client.post(
                "/collect",
                json={"source": "fake", "query": "stage AI", "location": "France", "limit": 1},
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["saved"], 1)

        jobs = self.client.get("/jobs", params={"min_score": 20}).json()
        self.assertEqual(len(jobs), 1)
        self.assertGreater(jobs[0]["score"], 20)

        job_id = jobs[0]["id"]
        updated = self.client.patch(f"/jobs/{job_id}/status", json={"status": "shortlisted"})
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.json()["status"], "shortlisted")

    def test_rejects_unknown_status(self) -> None:
        response = self.client.get("/jobs", params={"status": "not-real"})
        self.assertEqual(response.status_code, 422)

    def test_profile_collection_skips_non_internship_keyword_matches(self) -> None:
        with patch("pfe_job_copilot.api.get_collector", return_value=MixedCollector()):
            response = self.client.post(
                "/collect/profile",
                json={"source": "fake", "max_queries": 1, "limit_per_query": 10},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["saved"], 1)
        self.assertEqual(response.json()["skipped"], 1)

    def test_ingests_job_alert_html(self) -> None:
        response = self.client.post(
            "/alerts/ingest",
            json={
                "subject": "New PFE jobs",
                "html": '<a href="https://www.linkedin.com/jobs/view/42?trackingId=email">Stage PFE AI</a>',
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["extracted"], 1)
        self.assertEqual(response.json()["saved"], 1)

if __name__ == "__main__":
    unittest.main()
