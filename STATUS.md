# PFE Job Copilot — Implementation Status

Last audited: 2026-08-25

## Working and verified

| Component | Evidence | State |
| --- | --- | --- |
| FastAPI backend | `/health` responds and reports 98 jobs | Verified |
| Next.js dashboard | Runs at `http://localhost:3001` and reads the API | Verified |
| Local SQLite storage | 98 jobs persisted in Docker volume | Verified |
| Deduplication | Repeated URLs are normalized before storage | Tested |
| Match scoring | Scores are capped to 0–100; existing invalid score repaired | Tested and deployed |
| Gmail OAuth | Read-only Gmail access granted | Verified |
| LinkedIn Gmail alerts | One real email produced 4 extracted and 4 saved jobs | Verified and active |
| France Travail API | Four real profile queries completed with no failures | Verified |
| France Travail schedule | Published in n8n; runs every 4 hours | Active |
| Indeed logged-out discovery | Two small live runs succeeded; relevance gate retained the Safran PFE role and rejected a teaching false positive | Verified; active every 12 hours |
| Welcome to the Jungle public collector | Logged-out profile run saved 16 relevant roles and skipped 4; workflow imported into n8n | Verified; workflow inactive pending UI execution |
| HelloWork public collector | Logged-out profile run saved 12 roles and skipped 8; stable catalogue fallback verified; workflow imported | Verified; workflow inactive pending UI execution |
| Job lifecycle | First/last seen, active state, three-miss expiration guard, explicit deadline extraction, source health | Implemented and tested |

## Active but requiring a clean verification run

| Component | Current evidence | Required check |
| --- | --- | --- |
| Startup/company ATS schedule | All 11 targets succeeded in a manual run; 5 relevant jobs saved and 98 unrelated roles skipped | Verified and active |
| Email alert webhook | Active in n8n | Keep only if a non-Gmail sender will use it |

Current ATS targets: Dataiku, Shift Technology, Datadog, Alan, Dust, Pennylane,
Photoroom, Nabla, Poolside, Akur8, and Doctolib.

## Not implemented yet

- Additional website discovery is not configured. Indeed now has a conservative
  production n8n schedule. JobSpy adapters for logged-out LinkedIn, Glassdoor,
  and Google Jobs remain experimental with no production schedule, blocking
  detection, backoff, or verified live run.
- Collectors for JobTeaser, Apec, Talent.com, Wellfound, StepStone, and XING are
  not implemented.
- Alerts and Gmail filters for Welcome to the Jungle, Indeed, HelloWork, Apec,
  Talent.com, Glassdoor, Wellfound, StepStone, and XING.
- Welcome to the Jungle account preferences are configured for Software Engineer,
  entry-level internships in France. WTTJ currently displays "Alerts unavailable
  at the moment" while its alerts feature is being rebuilt, so email alerts cannot
  be enabled yet.
- Direct integrations for company career systems outside Greenhouse, Lever, and
  Ashby (for example Airbus, Thales, Orange, Capgemini, Dassault Systèmes, and
  Sopra Steria).
- Supabase as the production job database. The schema exists, but SQLite is live.
- CV customization, cover-letter generation, application preparation, and
  automatic application submission.
- Monitoring and failure notifications for scheduled workflows.

## Ordered next work

1. Execute the imported WTTJ and HelloWork workflows once in n8n, inspect their
   output, then publish both 12-hour schedules.
2. Review relevance of the existing ATS and public-page jobs and clean stale or
   non-internship data.
3. Monitor the first scheduled Indeed/WTTJ/HelloWork runs and add collection-run
   visibility plus error notifications.
4. Add Gmail filters that apply the existing `JobAlerts` label to each verified sender.
5. Improve email parsing/source attribution using real samples from each website.
6. Research and implement permitted public/API routes for the remaining websites;
   use alerts/manual intake where reliable scraping is unavailable.
7. Expand the public ATS target list with relevant French AI/software companies.
8. Move storage to Supabase only after collection quality is stable.
9. Build CV/application assistance after the job queue is trustworthy.

## Operating rule

For every new source, use this sequence: configure → manual test → inspect extracted
jobs → verify deduplication/relevance → publish → monitor the first scheduled run.
