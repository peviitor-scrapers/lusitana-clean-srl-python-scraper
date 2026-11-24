"""
jobRapid.ro Job Source Module

Searches jobRapid.ro for postings published by a specific company and extracts
ONLY title, canonical job URL, location, and posting date from JobPosting JSON-LD
(strictly GDPR-compliant: no job description text, no personal data).
"""

import html
import json
import re
from urllib.parse import urljoin

import requests

BASE_URL = "https://www.jobrapid.ro"
SEARCH_URL = f"{BASE_URL}/angajare"
HEADERS = {"User-Agent": "job_seeker_ro_spider"}
TIMEOUT = 15

_CARD_RE = re.compile(r"<div class=['\"]container_lista_continut[^'\"]*['\"]([^>]*)>", re.S)
_COMPANY_RE = re.compile(r"data-company=['\"]([^'\"]*)['\"]")
_HREF_RE = re.compile(r"data-href=['\"]([^'\"]*)['\"]")
_JSONLD_RE = re.compile(
    r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
    re.S | re.I,
)


def _normalize_name(name):
    cleaned = re.sub(r"[^a-z0-9]+", " ", (name or "").casefold())
    tokens = [t for t in cleaned.split() if t not in {"srl", "sa", "s", "r", "l"}]
    return " ".join(tokens)


def _same_company(card_name, company_name):
    norm_card = _normalize_name(card_name)
    norm_target = _normalize_name(company_name)
    return bool(norm_card and norm_target and norm_card == norm_target)


def extract_company_hrefs(page_html, company_name):
    """Extract job detail hrefs whose data-company strictly matches company_name."""
    hrefs = []
    seen = set()
    for match in _CARD_RE.finditer(page_html or ""):
        attrs = match.group(1)
        company_match = _COMPANY_RE.search(attrs)
        href_match = _HREF_RE.search(attrs)
        if not company_match or not href_match:
            continue
        if not _same_company(html.unescape(company_match.group(1)), company_name):
            continue
        href = html.unescape(href_match.group(1))
        if href and href not in seen:
            seen.add(href)
            hrefs.append(href)
    return hrefs


def parse_job_detail(detail_html, job_url):
    """Parse JobPosting JSON-LD from a jobRapid detail page (title, url, location, date only)."""
    for match in _JSONLD_RE.finditer(detail_html or ""):
        try:
            data = json.loads(match.group(1))
        except json.JSONDecodeError:
            continue
        entries = data if isinstance(data, list) else [data]
        for entry in entries:
            if not isinstance(entry, dict) or entry.get("@type") != "JobPosting":
                continue
            title = (entry.get("title") or "").strip()
            if not title:
                continue
            job = {"url": job_url.split("?")[0], "title": title, "source": "jobRapid"}
            loc = entry.get("jobLocation")
            if isinstance(loc, dict):
                addr = loc.get("address") or {}
                city = addr.get("addressLocality") if isinstance(addr, dict) else None
                if city:
                    job["location"] = [str(city).strip()]
            if entry.get("datePosted"):
                job["date"] = str(entry["datePosted"])
            return job
    return None


def search_jobrapid(company_name):
    """Search jobRapid.ro for active job postings matching company_name."""
    query = _normalize_name(company_name)
    if not query:
        return []

    try:
        res = requests.get(SEARCH_URL, params={"q": query}, headers=HEADERS, timeout=TIMEOUT)
        res.raise_for_status()
    except Exception as exc:
        print(f"[jobRapid] Warning: search failed for '{query}': {exc}")
        return []

    jobs = []
    for href in extract_company_hrefs(res.text, company_name):
        detail_url = urljoin(BASE_URL, href).split("?")[0]
        try:
            detail_res = requests.get(detail_url, headers=HEADERS, timeout=TIMEOUT)
            detail_res.raise_for_status()
            parsed = parse_job_detail(detail_res.text, detail_url)
            if parsed:
                jobs.append(parsed)
        except Exception as exc:
            print(f"[jobRapid] Warning: detail fetch failed for {detail_url}: {exc}")

    return jobs
