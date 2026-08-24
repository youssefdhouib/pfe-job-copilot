# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

Next.js App Router with TypeScript and Tailwind CSS provides the production web interface. FastAPI owns collectors and scoring, n8n owns scheduled workflows, SQLite is the current local store, and Supabase Auth/Postgres is the prepared hosted data layer.

## Users

The primary user is one engineering student searching from Tunisia for a final-year PFE internship in France, especially AI engineering, generative AI, machine learning, data, and software engineering roles in French or English.

## Product Purpose

PFE Job Copilot continuously gathers relevant offers, ranks them against the user's search profile, removes duplicates, and provides one place to triage and track applications. Success means finding more relevant offers early while spending less time repeatedly searching job boards.

## Positioning

The product combines official APIs, public ATS feeds, conservative discovery, and job-alert ingestion into one profile-specific pipeline instead of depending on a single job board or blindly automating applications.

## Operating Context

The user reviews fresh jobs daily, opens promising offers on their original websites, and moves them through a lightweight application pipeline. n8n runs scheduled collection. Protected job boards should rely primarily on alerts and logged-out, limited discovery to reduce account risk.

## Capabilities and Constraints

- Working collectors: France Travail, Adzuna, Greenhouse, Lever, and optional JobSpy discovery.
- Current storage: local SQLite with a prepared Supabase migration.
- Current automation: an imported, inactive France Travail n8n schedule.
- Status vocabulary: new, shortlisted, preparing, ready, applied, interview, rejected, offer, ignored.
- Collection must respect source restrictions, avoid account cookies and credentials, and keep protected-board runs small and infrequent.
- Automatic form submission and CV customization remain future work.

## Brand Commitments

The product name is PFE Job Copilot. Interface language should be direct, practical, and calm; controls name the action they perform.

## Evidence on Hand

The repository contains the working collection pipeline, API tests, a Supabase schema, an n8n workflow, and real France Travail API results. It has no testimonials, performance benchmarks, or commercial claims; future surfaces must not fabricate them.

## Product Principles

- Relevance before volume.
- One trustworthy queue across many sources.
- Keep the human in control of applications.
- Prefer official APIs and alerts over fragile authenticated scraping.
- Make every job's next action obvious.

## Accessibility & Inclusion

The dashboard must remain keyboard-accessible, responsive on mobile web, readable in French and English job content, and respectful of reduced-motion preferences.
