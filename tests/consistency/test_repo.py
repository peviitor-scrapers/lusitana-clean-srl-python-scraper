import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent

REQUIRED_FILES = [
    "README.md",
    "LICENSE",
    "CHANGELOG.md",
    "CODE_OF_CONDUCT.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "requirements.txt",
    "pytest.ini",
    ".gitignore",
    "scraper/index.py",
    "scraper/api.py",
    "scraper/anaf.py",
    "scraper/ejobs.py",
    "scraper/jobrapid.py",
    "scraper/company.py",
    "scraper/job_validator.py",
    "scraper/validate_jobs.py",
    "scraper/markdown_generator.py",
    "scraper/config/company.json",
    "scraper/config/scraper.json",
    "docs/index.html",
    "docs/company.json",
    "docs/jobs.md",
    ".github/workflows/job-seeker-ro-spider.yml",
    ".github/workflows/automation-testing.yml",
    ".github/workflows/job-deep-validate.yml",
    ".github/workflows/job-recovery-from-disaster.yml",
]


def test_required_files_exist():
    missing = [f for f in REQUIRED_FILES if not (REPO_ROOT / f).exists()]
    assert not missing, f"Missing required repository files: {missing}"
