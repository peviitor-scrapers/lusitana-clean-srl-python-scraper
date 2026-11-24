"""
Peviitor v1 API Client Module

All Solr operations go through https://api.peviitor.ro/v1:
- GET    /v1/firme/company/?cif=...
- PUT    /v1/firme/company/add/
- GET    /v1/scraper/jobs/?cif=...&rows=...
- POST   /v1/scraper/jobs/upload/
- DELETE /v1/scraper/jobs/delete/
"""

import requests

API_BASE_URL = "https://api.peviitor.ro/v1"
TIMEOUT = 15
HEADERS = {"User-Agent": "job_seeker_ro_spider"}


def pad_cif(cif):
    """Zero-pad a CIF to 8 digits if shorter, preserving longer CIFs."""
    return str(cif).strip().zfill(8)


def get_company_by_cif(cif):
    """Fetch a company from Peviitor Core by CIF."""
    url = f"{API_BASE_URL}/firme/company/?cif={pad_cif(cif)}"
    res = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    res.raise_for_status()
    data = res.json()
    if not data.get("success"):
        raise RuntimeError(f"Peviitor company lookup failed: {data}")
    rows = data.get("data") or []
    return rows[0] if rows else None


def upsert_company(company_data):
    """Create or update a company in Peviitor Core."""
    url = f"{API_BASE_URL}/firme/company/add/"
    res = requests.put(
        url,
        json=company_data,
        headers={**HEADERS, "Content-Type": "application/json"},
        timeout=TIMEOUT,
    )
    res.raise_for_status()
    return res.json()


def query_solr(cif, rows=250):
    """Fetch currently indexed jobs for a company CIF via Peviitor API."""
    url = f"{API_BASE_URL}/scraper/jobs/"
    res = requests.get(
        url,
        params={"cif": pad_cif(cif), "rows": rows},
        headers=HEADERS,
        timeout=TIMEOUT,
    )
    if res.status_code == 404:
        return []
    res.raise_for_status()
    data = res.json()
    if isinstance(data, dict):
        if "response" in data and isinstance(data["response"], dict):
            return data["response"].get("docs") or []
        return data.get("data") or data.get("jobs") or []
    return data if isinstance(data, list) else []


def upsert_jobs(jobs):
    """Upload a non-empty list of validated jobs to Peviitor."""
    clean = [{k: v for k, v in job.items() if v not in (None, "", [])} for job in jobs]
    if not clean:
        return {"success": True, "count": 0}
    url = f"{API_BASE_URL}/scraper/jobs/upload/"
    res = requests.post(
        url,
        json=clean,
        headers={**HEADERS, "Content-Type": "application/json"},
        timeout=TIMEOUT,
    )
    res.raise_for_status()
    return res.json()


def delete_job_by_url(job_url):
    """Delete a single stale job by URL via Peviitor API."""
    url = f"{API_BASE_URL}/scraper/jobs/delete/"
    res = requests.delete(
        url,
        json={"url": job_url},
        headers={**HEADERS, "Content-Type": "application/json"},
        timeout=TIMEOUT,
    )
    if res.status_code == 404:
        return {"deleted": False}
    res.raise_for_status()
    return res.json()


def delete_jobs_by_cif(cif):
    """Delete all jobs for a given CIF via Peviitor API."""
    url = f"{API_BASE_URL}/scraper/jobs/delete/"
    res = requests.delete(
        url,
        json={"cif": pad_cif(cif)},
        headers={**HEADERS, "Content-Type": "application/json"},
        timeout=TIMEOUT,
    )
    if res.status_code == 404:
        return {"deleted": False}
    res.raise_for_status()
    return res.json()
