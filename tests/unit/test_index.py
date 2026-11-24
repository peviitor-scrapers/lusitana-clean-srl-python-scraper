from unittest.mock import patch

from scraper.index import run


def test_run_dry_run_handles_zero_jobs(tmp_path, monkeypatch):
    monkeypatch.setattr("scraper.index.DATA_DIR", tmp_path)
    monkeypatch.setattr("scraper.index.STATE_FILE", tmp_path / "state.json")
    monkeypatch.setattr("scraper.index.UPLOADED_FILE", tmp_path / "uploaded_urls.txt")
    monkeypatch.setattr("scraper.markdown_generator.DOCS_DIR", tmp_path / "docs")

    company_stub = {
        "id": "39167242",
        "company": "LUSITANA CLEAN S.R.L.",
        "brand": "Lusitana",
        "status": "activ",
    }

    with patch("scraper.index.validate_and_get_company", return_value=company_stub), \
         patch("scraper.index.search_anofm", return_value=[]), \
         patch("scraper.index.search_ejobs", return_value=[]), \
         patch("scraper.index.search_jobrapid", return_value=[]):
        state = run(dry_run=True)

    assert state["cif"] == "39167242"
    assert state["fetched"] == 0
    assert state["uploaded"] == 0
    assert state["dry_run"] is True
    assert (tmp_path / "state.json").exists()
    assert (tmp_path / "docs" / "jobs.md").exists()
