"""PromptBase adapter: live attempt + curated fallback via universal.

PromptBase serves a Cloudflare challenge to bots (verified 403 on /, /marketplace,
/trending, /sitemap.xml), so live scraping yields nothing and robots-respect means we
don't fight it. Rows below are blurb-only (own summaries, no paywalled copying) with
source links to real PromptBase browse pages. If the site ever becomes bot-readable,
the live path picks up real cards automatically.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from universal import fetch_many  # noqa: E402
from bs4 import BeautifulSoup  # noqa: E402

BASE = "https://promptbase.com"
LIST_URLS = [f"{BASE}/marketplace?itemType=prompt&sortBy=hotness", f"{BASE}/best-ai-prompts"]
OUT = Path(__file__).resolve().parents[2] / "data" / "seed" / "prompts-base.json"

# (slug, name seen on PromptBase listings, own blurb-only summary, url, tags)
CURATED = [
    ("psychedelic-neon-comic", "Psychedelic Neon Comic Characters", "Neon comic-style character art prompts.", f"{BASE}/midjourney", ["art", "midjourney", "comic"]),
    ("handdrawn-travel-posters", "Handdrawn Ink Travel Posters", "Ink-style vintage travel poster prompts.", f"{BASE}/midjourney", ["art", "poster", "travel"]),
    ("psychedelic-fantasy-worlds", "Psychedelic Fantasy Worlds", "Trippy fantasy landscape art prompts.", f"{BASE}/midjourney", ["art", "fantasy"]),
    ("paper-diorama-poster", "Painted Paper Diorama Poster Art", "Layered paper-craft poster prompts.", f"{BASE}/midjourney", ["art", "poster"]),
    ("mythic-clipart", "Cool Blue Mythic Clipart", "Mythic creature clipart prompts in blue tones.", f"{BASE}/midjourney", ["art", "clipart"]),
    ("editorial-illustrations", "Textured Monoprint Editorial Illustrations", "Editorial illustration prompts with texture.", f"{BASE}/midjourney", ["art", "editorial"]),
    ("epic-fantasy-covers", "Vintage Epic Fantasy Covers", "Fantasy book-cover art prompts.", f"{BASE}/midjourney", ["art", "fantasy", "books"]),
    ("christmas-illustrations", "Christmas Girls Fashion Illustrations", "Holiday fashion illustration prompts.", f"{BASE}/best-ai-prompts", ["art", "fashion", "holiday"]),
    ("pixel-orbs", "Elements Under Glass Pixel Orbs", "Pixel-art orb illustration prompts.", f"{BASE}/best-ai-prompts", ["art", "pixel-art"]),
    ("cottage-seamless-paper", "Cottage Chintz Seamless Papers", "Seamless pattern paper prompts.", f"{BASE}/best-ai-prompts", ["art", "pattern"]),
    ("golden-hour-portraits", "Dramatic Golden Hour Portraits", "Golden-hour portrait photo prompts.", f"{BASE}/best-ai-prompts", ["photo", "portrait"]),
    ("vector-tshirt", "Vector Silhouette T-shirt Designs", "Silhouette tee graphic prompts.", f"{BASE}/midjourney", ["design", "merch"]),
    ("fashionable-tee", "Fashionable Tshirt Designs", "Trendy tee graphic prompts.", f"{BASE}/midjourney", ["design", "merch", "fashion"]),
    ("tarot-arcana", "Fantasy Major Arcana Tarot Cards", "Tarot card art prompts.", f"{BASE}/midjourney", ["art", "fantasy", "tarot"]),
    ("retro-anime", "Retro Anime Characters", "Retro anime character prompts.", f"{BASE}/midjourney", ["art", "anime"]),
    ("dnd-terrain", "Tabletop Game Terrain Maps", "DnD battlemap art prompts.", f"{BASE}/midjourney", ["gaming", "maps"]),
    ("startup-logo-architect", "Vibrant Startup Logo Identity Architect", "Startup logo identity prompts.", f"{BASE}/logos", ["design", "logo", "startup"]),
    ("mascot-logos", "Custom Esports Mascot Logo Vectors", "Esports mascot logo prompts.", f"{BASE}/logos", ["design", "logo", "gaming"]),
    ("monoline-emblems", "Monoline Emblems", "Single-weight-line emblem logo prompts.", f"{BASE}/modern-logos", ["design", "logo"]),
    ("art-deco-emblems", "Art Deco Emblems", "Deco-style emblem logo prompts.", f"{BASE}/modern-logos", ["design", "logo", "retro"]),
    ("monogram-generator", "Monogram Generator", "Letter monogram logo prompts.", f"{BASE}/logos", ["design", "logo", "typography"]),
    ("font-generator", "Font Generator Custom Type Pack", "Custom typeface design prompts.", f"{BASE}/logos", ["design", "typography"]),
]


def parse_listing(html: str) -> list[dict]:
    rows = []
    if not html or "Just a moment" in html:
        return rows
    for a in BeautifulSoup(html, "html.parser").find_all("a", href=True):
        h, t = a["href"], a.get_text(" ", strip=True)
        if h.startswith("/prompt/") and len(t) > 8:
            rows.append({"id": f"prompts/base-{h.strip('/').split('/')[-1][:60]}", "kind": "prompts",
                         "name": t[:120], "blurb": f"PromptBase marketplace prompt: {t[:120]}.",
                         "url": BASE + h, "tags": ["promptbase"], "past": False})
    seen, uniq = set(), []
    for r in rows:
        if r["id"] not in seen:
            seen.add(r["id"])
            uniq.append(r)
    return uniq


def main() -> None:
    pages = fetch_many(LIST_URLS)
    live = []
    for html in pages:
        live.extend(parse_listing(html))
    rows = list(live)
    if len(rows) < 20:  # expected: Cloudflare challenge blocks bots
        have = {r["id"] for r in rows}
        for s, name, blurb, url, tags in CURATED:
            rid = f"prompts/base-{s}"
            if rid not in have:
                rows.append({"id": rid, "kind": "prompts", "name": name, "blurb": blurb,
                             "url": url, "tags": sorted(set(tags + ["promptbase"])), "past": False})
            if len(rows) >= 20:
                break
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(rows, indent=2) + "\n")
    print(f"wrote {len(rows)} rows (live={len(live)}) -> {OUT}")


if __name__ == "__main__":
    main()
