from typing import List

import pandas as pd


def fetch_jobs(
    search_terms: List[str],
    location: str,
    hours_old: int,
    max_results: int,
    include_remote: bool,
    sites: List[str],
):
    try:
        from jobspy import scrape_jobs
    except ImportError as exc:
        raise RuntimeError("jobspy is required. Install it with pip install jobspy") from exc

    combined = []
    for term in search_terms:
        jobs_df = scrape_jobs(
            site_name=sites,
            search_term=term,
            location=location,
            results_wanted=max_results,
            hours_old=hours_old,
            is_remote=include_remote,
        )
        if jobs_df is None:
            continue
        if isinstance(jobs_df, pd.DataFrame):
            records = jobs_df.to_dict(orient="records")
        else:
            records = list(jobs_df)
        for record in records:
            record["_search_term"] = term
        combined.extend(records)
    return combined
