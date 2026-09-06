"""
Agile Reimagined With AI series agent.
Posts at 12:00 PM Paris time Mon-Fri via cron-job.org -> GitHub Actions.
Run manually: python agent_agile_ai.py
"""

import json
import logging
import os
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from content_generator import get_image_for_date
from linkedin_client import publish
from report_logger import log_report
from content_verifier import verify_post_matches_image

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

IMAGES_DIR = Path(__file__).parent / "Agile_Reimagined_With_AI"
POSTS_FILE = Path(__file__).parent / "posts_agile_ai.json"

SERIES_NAME = "Agile Reimagined With AI"
SERIES_FOLDER = "Agile_Reimagined_With_AI"


def run_agent():
    today_str = date.today().isoformat()

    IMAGES_DIR.mkdir(exist_ok=True)

    image_path = get_image_for_date(IMAGES_DIR)
    image_found = image_path is not None
    if image_found:
        logger.info(f"Image found: {image_path.name}")
    else:
        logger.info("No image found for today")

    # Load pre-written post
    pre_written = {}
    if POSTS_FILE.exists():
        with open(POSTS_FILE) as f:
            pre_written = json.load(f)

    json_post_found = today_str in pre_written
    json_verified = image_found and json_post_found
    logger.info(f"Image found: {image_found} | JSON post found: {json_post_found} | Verified: {json_verified}")

    if not json_post_found:
        logger.info(f"No pre-written post found for {today_str} — skipping today.")
        log_report(
            series=SERIES_NAME,
            folder=SERIES_FOLDER,
            image_file=image_path.name if image_path else None,
            post_date=today_str,
            json_post_matched=False,
            status="Skipped — no post scheduled for today",
        )
        return

    post_text = pre_written[today_str]
    logger.info(f"Using pre-written post for {today_str}")
    logger.info(f"Post:\n{post_text}")

    # Verify post matches image
    if image_path:
        logger.info("Verifying post matches image content via GPT-4o...")
        is_match, reason = verify_post_matches_image(image_path, post_text)
        logger.info(f"Verification result: {'MATCH' if is_match else 'NO MATCH'} — {reason}")
    else:
        is_match, reason = True, "No image — skipping visual verification"

    if not is_match:
        logger.error(f"Post blocked — content does not match image: {reason}")
        log_report(
            series=SERIES_NAME,
            folder=SERIES_FOLDER,
            image_file=image_path.name if image_path else None,
            post_date=today_str,
            json_post_matched=False,
            status="Blocked — content mismatch",
            error=reason,
        )
        return

    # Dry run check
    if os.getenv("DRY_RUN", "false").lower() == "true":
        logger.info("DRY RUN — skipping LinkedIn publish. Verification passed.")
        log_report(
            series=SERIES_NAME,
            folder=SERIES_FOLDER,
            image_file=image_path.name if image_path else None,
            post_date=today_str,
            json_post_matched=json_verified,
            status="Dry Run — verified OK, not posted",
        )
        return

    logger.info("Publishing to LinkedIn...")
    try:
        post_urn = publish(post_text, image_path=str(image_path) if image_path else None)
        log_report(
            series=SERIES_NAME,
            folder=SERIES_FOLDER,
            image_file=image_path.name if image_path else None,
            post_date=today_str,
            json_post_matched=json_verified,
            status="Success",
        )
        logger.info(f"Done! Post published: {post_urn}")
    except Exception as e:
        log_report(
            series=SERIES_NAME,
            folder=SERIES_FOLDER,
            image_file=image_path.name if image_path else None,
            post_date=today_str,
            json_post_matched=json_verified,
            status="Failed",
            error=str(e),
        )
        raise


if __name__ == "__main__":
    run_agent()
