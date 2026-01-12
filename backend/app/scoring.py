import re
from dataclasses import dataclass
from typing import List, Optional, Set


@dataclass(frozen=True)
class MatchResult:
    score: Optional[int]
    matched: List[str]
    missing: List[str]


_WORD_RE = re.compile(r"[^a-z0-9+#./ ]+")


def _normalize(text: str) -> str:
    return _WORD_RE.sub(" ", text.lower()).strip()


def _tokenize(text: str) -> Set[str]:
    return {token for token in _normalize(text).split() if len(token) > 1}


def score_skills(job_text: str, skills: List[str]) -> MatchResult:
    if not skills:
        return MatchResult(score=None, matched=[], missing=[])

    normalized_job = _normalize(job_text)
    tokens = _tokenize(job_text)
    matched: List[str] = []
    missing: List[str] = []

    for skill in skills:
        normalized_skill = _normalize(skill)
        if not normalized_skill:
            continue
        if " " in normalized_skill:
            is_match = normalized_skill in normalized_job
        else:
            is_match = normalized_skill in tokens

        if is_match:
            matched.append(skill)
        else:
            missing.append(skill)

    if not matched and not missing:
        return MatchResult(score=None, matched=[], missing=[])

    total = len(matched) + len(missing)
    score = int(round((len(matched) / total) * 100)) if total else None
    return MatchResult(score=score, matched=matched, missing=missing)


def chance_of_hire(score: Optional[int]) -> str:
    if score is None:
        return "unknown"
    if score >= 75:
        return "high"
    if score >= 55:
        return "medium"
    return "low"


def build_match_summary(result: MatchResult) -> str:
    if result.score is None:
        return "Provide skills to calculate fit."
    if result.matched:
        matched_preview = ", ".join(result.matched[:5])
        extra = "" if len(result.matched) <= 5 else "..."
        return f"Matched {len(result.matched)} of {len(result.matched) + len(result.missing)} skills: {matched_preview}{extra}"
    return "No matching skills found."
