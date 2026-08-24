from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol

from pfe_job_copilot.models import Job


class Collector(Protocol):
    source: str

    def search(self, query: str, location: str, limit: int) -> Iterable[Job]:
        pass
