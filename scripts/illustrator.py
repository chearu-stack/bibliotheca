"""Prompt construction, caching, and optional Pollinations.ai image fetching."""

from __future__ import annotations

import argparse
import json
import os
import re
import time
from pathlib import Path
from urllib.parse import quote

import requests
from dotenv import load_dotenv

# Disable broken system proxy settings for direct API requests.
for _proxy_variable in (
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "http_proxy",
    "https_proxy",
    "ALL_PROXY",
    "all_proxy",
):
    os.environ[_proxy_variable] = ""

DIRECT_SESSION = requests.Session()
DIRECT_SESSION.trust_env = False

from build_site import slugify


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
WORKS_IMG_DIR = os.path.join(BASE_DIR, "assets", "images", "works")
os.makedirs(WORKS_IMG_DIR, exist_ok=True)
ROOT = Path(BASE_DIR)
WORKS_DIR = Path(WORKS_IMG_DIR)
load_dotenv(ROOT / ".env")
API_URL = "https://api.deepseek.com/chat/completions"
MODEL = "deepseek-v4-flash"
ALLOWED_MODELS = ("deepseek-v4-flash", "deepseek-v4-pro")
STYLE = "minimalist dark pencil drawing, Pushkin manuscript margin sketch style, solitary and poetic vibe, clean line art, monochrome on dark paper"
FINAL_STYLE = "minimalist dark pencil sketch, Pushkin manuscript margin drawing style, clean monochrome line art, dark paper texture"
POLLINATIONS_STYLE_SUFFIX = ", strict academic drawing, heavy charcoal sketch, raw graphite pencil, highly detailed crosshatching, classic book illustration, monochromatic black and white. ABSOLUTELY NO anime, NO manga, NO comic, NO smooth digital rendering, NO cartoon."
DIRECTOR_SYSTEM_PROMPT = "Ты — арт-директор книжного издания. Прочитай текст и выдели 1-2 главных ключевых ВЕЩЕСТВЕННЫХ предмета или сцену (например: сосновый лес, костер, старый рюкзак, мотоцикл на дороге). Напиши короткий промпт на английском (до 15 слов) для генерации лаконичного наброска карандашом/тушью."


def generate_art_prompt(text_content: str) -> str:
    """Ask DeepSeek via BotHub for a short, text-grounded visual scene."""
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise RuntimeError("DEEPSEEK_API_KEY is not set in the local .env file.")
    if MODEL not in ALLOWED_MODELS:
        raise RuntimeError(f"Unsupported DeepSeek model: {MODEL}")
    truncated_text = text_content[:1200]
    payload = {
        "model": MODEL,
        "temperature": 0.2,
        "max_tokens": 2048,
        "messages": [
            {"role": "system", "content": DIRECTOR_SYSTEM_PROMPT},
            {"role": "user", "content": truncated_text},
        ],
    }
    response = DIRECT_SESSION.post(
        API_URL,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json=payload,
        proxies={"http": None, "https": None},
        timeout=90,
    )
    if response.status_code != 200:
        print(f"Ошибка DeepSeek: {response.status_code} - {response.text}")
        response.raise_for_status()
    try:
        result = response.json()["choices"][0]["message"]["content"] or ""
    except (KeyError, IndexError, TypeError, ValueError):
        print(f"Ошибка DeepSeek: {response.status_code} - {response.text}")
        raise RuntimeError("DeepSeek returned an invalid response payload.")
    scene = re.sub(r"[\"'`]+", "", re.sub(r"\s+", " ", result)).strip(" .,:;—-\n")
    scene = " ".join(scene.split()[:15])
    if not scene:
        print(f"Ошибка DeepSeek: {response.status_code} - {response.text}")
        raise RuntimeError("DeepSeek returned an empty art prompt.")
    return scene


def build_prompt(work: dict) -> str:
    """Build the final Pollinations prompt from DeepSeek's art direction."""
    scene = generate_art_prompt(work.get("text", ""))
    return f"{scene}, {FINAL_STYLE}"


def pollinations_url(prompt: str, width: int = 1024, height: int = 768) -> str:
    """Return a deterministic Pollinations.ai image URL for a prompt."""
    encoded_prompt = quote(prompt, safe="")
    return f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&nologo=true"


class PollinationsError(RuntimeError):
    """Raised when Pollinations cannot produce an image after retries."""


def fetch_image(prompt: str, output_path: Path, timeout: int = 90) -> tuple[str, Path]:
    """Fetch a generated PNG, retrying throttled or timed-out requests."""
    final_prompt = prompt.strip() + POLLINATIONS_STYLE_SUFFIX
    url = pollinations_url(final_prompt)
    for attempt in range(1, 4):
        try:
            response = DIRECT_SESSION.get(
                url,
                proxies={"http": None, "https": None},
                timeout=timeout,
            )
            if response.status_code == 429:
                if attempt < 3:
                    print("Pollinations 429: жду 30 секунд...")
                    time.sleep(30)
                    continue
                raise PollinationsError("HTTP 429 after 3 attempts")
            response.raise_for_status()
            if len(response.content) < 10000:
                print("Файл слишком мал, это не картинка")
                raise PollinationsError("response content is smaller than 10 KB")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(response.content)
            return url, output_path
        except requests.exceptions.Timeout:
            if attempt < 3:
                print("Pollinations 429: жду 30 секунд...")
                time.sleep(30)
                continue
            raise PollinationsError("timeout after 3 attempts") from None
        except requests.exceptions.RequestException as error:
            raise PollinationsError(str(error)) from error
    raise PollinationsError("request failed after 3 attempts")


def load_works(input_path: Path | None) -> list[dict]:
    """Load either one requested archive or the complete prose and poetry archive."""
    paths = [input_path] if input_path else [ROOT / "data" / "prose.json", ROOT / "data" / "poetry.json"]
    works = []
    for path in paths:
        works.extend(json.loads(path.read_text(encoding="utf-8")))
    return works


def find_work(works: list[dict], requested_slug: str) -> dict:
    """Resolve a work by its generated slug or the documented romance alias."""
    normalized = requested_slug.removeprefix("slug_").replace("_", "-")
    for work in works:
        if slugify(work.get("title", "untitled")) == normalized:
            return work
    if normalized == "romantika":
        for work in works:
            if slugify(work.get("title", "")).startswith("романтика-vs-романтик"):
                return work
    # Reader filenames can differ from the source record title; resolve them by source URL.
    for markdown_path in ROOT.joinpath("content").glob(f"**/{normalized}.md"):
        markdown_text = markdown_path.read_text(encoding="utf-8")
        source_match = re.search(r'^source:\s*["\']?([^"\'\r\n]+)', markdown_text, re.MULTILINE)
        if source_match:
            source_url = source_match.group(1).strip()
            for work in works:
                if work.get("source") == source_url or work.get("url") == source_url:
                    content = markdown_text.split("---", 2)[-1].strip()
                    resolved = dict(work)
                    resolved["title"] = normalized
                    resolved["text"] = content
                    resolved["_slug"] = normalized
                    return resolved
    raise ValueError(f"Work slug not found: {requested_slug}")


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
    parser.add_argument("--slug", default=None, help="Generate only the selected work slug.")
    parser.add_argument("--exclude-slug", action="append", default=[], help="Never process this work slug.")
    args = parser.parse_args()

    if args.limit < 0 or args.delay < 0:
        parser.error("--limit and --delay must be non-negative")

    works = load_works(args.input.resolve() if args.input else None)
    if args.slug:
        works = [find_work(works, args.slug)]
    excluded_slugs = {item.removeprefix("slug_").replace("_", "-") for item in args.exclude_slug}
    generated = 0
    for work in works:
        slug = work.get("_slug") or slugify(work.get("title", "untitled"))
        if slug in excluded_slugs:
            print(f"Исключено: {slug}")
            continue
        cached = cached_image_path(slug)
        if cached and not args.force:
            print(f"Пропущено (кэш): {slug}")
            continue
        if generated >= args.limit:
            break

        try:
            prompt = build_prompt(work)
            scene = prompt.removesuffix(f", {FINAL_STYLE}")
            print(f"DeepSeek prompt: {scene}")
            output_path = WORKS_DIR / f"{slug}.png"
            url, path = fetch_image(prompt, output_path)
        except PollinationsError:
            print(f"Пропуск: {slug} (ошибка Pollinations)")
            continue
        except Exception as error:
            print(f"Ошибка: {slug}: {error}")
            continue
        generated += 1
        print(f"Сгенерировано: {slug}")
        print(f"URL: {url}")
        print(f"Сохранено: {path} ({path.stat().st_size} bytes)")
        print(f"Абсолютный путь: {path.resolve()}")
        print(f"Размер: {path.stat().st_size / 1024:.2f} КБ")
        if generated < args.limit:
            time.sleep(args.delay)

    print(f"Новых изображений: {generated}")


if __name__ == "__main__":
    main()
