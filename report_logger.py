"""
Appends a post result entry to post_reports.json after each run.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

REPORTS_FILE = Path(__file__).parent / "post_reports.json"


def log_report(
    series: str,
    folder: str,
    image_file: str | None,
    post_date: str,
    json_post_matched: bool,
    status: str,
    error: str | None = None,
):
    reports = []
    if REPORTS_FILE.exists():
        with open(REPORTS_FILE) as f:
            reports = json.load(f)

    reports.append({
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "date_posted": post_date,
        "image_file": image_file or "None",
        "folder": folder,
        "json_post_verified": "Yes" if json_post_matched else "No",
        "status": status,
        "error": error or "",
        "series": series,
    })

    with open(REPORTS_FILE, "w") as f:
        json.dump(reports, f, indent=2)
