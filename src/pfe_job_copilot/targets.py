from __future__ import annotations

import os


# Public ATS identifiers only. Override with PFE_ATS_TARGETS as a comma-separated list.
DEFAULT_ATS_TARGETS = (
    "greenhouse:dataiku",
    "greenhouse:shifttechnology",
    "greenhouse:datadog",
    "ashby:alan",
    "ashby:dust",
    "ashby:pennylane",
    "ashby:photoroom",
    "ashby:nabla",
    "ashby:poolside",
    "ashby:akur8",
    "ashby:doctolib",
)


def ats_targets() -> tuple[str, ...]:
    configured = os.getenv("PFE_ATS_TARGETS", "")
    if not configured.strip():
        return DEFAULT_ATS_TARGETS
    return tuple(item.strip() for item in configured.split(",") if item.strip())
