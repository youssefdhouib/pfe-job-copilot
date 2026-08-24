# n8n setup

Start the backend and n8n with:

```powershell
docker compose up -d --build
```

Open `http://localhost:5678`, create the local n8n owner account, then import
the JSON files from `/workflows` using the n8n workflow import menu. Run each
collection workflow manually once before activating its schedule.

- `france-travail-collection.json` runs the official France Travail searches.
- `ats-portfolio-collection.json` checks the configured Greenhouse and Ashby
  startup/company boards every 12 hours.
- `email-alert-webhook.json` accepts rendered alert emails and sends their job
  links through the same normalization, scoring, and deduplication pipeline.
- `gmail-alert-ingestion.json` is the direct Gmail automation template. Attach
  a Gmail OAuth2 credential to its trigger, test it once, then activate it.
- `indeed-discovery.json` runs one small logged-out Indeed discovery query every
  12 hours. It uses no account credentials or cookies and filters non-internships
  before storage.
- `wttj-public-collection.json` and `hellowork-public-collection.json` read only
  logged-out, public internship catalogues every 12 hours. They stop on access
  controls and pass every result through the internship/relevance gate.

For Gmail alerts, open the imported Gmail workflow and attach your OAuth
credential to **Receive Gmail job alerts**. Do not give the scraper a LinkedIn password or browser cookie;
LinkedIn, Indeed, Welcome to the Jungle, Glassdoor, StepStone, XING, and other
board alerts can all arrive through this email path.

Create a Gmail label named `JobAlerts`. For each job-board sender, open one alert
email, choose **More → Filter messages like these → Create filter**, and select
**Apply the label → JobAlerts**. The Gmail workflow reads only this label.

The webhook accepts this JSON shape:

```json
{
  "source": "gmail-alert",
  "subject": "New AI internship jobs",
  "html": "<rendered email HTML>",
  "text": "plain-text fallback"
}
```

n8n generates its credential-encryption key inside the persistent `n8n_data`
volume. Back up that volume before moving the installation to another machine.

The workflow calls the backend over Docker's private network. France Travail
credentials remain in the backend container and are never stored in the n8n
workflow JSON.
