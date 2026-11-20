"""PromptDen adapter: live-scrape promptden.com listing + post pages via universal.

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

BASE = "https://www.promptden.com"
LIST_URLS = [f"{BASE}/prompts"]
OUT = Path(__file__).resolve().parents[2] / "data" / "seed" / "prompts-den.json"

CURATED = [
    ("seo-keyword-clusters", "SEO Keyword Cluster Builder", "Group keywords into topical clusters for content planning.", ["seo", "marketing"]),
    ("blog-outline", "Blog Post Outline Maker", "Turn a title into a structured article outline.", ["writing", "blog"]),
    ("ad-copy", "Ad Copy Variants", "Draft short ad variants from a product blurb.", ["marketing", "copywriting"]),
    ("product-description", "Product Description Writer", "Write concise product descriptions from feature lists.", ["copywriting", "ecommerce"]),
    ("email-subject", "Email Subject Line Tester", "Generate subject-line options for newsletters.", ["marketing", "email"]),
    ("social-calendar", "Social Media Calendar", "Plan a week of posts from one campaign idea.", ["marketing", "social"]),
    ("job-cover-letter", "Cover Letter Drafter", "Draft a tailored cover letter from a job post.", ["career", "writing"]),
    ("interview-prep", "Interview Prep Coach", "Practice answers to common interview questions.", ["career", "interview"]),
    ("code-explainer", "Code Explainer", "Explain unfamiliar code in plain language.", ["code", "learning"]),
    ("regex-builder", "Regex Builder", "Build a regex from a plain-language description.", ["code", "regex"]),
    ("sql-query", "SQL Query Writer", "Write queries from schema plus question.", ["code", "sql"]),
    ("startup-ideas", "Startup Idea Brainstorm", "Generate startup angles from a skill set.", ["business", "ideas"]),
    ("business-plan", "One-Page Business Plan", "Condense an idea into a lean plan.", ["business", "planning"]),
    ("story-starter", "Story Starter", "Open a short story from a genre plus twist.", ["writing", "fiction"]),
    ("character-sheet", "Character Sheet Builder", "Flesh out a fictional character profile.", ["writing", "fiction"]),
    ("meal-plan", "Weekly Meal Planner", "Plan meals from diet plus budget.", ["lifestyle", "food"]),
    ("workout-plan", "Workout Plan Builder", "Build a routine from goals plus equipment.", ["lifestyle", "fitness"]),
    ("travel-itinerary", "Travel Itinerary Planner", "Sketch a multi-day trip plan.", ["travel", "planning"]),
    ("study-guide", "Study Guide Maker", "Turn notes into quiz-style review sheets.", ["learning", "study"]),
    ("meeting-notes", "Meeting Notes Summarizer", "Condense notes into decisions plus actions.", ["productivity", "meetings"]),
]


def slug(href: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", href.strip("/").split("/")[-1].lower()).strip("-")


def parse_listing(html: str) -> list[tuple[str, str]]:
    out = []
    for a in BeautifulSoup(html, "html.parser").find_all("a", href=True):
        h = a["href"].split("?")[0]
        t = a.get_text(" ", strip=True)
        if "/post/" in h and len(t) > 10 and not any(u == h for u, _ in out):
            out.append((h if h.startswith("http") else BASE + h, t))
    return out


def clean_title(raw: str) -> tuple[str, list[str]]:
    # Card text looks like "SEO Long-tail ... generation ChatGPT 23 2.82k" or "Category Title Model stats"
    parts = re.split(r"\s+(ChatGPT|Claude|Gemini|Other|Midjourney)\b", raw, maxsplit=1)
    head = parts[0].strip()
    head = re.sub(r"\s+\d[\d\s.,k]*$", "", head).strip() or raw.strip()
    first = head.split()[0].lower() if head else ""
    cats = {"marketing", "seo", "copywriting", "devops", "productivity", "software",
            "engineering", "business", "other", "subject"}
    return head[:120], [first] if first in cats else []


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
        for (url, raw), html in zip(cards, detail):
            title, tags = clean_title(raw)
            blurb = blurb_of(html) or f"Community prompt: {title}."
            live.append({"id": f"prompts/den-{slug(url)}", "kind": "prompts", "name": title[:120],
                         "blurb": blurb[:200], "url": url, "tags": sorted(set(tags + ["promptden"])),
                         "past": False})
    rows = list(live)
    if len(rows) < 20:  # site blocked us; curated blurb-only fallback with source links
        have = {r["id"] for r in rows}
        for s, name, blurb, tags in CURATED:
            rid = f"prompts/den-{s}"
            if rid not in have:
                rows.append({"id": rid, "kind": "prompts", "name": name, "blurb": blurb,
                             "url": f"{BASE}/prompts", "tags": sorted(set(tags + ["promptden"])), "past": False})
            if len(rows) >= 20:
                break
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(rows, indent=2) + "\n")
    print(f"wrote {len(rows)} rows (live={len(live)}) -> {OUT}")


if __name__ == "__main__":
    main()
