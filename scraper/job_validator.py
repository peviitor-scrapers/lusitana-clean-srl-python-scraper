"""
Job Validation & GDPR Data Minimization Module

Enforces peviitor.ro data model, URL hygiene, and GDPR rules:
- Mandatory fields: url, title, company, cif
- Rejects placeholder titles and titles shorter than 3 characters
- Strips tracking query params and rejects URLs containing unescaped '&'
- Rejects tracking redirector hosts and generic career homepages
- Whitelists ONLY allowed non-personal fields (no descriptions, CVs, or personal data)
"""

from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

ALLOWED_FIELDS = {
    "url",
    "title",
    "company",
    "cif",
    "location",
    "workmode",
    "tags",
    "date",
    "status",
    "expirationdate",
    "salary",
}

PLACEHOLDER_TITLES = {
    "n/a",
    "na",
    "-",
    "--",
    "nespecificat",
    "fara titlu",
    "untitled",
    "job",
    "post",
}

TRACKING_HOSTS = {
    "bit.ly",
    "t.co",
    "tinyurl.com",
    "jobviewtrack.com",
    "goo.gl",
}

TRACKING_PARAMS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "fbclid",
    "gclid",
    "ref",
    "source",
}

GENERIC_PATHS = {
    "",
    "/",
    "/careers",
    "/careers/",
    "/cariere",
    "/cariere/",
    "/jobs",
    "/jobs/",
    "/angajari",
    "/angajari/",
}


def clean_url(raw_url):
    """Strip tracking query parameters and normalize whitespace."""
    if not raw_url or not isinstance(raw_url, str):
        return ""
    parsed = urlparse(raw_url.strip())
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return ""

    host = parsed.netloc.lower()
    if host in TRACKING_HOSTS:
        return ""
    if parsed.path.lower() in GENERIC_PATHS and not parsed.query:
        return ""

    filtered_qs = [
        (k, v) for k, v in parse_qsl(parsed.query, keep_blank_values=False)
        if k.lower() not in TRACKING_PARAMS
    ]
    cleaned = urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        "",
        urlencode(filtered_qs),
        "",
    ))

    # Peviitor upload API runs htmlspecialchars(), turning '&' into '&amp;'
    if "&" in cleaned:
        return ""
    return cleaned


def validate_job(job):
    """Validate and sanitize a single job dict. Returns cleaned job or None if invalid."""
    if not isinstance(job, dict):
        return None

    title = (job.get("title") or "").strip()
    if len(title) < 3 or title.casefold() in PLACEHOLDER_TITLES:
        return None

    url = clean_url(job.get("url"))
    if not url:
        return None

    company = (job.get("company") or "").strip()
    cif = str(job.get("cif") or "").strip()
    if not company or not cif.isdigit() or not (2 <= len(cif) <= 10):
        return None

    sanitized = {
        "url": url,
        "title": title,
        "company": company,
        "cif": cif,
    }
    for key in ALLOWED_FIELDS - {"url", "title", "company", "cif"}:
        val = job.get(key)
        if val not in (None, "", []):
            sanitized[key] = val

    return sanitized


def validate_jobs(jobs):
    """Validate and deduplicate a list of jobs by canonical URL."""
    valid = []
    seen_urls = set()
    for job in jobs:
        cleaned = validate_job(job)
        if cleaned and cleaned["url"] not in seen_urls:
            seen_urls.add(cleaned["url"])
            valid.append(cleaned)
    return valid
