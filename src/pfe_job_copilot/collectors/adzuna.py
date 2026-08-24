from __future__ import annotations

from collections.abc import Iterable
import os

import httpx

from pfe_job_copilot.models import Job
from pfe_job_copilot.normalize import clean_text, normalize_url


class AdzunaCollector:
    source = "adzuna"

    def search(self, query: str, location: str, limit: int) -> Iterable[Job]:
        app_id = os.getenv("ADZUNA_APP_ID")
        app_key = os.getenv("ADZUNA_APP_KEY")
        if not app_id or not app_key:
            raise RuntimeError("Adzuna needs ADZUNA_APP_ID and ADZUNA_APP_KEY environment variables")

        try:
            response = httpx.get(
                "https://api.adzuna.com/v1/api/jobs/fr/search/1",
                params={
                    "app_id": app_id,
                    "app_key": app_key,
                    "what": query,
                    "where": location,
                    "results_per_page": min(limit, 50),
                    "content-type": "application/json",
                },
                timeout=20,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Adzuna search failed: {exc}") from exc
        data = response.json()

        for item in data.get("results", [])[:limit]:
            company = item.get("company") or {}
            url = item.get("redirect_url") or item.get("url") or ""
            if not url:
                continue
            yield Job(
                title=clean_text(item.get("title")),
                company=clean_text(company.get("display_name")),
                location=clean_text((item.get("location") or {}).get("display_name")),
                url=normalize_url(url),
                source=self.source,
                description=clean_text(item.get("description")),
            )
