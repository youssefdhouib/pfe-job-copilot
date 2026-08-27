from __future__ import annotations

from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


TRACKING_PREFIXES = ("utm_", "trk")
TRACKING_KEYS = {
    "campaign", "eid", "fbclid", "gclid", "lipi", "midSig", "midToken",
    "msclkid", "originalSubdomain", "recommendedFlavor", "ref", "refId",
    "source", "trackingId",
}


def clean_text(value: object | None) -> str:
    return " ".join(("" if value is None else str(value)).split())


def normalize_url(url: str) -> str:
    parts = urlsplit(url.strip())
    query = [
        (key, value)
        for key, value in parse_qsl(parts.query, keep_blank_values=True)
        if key not in TRACKING_KEYS and not key.startswith(TRACKING_PREFIXES)
    ]
    return urlunsplit(
        (
            parts.scheme.lower(),
            parts.netloc.lower(),
            parts.path.rstrip("/"),
            urlencode(query),
            "",
        )
    )
