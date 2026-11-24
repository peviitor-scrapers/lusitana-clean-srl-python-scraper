"""
Markdown & Docs Generator Module

Generates docs/jobs.md and updates docs/company.json for GitHub Pages presentation.
"""

import datetime
import json
import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
DOCS_DIR = REPO_ROOT / "docs"


def generate_jobs_markdown(jobs, company_info):
    """Write docs/jobs.md and docs/company.json from the latest scrape run."""
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    now_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    company_name = company_info.get("company", "LUSITANA CLEAN S.R.L.")
    cif = company_info.get("id", "39167242")

    lines = [
        f"# {company_name} — Active Jobs",
        "",
        f"- **CIF/CUI:** `{cif}`",
        f"- **Last updated:** {now_str}",
        f"- **Active jobs found:** {len(jobs)}",
        "",
    ]

    if jobs:
        lines.extend([
            "| # | Job Title | Location | Link |",
            "|---|-----------|----------|------|",
        ])
        for idx, job in enumerate(jobs, start=1):
            title = job.get("title", "").replace("|", "\\|")
            loc = ", ".join(job.get("location") or ["România"])
            url = job.get("url", "")
            lines.append(f"| {idx} | {title} | {loc} | [Apply]({url}) |")
    else:
        lines.append("_No active job postings currently found on ANOFM, eJobs, or jobRapid._")

    lines.append("")
    (DOCS_DIR / "jobs.md").write_text("\n".join(lines), encoding="utf-8")

    public_company = {k: v for k, v in company_info.items() if not k.startswith("_")}
    public_company["lastScraped"] = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    (DOCS_DIR / "company.json").write_text(
        json.dumps(public_company, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
