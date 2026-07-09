import base64
import json
import re
from datetime import date
from pathlib import Path
import requests

OLLAMA_URL = "http://localhost:11434/api/chat"
TEXT_MODEL = "llama3.2"
VISION_MODEL = "llava"

IMAGES_DIR = Path(__file__).parent / "Lessons_from_My_Agile_Journey"

FIXED_HASHTAGS = (
    "#AgileJourney #ScrumMaster #AgileMindset #ContinuousLearning #Leadership "
    "#TeamCollaboration #AgileDelivery #EnterpriseAgility #ProfessionalGrowth "
    "#ProjectManagement #DigitalTransformation #ContinuousImprovement "
    "#StakeholderManagement #LearningJourney #OpenToWork #France"
)

SYSTEM_PROMPT = """You are Ganesh Kumar, a Scrum Master and Agile practitioner based in Paris, actively looking for Scrum Master opportunities in France and Europe.

Your LinkedIn posts serve two goals:
1. Demonstrate your Scrum Master expertise to recruiters and hiring managers
2. Build a professional network that leads to job interviews and referrals

Your writing style:
- Opens with a punchy one-liner or provocative question (no hashtags yet)
- Tells a short personal story (2-4 lines) grounded in real Agile/Scrum team experience
- Distills ONE clear lesson or insight that shows your Scrum Master competence
- Ends with a reflective question to invite comments and engagement
- Always written as YOUR personal story from a real past project — never reference an image, graphic, or visual
- Subtly signals you are open to new Scrum Master roles in France/Europe where relevant
- Uses line breaks generously — never a wall of text
- Conversational and direct, not corporate or buzzword-heavy
- 150-250 words total

Format: plain text, line breaks between paragraphs. No hashtags — they are added separately.
Do NOT include emojis unless they are natural (max 1-2).
Do NOT add a title or heading line."""


def get_today_image() -> Path | None:
    """Look for an image named YYYY-MM-DD.* in the images folder."""
    today = date.today().isoformat()  # e.g. 2026-07-01
    for ext in ("png", "jpg", "jpeg", "webp"):
        path = IMAGES_DIR / f"{today}.{ext}"
        if path.exists():
            return path
    return None


def get_image_for_date(images_dir: Path) -> Path | None:
    """Look for an image named YYYY-MM-DD.* in the given directory."""
    today = date.today().isoformat()
    for ext in ("png", "jpg", "jpeg", "webp"):
        path = images_dir / f"{today}.{ext}"
        if path.exists():
            return path
    return None


def generate_post_custom(
    topic: dict,
    system_prompt: str,
    fixed_hashtags: str,
    image_description: str | None = None,
) -> str:
    """Generate a post using a custom system prompt and hashtag set."""
    if image_description:
        user_prompt = f"""Write a LinkedIn post for this series.

Topic: {topic['title']}
Opening hook: {topic['hook']}

Write as MY personal story from a real past project — first person, specific.
The image I'm sharing is about: {image_description}

Rules:
- Do NOT reference the image, graphic, or visual in the text — the post stands alone
- Tell what happened, what I did, what the result was
- End with a question to the reader

Write the full post now."""
    else:
        user_prompt = f"""Write a LinkedIn post for this series.

Topic: {topic['title']}
Theme: {topic['theme']}
Opening hook to build from: {topic['hook']}
Suggested hashtags: {', '.join('#' + t for t in topic['tags'])}

Write the full post now."""

    payload = {
        "model": TEXT_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "stream": False,
    }

    response = requests.post(OLLAMA_URL, json=payload, timeout=300)
    response.raise_for_status()
    post_body = response.json()["message"]["content"].strip()

    lines = post_body.splitlines()
    lines = [l for l in lines if not l.strip().startswith("#")]
    post_body = "\n".join(lines).strip()

    return f"{post_body}\n\n{fixed_hashtags}"


def describe_image(image_path: Path) -> str:
    """Use llava to describe the Agile image and extract its key message."""
    with open(image_path, "rb") as f:
        image_b64 = base64.b64encode(f.read()).decode("utf-8")

    payload = {
        "model": VISION_MODEL,
        "messages": [
            {
                "role": "user",
                "content": (
                    "This is an Agile/Scrum infographic or visual. "
                    "Describe what it shows: the main topic, key points, and the core message. "
                    "Be specific and concise — 3 to 5 sentences."
                ),
                "images": [image_b64],
            }
        ],
        "stream": False,
    }
    response = requests.post(OLLAMA_URL, json=payload, timeout=300)
    response.raise_for_status()
    return response.json()["message"]["content"].strip()


def generate_post(topic: dict, image_description: str | None = None) -> str:
    if image_description:
        user_prompt = f"""Write a LinkedIn post for my "Lessons from My Agile Journey" series.

Topic: {topic['title']}
Opening hook: {topic['hook']}

The post must be written as MY personal story from a real past project — first person, specific, grounded in my experience as a Scrum Master.
I am also sharing an image with this post. The image is about: {image_description}

Rules:
- Write as if I (Ganesh) lived this story on a real team — do NOT say "the image says" or "the image shows" or reference the image at all in the text
- The image is just visual support — the post stands on its own as my story
- Tell what happened, what I did, what the result was
- End with a question to the reader

Write the full post now."""
    else:
        user_prompt = f"""Write a LinkedIn post for my "Lessons from My Agile Journey" series.

Topic: {topic['title']}
Theme: {topic['theme']}
Opening hook to build from: {topic['hook']}
Suggested hashtags: {', '.join('#' + t for t in topic['tags'])}

Write the full post now."""

    payload = {
        "model": TEXT_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "stream": False,
    }

    response = requests.post(OLLAMA_URL, json=payload, timeout=300)
    response.raise_for_status()
    post_body = response.json()["message"]["content"].strip()

    # Strip any hashtags the model added, then append the fixed set
    lines = post_body.splitlines()
    lines = [l for l in lines if not l.strip().startswith("#")]
    post_body = "\n".join(lines).strip()

    return f"{post_body}\n\n{FIXED_HASHTAGS}"


if __name__ == "__main__":
    with open("topics.json") as f:
        topics = json.load(f)

    topic = topics[0]
    image_path = get_today_image()

    if image_path:
        print(f"Image found: {image_path.name}")
        desc = describe_image(image_path)
        print(f"Image description: {desc}\n")
        post = generate_post(topic, image_description=desc)
    else:
        print("No image found for today — generating text-only post\n")
        post = generate_post(topic)

    print("--- POST ---")
    print(post)
