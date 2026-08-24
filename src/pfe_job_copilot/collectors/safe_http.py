from __future__ import annotations

import random
import time
from dataclasses import dataclass, field
from email.utils import parsedate_to_datetime
from urllib.parse import urlsplit

import httpx


DEFAULT_HEADERS = {
    "User-Agent": "PFEJobCopilot/0.1 (personal job research; low frequency)",
    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.6",
    "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.7",
}


@dataclass
class SafeHttpClient:
    """Small, polite HTTP client for logged-out public job pages."""

    min_interval_seconds: float = 2.0
    max_retries: int = 2
    timeout_seconds: float = 20.0
    _last_request: dict[str, float] = field(default_factory=dict, init=False)

    def _wait_for_host(self, url: str) -> None:
        host = urlsplit(url).netloc.casefold()
        elapsed = time.monotonic() - self._last_request.get(host, 0.0)
        delay = self.min_interval_seconds - elapsed
        if delay > 0:
            time.sleep(delay + random.uniform(0, min(0.35, self.min_interval_seconds / 4)))
        self._last_request[host] = time.monotonic()

    @staticmethod
    def _retry_after(response: httpx.Response, attempt: int) -> float:
        value = response.headers.get("Retry-After", "").strip()
        if value.isdigit():
            return min(float(value), 60.0)
        if value:
            try:
                return min(max((parsedate_to_datetime(value).timestamp() - time.time()), 0.0), 60.0)
            except (TypeError, ValueError, OverflowError):
                pass
        return min(2**attempt, 30) + random.uniform(0, 0.5)

    def get(self, url: str) -> httpx.Response:
        for attempt in range(self.max_retries + 1):
            self._wait_for_host(url)
            try:
                response = httpx.get(
                    url,
                    headers=DEFAULT_HEADERS,
                    follow_redirects=True,
                    timeout=self.timeout_seconds,
                )
            except httpx.HTTPError as exc:
                if attempt >= self.max_retries:
                    raise RuntimeError(f"Public page request failed: {exc}") from exc
                time.sleep(self._retry_after(httpx.Response(503), attempt))
                continue

            if response.status_code in {403, 429}:
                raise RuntimeError(
                    f"Public page access paused after HTTP {response.status_code}; "
                    "the collector will not bypass the site's protection"
                )
            if response.status_code >= 500 and attempt < self.max_retries:
                time.sleep(self._retry_after(response, attempt))
                continue
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                raise RuntimeError(f"Public page rejected the request: HTTP {response.status_code}") from exc
            return response

        raise RuntimeError("Public page request failed after retries")
