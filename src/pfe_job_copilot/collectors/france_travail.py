from __future__ import annotations

import os
from collections.abc import Iterable

import httpx

from pfe_job_copilot.models import Job
from pfe_job_copilot.normalize import clean_text


DEFAULT_TOKEN_URL = "https://entreprise.francetravail.fr/connexion/oauth2/access_token"
DEFAULT_SEARCH_URL = "https://api.francetravail.io/partenaire/offresdemploi/v2/offres/search"
DEFAULT_SCOPE = "o2dsoffre api_offresdemploiv2"


class FranceTravailCollector:
    source = "france-travail"

    def _access_token(self) -> str:
        client_id = os.getenv("FRANCE_TRAVAIL_CLIENT_ID")
        client_secret = os.getenv("FRANCE_TRAVAIL_CLIENT_SECRET")
        if not client_id or not client_secret:
            raise RuntimeError(
                "France Travail needs FRANCE_TRAVAIL_CLIENT_ID and "
                "FRANCE_TRAVAIL_CLIENT_SECRET environment variables"
            )

        token_url = os.getenv("FRANCE_TRAVAIL_TOKEN_URL", DEFAULT_TOKEN_URL)
        try:
            response = httpx.post(
                token_url,
                params={"realm": "/partenaire"},
                data={
                    "grant_type": "client_credentials",
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "scope": os.getenv("FRANCE_TRAVAIL_SCOPE", DEFAULT_SCOPE),
                },
                timeout=20,
            )
            if response.is_error:
                try:
                    payload = response.json()
                    error = clean_text(payload.get("error"))
                    description = clean_text(payload.get("error_description"))
                    detail = ": ".join(part for part in (error, description) if part)
                except ValueError:
                    detail = "no error details returned"
                raise RuntimeError(
                    f"France Travail authentication failed ({response.status_code}): {detail}"
                )
            response.raise_for_status()
            return response.json()["access_token"]
        except RuntimeError:
            raise
        except (httpx.HTTPError, KeyError, ValueError) as exc:
            raise RuntimeError(f"France Travail authentication failed: {exc}") from exc

    def search(self, query: str, location: str, limit: int) -> Iterable[Job]:
        token = self._access_token()
        search_url = os.getenv("FRANCE_TRAVAIL_SEARCH_URL", DEFAULT_SEARCH_URL)
        params = {
            "motsCles": query,
            "range": f"0-{max(0, limit - 1)}",
        }
        if location.casefold() != "france":
            params["commune"] = location

        try:
            response = httpx.get(
                search_url,
                params=params,
                headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
                timeout=30,
            )
            response.raise_for_status()
            results = [] if response.status_code == 204 else response.json().get("resultats", [])
        except (httpx.HTTPError, ValueError) as exc:
            raise RuntimeError(f"France Travail search failed: {exc}") from exc

        for item in results[:limit]:
            job_id = clean_text(item.get("id"))
            company = clean_text((item.get("entreprise") or {}).get("nom"))
            job_location = clean_text((item.get("lieuTravail") or {}).get("libelle"))
            origin_url = clean_text((item.get("origineOffre") or {}).get("urlOrigine"))
            application_url = clean_text((item.get("contact") or {}).get("urlPostulation"))
            yield Job(
                title=clean_text(item.get("intitule")),
                company=company,
                location=job_location,
                url=origin_url
                or application_url
                or f"https://candidat.francetravail.fr/offres/recherche/detail/{job_id}",
                source=self.source,
                description=clean_text(item.get("description")),
            )
