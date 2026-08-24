from __future__ import annotations

from collections.abc import Iterable

import httpx
from bs4 import BeautifulSoup

from pfe_job_copilot.models import Job
from pfe_job_copilot.normalize import clean_text
from pfe_job_copilot.scoring import normalize_for_matching


def _plain_text(value: str | None) -> str:
    return clean_text(BeautifulSoup(value or "", "html.parser").get_text(" "))


def _matches_query(query: str, haystack: str) -> bool:
    words = set(normalize_for_matching(haystack).split())
    return not query.strip() or any(term in words for term in normalize_for_matching(query).split())


class GreenhouseCollector:
    source = "greenhouse"

    def __init__(self, board_token: str) -> None:
        self.board_token = board_token

    def search(self, query: str, location: str, limit: int) -> Iterable[Job]:
        base_url = f"https://boards-api.greenhouse.io/v1/boards/{self.board_token}"
        try:
            board = httpx.get(base_url, timeout=20).json()
            response = httpx.get(f"{base_url}/jobs", params={"content": "true"}, timeout=30)
            response.raise_for_status()
        except (httpx.HTTPError, ValueError) as exc:
            raise RuntimeError(f"Greenhouse board '{self.board_token}' could not be read: {exc}") from exc

        company = clean_text(board.get("name")) or self.board_token
        jobs = response.json().get("jobs", [])
        matched = 0
        for item in jobs:
            description = _plain_text(item.get("content"))
            title = clean_text(item.get("title"))
            job_location = clean_text((item.get("location") or {}).get("name"))
            if not _matches_query(query, f"{title} {job_location} {description}"):
                continue
            yield Job(
                title=title,
                company=company,
                location=job_location,
                url=item.get("absolute_url", ""),
                source=self.source,
                description=description,
            )
            matched += 1
            if matched >= limit:
                break


class LeverCollector:
    source = "lever"

    def __init__(self, site: str) -> None:
        self.site = site

    def search(self, query: str, location: str, limit: int) -> Iterable[Job]:
        url = f"https://api.lever.co/v0/postings/{self.site}"
        try:
            response = httpx.get(url, params={"mode": "json"}, timeout=30)
            response.raise_for_status()
            jobs = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise RuntimeError(f"Lever site '{self.site}' could not be read: {exc}") from exc

        matched = 0
        for item in jobs:
            categories = item.get("categories") or {}
            description = clean_text(
                " ".join(
                    filter(
                        None,
                        [item.get("descriptionPlain"), item.get("additionalPlain")],
                    )
                )
            )
            title = clean_text(item.get("text"))
            job_location = clean_text(categories.get("location"))
            if not _matches_query(query, f"{title} {job_location} {description}"):
                continue
            yield Job(
                title=title,
                company=self.site,
                location=job_location,
                url=item.get("hostedUrl") or item.get("applyUrl") or "",
                source=self.source,
                description=description,
            )
            matched += 1
            if matched >= limit:
                break


class AshbyCollector:
    source = "ashby"

    def __init__(self, board_name: str) -> None:
        self.board_name = board_name

    def search(self, query: str, location: str, limit: int) -> Iterable[Job]:
        url = f"https://api.ashbyhq.com/posting-api/job-board/{self.board_name}"
        try:
            response = httpx.get(url, timeout=30)
            response.raise_for_status()
            jobs = response.json().get("jobs", [])
        except (httpx.HTTPError, ValueError) as exc:
            raise RuntimeError(f"Ashby board '{self.board_name}' could not be read: {exc}") from exc

        matched = 0
        for item in jobs:
            description = _plain_text(item.get("descriptionHtml") or item.get("descriptionPlain"))
            title = clean_text(item.get("title"))
            job_location = clean_text(item.get("location"))
            if not _matches_query(query, f"{title} {job_location} {description}"):
                continue
            yield Job(
                title=title,
                company=self.board_name,
                location=job_location,
                url=item.get("jobUrl") or item.get("applyUrl") or "",
                source=self.source,
                description=description,
            )
            matched += 1
            if matched >= limit:
                break
