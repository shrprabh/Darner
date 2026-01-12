from typing import List, Optional
from pydantic import BaseModel, Field


class RoleOption(BaseModel):
    key: str
    label: str
    experience_level: str
    search_terms: List[str]


class JobSearchRequest(BaseModel):
    role: str = Field(..., description="Role key from /roles")
    location: Optional[str] = None
    include_remote: bool = True
    skills: List[str] = Field(default_factory=list)
    max_results: Optional[int] = None


class JobSummary(BaseModel):
    id: str
    title: str
    company: str
    location: str
    link: str
    description_snippet: Optional[str] = None
    date_posted: Optional[str] = None
    age_minutes: Optional[int] = None
    sponsorship: str
    match_score: Optional[int] = None
    match_summary: str
    hire_chance: str
    source: Optional[str] = None


class WindowedJobs(BaseModel):
    label: str
    minutes: int
    count: int
    jobs: List[JobSummary]


class JobSearchResponse(BaseModel):
    generated_at: str
    role: RoleOption
    location: str
    windows: List[WindowedJobs]
    total_jobs: int
    search_terms: List[str]
