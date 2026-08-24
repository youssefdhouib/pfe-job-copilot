from __future__ import annotations

from collections.abc import Iterable

from pfe_job_copilot.models import Job
from pfe_job_copilot.normalize import clean_text


class JobSpyCollector:
    def __init__(self, site: str) -> None:
        self.site = site
        self.source = f"jobspy-{site}"

    def search(self, query: str, location: str, limit: int) -> Iterable[Job]:
        try:
            from jobspy import scrape_jobs
        except ImportError as exc:
            raise RuntimeError(
                "JobSpy is optional. Install it with: pip install -e .[discovery]"
            ) from exc

        try:
            rows = scrape_jobs(
                site_name=[self.site],
                search_term=query,
                location=location,
                results_wanted=limit,
                country_indeed="France",
                linkedin_fetch_description=False,
                verbose=0,
            )
        except Exception as exc:
            raise RuntimeError(f"JobSpy {self.site} collection failed: {exc}") from exc

        for row in rows.to_dict(orient="records"):
            yield Job(
                title=clean_text(row.get("title")),
                company=clean_text(row.get("company")),
                location=clean_text(row.get("location")),
                url=row.get("job_url_direct") or row.get("job_url") or "",
                source=self.source,
                description=clean_text(row.get("description")),
            )
