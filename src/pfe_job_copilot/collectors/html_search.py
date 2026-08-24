from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from urllib.parse import urlencode, urljoin

import httpx
from bs4 import BeautifulSoup

from pfe_job_copilot.models import Job
from pfe_job_copilot.normalize import clean_text, normalize_url


HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; PFEJobCopilot/0.1; +local)",
    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.6",
}


@dataclass(frozen=True)
class HtmlSearchCollector:
    source: str
    base_url: str
    search_path: str
    query_param: str
    location_param: str
    card_selector: str
    title_selector: str
    company_selector: str
    location_selector: str
    link_selector: str

    def search_url(self, query: str, location: str) -> str:
        return urljoin(
            self.base_url,
            f"{self.search_path}?{urlencode({self.query_param: query, self.location_param: location})}",
        )

    def search(self, query: str, location: str, limit: int) -> Iterable[Job]:
        url = self.search_url(query, location)
        try:
            response = httpx.get(url, headers=HEADERS, follow_redirects=True, timeout=20)
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise RuntimeError(f"{self.source} blocked or rejected the search page: {exc.response.status_code}") from exc
        except httpx.HTTPError as exc:
            raise RuntimeError(f"{self.source} search failed: {exc}") from exc
        soup = BeautifulSoup(response.text, "html.parser")
        seen: set[str] = set()

        for card in soup.select(self.card_selector):
            title_node = card.select_one(self.title_selector)
            link_node = card.select_one(self.link_selector)
            if not title_node or not link_node:
                continue

            href = link_node.get("href")
            if not href:
                continue

            url = normalize_url(urljoin(self.base_url, href))
            if url in seen:
                continue
            seen.add(url)

            company_node = card.select_one(self.company_selector)
            location_node = card.select_one(self.location_selector)
            yield Job(
                title=clean_text(title_node.get_text(" ")),
                company=clean_text(company_node.get_text(" ") if company_node else ""),
                location=clean_text(location_node.get_text(" ") if location_node else location),
                url=url,
                source=self.source,
                description=clean_text(card.get_text(" ")),
            )

            if len(seen) >= limit:
                break


COLLECTORS = {
    "indeed": HtmlSearchCollector(
        source="indeed",
        base_url="https://fr.indeed.com",
        search_path="/jobs",
        query_param="q",
        location_param="l",
        card_selector="div.job_seen_beacon, td.resultContent",
        title_selector="h2.jobTitle, a.jcs-JobTitle",
        company_selector="[data-testid='company-name'], span.companyName",
        location_selector="[data-testid='text-location'], div.companyLocation",
        link_selector="a.jcs-JobTitle, h2.jobTitle a",
    ),
}


def get_collector(source: str) -> HtmlSearchCollector:
    try:
        return COLLECTORS[source]
    except KeyError as exc:
        available = ", ".join(sorted(COLLECTORS))
        raise ValueError(f"Unknown source '{source}'. Available sources: {available}") from exc
