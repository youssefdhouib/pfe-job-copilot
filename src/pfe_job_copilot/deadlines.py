from __future__ import annotations

import re
from datetime import date


DEADLINE_PATTERN = re.compile(
    r"(?:application\s+deadline|apply\s+by|closing\s+date|date\s+limite|"
    r"limite\s+de\s+candidature|cl[oô]ture\s+des\s+candidatures)"
    r"\s*(?::|-|est|le|is|on)?\s*"
    r"(?P<date>20\d{2}-\d{2}-\d{2}|\d{1,2}[/-]\d{1,2}[/-]20\d{2})",
    re.IGNORECASE,
)


def extract_application_deadline(text: str) -> str | None:
    """Return an ISO date only when the prose explicitly labels it a deadline."""
    match = DEADLINE_PATTERN.search(text)
    if not match:
        return None
    value = match.group("date")
    try:
        if value[:4].isdigit() and value[4] == "-":
            parsed = date.fromisoformat(value)
        else:
            day, month, year = (int(part) for part in re.split(r"[/-]", value))
            parsed = date(year, month, day)
    except (ValueError, IndexError):
        return None
    return parsed.isoformat()
