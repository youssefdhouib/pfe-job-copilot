from __future__ import annotations

import json
import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Callable, Protocol
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

from pfe_job_copilot.collectors.safe_http import SafeHttpClient
from pfe_job_copilot.models import Job
from pfe_job_copilot.normalize import clean_text, normalize_url


class PageFetcher(Protocol):
    def get(self, url: str): ...


def _jsonld_nodes(value):
    if isinstance(value, list):
        for item in value:
            yield from _jsonld_nodes(item)
    elif isinstance(value, dict):
        yield value
        for key in ("@graph", "itemListElement"):
            if key in value:
                yield from _jsonld_nodes(value[key])
        if "item" in value:
            yield from _jsonld_nodes(value["item"])


def _location(value) -> str:
    if isinstance(value, str):
        return clean_text(value)
    if not isinstance(value, dict):
        return ""
    address = value.get("address", value)
    if isinstance(address, str):
        return clean_text(address)
    if not isinstance(address, dict):
        return ""
    return clean_text(", ".join(str(address.get(key, "")) for key in ("addressLocality", "addressRegion", "addressCountry") if address.get(key)))


@dataclass
class PublicJobsPageCollector:
    source: str
    base_url: str
    url_builder: Callable[[str, str], str]
    job_path_pattern: re.Pattern[str]
    fetcher: PageFetcher = field(default_factory=SafeHttpClient)

    def search_url(self, query: str, location: str) -> str:
        return self.url_builder(query, location)

    def _from_jsonld(self, soup: BeautifulSoup) -> Iterable[Job]:
        for script in soup.select('script[type="application/ld+json"]'):
            try:
                payload = json.loads(script.string or script.get_text())
            except (json.JSONDecodeError, TypeError):
                continue
            for node in _jsonld_nodes(payload):
                node_type = node.get("@type", "")
                if isinstance(node_type, list):
                    is_job = "JobPosting" in node_type
                else:
                    is_job = node_type == "JobPosting"
                if not is_job:
                    continue
                url = node.get("url") or node.get("sameAs")
                title = clean_text(node.get("title") or node.get("name"))
                if not url or not title:
                    continue
                organization = node.get("hiringOrganization") or {}
                company = organization.get("name", "") if isinstance(organization, dict) else str(organization)
                yield Job(
                    title=title,
                    company=clean_text(company),
                    location=_location(node.get("jobLocation")),
                    url=normalize_url(urljoin(self.base_url, url)),
                    source=self.source,
                    description=clean_text(BeautifulSoup(str(node.get("description", "")), "html.parser").get_text(" ")),
                    source_job_id=clean_text(
                        (node.get("identifier") or {}).get("value")
                        if isinstance(node.get("identifier"), dict)
                        else node.get("identifier")
                    ),
                    published_at=clean_text(node.get("datePosted")) or None,
                    application_deadline=clean_text(node.get("validThrough")) or None,
                )

    def _from_links(self, soup: BeautifulSoup, fallback_location: str) -> Iterable[Job]:
        for link in soup.select("a[href]"):
            href = str(link.get("href", ""))
            if not self.job_path_pattern.search(href):
                continue
            container: Tag = link
            for parent in link.parents:
                if not isinstance(parent, Tag):
                    continue
                if parent.name in {"article", "li"} or parent.get("data-testid"):
                    container = parent
                    break
            title = clean_text(link.get_text(" "))
            context = clean_text(container.get_text(" "))
            if len(title) < 4 or len(title) > 240:
                continue
            yield Job(
                title=title,
                company="",
                location=fallback_location,
                url=normalize_url(urljoin(self.base_url, href)),
                source=self.source,
                description=context,
            )

    def search(self, query: str, location: str, limit: int) -> Iterable[Job]:
        response = self.fetcher.get(self.search_url(query, location))
        soup = BeautifulSoup(response.text, "html.parser")
        seen: set[str] = set()
        for job in (*self._from_jsonld(soup), *self._from_links(soup, location)):
            if job.url in seen:
                continue
            seen.add(job.url)
            yield job
            if len(seen) >= limit:
                return


def _wttj_url(query: str, location: str) -> str:
    # WTTJ exposes this public, server-rendered internship catalogue. Filtering
    # remains in our relevance layer so it does not depend on private APIs.
    return "https://www.welcometothejungle.com/fr/pages/stage-intelligence-artificielle"


def _hellowork_url(query: str, location: str) -> str:
    # Arbitrary keyword slugs can return 404 even though this broad public
    # catalogue exists. The shared profile gate performs the final filtering.
    return "https://www.hellowork.com/fr-fr/stage/mot-cle_intelligence-artificielle.html"


WTTJ_COLLECTOR = PublicJobsPageCollector(
    source="wttj",
    base_url="https://www.welcometothejungle.com",
    url_builder=_wttj_url,
    job_path_pattern=re.compile(r"/fr/companies/[^/]+/jobs/[^/?#]+"),
)

HELLOWORK_COLLECTOR = PublicJobsPageCollector(
    source="hellowork",
    base_url="https://www.hellowork.com",
    url_builder=_hellowork_url,
    job_path_pattern=re.compile(r"/fr-fr/emplois/\d+\.html"),
)
