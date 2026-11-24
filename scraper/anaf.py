"""
ANAF & ANOFM Data Module

- search_anofm(cif): Queries ANOFM (mediere.anofm.ro) for public job postings by employer CIF.
- get_company_from_anaf_with_fallback(cif): Validates company metadata via CUIscan / demoanaf
  with a 7-day local JSON cache and graceful fallback.
"""

import datetime
import json
import pathlib
import time

import requests

ANOFM_API_URL = "https://mediere.anofm.ro/api/entity/vw_public_job_posting"
ANOFM_JOB_PREFIX = "https://mediere.anofm.ro/app/module/mediere/job/"
CUISCAN_API_URL = "https://cuiscan.ro/api.php"
ANAF_API_URL = "https://demoanaf.ro/api/company/"

HEADERS = {"User-Agent": "job_seeker_ro_spider"}
TIMEOUT = 15
CACHE_TTL_SECONDS = 7 * 24 * 3600
CACHE_FILE = pathlib.Path(__file__).resolve().parent / "anaf_cache.json"


def _read_cache():
    if CACHE_FILE.exists():
        try:
            return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def _write_cache(cache):
    try:
        CACHE_FILE.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError:
        pass


def search_anofm(cif):
    """Query ANOFM public job postings API for a given employer CIF (digits only)."""
    clean_cif = str(int(str(cif).strip()))
    payload = {
        "current": 1,
        "rowCount": 250,
        "sort": {"created_at": "desc"},
        "employer_tax_code": clean_cif,
    }
    try:
        res = requests.post(
            ANOFM_API_URL,
            json=payload,
            headers={**HEADERS, "Content-Type": "application/json"},
            timeout=TIMEOUT,
        )
        res.raise_for_status()
        data = res.json()
    except Exception as exc:
        print(f"[ANOFM] Warning: request failed for CIF {clean_cif}: {exc}")
        return []

    jobs = []
    for row in data.get("rows") or []:
        job_id = row.get("id")
        title = (row.get("occupation") or "").strip()
        if not job_id or not title:
            continue

        loc_raw = (row.get("address_locality_name") or "").strip()
        loc_parts = [p.strip() for p in loc_raw.split(">") if p.strip()]
        location = [loc_parts[-1]] if loc_parts else []

        job = {
            "url": f"{ANOFM_JOB_PREFIX}{job_id}",
            "title": title,
            "source": "ANOFM",
        }
        if location:
            job["location"] = location
        if row.get("created_at"):
            job["date"] = str(row["created_at"])
        jobs.append(job)

    return jobs


def get_company_from_anaf(cif):
    """Fetch company details from cuiscan.ro, falling back to demoanaf.ro."""
    clean_cif = str(int(str(cif).strip()))
    errors = []

    for url, params in [
        (CUISCAN_API_URL, {"cui": clean_cif}),
        (f"{ANAF_API_URL}{clean_cif}", None),
    ]:
        try:
            res = requests.get(url, params=params, headers=HEADERS, timeout=10)
            res.raise_for_status()
            data = res.json()
            if isinstance(data, dict) and not data.get("error"):
                name = (
                    data.get("denumire")
                    or data.get("company")
                    or data.get("name")
                    or (data.get("data") or {}).get("denumire")
                )
                if name:
                    return {
                        "id": str(cif).strip(),
                        "company": str(name).strip().upper(),
                        "status": "activ",
                        "fetched_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    }
        except Exception as exc:
            errors.append(f"{url}: {exc}")

    raise RuntimeError(f"ANAF/CUIscan lookup failed for CIF {clean_cif}: {'; '.join(errors)}")


def get_company_from_anaf_with_fallback(cif):
    """Return ANAF/CUIscan company info using a 7-day cache and stale-cache fallback."""
    key = str(cif).strip()
    cache = _read_cache()
    cached = cache.get(key)

    if cached and (time.time() - cached.get("_cached_ts", 0)) < CACHE_TTL_SECONDS:
        return cached

    try:
        fresh = get_company_from_anaf(key)
        fresh["_cached_ts"] = time.time()
        cache[key] = fresh
        _write_cache(cache)
        return fresh
    except Exception as exc:
        if cached:
            print(f"[ANAF] Using stale cache for CIF {key} ({exc})")
            return cached
        print(f"[ANAF] Warning: lookup unavailable for CIF {key} ({exc})")
        return None
