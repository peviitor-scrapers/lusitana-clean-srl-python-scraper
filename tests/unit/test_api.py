from unittest.mock import MagicMock, patch

from scraper.api import get_company_by_cif, pad_cif, upsert_jobs


def test_pad_cif():
    assert pad_cif("39167242") == "39167242"
    assert pad_cif("3213771") == "03213771"


def test_get_company_by_cif():
    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = {
        "success": True,
        "data": [{"id": "39167242", "company": "LUSITANA CLEAN S.R.L."}],
    }
    with patch("scraper.api.requests.get", return_value=mock_resp):
        company = get_company_by_cif("39167242")
    assert company["id"] == "39167242"
    assert company["company"] == "LUSITANA CLEAN S.R.L."


def test_upsert_jobs_empty_returns_zero():
    result = upsert_jobs([])
    assert result["count"] == 0
