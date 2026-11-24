from scraper.job_validator import clean_url, validate_job, validate_jobs


def test_clean_url_strips_tracking_params():
    raw = "https://www.ejobs.ro/user/locuri-de-munca/agent-curatenie/12345?utm_source=google&fbclid=abc"
    assert clean_url(raw) == "https://www.ejobs.ro/user/locuri-de-munca/agent-curatenie/12345"


def test_clean_url_rejects_unescaped_ampersand_and_generic_paths():
    assert clean_url("https://example.com/job?a=1&b=2") == ""
    assert clean_url("https://www.lusitana.ro/") == ""
    assert clean_url("https://example.com/careers") == ""
    assert clean_url("https://bit.ly/3xyz") == ""


def test_validate_job_enforces_gdpr_and_required_fields():
    raw = {
        "url": "https://mediere.anofm.ro/app/module/mediere/job/99999",
        "title": "Agent de curățenie",
        "company": "LUSITANA CLEAN S.R.L.",
        "cif": "39167242",
        "location": ["Piatra Neamț"],
        "description": "MUST BE STRIPPED FOR GDPR",
        "candidate_email": "secret@example.com",
    }
    cleaned = validate_job(raw)
    assert cleaned is not None
    assert cleaned["title"] == "Agent de curățenie"
    assert "description" not in cleaned
    assert "candidate_email" not in cleaned


def test_validate_job_rejects_placeholders_and_deduplicates():
    jobs = [
        {"url": "https://mediere.anofm.ro/app/module/mediere/job/1", "title": "N/A", "company": "LUSITANA CLEAN S.R.L.", "cif": "39167242"},
        {"url": "https://mediere.anofm.ro/app/module/mediere/job/2", "title": "Agent curățenie", "company": "LUSITANA CLEAN S.R.L.", "cif": "39167242"},
        {"url": "https://mediere.anofm.ro/app/module/mediere/job/2", "title": "Agent curățenie", "company": "LUSITANA CLEAN S.R.L.", "cif": "39167242"},
    ]
    valid = validate_jobs(jobs)
    assert len(valid) == 1
    assert valid[0]["url"].endswith("/2")
