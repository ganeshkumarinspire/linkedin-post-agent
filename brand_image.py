"""
brand_image.py — Brands a raw ChatGPT illustration into a LinkedIn-ready post image.

Usage:
  python brand_image.py raw_images/2026-07-07.png --series data_agile
  python brand_image.py raw_images/2026-07-07.png --series agile_journey

Output goes to images_data_agile/ or images/ depending on --series flag.
The script reads the date from the filename to look up the topic automatically.
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import date, datetime
from PIL import Image, ImageDraw, ImageFont

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE = Path(__file__).parent

SERIES_CONFIG = {
    "data_agile": {
        "topics_file":  BASE / "topics_data_agile.json",
        "progress_file": BASE / "progress_data_agile.json",
        "output_dir":   BASE / "images_data_agile",
        "label":        "Data-Driven Agile",
        "accent":       (13, 148, 136),    # teal  #0D9488
        "accent2":      (37, 99, 235),     # blue  #2563EB
    },
    "agile_journey": {
        "topics_file":  BASE / "topics.json",
        "progress_file": BASE / "progress.json",
        "output_dir":   BASE / "images",
        "label":        "Lessons from My Agile Journey",
        "accent":       (37, 99, 235),     # blue
        "accent2":      (124, 58, 237),    # purple
    },
}

HANDLE   = "@ganeshkumarinspire"
DARK     = (15, 23, 42)        # near-black  #0F172A
WHITE    = (255, 255, 255)
LIGHT_BG = (241, 245, 249)     # slate-100
MUTED    = (148, 163, 184)     # slate-400

SIZE     = 1080   # square LinkedIn post


# ── Font helpers ───────────────────────────────────────────────────────────────
def load_font(size, bold=False):
    """Try to load a system sans-serif font, fall back to default."""
    candidates_bold = [
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/calibrib.ttf",
        "C:/Windows/Fonts/segoeui.ttf",
    ]
    candidates_regular = [
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/calibri.ttf",
        "C:/Windows/Fonts/segoeui.ttf",
    ]
    candidates = candidates_bold if bold else candidates_regular
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            pass
    return ImageFont.load_default()


def wrap_text(text, font, draw, max_width):
    """Wrap text to fit within max_width pixels."""
    words = text.split()
    lines = []
    current = ""
    for word in words:
        test = (current + " " + word).strip()
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] > max_width and current:
            lines.append(current)
            current = word
        else:
            current = test
    if current:
        lines.append(current)
    return lines


# ── Topic lookup ───────────────────────────────────────────────────────────────
def get_topic_for_date(series_key: str, img_date: date):
    cfg = SERIES_CONFIG[series_key]
    with open(cfg["topics_file"]) as f:
        topics = json.load(f)

    if cfg["progress_file"].exists():
        with open(cfg["progress_file"]) as f:
            progress = json.load(f)
        idx = progress.get("next_index", 0)
    else:
        idx = 0

    # Work out how many weekdays from today until img_date
    today = date.today()
    delta_days = (img_date - today).days
    extra_weekdays = sum(
        1 for d in range(delta_days)
        if (today.toordinal() + d) % 7 not in (5, 6)  # 5=Sat, 6=Sun
    )
    topic_idx = (idx + extra_weekdays) % len(topics)
    return topics[topic_idx], topic_idx + 1


# ── STAR boxes ────────────────────────────────────────────────────────────────
STAR_ITEMS = [
    ("S", "Situation",  "Real team challenge faced"),
    ("T", "Task",       "My role as Scrum Master"),
    ("A", "Action",     "Data-driven step I took"),
    ("R", "Result",     "Measurable improvement"),
]


def draw_star_strip(draw, y, width, accent, accent2, font_sm, font_xs):
    """Draw the 4-column STAR strip."""
    cols     = 4
    pad      = 12
    col_w    = (width - pad * (cols + 1)) // cols
    strip_h  = 90
    radius   = 10

    colors = [accent, accent2, accent, accent2]

    for i, (letter, label, desc) in enumerate(STAR_ITEMS):
        x = pad + i * (col_w + pad)

        # Rounded rect background
        draw.rounded_rectangle(
            [x, y, x + col_w, y + strip_h],
            radius=radius,
            fill=colors[i],
        )

        # Big letter
        lw = draw.textbbox((0, 0), letter, font=font_sm)[2]
        draw.text((x + 14, y + 12), letter, font=font_sm, fill=WHITE)

        # Label
        draw.text((x + 14 + lw + 6, y + 14), label, font=font_xs, fill=(200, 230, 255))

        # Description
        desc_lines = wrap_text(desc, font_xs, draw, col_w - 16)
        for j, line in enumerate(desc_lines):
            draw.text((x + 14, y + 46 + j * 16), line, font=font_xs, fill=WHITE)

    return strip_h


# ── Main branding function ─────────────────────────────────────────────────────
def brand_image(raw_path: Path, series_key: str):
    cfg = SERIES_CONFIG[series_key]
    accent  = cfg["accent"]
    accent2 = cfg["accent2"]
    label   = cfg["label"]

    # Parse date from filename
    stem = raw_path.stem   # e.g. "2026-07-07"
    try:
        img_date = datetime.strptime(stem, "%Y-%m-%d").date()
    except ValueError:
        print(f"Filename must be YYYY-MM-DD.png, got: {raw_path.name}")
        sys.exit(1)

    topic, post_num = get_topic_for_date(series_key, img_date)
    title = topic["title"]

    # ── Canvas ────────────────────────────────────────────────────────────────
    canvas = Image.new("RGB", (SIZE, SIZE), DARK)
    draw   = ImageDraw.Draw(canvas)

    # ── Fonts ─────────────────────────────────────────────────────────────────
    f_title  = load_font(38, bold=True)
    f_label  = load_font(22, bold=True)
    f_num    = load_font(18)
    f_handle = load_font(20, bold=True)
    f_star_l = load_font(28, bold=True)
    f_star_s = load_font(13)

    # ── Top banner ────────────────────────────────────────────────────────────
    BANNER_H = 80
    # Gradient-style: two rects
    draw.rectangle([0, 0, SIZE, BANNER_H], fill=accent)
    draw.rectangle([SIZE // 2, 0, SIZE, BANNER_H], fill=accent2)
    # Diagonal divider
    draw.polygon([(SIZE // 2 - 40, 0), (SIZE // 2 + 40, 0), (SIZE // 2, BANNER_H)],
                 fill=accent)

    # Series label
    draw.text((24, 18), label.upper(), font=f_label, fill=WHITE)
    # Post number badge
    badge_text = f"#{post_num:02d}"
    bw = draw.textbbox((0, 0), badge_text, font=f_label)[2]
    draw.rounded_rectangle([SIZE - bw - 36, 16, SIZE - 12, 64], radius=8, fill=DARK)
    draw.text((SIZE - bw - 24, 20), badge_text, font=f_label, fill=WHITE)

    # ── Illustration ──────────────────────────────────────────────────────────
    ILLUS_TOP    = BANNER_H + 8
    ILLUS_BOTTOM = 620
    ILLUS_H      = ILLUS_BOTTOM - ILLUS_TOP

    raw = Image.open(raw_path).convert("RGB")
    raw_resized = raw.resize((SIZE, ILLUS_H), Image.LANCZOS)
    canvas.paste(raw_resized, (0, ILLUS_TOP))

    # Gradient overlay at bottom of illustration so title is readable
    overlay = Image.new("RGBA", (SIZE, 160), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    for row in range(160):
        alpha = int(210 * (row / 160))
        od.rectangle([0, row, SIZE, row + 1], fill=(15, 23, 42, alpha))
    # Composite overlay onto canvas
    base_region = canvas.crop((0, ILLUS_BOTTOM - 160, SIZE, ILLUS_BOTTOM)).convert("RGBA")
    merged = Image.alpha_composite(base_region, overlay).convert("RGB")
    canvas.paste(merged, (0, ILLUS_BOTTOM - 160))

    # ── Title over illustration ────────────────────────────────────────────────
    TITLE_TOP = ILLUS_BOTTOM - 130
    title_lines = wrap_text(title, f_title, draw, SIZE - 40)
    for i, line in enumerate(title_lines[:3]):
        draw.text((20, TITLE_TOP + i * 46), line, font=f_title, fill=WHITE)

    # ── STAR strip ────────────────────────────────────────────────────────────
    STAR_Y = ILLUS_BOTTOM + 14
    draw_star_strip(draw, STAR_Y, SIZE, accent, accent2, f_star_l, f_star_s)

    # ── Bottom bar ────────────────────────────────────────────────────────────
    BOTTOM_Y = STAR_Y + 90 + 12
    draw.rectangle([0, BOTTOM_Y, SIZE, SIZE], fill=(10, 15, 30))

    # Accent line
    draw.rectangle([0, BOTTOM_Y, SIZE, BOTTOM_Y + 3], fill=accent)

    # Handle
    hw = draw.textbbox((0, 0), HANDLE, font=f_handle)[2]
    draw.text((SIZE - hw - 20, BOTTOM_Y + 16), HANDLE, font=f_handle, fill=accent)

    # LinkedIn label
    draw.text((20, BOTTOM_Y + 16), "LinkedIn Content Series", font=f_num, fill=MUTED)
    draw.text((20, BOTTOM_Y + 38), f"Scrum Master · Paris · Open to Work", font=f_star_s,
              fill=MUTED)

    # ── Save ──────────────────────────────────────────────────────────────────
    cfg["output_dir"].mkdir(exist_ok=True)
    out_path = cfg["output_dir"] / f"{stem}.png"
    canvas.save(out_path, "PNG", optimize=True)
    print(f"Saved: {out_path}")
    return out_path


# ── CLI ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Brand a raw image for LinkedIn")
    parser.add_argument("image", help="Path to raw ChatGPT illustration (YYYY-MM-DD.png)")
    parser.add_argument("--series", choices=["data_agile", "agile_journey"],
                        default="data_agile",
                        help="Which series this image belongs to")
    args = parser.parse_args()
    brand_image(Path(args.image), args.series)
