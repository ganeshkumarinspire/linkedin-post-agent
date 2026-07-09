"""
Main orchestration loop.
Run directly for a one-shot post:  python agent.py
Or let scheduler.py call run_agent() on schedule.
"""

import json
import logging
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from content_generator import describe_image, generate_post, get_today_image
from linkedin_client import publish
from report_logger import log_report

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

TOPICS_FILE    = Path(__file__).parent / "topics.json"
PROGRESS_FILE  = Path(__file__).parent / "progress.json"
POSTS_FILE     = Path(__file__).parent / "posts_agile_journey.json"


def load_topics() -> list[dict]:
    with open(TOPICS_FILE) as f:
        return json.load(f)


def load_progress() -> dict:
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE) as f:
            return json.load(f)
    return {"next_index": 0, "published": []}


def save_progress(progress: dict) -> None:
    with open(PROGRESS_FILE, "w") as f:
        json.dump(progress, f, indent=2)


def pick_topic(topics: list[dict], progress: dict) -> tuple[dict, int]:
    idx = progress.get("next_index", 0)
    if idx >= len(topics):
        logger.info("All topics exhausted — cycling back to start")
        idx = 0
    return topics[idx], idx


def run_agent() -> None:
    topics = load_topics()
    progress = load_progress()

    topic, idx = pick_topic(topics, progress)
    logger.info(f"Selected topic [{idx}]: {topic['title']}")

    # 1. Check for today's image
    image_path = get_today_image()

    # 2. Use pre-written post if available, otherwise generate with Ollama
    from datetime import date
    today_str = date.today().isoformat()

    pre_written = {}
    if POSTS_FILE.exists():
        with open(POSTS_FILE) as f:
            pre_written = json.load(f)

    if today_str in pre_written:
        post_text = pre_written[today_str]
        logger.info(f"Using pre-written post for {today_str}")
    else:
        logger.info("No pre-written post found — generating with Ollama (llama3.2)...")
        image_description = None
        if image_path:
            logger.info(f"Image found: {image_path.name} — analysing with llava...")
            image_description = describe_image(image_path)
            logger.info(f"Image description: {image_description}")
        post_text = generate_post(topic, image_description=image_description)
    logger.info(f"Post text:\n{post_text}")

    # 3. Publish to LinkedIn (with image if available)
    logger.info("Publishing to LinkedIn...")
    try:
        post_urn = publish(post_text, image_path=str(image_path) if image_path else None)
        log_report(
            series="Lessons from My Agile Journey",
            folder="Lessons_from_My_Agile_Journey",
            image_file=image_path.name if image_path else None,
            post_date=today_str,
            json_post_matched=today_str in pre_written,
            status="Success",
        )
        logger.info(f"Done! Post published: {post_urn}")
    except Exception as e:
        log_report(
            series="Lessons from My Agile Journey",
            folder="Lessons_from_My_Agile_Journey",
            image_file=image_path.name if image_path else None,
            post_date=today_str,
            json_post_matched=today_str in pre_written,
            status="Failed",
            error=str(e),
        )
        raise

    # 4. Record progress
    progress["next_index"] = idx + 1
    progress["published"].append(
        {
            "topic_id": topic["id"],
            "title": topic["title"],
            "post_urn": post_urn,
            "image": image_path.name if image_path else None,
        }
    )
    save_progress(progress)
    logger.info(f"Done! Post published: {post_urn}")


if __name__ == "__main__":
    run_agent()
