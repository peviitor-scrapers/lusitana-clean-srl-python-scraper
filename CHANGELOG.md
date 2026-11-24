# Changelog

All notable changes to this project will be documented in this file.

## [1.0.0] - 2026-11-23

### Added
- Initial Python scraper for **LUSITANA CLEAN S.R.L.** (CIF `39167242`).
- Multi-source job discovery via ANOFM (by CIF), eJobs, and jobRapid.
- Company verification against ANAF/CUIscan and Peviitor Core.
- GDPR-compliant job validation, URL hygiene checks, and audit trail (`data/state.json`, `data/uploaded_urls.txt`).
- Automated unit, integration, and repository consistency tests (`pytest`).
- GitHub Pages presentation (`docs/`) and GitHub Actions workflows (daily scrape, tests, deep validation, disaster recovery).
