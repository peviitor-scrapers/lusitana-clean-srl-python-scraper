from scraper.config import company_config, scraper_config


def test_company_config_fields():
    assert company_config["id"] == "39167242"
    assert company_config["company"] == "LUSITANA CLEAN S.R.L."
    assert company_config["status"] in {"activ", "suspendat", "inactiv", "radiat"}
    assert "https://www.lusitana.ro" in company_config["website"]


def test_scraper_config_fields():
    assert scraper_config["apiBase"] == "https://api.peviitor.ro/v1"
    assert scraper_config["jobDetailsPrefix"].startswith("https://mediere.anofm.ro/")
