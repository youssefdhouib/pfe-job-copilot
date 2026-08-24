from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Job:
    title: str
    company: str
    url: str
    source: str
    location: str = ""
    description: str = ""
    score: int = 0

