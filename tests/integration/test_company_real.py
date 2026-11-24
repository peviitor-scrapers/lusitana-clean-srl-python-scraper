from scraper.api import get_company_by_cif
from scraper.config import company_config


def test_company_exists_in_peviitor_core():
    company = get_company_by_cif(company_config["id"])
    assert company is not None, "LUSITANA CLEAN S.R.L. (39167242) must exist in Peviitor Core"
    assert company["id"] == "39167242"
    assert "LUSITANA" in company["company"].upper()
