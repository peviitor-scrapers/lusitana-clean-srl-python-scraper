[![Oportunitati si Cariere](https://github.com/peviitor-scrapers/lusitana-clean-srl-python-scraper/actions/workflows/job-seeker-ro-spider.yml/badge.svg)](https://github.com/peviitor-scrapers/lusitana-clean-srl-python-scraper/actions/workflows/job-seeker-ro-spider.yml)
[![Automation Tests](https://github.com/peviitor-scrapers/lusitana-clean-srl-python-scraper/actions/workflows/automation-testing.yml/badge.svg)](https://github.com/peviitor-scrapers/lusitana-clean-srl-python-scraper/actions/workflows/automation-testing.yml)
[![Version](https://img.shields.io/badge/version-1.0.0-blue)](CHANGELOG.md)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.12+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Website](https://img.shields.io/website?url=https%3A%2F%2Fpeviitor.ro&label=peviitor.ro)](https://peviitor.ro)
[![API](https://img.shields.io/website?url=https%3A%2F%2Fapi.peviitor.ro%2F&label=api.peviitor.ro)](https://api.peviitor.ro/)

# job_seeker_ro_spider — LUSITANA CLEAN S.R.L. Scraper

**job_seeker_ro_spider** — a Python scraper for **LUSITANA CLEAN S.R.L.** (CIF/CUI: `39167242`) jobs in Romania.

Because [lusitana.ro](https://www.lusitana.ro) does not host a dedicated careers page, this scraper searches public Romanian job platforms for announcements published by **LUSITANA CLEAN S.R.L.** and publishes them to [peviitor.ro](https://peviitor.ro) via the Peviitor v1 API:

- **[ANOFM](https://mediere.anofm.ro/app/module/mediere/jobs)** — queried by CIF (`39167242`)
- **[eJobs](https://www.ejobs.ro/)** — queried by company name (`LUSITANA CLEAN`), strictly matched
- **[jobRapid](https://www.jobrapid.ro/)** — queried by company name (`LUSITANA CLEAN`), strictly matched

## GDPR & Data Minimization

This scraper strictly follows [peviitor.ro GDPR guidelines](https://github.com/peviitor-ro/scraper-doc/blob/main/16-gdpr-data-minimization.md):
- Captures **only** job title, canonical job URL, company name, CIF/CUI, and optional non-personal fields (location, posting date, salary when explicitly provided).
- **Never** captures job description text, CVs, or candidate/applicant personal data.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Dry run (fetch & validate without uploading to peviitor.ro)
python -m scraper.index --dry-run

# Live run (fetch, validate, sync with Peviitor API, and regenerate docs/jobs.md)
python -m scraper.index

# Run automated tests
pytest -v
```

## Project Structure

```text
lusitana-clean-srl-python-scraper/
├── scraper/
│   ├── config/
│   │   ├── company.json          # Verified company identity (CIF 39167242)
│   │   └── scraper.json          # API base & job detail prefixes
│   ├── anaf.py                   # ANOFM job search + ANAF/CUIscan company lookup
│   ├── ejobs.py                  # eJobs job search (strict company match)
│   ├── jobrapid.py               # jobRapid job search (strict company match)
│   ├── api.py                    # Peviitor v1 API client
│   ├── company.py                # Company cross-validation (ANAF + Peviitor Core)
│   ├── job_validator.py          # URL hygiene, title & GDPR validation
│   ├── markdown_generator.py     # Generates docs/jobs.md & docs/company.json
│   ├── validate_jobs.py          # Post-upload verification & stale-job check
│   └── index.py                  # Main orchestrator (--dry-run supported)
├── tests/                        # Unit, integration, and consistency tests
├── docs/                         # GitHub Pages presentation & generated job list
└── .github/workflows/            # Daily scrape, automated tests, deep validation & recovery
```
