"""
Verifies that the pre-written JSON post matches the image content for the day.
Uses OpenAI GPT-4o vision to analyse the image and compare with the post text.
Returns (is_match: bool, reason: str)
"""
import base64
import os
from pathlib import Path
import requests


def _encode_image(image_path: Path) -> str:
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def verify_post_matches_image(image_path: Path, post_text: str) -> tuple[bool, str]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return False, "OPENAI_API_KEY not set — cannot verify"

    if not image_path or not image_path.exists():
        return False, "Image file not found — cannot verify"

    image_b64 = _encode_image(image_path)
    ext = image_path.suffix.lstrip(".")
    mime = f"image/{ext}" if ext in ("png", "jpg", "jpeg", "webp") else "image/png"

    prompt = f"""You are a LinkedIn content quality checker.

I will show you an image and a LinkedIn post. Your job is to decide if the post content is relevant to and consistent with the image.

LinkedIn Post:
\"\"\"
{post_text[:1500]}
\"\"\"

Answer ONLY in this exact format:
MATCH: Yes or No
REASON: one sentence explaining why"""

    payload = {
        "model": "gpt-4o",
        "max_tokens": 150,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime};base64,{image_b64}",
                            "detail": "low",
                        },
                    },
                ],
            }
        ],
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            json=payload,
            headers=headers,
            timeout=30,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"].strip()

        is_match = "MATCH: Yes" in content
        reason_line = next(
            (line for line in content.splitlines() if line.startswith("REASON:")),
            "REASON: No reason provided",
        )
        reason = reason_line.replace("REASON:", "").strip()
        return is_match, reason

    except Exception as e:
        return False, f"Verification error: {e}"
