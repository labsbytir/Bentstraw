"""YouMind adapter: live-scrape youmind.com prompt library via universal.

Rows: {id, kind:"prompts", name, blurb, url, tags, past:false}.
Blurb-only excerpts (meta description, truncated) + source links. No paywall copying.
Falls back to curated blurb-only rows if the site blocks us (<20 live rows).
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from universal import fetch_many  # noqa: E402
from bs4 import BeautifulSoup  # noqa: E402

BASE = "https://youmind.com"
LIST_URLS = [f"{BASE}/prompts"]
OUT = Path(__file__).resolve().parents[2] / "data" / "seed" / "prompts-youmind.json"

CURATED = [
    ("social-media-post", "Social Media Post Kit", "Draft platform-ready social posts from one announcement.", ["social", "marketing"]),
    ("newsletter-email", "Newsletter Writer", "Turn updates into a readable newsletter issue.", ["email", "writing"]),
    ("business-proposal", "Business Proposal Drafter", "Structure a proposal from goals plus scope.", ["business", "writing"]),
    ("academic-writing", "Academic Writing Helper", "Outline papers with thesis plus citations plan.", ["writing", "academic"]),
    ("startup-pitch-deck", "Startup Pitch Deck Outline", "Ten-slide pitch structure from a one-liner.", ["business", "pitch"]),
    ("sales-pitch-deck", "Sales Pitch Deck Builder", "Objection-handling slides from product notes.", ["business", "sales"]),
    ("marketing-presentation", "Marketing Plan Deck", "Campaign recap slides from metrics plus learnings.", ["marketing", "slides"]),
    ("cover-art", "Cover Art Prompt", "Minimalist cover-art image prompt for a single.", ["art", "image"]),
    ("poster-design", "Poster Design Prompt", "Artistic poster image prompts from a theme.", ["art", "poster"]),
    ("photo-edit", "Travel Photo Edit Pack", "Edit prompts that restyle travel shots.", ["photo", "travel"]),
    ("video-storyboard", "Short Film Storyboard", "Beat-by-beat visual plan for a short scene.", ["video", "film"]),
    ("animation-loop", "Animation Loop Prompt", "Seamless loop animation prompts.", ["video", "animation"]),
    ("product-shot", "Product Shot Prompt", "Studio-style product image prompts.", ["photo", "product"]),
    ("portrait-pack", "Portrait Prompt Pack", "Lighting plus mood portrait prompts.", ["photo", "portrait"]),
    ("logo-mark", "Logo Mark Prompt", "Minimal logo-mark image prompts.", ["design", "logo"]),
    ("brand-moodboard", "Brand Moodboard Prompts", "Visual moodboard prompts from brand words.", ["design", "brand"]),
    ("tshirt-graphic", "T-Shirt Graphic Prompt", "Print-ready graphic prompts.", ["design", "merch"]),
    ("sticker-pack", "Sticker Pack Prompts", "Die-cut sticker style prompts.", ["design", "stickers"]),
    ("wallpaper-pack", "Wallpaper Prompt Pack", "Desktop wallpaper image prompts.", ["art", "wallpaper"]),
    ("pixel-sprites", "Pixel Sprite Prompts", "Game sprite sheet prompts.", ["gaming", "pixel-art"]),
]


def slug(url: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", url.rstrip("/").split("/")[-1].lower()).strip("-")


def parse_listing(html: str) -> list[tuple[str, str]]:
    out, seen = [], set()
    for a in BeautifulSoup(html, "html.parser").find_all("a", href=True):
        h = a["href"].split("#")[0]
        t = " ".join(a.get_text(" ", strip=True).split())
        if ("/prompts/" in h or "/video-prompts/" in h) and 12 < len(t) < 140 and h not in seen:
            seen.add(h)
            out.append((h if h.startswith("http") else BASE + h, t))
    return out


def blurb_of(html: str) -> str:
    if not html:
        return ""
    s = BeautifulSoup(html, "html.parser")
    m = s.find("meta", attrs={"name": "description"}) or s.find("meta", attrs={"property": "og:description"})
    return ((m.get("content", "") if m else "") or "").strip()[:200]


def main() -> None:
    live: list[dict] = []
    pages = fetch_many(LIST_URLS)
    cards = parse_listing(pages[0]) if pages and pages[0] else []
    if cards:
        detail = fetch_many([u for u, _ in cards[:24]])
        for (url, title), html in zip(cards, detail):
            name = re.sub(r"\s+@.*$", "", title).strip()[:120] or title[:120]
            blurb = blurb_of(html) or f"Community prompt from the YouMind library: {name}."
            kind_tag = "video" if "/video-prompts/" in url else "image"
            live.append({"id": f"prompts/youmind-{slug(url)}", "kind": "prompts", "name": name,
                         "blurb": blurb[:200], "url": url, "tags": [kind_tag, "youmind"], "past": False})
    rows = list(live)
    if len(rows) < 20:  # site blocked us; curated blurb-only fallback with source links
        have = {r["id"] for r in rows}
        for s, name, blurb, tags in CURATED:
            rid = f"prompts/youmind-{s}"
            if rid not in have:
                rows.append({"id": rid, "kind": "prompts", "name": name, "blurb": blurb,
                             "url": f"{BASE}/{s}", "tags": sorted(set(tags + ["youmind"])), "past": False})
            if len(rows) >= 20:
                break
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(rows, indent=2) + "\n")
    print(f"wrote {len(rows)} rows (live={len(live)}) -> {OUT}")


if __name__ == "__main__":
    main()
