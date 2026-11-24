"""
LUSITANA CLEAN S.R.L. Scraper — Main Entrypoint

Collects job postings for LUSITANA CLEAN S.R.L. (CIF 39167242) from:
1. ANOFM (mediere.anofm.ro) by CIF
2. eJobs (ejobs.ro) by strict company name match
3. jobRapid (jobrapid.ro) by strict company name match

GDPR-compliant: captures ONLY title, canonical job URL, company name, CIF,
and optional non-personal fields (location, date, salary).
"""

import argparse
import datetime
import json
import pathlib

from .anaf import search_anofm
from .api import delete_job_by_url, query_solr, upsert_company, upsert_jobs
from .company import validate_and_get_company
from .config import company_config
from .ejobs import search_ejobs
from .job_validator import validate_jobs
from .jobrapid import search_jobrapid
from .markdown_generator import generate_jobs_markdown

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"
STATE_FILE = DATA_DIR / "state.json"
UPLOADED_FILE = DATA_DIR / "uploaded_urls.txt"


def map_to_job_model(raw_job, cif, company_name):
    """Map a raw scraped job dict to the Peviitor job model schema."""
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    job = {
        "url": raw_job.get("url"),
        "title": raw_job.get("title"),
        "company": company_name,
        "cif": str(cif).strip(),
        "date": raw_job.get("date") or now,
        "status": "scraped",
    }
    if raw_job.get("location"):
        job["location"] = raw_job["location"]
    if raw_job.get("workmode"):
        job["workmode"] = raw_job["workmode"]
    if raw_job.get("salary"):
        job["salary"] = raw_job["salary"]
    return job


def fetch_all_jobs(cif, company_name):
    """Fetch raw jobs from all configured external sources."""
    raw = []
    anofm_jobs = search_anofm(cif)
    print(f"[Scraper] ANOFM jobs found: {len(anofm_jobs)}")
    raw.extend(anofm_jobs)

    ejobs_jobs = search_ejobs(company_name)
    print(f"[Scraper] eJobs jobs found: {len(ejobs_jobs)}")
    raw.extend(ejobs_jobs)

    jobrapid_jobs = search_jobrapid(company_name)
    print(f"[Scraper] jobRapid jobs found: {len(jobrapid_jobs)}")
    raw.extend(jobrapid_jobs)

    return raw


def _append_uploaded_urls(urls):
    if not urls:
        return
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    existing = set()
    if UPLOADED_FILE.exists():
        existing = set(UPLOADED_FILE.read_text(encoding="utf-8").splitlines())
    new_urls = [u for u in urls if u not in existing]
    if new_urls:
        with UPLOADED_FILE.open("a", encoding="utf-8") as fh:
            for u in new_urls:
                fh.write(f"{u}\n")


def _save_state(state):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def run(dry_run=False):
    """Execute a full scrape, validation, sync, and docs generation cycle."""
    company_info = validate_and_get_company()
    cif = str(company_info["id"]).strip()
    company_name = company_info["company"]
    print(f"[Scraper] Starting run for {company_name} (CIF: {cif}) | dry_run={dry_run}")

    raw_jobs = fetch_all_jobs(cif, company_name)
    mapped = [map_to_job_model(j, cif, company_name) for j in raw_jobs]
    valid_jobs = validate_jobs(mapped)
    print(f"[Scraper] Valid unique jobs: {len(valid_jobs)}")

    uploaded_count = 0
    deleted_count = 0

    if not dry_run:
        # 1. Remove stale jobs currently in Peviitor that are no longer active
        current_urls = {j["url"] for j in valid_jobs}
        try:
            existing_docs = query_solr(cif)
            for doc in existing_docs:
                old_url = doc.get("url")
                if old_url and old_url not in current_urls:
                    delete_job_by_url(old_url)
                    deleted_count += 1
        except Exception as exc:
            print(f"[Scraper] Warning: stale-job cleanup skipped ({exc})")

        # 2. Upload active jobs
        if valid_jobs:
            res = upsert_jobs(valid_jobs)
            uploaded_count = int(res.get("count", len(valid_jobs)))
            _append_uploaded_urls([j["url"] for j in valid_jobs[:uploaded_count]])

        # 3. Update company metadata (lastScraped, website, scraperFile) in Peviitor Core
        company_payload = {k: v for k, v in company_info.items() if not k.startswith("_")}
        company_payload["lastScraped"] = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
        try:
            upsert_company(company_payload)
        except Exception as exc:
            print(f"[Scraper] Warning: company upsert failed ({exc})")

    # 4. Update docs/jobs.md & docs/company.json and local state.json
    generate_jobs_markdown(valid_jobs, company_info)
    state = {
        "last_run": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "company": company_name,
        "cif": cif,
        "fetched": len(raw_jobs),
        "valid": len(valid_jobs),
        "uploaded": uploaded_count,
        "deleted_stale": deleted_count,
        "dry_run": dry_run,
    }
    _save_state(state)
    print(
        f"[Scraper] Done: fetched={len(raw_jobs)} valid={len(valid_jobs)} "
        f"uploaded={uploaded_count} deleted_stale={deleted_count} dry_run={dry_run}"
    )
    return state


def main():
    parser = argparse.ArgumentParser(description="LUSITANA CLEAN S.R.L. scraper for peviitor.ro")
    parser.add_argument("--dry-run", action="store_true", help="Fetch and validate without uploading to Peviitor")
    args = parser.parse_args()
    run(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
