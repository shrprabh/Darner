import os
from dataclasses import dataclass
from typing import List


def _parse_csv_env(key: str, default: List[str]) -> List[str]:
    raw = os.getenv(key)
    if not raw:
        return default
    return [item.strip() for item in raw.split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    allowed_origins: List[str]
    job_sites: List[str]
    default_location: str
    max_results: int
    hours_window: int
    request_timeout: int


def get_settings() -> Settings:
    return Settings(
        allowed_origins=_parse_csv_env("ALLOWED_ORIGINS", ["http://localhost:5173"]),
        job_sites=_parse_csv_env("JOB_SITES", ["indeed", "linkedin", "google"]),
        default_location=os.getenv("DEFAULT_LOCATION", "United States"),
        max_results=int(os.getenv("MAX_RESULTS", "50")),
        hours_window=int(os.getenv("HOURS_WINDOW", "25")),
        request_timeout=int(os.getenv("REQUEST_TIMEOUT", "30")),
    )


settings = get_settings()
