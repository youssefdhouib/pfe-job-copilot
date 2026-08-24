from __future__ import annotations

import os
from pathlib import Path

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from pfe_job_copilot.collectors import get_collector
from pfe_job_copilot.alerts import extract_alert_jobs
from pfe_job_copilot.db import JOB_STATUSES, init_db, job_stats, query_jobs, update_job_status, upsert_job
from pfe_job_copilot.search_profile import DEFAULT_PROFILE
from pfe_job_copilot.scoring import is_target_internship
from pfe_job_copilot.targets import ats_targets


load_dotenv()
API_DB = Path(os.getenv("PFE_DB_PATH", "jobs.sqlite3"))
app = FastAPI(title="PFE Job Copilot API", version="0.1.0")


class CollectionRequest(BaseModel):
    source: str
    query: str = "stage PFE intelligence artificielle"
    location: str = "France"
    limit: int = Field(default=10, ge=1, le=50)


class ProfileCollectionRequest(BaseModel):
    source: str
    location: str = "France"
    max_queries: int = Field(default=4, ge=1, le=16)
    limit_per_query: int = Field(default=10, ge=1, le=25)


class StatusRequest(BaseModel):
    status: str


class AlertIngestRequest(BaseModel):
    source: str = Field(default="email-alert", max_length=80)
    subject: str = Field(default="", max_length=500)
    html: str = Field(default="", max_length=2_000_000)
    text: str = Field(default="", max_length=2_000_000)
    limit: int = Field(default=100, ge=1, le=500)


class PortfolioCollectionRequest(BaseModel):
    query: str = "stage stagiaire internship intern pfe"
    location: str = "France"
    limit_per_target: int = Field(default=25, ge=1, le=100)


@app.on_event("startup")
def initialize() -> None:
    init_db(API_DB)


@app.get("/health")
def health() -> dict[str, object]:
    init_db(API_DB)
    return {"status": "ok", "database": str(API_DB), "jobs": job_stats(API_DB)}


@app.get("/jobs")
def jobs(
    limit: int = Query(default=25, ge=1, le=200),
    min_score: int = Query(default=0, ge=0),
    status: str | None = None,
) -> list[dict[str, object]]:
    if status and status not in JOB_STATUSES:
        raise HTTPException(status_code=422, detail=f"Unknown status '{status}'")
    return [dict(row) for row in query_jobs(API_DB, limit, min_score, status)]


@app.get("/stats")
def stats() -> dict[str, int]:
    return job_stats(API_DB)


@app.patch("/jobs/{job_id}/status")
def set_status(job_id: int, request: StatusRequest) -> dict[str, object]:
    try:
        changed = update_job_status(job_id, request.status, API_DB)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if not changed:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"id": job_id, "status": request.status}


def _collector(source: str):
    try:
        return get_collector(source)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/collect")
def collect(request: CollectionRequest) -> dict[str, object]:
    collector = _collector(request.source)
    saved = 0
    try:
        for job in collector.search(request.query, request.location, request.limit):
            if upsert_job(job, API_DB):
                saved += 1
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return {"source": request.source, "query": request.query, "saved": saved}


@app.post("/collect/profile")
def collect_profile(request: ProfileCollectionRequest) -> dict[str, object]:
    collector = _collector(request.source)
    saved = 0
    skipped = 0
    failures: list[dict[str, str]] = []
    queries = DEFAULT_PROFILE.queries[: request.max_queries]
    for query in queries:
        try:
            for job in collector.search(query, request.location, request.limit_per_query):
                if not is_target_internship(job.title, job.company, job.location, job.description):
                    skipped += 1
                    continue
                if upsert_job(job, API_DB):
                    saved += 1
        except RuntimeError as exc:
            failures.append({"query": query, "error": str(exc)})
    if len(failures) == len(queries):
        raise HTTPException(status_code=502, detail={"message": "All queries failed", "failures": failures})
    return {
        "source": request.source,
        "queries": len(queries),
        "saved": saved,
        "skipped": skipped,
        "failures": failures,
    }


@app.post("/alerts/ingest")
def ingest_alert(request: AlertIngestRequest) -> dict[str, object]:
    if not request.html.strip() and not request.text.strip():
        raise HTTPException(status_code=422, detail="Alert html or text is required")
    extracted = extract_alert_jobs(
        subject=request.subject, html=request.html, text=request.text,
        source_hint=request.source, limit=request.limit,
    )
    saved = sum(1 for job in extracted if upsert_job(job, API_DB))
    return {"source": request.source, "extracted": len(extracted), "saved": saved}


@app.post("/collect/portfolio")
def collect_portfolio(request: PortfolioCollectionRequest) -> dict[str, object]:
    saved = 0
    skipped = 0
    results: list[dict[str, object]] = []
    for source in ats_targets():
        target_saved = 0
        try:
            collector = _collector(source)
            for job in collector.search(request.query, request.location, request.limit_per_target):
                if not is_target_internship(job.title, job.company, job.location, job.description):
                    skipped += 1
                    continue
                if upsert_job(job, API_DB):
                    target_saved += 1
                    saved += 1
            results.append({"source": source, "saved": target_saved, "status": "ok"})
        except RuntimeError as exc:
            results.append({"source": source, "saved": 0, "status": "failed", "error": str(exc)})
    return {"targets": len(results), "saved": saved, "skipped": skipped, "results": results}


def run() -> None:
    uvicorn.run("pfe_job_copilot.api:app", host="0.0.0.0", port=8000, reload=False)
