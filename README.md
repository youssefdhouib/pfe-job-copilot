# PFE Job Copilot

Small local pipeline for collecting and ranking PFE internship offers in France.

## What it does now

- Stores jobs in SQLite.
- Accepts pasted job URLs.
- Collects jobs from API-backed sources and isolated collectors.
- Deduplicates jobs by stable ATS/global ID, falling back to normalized URL.
- Scores offers against a fixed PFE AI/software profile.
- Generates focused French and English PFE/AI search queries.
- Supports public Greenhouse, Lever, and Ashby company feeds.
- Ingests rendered job-alert emails through the same normalized job pipeline.
- Runs a configurable portfolio of verified startup/company ATS boards.
- Provides optional, conservative JobSpy discovery.
- Tracks first/last seen timestamps, explicit application deadlines, active state, and source health.
- Tracks the planned source strategy for job boards, APIs, alerts, and startup ATS pages.

## Quick Start

```powershell
cd E:\reee\pfe-job-copilot
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
pfe init-db
pfe profile
pfe add-url "https://example.com/job" --title "Stage PFE IA" --company "Example"
pfe scrape --source adzuna --query "stage PFE intelligence artificielle" --location "France"
pfe scrape --source greenhouse:BOARD_TOKEN --query "internship AI" --location "France"
pfe scrape --source lever:SITE_NAME --query "stage machine learning" --location "France"
pfe scrape --source ashby:BOARD_NAME --query "internship AI" --location "France"
pfe collect-profile --source jobspy-indeed --max-queries 4 --limit-per-query 10
pfe sources
pfe list
```

`collect-profile` runs only four configured queries by default and waits five
seconds between them. Increase those values deliberately rather than using large
unattended runs on protected job boards.

Install the optional JobSpy connector with:

```powershell
pip install -e ".[discovery]"
pfe scrape --source jobspy-linkedin --query "AI engineer internship" --location "France" --limit 20
```

Supported JobSpy source names are `jobspy-linkedin`, `jobspy-indeed`,
`jobspy-glassdoor`, and `jobspy-google`. Do not provide account credentials or
cookies. Keep runs small and infrequent, and stop using a source if it returns
blocking or verification responses.

For Adzuna, set these environment variables first:

```powershell
$env:ADZUNA_APP_ID = "your_app_id"
$env:ADZUNA_APP_KEY = "your_app_key"
```

For France Travail, request access to the official **API Offres d'emploi** on
France Travail IO, then set:

```powershell
$env:FRANCE_TRAVAIL_CLIENT_ID = "your_client_id"
$env:FRANCE_TRAVAIL_CLIENT_SECRET = "your_client_secret"
pfe scrape --source france-travail --query "stage PFE intelligence artificielle" --location France
```

Copy `.env.example` to `.env` when we connect n8n/FastAPI. Do not commit the
real `.env` file.

## Supabase setup

The initial hosted schema is in `supabase/migrations/0001_initial.sql`. It adds
jobs, source provenance, collector runs, applications, private document metadata,
and per-user Row-Level Security. SQLite remains the CLI fallback until the
FastAPI/Supabase adapter is added.

To prepare the hosted database:

1. Create a Supabase project in an EU region.
2. Open the SQL editor and run `supabase/migrations/0001_initial.sql`, then
   `supabase/migrations/0002_auth_profile_trigger.sql`.
3. Put the project URL, publishable key, server secret, and pooled database URL
   in `.env` using `.env.example` as the template.
4. In Authentication → URL Configuration, set the Site URL to
   `http://localhost:3001` for local use.
5. In Authentication → Users, create the private owner account used to sign in.
6. Never place the secret/service-role key in frontend code.

Authentication is opt-in with `NEXT_PUBLIC_PFE_AUTH_ENABLED=true`. It remains
off by default while the local collection pipeline is being built.

## API and n8n

The local FastAPI service provides:

- `GET /health`
- `GET /jobs`
- `GET /stats`
- `GET /sources/health`
- `POST /collect`
- `POST /collect/profile`
- `POST /collect/portfolio`
- `POST /alerts/ingest`
- `PATCH /jobs/{id}/status`

Start the complete local stack:

```powershell
docker compose up -d --build
```

Open the Next.js job dashboard at `http://localhost:3001`, API documentation at
`http://localhost:8000/docs`, and n8n at `http://localhost:5678`. All ports bind
to localhost only. The TypeScript/Tailwind dashboard can filter and rank jobs,
update application status, and trigger a focused collection through FastAPI.
See `n8n/README.md` for workflow import instructions.

The frontend lives in `apps/web`. For local frontend development outside
Docker, copy `apps/web/.env.example` to `apps/web/.env.local`, start FastAPI on
port 8000, then run `npm run dev` from `apps/web`.

## Notes

Scraping websites is fragile because job boards change their HTML and may restrict automated access. This project keeps each collector separate and favors sources that allow API access.

## Target Sources

| Source | First method | Status |
| --- | --- | --- |
| Adzuna | API | active |
| France Travail | official API | active; credentials required |
| LinkedIn Jobs | alerts + optional JobSpy | experimental |
| Welcome to the Jungle | alerts/manual URLs | planned |
| Indeed France | alerts + optional JobSpy | experimental |
| HelloWork | alerts/manual URLs | manual only |
| JobTeaser | manual/browser later | planned |
| Apec | manual/API check | planned |
| Talent.com | alerts/manual URLs | planned |
| Glassdoor | alerts + optional JobSpy | experimental |
| Wellfound | manual/browser later | planned |
| StepStone | alerts/public route check | planned |
| XING Jobs | alerts/public route check | planned |
| Company career pages | ATS collectors | planned |
| Startup ATS pages | Greenhouse/Lever APIs | active |
