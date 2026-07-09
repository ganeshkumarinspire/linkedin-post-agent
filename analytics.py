"""
LinkedIn Post Analytics — fetches likes + comments for all posts
and groups them by series based on hashtags.

Run: python analytics.py
"""

import os
import time
import requests
from dotenv import load_dotenv
from collections import defaultdict

load_dotenv()

ACCESS_TOKEN = os.environ["LINKEDIN_ACCESS_TOKEN"]
PERSON_URN = os.environ["LINKEDIN_PERSON_URN"]

HEADERS = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "X-Restli-Protocol-Version": "2.0.0",
    "Content-Type": "application/json",
}

# Map hashtags to series names
SERIES_HASHTAGS = {
    "50 Days Kanban Journey":       ["#kanban", "#kanbanjourney", "#50dayskanban"],
    "SAFe Learning Series":         ["#safe", "#safescrum", "#safelearning", "#scaledagile"],
    "Scrum Master in Action":       ["#scrummasterinaction", "#scrummaster"],
    "Lessons from My Agile Journey":["#agilejourney", "#lessonslearned", "#agilemindset"],
}


def get_all_posts() -> list[dict]:
    """Fetch all UGC posts for the authenticated member."""
    posts = []
    start = 0
    count = 50

    print("Fetching posts from LinkedIn...")
    while True:
        encoded_urn = requests.utils.quote(PERSON_URN, safe="")
        url = (
            f"https://api.linkedin.com/v2/ugcPosts"
            f"?q=authors&authors=List({encoded_urn})"
            f"&start={start}&count={count}"
        )
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        elements = data.get("elements", [])
        if not elements:
            break

        posts.extend(elements)
        print(f"  Fetched {len(posts)} posts so far...")

        if len(elements) < count:
            break
        start += count
        time.sleep(0.5)

    return posts


def get_post_stats(post_urn: str) -> dict:
    """Get likes and comments count for a single post."""
    stats = {"likes": 0, "comments": 0}

    # Likes (reactions)
    try:
        url = f"https://api.linkedin.com/v2/socialActions/{requests.utils.quote(post_urn, safe='')}/likes?count=0"
        resp = requests.get(url, headers=HEADERS, timeout=10)
        if resp.ok:
            stats["likes"] = resp.json().get("paging", {}).get("total", 0)
    except Exception:
        pass

    # Comments
    try:
        url = f"https://api.linkedin.com/v2/socialActions/{requests.utils.quote(post_urn, safe='')}/comments?count=0"
        resp = requests.get(url, headers=HEADERS, timeout=10)
        if resp.ok:
            stats["comments"] = resp.json().get("paging", {}).get("total", 0)
    except Exception:
        pass

    return stats


def extract_text(post: dict) -> str:
    """Extract post text from UGC post object."""
    try:
        return post["specificContent"]["com.linkedin.ugc.ShareContent"]["shareCommentary"]["text"]
    except (KeyError, TypeError):
        return ""


def classify_post(text: str) -> str:
    """Return series name based on hashtags found in post text."""
    text_lower = text.lower()
    for series, tags in SERIES_HASHTAGS.items():
        for tag in tags:
            if tag.lower() in text_lower:
                return series
    return "Other / Uncategorised"


def run_analytics():
    posts = get_all_posts()
    print(f"\nTotal posts found: {len(posts)}\n")

    series_stats = defaultdict(lambda: {"posts": 0, "likes": 0, "comments": 0})

    for i, post in enumerate(posts):
        post_urn = post.get("id", "")
        text = extract_text(post)
        series = classify_post(text)

        print(f"[{i+1}/{len(posts)}] {series[:40]:<40} — fetching stats...")
        stats = get_post_stats(post_urn)

        series_stats[series]["posts"] += 1
        series_stats[series]["likes"] += stats["likes"]
        series_stats[series]["comments"] += stats["comments"]
        time.sleep(0.3)  # avoid rate limiting

    # Print report
    print("\n" + "="*70)
    print(f"{'SERIES':<40} {'POSTS':>6} {'LIKES':>7} {'COMMENTS':>10} {'ENGAGE':>8}")
    print("="*70)

    total_posts = total_likes = total_comments = 0

    for series in [
        "Lessons from My Agile Journey",
        "50 Days Kanban Journey",
        "SAFe Learning Series",
        "Scrum Master in Action",
        "Other / Uncategorised",
    ]:
        s = series_stats.get(series, {"posts": 0, "likes": 0, "comments": 0})
        engage = s["likes"] + s["comments"]
        print(f"{series:<40} {s['posts']:>6} {s['likes']:>7} {s['comments']:>10} {engage:>8}")
        total_posts += s["posts"]
        total_likes += s["likes"]
        total_comments += s["comments"]

    print("-"*70)
    print(f"{'TOTAL':<40} {total_posts:>6} {total_likes:>7} {total_comments:>10} {total_likes+total_comments:>8}")
    print("="*70)

    # Save to file
    import json
    from datetime import date
    output = {
        "generated": date.today().isoformat(),
        "total_posts": total_posts,
        "series": dict(series_stats),
    }
    with open("analytics_report.json", "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nFull report saved to analytics_report.json")


if __name__ == "__main__":
    run_analytics()
