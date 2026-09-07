"""Prompt construction, caching, and optional Pollinations.ai image fetching."""

from __future__ import annotations

import argparse
import json
import re
import time
from pathlib import Path
from urllib.parse import quote

import requests

from build_site import slugify


ROOT = Path(__file__).resolve().parent.parent
WORKS_DIR = ROOT / "assets" / "images" / "works"
STYLE = "minimalist dark pencil drawing, Pushkin manuscript margin sketch style, solitary and poetic vibe, clean line art, monochrome on dark paper"


def build_prompt(work: dict) -> str:
    """Build a concise illustration prompt from a work record."""
    title = work.get("title", "Untitled work")
    text = re.sub(r"\s+", " ", work.get("text", "")).strip()
    excerpt = text[:700]
    return f"{STYLE}. Literary marginal illustration inspired by '{title}'. Subject and mood: {excerpt}"


def pollinations_url(prompt: str, width: int = 1024, height: int = 768) -> str:
    """Return a deterministic Pollinations.ai image URL for a prompt."""
    encoded_prompt = quote(prompt, safe="")
    return f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&nologo=true"


def fetch_image(prompt: str, output_path: Path, timeout: int = 90) -> tuple[str, Path]:
    """Fetch a generated PNG and return its source URL and local path."""
    url = pollinations_url(prompt)
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(response.content)
    return url, output_path


def load_works(input_path: Path | None) -> list[dict]:
    """Load either one requested archive or the complete prose and poetry archive."""
    paths = [input_path] if input_path else [ROOT / "data" / "prose.json", ROOT / "data" / "poetry.json"]
    works = []
    for path in paths:
        works.extend(json.loads(path.read_text(encoding="utf-8")))
    return works


def cached_image_path(slug: str) -> Path | None:
    """Return an existing cached illustration path for a work slug."""
    for extension in (".png", ".jpg", ".jpeg"):
        candidate = WORKS_DIR / f"{slug}{extension}"
        if candidate.exists():
            return candidate
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate cached literary illustrations.")
    parser.add_argument("--input", type=Path, default=None, help="Optional single archive JSON file.")
    parser.add_argument("--limit", type=int, default=10, help="Maximum number of new images per session.")
    parser.add_argument("--delay", type=float, default=10, help="Delay between API requests in seconds.")
    parser.add_argument("--force", action="store_true", help="Ignore cached images and regenerate them.")
    args = parser.parse_args()

    if args.limit < 0 or args.delay < 0:
        parser.error("--limit and --delay must be non-negative")

    works = load_works(args.input.resolve() if args.input else None)
    generated = 0
    for work in works:
        slug = slugify(work.get("title", "untitled"))
        cached = cached_image_path(slug)
        if cached and not args.force:
            print(f"Пропущено (кэш): {slug}")
            continue
        if generated >= args.limit:
            break

        prompt = build_prompt(work)
        output_path = WORKS_DIR / f"{slug}.png"
        url, path = fetch_image(prompt, output_path)
        generated += 1
        print(f"Сгенерировано: {slug}")
        print(f"URL: {url}")
        print(f"Сохранено: {path} ({path.stat().st_size} bytes)")
        if generated < args.limit:
            time.sleep(args.delay)

    print(f"Новых изображений: {generated}")


if __name__ == "__main__":
    main()
