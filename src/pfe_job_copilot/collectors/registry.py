from __future__ import annotations

from pfe_job_copilot.collectors.adzuna import AdzunaCollector
from pfe_job_copilot.collectors.ats import AshbyCollector, GreenhouseCollector, LeverCollector
from pfe_job_copilot.collectors.base import Collector
from pfe_job_copilot.collectors.france_travail import FranceTravailCollector
from pfe_job_copilot.collectors.html_search import COLLECTORS as HTML_COLLECTORS
from pfe_job_copilot.collectors.jobspy import JobSpyCollector
from pfe_job_copilot.collectors.public_pages import HELLOWORK_COLLECTOR, WTTJ_COLLECTOR


COLLECTORS: dict[str, Collector] = {
    "adzuna": AdzunaCollector(),
    "france-travail": FranceTravailCollector(),
    "indeed": HTML_COLLECTORS["indeed"],
    "hellowork": HELLOWORK_COLLECTOR,
    "wttj": WTTJ_COLLECTOR,
}


def get_collector(source: str) -> Collector:
    if ":" in source:
        kind, identifier = source.split(":", 1)
        if kind == "greenhouse" and identifier:
            return GreenhouseCollector(identifier)
        if kind == "lever" and identifier:
            return LeverCollector(identifier)
        if kind == "ashby" and identifier:
            return AshbyCollector(identifier)
    if source.startswith("jobspy-"):
        site = source.removeprefix("jobspy-")
        if site in {"linkedin", "indeed", "glassdoor", "google"}:
            return JobSpyCollector(site)
    try:
        return COLLECTORS[source]
    except KeyError as exc:
        available = ", ".join(sorted(COLLECTORS))
        raise ValueError(f"Unknown source '{source}'. Available sources: {available}") from exc
