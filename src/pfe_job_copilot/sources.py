from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SourcePlan:
    name: str
    method: str
    status: str
    note: str


SOURCE_PLANS = [
    SourcePlan("Adzuna", "api", "active", "Aggregator API for France jobs; useful direct intake."),
    SourcePlan("France Travail", "api", "active", "Official API collector; requires a free client ID and secret."),
    SourcePlan("LinkedIn Jobs", "alerts/jobspy", "experimental", "Alerts first; JobSpy is logged-out, limited, and optional."),
    SourcePlan("Welcome to the Jungle", "alerts/manual", "planned", "Good PFE/startup source; add alerts or saved URLs first."),
    SourcePlan("Indeed France", "alerts/jobspy", "experimental", "Use JobSpy conservatively plus official alerts."),
    SourcePlan("HelloWork", "alerts/manual", "manual-only", "Page source states automated scraping is not allowed."),
    SourcePlan("JobTeaser", "manual/browser-later", "planned", "Often needs account/session access."),
    SourcePlan("Apec", "manual/api-check", "planned", "Useful for engineering roles; check allowed feeds/API before scraping."),
    SourcePlan("Talent.com", "alerts/manual", "planned", "Aggregator source; start with alerts/manual URLs."),
    SourcePlan("Glassdoor", "alerts/jobspy", "experimental", "Use JobSpy conservatively plus official alerts."),
    SourcePlan("Wellfound", "manual/browser-later", "planned", "Startup-focused; likely needs session-aware collection."),
    SourcePlan("StepStone", "alerts/public-check", "planned", "Alerts first; add a limited collector only after verification."),
    SourcePlan("XING Jobs", "alerts/public-check", "planned", "Alerts first; add a limited collector only after verification."),
    SourcePlan("Company career pages", "alerts + ats collectors", "active", "Email alerts cover custom career sites; public ATS boards run in a batch."),
    SourcePlan("Greenhouse startups", "ats api", "active", "Public company job-board API; use greenhouse:BOARD_TOKEN."),
    SourcePlan("Lever startups", "ats api", "active", "Public postings API; use lever:SITE_NAME."),
    SourcePlan("Ashby startups", "ats api", "active", "Public startup job-board API; use ashby:BOARD_NAME."),
]
