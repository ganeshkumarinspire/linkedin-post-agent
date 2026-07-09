"""
Data-Driven Agile series agent.
Posts at 12:00 PM Paris time Mon-Fri via Windows Task Scheduler.
Run manually: python agent_data_agile.py
"""

import json
import logging
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from content_generator import describe_image, generate_post_custom, get_image_for_date
from linkedin_client import publish
from report_logger import log_report

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

TOPICS_FILE    = Path(__file__).parent / "topics_data_agile.json"
PROGRESS_FILE  = Path(__file__).parent / "progress_data_agile.json"
IMAGES_DIR     = Path(__file__).parent / "Data_Driven_Agile"
POSTS_FILE     = Path(__file__).parent / "posts_data_agile.json"

SYSTEM_PROMPT = """You are Ganesh Kumar, a Scrum Master and Data Engineer based in Paris, actively looking for Scrum Master roles in France and Europe.

You write a LinkedIn series called "Data-Driven Agile" — where you share how using data, metrics, and analytics makes Agile teams deliver better.

Your unique angle: you combine a Data Engineering background with hands-on Scrum Master experience across Verizon, Adidas, ABB, and ADM.

Your writing style:
- Opens with a punchy one-liner or a surprising data insight
- Tells a short personal story from a real project — first person, specific
- Shows HOW you used data to solve a team problem or improve delivery
- Ends with a practical tip or a question that invites comments
- Subtly signals you are open to Scrum Master roles in France/Europe
- Conversational and direct — no buzzwords, no generic Agile theory
- 150–250 words total

Format: plain text, line breaks between paragraphs. No hashtags — added separately.
Do NOT reference any image or visual in the text.
Do NOT add a title or heading line."""

FIXED_HASHTAGS = (
    "#DataDrivenAgile #AgileMetrics #ScrumMaster #AgileMindset #ContinuousImprovement "
    "#AgileDelivery #DataEngineering #Leadership #TeamCollaboration #ProjectManagement "
    "#DigitalTransformation #EnterpriseAgility #ProfessionalGrowth #LearningJourney "
    "#OpenToWork #France"
)


def load_topics():
    with open(TOPICS_FILE) as f:
        return json.load(f)


def load_progress():
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE) as f:
            return json.load(f)
    return {"next_index": 0, "published": []}


def save_progress(progress):
    with open(PROGRESS_FILE, "w") as f:
        json.dump(progress, f, indent=2)


def run_agent():
    topics   = load_topics()
    progress = load_progress()

    idx = progress.get("next_index", 0)
    if idx >= len(topics):
        logger.info("All Data-Driven Agile topics exhausted — cycling back")
        idx = 0

    topic = topics[idx]
    logger.info(f"Selected topic [{idx}]: {topic['title']}")

    # Check for today's image
    IMAGES_DIR.mkdir(exist_ok=True)
    image_path = get_image_for_date(IMAGES_DIR)

    # Use pre-written post if available, otherwise generate with Ollama
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
        logger.info("No pre-written post found — generating with Ollama...")
        image_description = None
        if image_path:
            logger.info(f"Image found: {image_path.name} — analysing...")
            image_description = describe_image(image_path)
            logger.info(f"Image description: {image_description}")
        post_text = generate_post_custom(topic, SYSTEM_PROMPT, FIXED_HASHTAGS, image_description)
    logger.info(f"Post:\n{post_text}")

    logger.info("Publishing to LinkedIn...")
    try:
        post_urn = publish(post_text, image_path=str(image_path) if image_path else None)
        log_report(
            series="Data-Driven Agile",
            folder="Data_Driven_Agile",
            image_file=image_path.name if image_path else None,
            post_date=today_str,
            json_post_matched=today_str in pre_written,
            status="Success",
        )
        logger.info(f"Done! Post published: {post_urn}")
    except Exception as e:
        log_report(
            series="Data-Driven Agile",
            folder="Data_Driven_Agile",
            image_file=image_path.name if image_path else None,
            post_date=today_str,
            json_post_matched=today_str in pre_written,
            status="Failed",
            error=str(e),
        )
        raise

    progress["next_index"] = idx + 1
    progress["published"].append({
        "topic_id": topic["id"],
        "title": topic["title"],
        "post_urn": post_urn,
        "image": image_path.name if image_path else None,
    })
    save_progress(progress)
    logger.info(f"Done! Post published: {post_urn}")


if __name__ == "__main__":
    run_agent()
