from __future__ import annotations

from pathlib import Path
from time import sleep

import typer
from dotenv import load_dotenv

from pfe_job_copilot.collectors import get_collector
from pfe_job_copilot.db import DEFAULT_DB, init_db, list_jobs, upsert_job
from pfe_job_copilot.models import Job
from pfe_job_copilot.search_profile import DEFAULT_PROFILE
from pfe_job_copilot.sources import SOURCE_PLANS


load_dotenv()

app = typer.Typer(help="Collect and rank PFE internship jobs.")


@app.command("profile")
def show_profile() -> None:
    typer.echo("Search locations:")
    for location in DEFAULT_PROFILE.locations:
        typer.echo(f"  - {location}")
    typer.echo("Search queries:")
    for query in DEFAULT_PROFILE.queries:
        typer.echo(f"  - {query}")


@app.command("sources")
def list_sources() -> None:
    for source in SOURCE_PLANS:
        typer.echo(f"{source.name:<24} {source.method:<20} {source.status:<12} {source.note}")


@app.command("init-db")
def init_database(db: Path = DEFAULT_DB) -> None:
    init_db(db)
    typer.echo(f"Initialized {db}")


@app.command("add-url")
def add_url(
    url: str,
    title: str = "Untitled job",
    company: str = "",
    location: str = "",
    source: str = "manual",
    db: Path = DEFAULT_DB,
) -> None:
    init_db(db)
    changed = upsert_job(Job(title=title, company=company, location=location, url=url, source=source), db)
    typer.echo("Saved job" if changed else "Job already tracked")


@app.command("scrape")
def scrape(
    source: str = "adzuna",
    query: str = "stage PFE intelligence artificielle",
    location: str = "France",
    limit: int = 20,
    db: Path = DEFAULT_DB,
) -> None:
    init_db(db)
    try:
        collector = get_collector(source)
    except ValueError as exc:
        typer.echo(str(exc))
        raise typer.Exit(code=2) from exc
    saved = 0
    try:
        for job in collector.search(query=query, location=location, limit=limit):
            if upsert_job(job, db):
                saved += 1
    except RuntimeError as exc:
        typer.echo(f"Scrape failed: {exc}")
        raise typer.Exit(code=1) from exc
    typer.echo(f"Saved or refreshed {saved} jobs from {source}")


@app.command("collect-profile")
def collect_profile(
    source: str = typer.Option(..., "--source", help="Collector name or ATS identifier."),
    location: str = "France",
    max_queries: int = 4,
    limit_per_query: int = 10,
    delay_seconds: float = 5.0,
    db: Path = DEFAULT_DB,
) -> None:
    """Run a conservative subset of the configured search queries."""
    if max_queries < 1 or limit_per_query < 1 or delay_seconds < 0:
        typer.echo("max-queries and limit-per-query must be positive; delay cannot be negative")
        raise typer.Exit(code=2)

    init_db(db)
    try:
        collector = get_collector(source)
    except ValueError as exc:
        typer.echo(str(exc))
        raise typer.Exit(code=2) from exc

    saved = 0
    failures = 0
    queries = DEFAULT_PROFILE.queries[:max_queries]
    for index, query in enumerate(queries):
        typer.echo(f"[{index + 1}/{len(queries)}] {query}")
        try:
            for job in collector.search(query=query, location=location, limit=limit_per_query):
                if upsert_job(job, db):
                    saved += 1
        except RuntimeError as exc:
            failures += 1
            typer.echo(f"  failed: {exc}")
        if index + 1 < len(queries) and delay_seconds:
            sleep(delay_seconds)

    typer.echo(f"Finished {len(queries)} queries: {saved} saved/refreshed, {failures} failed")
    if failures == len(queries):
        raise typer.Exit(code=1)


@app.command("list")
def list_saved_jobs(limit: int = 25, db: Path = DEFAULT_DB) -> None:
    init_db(db)
    rows = list_jobs(db, limit)
    if not rows:
        typer.echo("No jobs yet.")
        return

    for row in rows:
        typer.echo(
            f"[{row['id']}] {row['score']:>3} {row['status']:<10} "
            f"{row['title']} | {row['company']} | {row['location']} | {row['source']}\n"
            f"    {row['url']}"
        )
