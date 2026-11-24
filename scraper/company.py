"""
Company Validation Module

Cross-validates company identity between local config, ANAF/CUIscan, and Peviitor Core.
"""

from .anaf import get_company_from_anaf_with_fallback
from .api import get_company_by_cif
from .config import company_config


def validate_and_get_company():
    """Return verified company metadata dict (id, company, brand, status, location, etc.)."""
    cif = str(company_config["id"]).strip()
    verified = dict(company_config)

    # 1. Cross-check with ANAF/CUIscan (non-fatal if external service is temporarily down)
    anaf_data = get_company_from_anaf_with_fallback(cif)
    if anaf_data and anaf_data.get("company"):
        verified["company"] = anaf_data["company"]

    # 2. Cross-check with Peviitor Core
    try:
        core_company = get_company_by_cif(cif)
        if core_company and core_company.get("company"):
            verified["company"] = core_company["company"]
            verified["_exists_in_core"] = True
        else:
            verified["_exists_in_core"] = False
    except Exception as exc:
        print(f"[Company] Warning: Peviitor Core check failed for CIF {cif}: {exc}")
        verified["_exists_in_core"] = False

    return verified
