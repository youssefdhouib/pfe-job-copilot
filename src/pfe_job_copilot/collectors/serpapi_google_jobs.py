from __future__ import annotations

from collections.abc import Iterable
import os

import httpx

from pfe_job_copilot.models import Job
from pfe_job_copilot.normalize import clean_text, normalize_url


class SerpApiGoogleJobsCollector:
    source = "google-jobs"
    endpoint = "https://serpapi.com/search"

    def search(self, query: str, location: str, limit: int) -> Iterable[Job]:
        api_key = os.getenv("SERPAPI_API_KEY")
        if not api_key:
            raise RuntimeError("Google Jobs needs the SERPAPI_API_KEY environment variable")

        remaining = limit
        next_page_token: str | None = None
        while remaining > 0:
            params = {
                "engine": "google_jobs",
                "q": query,
                "location": location,
                "gl": "fr",
                "hl": "fr",
                "google_domain": "google.fr",
                "api_key": api_key,
            }
            if next_page_token:
                params["next_page_token"] = next_page_token

            try:
                response = httpx.get(self.endpoint, params=params, timeout=30)
                response.raise_for_status()
                payload = response.json()
            except (httpx.HTTPError, ValueError) as exc:
                raise RuntimeError(f"Google Jobs search failed: {exc}") from exc

            if payload.get("error"):
                raise RuntimeError(f"Google Jobs search failed: {clean_text(payload['error'])}")

            results = payload.get("jobs_results") or []
            for item in results[:remaining]:
                apply_options = item.get("apply_options") or []
                url = next(
                    (clean_text(option.get("link")) for option in apply_options if option.get("link")),
                    clean_text(item.get("share_link")),
                )
                if not url:
                    continue
                yield Job(
                    title=clean_text(item.get("title")),
                    company=clean_text(item.get("company_name")),
                    location=clean_text(item.get("location")),
                    url=normalize_url(url),
                    source=self.source,
                    description=clean_text(item.get("description")),
                    source_job_id=clean_text(item.get("job_id")),
                )
                remaining -= 1
                if remaining == 0:
                    return

            next_page_token = clean_text(
                (payload.get("serpapi_pagination") or {}).get("next_page_token")
            ) or None
            if not next_page_token or not results:
                return
