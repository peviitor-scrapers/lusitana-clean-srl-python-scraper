from unittest.mock import MagicMock, patch

from scraper.anaf import search_anofm
from scraper.ejobs import is_same_company, search_ejobs
from scraper.jobrapid import extract_company_hrefs, parse_job_detail


def test_search_anofm_parses_rows():
    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = {
        "rows": [
            {
                "id": 55501,
                "occupation": "Agent de curățenie",
                "address_locality_name": "NEAMT > PIATRA-NEAMT",
                "created_at": "2026-11-20",
            }
        ]
    }
    with patch("scraper.anaf.requests.post", return_value=mock_resp):
        jobs = search_anofm("39167242")
    assert len(jobs) == 1
    assert jobs[0]["url"] == "https://mediere.anofm.ro/app/module/mediere/job/55501"
    assert jobs[0]["title"] == "Agent de curățenie"
    assert jobs[0]["location"] == ["PIATRA-NEAMT"]


def test_ejobs_strict_company_matching():
    assert is_same_company("LUSITANA CLEAN S.R.L.", "LUSITANA CLEAN S.R.L.")
    assert is_same_company("Lusitana Clean", "LUSITANA CLEAN S.R.L.")
    assert not is_same_company("Lusitania Travel SRL", "LUSITANA CLEAN S.R.L.")


def test_search_ejobs_filters_unrelated_companies():
    mock_resp = MagicMock()
    mock_resp.ok = True
    mock_resp.json.return_value = {
        "jobs": [
            {
                "id": 101,
                "slug": "agent-curatenie",
                "title": "Agent Curățenie",
                "company": {"name": "LUSITANA CLEAN S.R.L."},
                "locations": [{"name": "Piatra Neamț"}],
            },
            {
                "id": 102,
                "slug": "sofer",
                "title": "Șofer",
                "company": {"name": "OTHER COMPANY SRL"},
                "locations": [{"name": "București"}],
            },
        ]
    }
    with patch("scraper.ejobs.requests.get", return_value=mock_resp):
        jobs = search_ejobs("LUSITANA CLEAN S.R.L.")
    assert len(jobs) == 1
    assert jobs[0]["url"] == "https://www.ejobs.ro/user/locuri-de-munca/agent-curatenie/101"


def test_jobrapid_extract_and_parse():
    list_html = (
        '<div class="container_lista_continut" data-company="LUSITANA CLEAN S.R.L." '
        'data-href="/locuri-de-munca/agent-1.html"></div>'
        '<div class="container_lista_continut" data-company="ALTCEVA SRL" '
        'data-href="/locuri-de-munca/other-2.html"></div>'
    )
    hrefs = extract_company_hrefs(list_html, "LUSITANA CLEAN S.R.L.")
    assert hrefs == ["/locuri-de-munca/agent-1.html"]

    detail_html = (
        '<script type="application/ld+json">'
        '{"@type":"JobPosting","title":"Agent curățenie","datePosted":"2026-11-20",'
        '"jobLocation":{"address":{"addressLocality":"Piatra Neamț"}}}'
        "</script>"
    )
    parsed = parse_job_detail(detail_html, "https://www.jobrapid.ro/locuri-de-munca/agent-1.html")
    assert parsed["title"] == "Agent curățenie"
    assert parsed["location"] == ["Piatra Neamț"]
