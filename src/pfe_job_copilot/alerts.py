from __future__ import annotations

import re
from urllib.parse import parse_qs, urlencode, urlsplit, urlunsplit

from bs4 import BeautifulSoup

from pfe_job_copilot.models import Job
from pfe_job_copilot.normalize import clean_text, normalize_url


URL_RE = re.compile(r"https?://[^\s<>\"']+")
GENERIC_TITLES = {
    "apply", "apply now", "en savoir plus", "learn more", "see job", "view job",
    "voir l'offre", "voir le poste", "voir plus",
}
JOB_SITES: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("linkedin", "linkedin.com", ("/jobs/view", "/comm/jobs/view")),
    ("welcome-to-the-jungle", "welcometothejungle.com", ("/jobs/",)),
    ("indeed", "indeed.", ("/viewjob", "/rc/clk")),
    ("hellowork", "hellowork.com", ("/emplois/",)),
    ("jobteaser", "jobteaser.com", ("/job-offers/",)),
    ("apec", "apec.fr", ("/detail-offre/",)),
    ("talent", "talent.com", ("/view", "/job/")),
    ("glassdoor", "glassdoor.", ("/job-listing/",)),
    ("france-travail", "francetravail.fr", ("/offres/recherche/detail/",)),
    ("wellfound", "wellfound.com", ("/jobs/",)),
    ("stepstone", "stepstone.", ("/stellenangebote--", "/job/")),
    ("xing", "xing.com", ("/jobs/",)),
    ("greenhouse", "greenhouse.io", ("/jobs/",)),
    ("lever", "lever.co", ("/",)),
    ("ashby", "ashbyhq.com", ("/",)),
)


def _source_for(url: str) -> str | None:
    parts = urlsplit(url)
    host = parts.netloc.casefold().removeprefix("www.")
    path = parts.path.casefold()
    for source, domain, paths in JOB_SITES:
        if domain in host and any(fragment in path for fragment in paths):
            return source
    return None


def _canonical_url(url: str) -> str:
    url = url.rstrip(".,);]")
    parts = urlsplit(url)
    query = parse_qs(parts.query)
    if "indeed." in parts.netloc.casefold() and parts.path == "/rc/clk" and query.get("jk"):
        url = urlunsplit((parts.scheme, parts.netloc, "/viewjob", urlencode({"jk": query["jk"][0]}), ""))
    elif "linkedin.com" in parts.netloc.casefold() and parts.path.startswith("/comm/jobs/view"):
        url = urlunsplit((parts.scheme, parts.netloc, parts.path.removeprefix("/comm"), parts.query, ""))
    return normalize_url(url)


def _useful_title(value: str, subject: str) -> str:
    title = clean_text(value)
    if not title or title.casefold() in GENERIC_TITLES or len(title) > 180:
        title = clean_text(subject)
    return title[:180] or "Job alert offer"


def extract_alert_jobs(
    *, subject: str = "", html: str = "", text: str = "", source_hint: str = "email-alert", limit: int = 100,
) -> list[Job]:
    """Extract supported job-board links from a rendered alert email."""
    jobs: list[Job] = []
    seen: set[str] = set()

    if html:
        soup = BeautifulSoup(html, "html.parser")
        for anchor in soup.select("a[href]"):
            raw_url = str(anchor.get("href") or "")
            source = _source_for(raw_url)
            if not source:
                continue
            url = _canonical_url(raw_url)
            if url in seen:
                continue
            seen.add(url)
            context = clean_text(anchor.parent.get_text(" ") if anchor.parent else "")[:1200]
            jobs.append(Job(
                title=_useful_title(anchor.get_text(" "), subject), company="", url=url,
                source=f"alert-{source}" if source else source_hint, description=context,
            ))
            if len(jobs) >= limit:
                return jobs

    body = text or (BeautifulSoup(html, "html.parser").get_text(" ") if html else "")
    for raw_url in URL_RE.findall(body):
        source = _source_for(raw_url)
        if not source:
            continue
        url = _canonical_url(raw_url)
        if url in seen:
            continue
        seen.add(url)
        jobs.append(Job(
            title=_useful_title("", subject), company="", url=url,
            source=f"alert-{source}" if source else source_hint,
        ))
        if len(jobs) >= limit:
            break
    return jobs
