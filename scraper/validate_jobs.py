"""
Post-Scrape Validation Script

Checks jobs currently indexed in Peviitor for LUSITANA CLEAN S.R.L. (CIF 39167242)
and verifies that their URLs are still reachable (HTTP < 400).
"""

import sys

import requests

from .api import delete_job_by_url, query_solr
from .config import company_config

HEADERS = {"User-Agent": "job_seeker_ro_spider"}


def validate_indexed_jobs(delete_expired=False):
    cif = str(company_config["id"])
    indexed = query_solr(cif)
    print(f"[Validate] Found {len(indexed)} indexed jobs in Peviitor for CIF {cif}")

    expired = []
    for doc in indexed:
        url = doc.get("url")
        if not url:
            continue
        try:
            res = requests.head(url, headers=HEADERS, timeout=10, allow_redirects=True)
            if res.status_code >= 400:
                expired.append(url)
        except Exception:
            expired.append(url)

    print(f"[Validate] Expired/unreachable URLs: {len(expired)}")
    if delete_expired:
        for url in expired:
            print(f"[Validate] Deleting expired job: {url}")
            delete_job_by_url(url)

    return {"indexed": len(indexed), "expired": len(expired)}


if __name__ == "__main__":
    delete_flag = "--delete-expired" in sys.argv
    validate_indexed_jobs(delete_expired=delete_flag)
