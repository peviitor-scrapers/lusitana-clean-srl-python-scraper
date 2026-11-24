"""
eJobs.ro Job Source Module

Searches eJobs.ro for job listings published by a specific company and extracts
ONLY title, canonical job URL, location, and posting date (strictly GDPR-compliant:
no job description text, no CVs, no personal data).
"""

import json
import re
from urllib.parse import quote_plus, urljoin

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.ejobs.ro"
API_SEARCH_URL = "https://api.ejobs.ro/jobs"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json, text/html",
}
TIMEOUT = 15

_LEGAL_SUFFIXES = {"srl", "sa", "s", "r", "l", "romania"}


def normalize_company_name(name):
    """Normalize a company name for strict employer matching."""
    cleaned = re.sub(r"[^a-z0-9]+", " ", (name or "").casefold())
    tokens = [t for t in cleaned.split() if t not in _LEGAL_SUFFIXES]
    return " ".join(tokens)


def is_same_company(found_name, target_name):
    """Return True only when the listing employer clearly matches the target company."""
    norm_found = normalize_company_name(found_name)
    norm_target = normalize_company_name(target_name)
    if not norm_found or not norm_target:
        return False
    return norm_found == norm_target or norm_target in norm_found


def _parse_api_jobs(payload, target_company):
    """Extract matching jobs from eJobs JSON API response."""
    jobs = []
    seen = set()
    items = []
    if isinstance(payload, dict):
        items = payload.get("jobs") or payload.get("data") or payload.get("items") or []
    elif isinstance(payload, list):
        items = payload

    for item in items:
        if not isinstance(item, dict):
            continue
        company_obj = item.get("company")
        employer = (
            company_obj.get("name")
            if isinstance(company_obj, dict)
            else str(company_obj or item.get("companyName") or "")
        )
        if not is_same_company(employer, target_company):
            continue

        title = (item.get("title") or "").strip()
        slug = item.get("slug") or ""
        job_id = item.get("id")
        raw_url = item.get("url") or (f"/user/locuri-de-munca/{slug}/{job_id}" if slug and job_id else "")
        if not title or not raw_url:
            continue

        full_url = urljoin(BASE_URL, raw_url).split("?")[0]
        if full_url in seen:
            continue
        seen.add(full_url)

        locations = []
        for loc in item.get("locations") or []:
            if isinstance(loc, dict) and loc.get("name"):
                locations.append(str(loc["name"]).strip())
            elif isinstance(loc, str) and loc.strip():
                locations.append(loc.strip())

        job = {"url": full_url, "title": title, "source": "eJobs"}
        if locations:
            job["location"] = locations
        if item.get("creationDate"):
            job["date"] = str(item["creationDate"])
        jobs.append(job)

    return jobs


def _parse_html_jsonld(page_html, target_company):
    """Extract JobPosting JSON-LD entries from eJobs HTML search page."""
    soup = BeautifulSoup(page_html or "", "html.parser")
    jobs = []
    seen = set()

    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        raw_text = (script.string or script.get_text() or "").strip()
        if not raw_text:
            continue
        try:
            data = json.loads(raw_text)
        except json.JSONDecodeError:
            continue

        entries = data if isinstance(data, list) else [data]
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            if entry.get("@type") == "ItemList":
                entries.extend(
                    el.get("item", el) for el in (entry.get("itemListElement") or []) if isinstance(el, dict)
                )
                continue
            if entry.get("@type") != "JobPosting":
                continue

            org = entry.get("hiringOrganization")
            employer = org.get("name") if isinstance(org, dict) else str(org or "")
            if not is_same_company(employer, target_company):
                continue

            title = (entry.get("title") or "").strip()
            url = (entry.get("url") or "").split("?")[0].strip()
            if not title or not url or url in seen:
                continue
            seen.add(url)

            job = {"url": url, "title": title, "source": "eJobs"}
            loc = entry.get("jobLocation")
            if isinstance(loc, dict):
                addr = loc.get("address") or {}
                city = addr.get("addressLocality") if isinstance(addr, dict) else None
                if city:
                    job["location"] = [str(city).strip()]
            if entry.get("datePosted"):
                job["date"] = str(entry["datePosted"])
            jobs.append(job)

    return jobs


def search_ejobs(company_name):
    """Search eJobs.ro for open positions matching company_name."""
    query = normalize_company_name(company_name)
    if not query:
        return []

    # 1. Try JSON API first
    try:
        res = requests.get(
            API_SEARCH_URL,
            params={"page": 1, "pageSize": 25, "filters.query": query},
            headers=HEADERS,
            timeout=TIMEOUT,
        )
        if res.ok:
            jobs = _parse_api_jobs(res.json(), company_name)
            if jobs:
                return jobs
    except Exception as exc:
        print(f"[eJobs] Warning: API query failed for '{query}': {exc}")

    # 2. Fallback to HTML search page JSON-LD
    try:
        slug = quote_plus(query.replace(" ", "-"))
        res = requests.get(f"{BASE_URL}/locuri-de-munca/{slug}", headers=HEADERS, timeout=TIMEOUT)
        if res.ok:
            return _parse_html_jsonld(res.text, company_name)
    except Exception as exc:
        print(f"[eJobs] Warning: HTML query failed for '{query}': {exc}")

    return []
