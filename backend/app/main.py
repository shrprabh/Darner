import hashlib
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .jobspy_client import fetch_jobs
from .roles import ROLE_CATALOG, ROLE_MAP
from .schemas import JobSearchRequest, JobSearchResponse, JobSummary, RoleOption, WindowedJobs
from .scoring import build_match_summary, chance_of_hire, score_skills
from .utils import age_minutes, detect_sponsorship, parse_posted_at, snippet


WINDOWS = [
    {"label": "Last 20 minutes", "minutes": 20},
    {"label": "Last 1 hour", "minutes": 60},
    {"label": "Last 3 hours", "minutes": 180},
    {"label": "Last 5 hours", "minutes": 300},
    {"label": "Last 10 hours", "minutes": 600},
    {"label": "Last 25 hours", "minutes": 1500},
]

CACHE_TTL_SECONDS = 300
JOB_CACHE: Dict[str, Dict[str, object]] = {}

app = FastAPI(title="Darner Job Scout", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _cache_key(role_key: str, location: str, include_remote: bool, max_results: int) -> str:
    return f"{role_key}:{location}:{include_remote}:{max_results}"


def _get_cached_jobs(cache_key: str):
    cached = JOB_CACHE.get(cache_key)
    if not cached:
        return None
    if time.time() - cached["timestamp"] > CACHE_TTL_SECONDS:
        JOB_CACHE.pop(cache_key, None)
        return None
    return cached["jobs"]


def _set_cached_jobs(cache_key: str, jobs):
    JOB_CACHE[cache_key] = {"timestamp": time.time(), "jobs": jobs}


def _normalize_job(raw_job: dict, skills: List[str]) -> Optional[JobSummary]:
    title = raw_job.get("title") or raw_job.get("job_title") or "Untitled"
    company = raw_job.get("company") or raw_job.get("company_name") or "Unknown"
    location = raw_job.get("location") or raw_job.get("job_location") or "Unlisted"
    link = (
        raw_job.get("job_url_direct")
        or raw_job.get("job_url")
        or raw_job.get("link")
        or raw_job.get("url")
    )
    if not link:
        return None

    description = raw_job.get("description") or raw_job.get("job_description") or ""
    search_term = raw_job.get("_search_term")
    source = raw_job.get("site") or raw_job.get("source") or search_term

    posted_at = parse_posted_at(raw_job.get("date_posted") or raw_job.get("date"))
    age = age_minutes(posted_at)

    job_text = f"{title}. {description}"
    match_result = score_skills(job_text, skills)

    job_id_seed = f"{title}|{company}|{link}"
    job_id = hashlib.sha1(job_id_seed.encode("utf-8")).hexdigest()[:12]

    return JobSummary(
        id=job_id,
        title=title,
        company=company,
        location=location,
        link=link,
        description_snippet=snippet(description) if description else None,
        date_posted=posted_at.isoformat() if posted_at else None,
        age_minutes=age,
        sponsorship=detect_sponsorship(f"{title} {description}"),
        match_score=match_result.score,
        match_summary=build_match_summary(match_result),
        hire_chance=chance_of_hire(match_result.score),
        source=source,
    )


def _dedupe_jobs(jobs: List[JobSummary]) -> List[JobSummary]:
    seen = set()
    deduped = []
    for job in jobs:
        if job.link in seen:
            continue
        seen.add(job.link)
        deduped.append(job)
    return deduped


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.get("/roles", response_model=List[RoleOption])
async def list_roles():
    return [RoleOption(**role) for role in ROLE_CATALOG]


@app.post("/jobs/search", response_model=JobSearchResponse)
async def search_jobs(request: JobSearchRequest):
    role = ROLE_MAP.get(request.role)
    if not role:
        raise HTTPException(status_code=400, detail="Unknown role key. Use /roles for options.")

    location = request.location or settings.default_location
    max_results = request.max_results or settings.max_results

    cache_key = _cache_key(request.role, location, request.include_remote, max_results)
    raw_jobs = _get_cached_jobs(cache_key)

    if raw_jobs is None:
        raw_jobs = fetch_jobs(
            search_terms=role["search_terms"],
            location=location,
            hours_old=settings.hours_window,
            max_results=max_results,
            include_remote=request.include_remote,
            sites=settings.job_sites,
        )
        _set_cached_jobs(cache_key, raw_jobs)

    normalized_jobs: List[JobSummary] = []
    for raw in raw_jobs:
        job = _normalize_job(raw, request.skills)
        if job is not None:
            normalized_jobs.append(job)

    normalized_jobs = _dedupe_jobs(normalized_jobs)
    normalized_jobs.sort(key=lambda job: job.age_minutes or 999999)

    windowed: List[WindowedJobs] = []
    for window in WINDOWS:
        if window["minutes"] == WINDOWS[-1]["minutes"]:
            jobs_in_window = [
                job
                for job in normalized_jobs
                if job.age_minutes is None or job.age_minutes <= window["minutes"]
            ]
        else:
            jobs_in_window = [
                job for job in normalized_jobs if job.age_minutes is not None and job.age_minutes <= window["minutes"]
            ]
        windowed.append(
            WindowedJobs(
                label=window["label"],
                minutes=window["minutes"],
                count=len(jobs_in_window),
                jobs=jobs_in_window,
            )
        )

    return JobSearchResponse(
        generated_at=datetime.now(timezone.utc).isoformat(),
        role=RoleOption(**role),
        location=location,
        windows=windowed,
        total_jobs=len(normalized_jobs),
        search_terms=role["search_terms"],
    )
