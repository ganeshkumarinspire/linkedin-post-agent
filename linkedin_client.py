import os
import requests

LINKEDIN_API_BASE = "https://api.linkedin.com/v2"

# Set via environment variable after OAuth exchange
ACCESS_TOKEN = os.environ.get("LINKEDIN_ACCESS_TOKEN")
PERSON_URN = os.environ.get("LINKEDIN_PERSON_URN")  # urn:li:person:XXXXXXXX


def _headers(extra: dict | None = None) -> dict:
    h = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "X-Restli-Protocol-Version": "2.0.0",
        "Content-Type": "application/json",
    }
    if extra:
        h.update(extra)
    return h


def get_person_urn() -> str:
    """Fetch the authenticated member's URN (run once to populate LINKEDIN_PERSON_URN)."""
    resp = requests.get(f"{LINKEDIN_API_BASE}/userinfo", headers=_headers(), timeout=15)
    resp.raise_for_status()
    data = resp.json()
    return f"urn:li:person:{data['sub']}"


def _register_image_upload() -> tuple[str, str]:
    """Step 1 of image upload: register and get upload URL + asset URN."""
    payload = {
        "registerUploadRequest": {
            "owner": PERSON_URN,
            "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
            "serviceRelationships": [
                {
                    "identifier": "urn:li:userGeneratedContent",
                    "relationshipType": "OWNER",
                }
            ],
        }
    }
    resp = requests.post(
        f"{LINKEDIN_API_BASE}/assets?action=registerUpload",
        headers=_headers(),
        json=payload,
        timeout=15,
    )
    resp.raise_for_status()
    result = resp.json()["value"]
    upload_url = result["uploadMechanism"][
        "com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"
    ]["uploadUrl"]
    asset_urn = result["asset"]
    return upload_url, asset_urn


def _upload_image_binary(upload_url: str, image_path: str) -> None:
    """Step 2: PUT the image bytes to the signed upload URL."""
    with open(image_path, "rb") as f:
        image_data = f.read()

    resp = requests.put(
        upload_url,
        headers={
            "Authorization": f"Bearer {ACCESS_TOKEN}",
            "Content-Type": "application/octet-stream",
        },
        data=image_data,
        timeout=30,
    )
    resp.raise_for_status()


def upload_image(image_path: str) -> str:
    """Upload image to LinkedIn and return asset URN."""
    upload_url, asset_urn = _register_image_upload()
    _upload_image_binary(upload_url, image_path)
    print(f"Image uploaded — asset URN: {asset_urn}")
    return asset_urn


def create_post(text: str, image_asset_urn: str | None = None) -> str:
    """Create a LinkedIn post (with optional image). Returns the post URN."""
    media = []
    if image_asset_urn:
        media = [
            {
                "status": "READY",
                "description": {"text": ""},
                "media": image_asset_urn,
                "title": {"text": ""},
            }
        ]

    payload = {
        "author": PERSON_URN,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": text},
                "shareMediaCategory": "IMAGE" if media else "NONE",
                "media": media,
            }
        },
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
    }

    resp = requests.post(
        f"{LINKEDIN_API_BASE}/ugcPosts",
        headers=_headers(),
        json=payload,
        timeout=15,
    )
    resp.raise_for_status()
    post_urn = resp.headers.get("X-RestLi-Id", "unknown")
    print(f"Post published — URN: {post_urn}")
    return post_urn


def publish(post_text: str, image_path: str | None = None) -> str:
    """Upload image (if any) and publish the post. Returns post URN."""
    asset_urn = upload_image(image_path) if image_path else None
    return create_post(post_text, asset_urn)
