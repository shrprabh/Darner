import re
from datetime import datetime, timedelta, timezone
from typing import Optional

from dateutil import parser as date_parser


_POSITIVE_SPONSORSHIP = [
    "h1b",
    "h-1b",
    "visa sponsorship",
    "sponsorship available",
    "sponsor",
    "opt",
    "cpt",
    "stem opt",
    "work visa",
]

_NEGATIVE_SPONSORSHIP = [
    "no sponsorship",
    "without sponsorship",
    "unable to sponsor",
    "cannot sponsor",
    "no visa",
    "must be authorized",
    "no c2c",
    "no corp to corp",
]

_RELATIVE_RE = re.compile(r"(?P<value>\d+)\s*(?P<unit>minute|hour|day|week)s?", re.IGNORECASE)


def detect_sponsorship(text: str) -> str:
    lowered = text.lower()
    if any(term in lowered for term in _NEGATIVE_SPONSORSHIP):
        return "unlikely"
    if any(term in lowered for term in _POSITIVE_SPONSORSHIP):
        return "likely"
    return "unknown"


def parse_posted_at(value) -> Optional[datetime]:
    if value is None:
        return None

    if isinstance(value, datetime):
        posted = value
    else:
        text = str(value).strip().lower()
        if not text:
            return None
        if text in {"just posted", "today"}:
            posted = datetime.now(timezone.utc)
        elif text == "yesterday":
            posted = datetime.now(timezone.utc) - timedelta(days=1)
        else:
            match = _RELATIVE_RE.search(text)
            if match:
                value_num = int(match.group("value"))
                unit = match.group("unit")
                delta = {
                    "minute": timedelta(minutes=value_num),
                    "hour": timedelta(hours=value_num),
                    "day": timedelta(days=value_num),
                    "week": timedelta(weeks=value_num),
                }.get(unit, timedelta())
                posted = datetime.now(timezone.utc) - delta
            else:
                try:
                    posted = date_parser.parse(text)
                except (ValueError, TypeError):
                    return None

    if posted.tzinfo is None:
        posted = posted.replace(tzinfo=timezone.utc)
    return posted


def age_minutes(posted_at: Optional[datetime]) -> Optional[int]:
    if posted_at is None:
        return None
    delta = datetime.now(timezone.utc) - posted_at
    return int(delta.total_seconds() // 60)


def snippet(text: str, limit: int = 220) -> str:
    cleaned = " ".join(text.split())
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 3].rstrip() + "..."
