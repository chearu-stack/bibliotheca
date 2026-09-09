import argparse
import json
import re
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

STIHI_AUTHOR_URL = "https://stihi.ru/avtor/djekpot2000"
PROZA_AUTHOR_URL = "https://proza.ru/avtor/djekpot2000"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; BibliothecaArchive/1.0)"}
ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
BOOK_PREFIX = "\u041a\u043d\u0438\u0433\u0430"
FAVORITES_BOOK = "\u041a\u043d\u0438\u0433\u0430 \u00ab\u0418\u0437\u0431\u0440\u0430\u043d\u043d\u043e\u0435\u00bb"
CONTAINER_TYPES = {
    "\u041a\u043d\u0438\u0433\u0430 \u00ab\u041e \u043b\u044e\u0431\u0432\u0438\u00bb": "collection",
    "\u041a\u043d\u0438\u0433\u0430 \u00ab\u041f\u043e\u0442\u0435\u0440\u044f\u043d\u043d\u044b\u0435 \u0433\u043e\u0434\u044b\u00bb": "collection",
    "\u041a\u043d\u0438\u0433\u0430 \u00ab\u0421\u043a\u0432\u043e\u0437\u044c \u0430\u0434\u00bb": "collection",
    "\u041a\u043d\u0438\u0433\u0430 \u00ab\u0418\u0437\u0431\u0440\u0430\u043d\u043d\u043e\u0435\u00bb": "collection",
    "\u041a\u043d\u0438\u0433\u0430 \u00ab\u0418\u0437\u0431\u0440\u0430\u043d\u043d\u0430\u044f \u043f\u0440\u043e\u0437\u0430\u00bb": "collection",
    "\u041a\u043d\u0438\u0433\u0430 \u00ab\u0426\u0438\u0432\u0438\u043b\u0438\u0437\u0430\u0446\u0438\u044f \u0433\u043b\u0430\u0437\u0430\u043c\u0438 \u0437\u0434\u0440\u0430\u0432\u043e\u0433\u043e \u0441\u043c\u044b\u0441\u043b\u0430\u00bb": "cycle",
}
PROSE_BOOK_RULES = [
    (re.compile(r"^(\u044d\u043f\u0438\u043b\u043e\u0433|\u043a\u043d\u0438\u0433\u0430\s+\u043f\u0435\u0440\u0432\u0430\b|\u043a\u043d\u0438\u0433\u0430\s+\u0432\u0442\u043e\u0440\u0430\b|\u043a\u043d\u0438\u0433\u0430\s+\u0442\u0440\u0435\u0442\u044c\u044f\b|\u043a\u043d\u0438\u0433\u0430\s+\u0447\u0435\u0442\u0432\u0451\u0440\u0442\u0430\b|\u043a\u043d\u0438\u0433\u0430\s+\u043f\u044f\u0442\u0430\u044f\b)", re.IGNORECASE), "\u041a\u043d\u0438\u0433\u0430 \u00ab\u041f\u044f\u0442\u044c \u0432\u043e\u043f\u0440\u043e\u0441\u043e\u0432 \u043a \u0431\u0435\u0437\u043c\u043e\u043b\u0432\u0438\u044e\u00bb"),
    (re.compile(r"^(\u043f\u0443\u0442\u044c \u0434\u0443\u0440\u0430\u043a\u0430|\u0432\u0441\u0442\u0443\u043f\u043b\u0435\u043d\u0438\u0435|\u0433\u043b\u0430\u0432\u0430 1\.\s*\u043e \u0434\u0435\u043d\u044c\u0433\u0430\u0445|\u0433\u043b\u0430\u0432\u0430 2\s+\u043e \u0432\u043e\u0437\u0440\u0430\u0441\u0442\u0435|\u0433\u043b\u0430\u0432\u0430 3\.\s*\u043e \u0441\u0430\u043c\u043e\u043e\u0431\u043c\u0430\u043d\u0435|\u0433\u043b\u0430\u0432\u0430 4\.\s*\u043e \u0437\u0430\u0432\u0438\u0441\u0438\u043c\u043e\u0441\u0442\u0438|\u0433\u043b\u0430\u0432\u0430 5\.\s*\u043e \u0434\u0435\u0442\u044f\u0445|\u0433\u043b\u0430\u0432\u0430 6\.\s*\u043e \u0434\u0443\u0440\u0430\u043a\u0435)", re.IGNORECASE), "\u041a\u043d\u0438\u0433\u0430 \u00ab\u041f\u0443\u0442\u044c \u0414\u0443\u0440\u0430\u043a\u0430\u00bb"),
    (re.compile(r"^\u0441\u043b\u043e\u0432\u043e\b", re.IGNORECASE), "\u041a\u043d\u0438\u0433\u0430 \u00ab\u0421\u043b\u043e\u0432\u043e\u00bb"),
    (re.compile(r"^(\u043f\u044f\u0442\u044c \u043f\u0440\u043e\u0446\u0435\u043d\u0442\u043e\u0432|\u043a\u043e\u0432\u0447\u0435\u0433|\u044d\u0432\u043e\u043b\u044e\u0446\u0438\u044f|\u043f\u0440\u0438\u0432\u0435\u0442 \u043e\u0442 \u0434\u0438\u043d\u043e\u0437\u0430\u0432\u0440\u043e\u0432)", re.IGNORECASE), "\u041a\u043d\u0438\u0433\u0430 \u00ab\u0426\u0438\u0432\u0438\u043b\u0438\u0437\u0430\u0446\u0438\u044f \u0433\u043b\u0430\u0437\u0430\u043c\u0438 \u0437\u0434\u0440\u0430\u0432\u043e\u0433\u043e \u0441\u043c\u044b\u0441\u043b\u0430\u00bb"),
    (re.compile(r"^(\u043e\u0442 \u0430\u0432\u0442\u043e\u0440\u0430|\u0433\u043b\u0430\u0432\u0430 [1-3])", re.IGNORECASE), "\u041a\u043d\u0438\u0433\u0430 \u00ab\u0424\u0443\u0433\u0443 \u0434\u043b\u044f \u0447\u0435\u043b\u043e\u0432\u0435\u0447\u0435\u0441\u0442\u0432\u0430\u00bb"),
]


def slugify(value: str) -> str:
    value = re.sub(r"[^\w\s-]", "", value, flags=re.UNICODE).strip().lower()
    return re.sub(r"[-\s]+", "-", value) or "untitled"


def container_type_for(book: str) -> str:
    """Return the scalable container taxonomy used by the site builder."""
    return CONTAINER_TYPES.get(book, "book")


def fetch(url: str, timeout: int = 15):
    last_error = None
    for attempt in range(1, 4):
        try:
            response = requests.get(url, headers=HEADERS, timeout=timeout)
            response.encoding = "windows-1251"
            response.raise_for_status()
            return response, BeautifulSoup(response.text, "html.parser")
        except requests.RequestException as error:
            last_error = error
            if attempt < 3:
                time.sleep(attempt)
    raise last_error


def absolute_url(domain: str, href: str) -> str:
    return domain + href if href.startswith("/") else href


def parse_work_page(url: str, book: str):
    try:
        response, soup = fetch(url, 12)
        text_div = soup.find("div", class_="text")
        if not text_div:
            return None
        for br in text_div.find_all("br"):
            br.replace_with("\n")
        title_node = soup.find("h1")
        title = title_node.get_text(strip=True) if title_node else "\u0411\u0435\u0437 \u043d\u0430\u0437\u0432\u0430\u043d\u0438\u044f"
        page_text = soup.get_text(" ", strip=True)
        date_match = re.search(r"\d{2}\.\d{2}\.\d{4}\s+\d{2}:\d{2}", response.text)
        date = date_match.group(0) if date_match else ""
        year = date[-4:] if date else ""
        copyright_match = re.search(r"©?\s*Copyright:\s*([^,\n]+,\s*\d{4})", page_text, re.IGNORECASE)
        copyright_text = copyright_match.group(1).strip() if copyright_match else f"\u0415\u0432\u0433\u0435\u043d\u0438\u0439 \u0410\u043b\u0435\u043a\u0441\u0430\u043d\u0434\u0440\u043e\u0432\u0438\u0447 \u0427\u0435\u0440\u043d\u044b\u0448\u0435\u0432{', ' + year if year else ''}"
        certificate_match = re.search(r"\u0421\u0432\u0438\u0434\u0435\u0442\u0435\u043b\u044c\u0441\u0442\u0432\u043e\s+\u043e\s+\u043f\u0443\u0431\u043b\u0438\u043a\u0430\u0446\u0438\u0438\s+\u2116?\s*(\d+)", page_text, re.IGNORECASE)
        certificate = f"\u0421\u0432\u0438\u0434\u0435\u0442\u0435\u043b\u044c\u0441\u0442\u0432\u043e \u043e \u043f\u0443\u0431\u043b\u0438\u043a\u0430\u0446\u0438\u0438 №{certificate_match.group(1)}" if certificate_match else "\u0421\u0432\u0438\u0434\u0435\u0442\u0435\u043b\u044c\u0441\u0442\u0432\u043e \u043e \u043f\u0443\u0431\u043b\u0438\u043a\u0430\u0446\u0438\u0438"
        return {"title": title, "book": book, "container_type": container_type_for(book), "date": date, "copyright": f"Copyright: {copyright_text}", "certificate": certificate, "url": url, "text": text_div.get_text().strip()}
    except requests.RequestException as error:
        print(f"[!] Request failed: {url}: {error}", flush=True)
        return None


def collect_book_links(domain: str, soup: BeautifulSoup):
    books = []
    seen_books = set()
    for link in soup.find_all("a", href=True):
        href = link["href"]
        if "book=" not in href:
            continue
        url = absolute_url(domain, href)
        if url in seen_books:
            continue
        seen_books.add(url)
        name = link.get_text(" ", strip=True) or "\u0411\u0435\u0437 \u043d\u0430\u0437\u0432\u0430\u043d\u0438\u044f"
        book = name if name.startswith(BOOK_PREFIX) else f"{BOOK_PREFIX} \u00ab{name}\u00bb"
        books.append((book, url))
    return books


def classify_prose_book(title: str) -> str:
    for pattern, book in PROSE_BOOK_RULES:
        if pattern.search(title.strip()):
            return book
    return "\u041a\u043d\u0438\u0433\u0430 \u00ab\u0418\u0437\u0431\u0440\u0430\u043d\u043d\u0430\u044f \u043f\u0440\u043e\u0437\u0430\u00bb"


def classify_prose_book(title: str) -> str:
    value = title.strip().lower()
    if value.startswith(("\u044d\u043f\u0438\u043b\u043e\u0433", "\u043a\u043d\u0438\u0433\u0430 \u043f\u0435\u0440\u0432\u0430\u044f", "\u043a\u043d\u0438\u0433\u0430 \u0432\u0442\u043e\u0440\u0430\u044f", "\u043a\u043d\u0438\u0433\u0430 \u0442\u0440\u0435\u0442\u044c\u044f", "\u043a\u043d\u0438\u0433\u0430 \u0447\u0435\u0442\u0432\u0451\u0440\u0442\u0430\u044f", "\u043a\u043d\u0438\u0433\u0430 \u043f\u044f\u0442\u0430\u044f")):
        return "\u041a\u043d\u0438\u0433\u0430 \u00ab\u041f\u044f\u0442\u044c \u0432\u043e\u043f\u0440\u043e\u0441\u043e\u0432 \u043a \u0431\u0435\u0437\u043c\u043e\u043b\u0432\u0438\u044e\u00bb"
    if value.startswith(("\u043f\u0443\u0442\u044c \u0434\u0443\u0440\u0430\u043a\u0430", "\u0432\u0441\u0442\u0443\u043f\u043b\u0435\u043d\u0438\u0435", "\u0433\u043b\u0430\u0432\u0430 1. \u043e \u0434\u0435\u043d\u044c\u0433\u0430\u0445", "\u0433\u043b\u0430\u0432\u0430 2 \u043e \u0432\u043e\u0437\u0440\u0430\u0441\u0442\u0435", "\u0433\u043b\u0430\u0432\u0430 3. \u043e \u0441\u0430\u043c\u043e\u043e\u0431\u043c\u0430\u043d\u0435", "\u0433\u043b\u0430\u0432\u0430 4. \u043e \u0437\u0430\u0432\u0438\u0441\u0438\u043c\u043e\u0441\u0442\u0438", "\u0433\u043b\u0430\u0432\u0430 5. \u043e \u0434\u0435\u0442\u044f\u0445", "\u0433\u043b\u0430\u0432\u0430 6. \u043e \u0434\u0443\u0440\u0430\u043a\u0435")):
        return "\u041a\u043d\u0438\u0433\u0430 \u00ab\u041f\u0443\u0442\u044c \u0414\u0443\u0440\u0430\u043a\u0430\u00bb"
    if value.startswith("\u0441\u043b\u043e\u0432\u043e"):
        return "\u041a\u043d\u0438\u0433\u0430 \u00ab\u0421\u043b\u043e\u0432\u043e\u00bb"
    if value.startswith(("\u043f\u044f\u0442\u044c \u043f\u0440\u043e\u0446\u0435\u043d\u0442\u043e\u0432", "\u043a\u043e\u0432\u0447\u0435\u0433", "\u044d\u0432\u043e\u043b\u044e\u0446\u0438\u044f", "\u043f\u0440\u0438\u0432\u0435\u0442 \u043e\u0442 \u0434\u0438\u043d\u043e\u0437\u0430\u0432\u0440\u043e\u0432")):
        return "\u041a\u043d\u0438\u0433\u0430 \u00ab\u0426\u0438\u0432\u0438\u043b\u0438\u0437\u0430\u0446\u0438\u044f \u0433\u043b\u0430\u0437\u0430\u043c\u0438 \u0437\u0434\u0440\u0430\u0432\u043e\u0433\u043e \u0441\u043c\u044b\u0441\u043b\u0430\u00bb"
    if value.startswith(("\u043e\u0442 \u0430\u0432\u0442\u043e\u0440\u0430", "\u0433\u043b\u0430\u0432\u0430 1. \u0441\u0442\u0430\u0440\u0438\u043a", "\u0433\u043b\u0430\u0432\u0430 2. \u043f\u0438\u0440\u0430\u043c\u0438\u0434\u044b", "\u0433\u043b\u0430\u0432\u0430 3. \u043e\u0434\u0438\u043d", "\u0433\u043b\u0430\u0432\u0430 4. \u043f\u0440\u043e\u043f\u0438\u0441\u043a\u0430 \u0432 \u0433\u043e\u043b\u043e\u0432\u0435")):
        return "\u041a\u043d\u0438\u0433\u0430 \u00ab\u0424\u0443\u0433\u0443 \u0434\u043b\u044f \u0447\u0435\u043b\u043e\u0432\u0435\u0447\u0435\u0441\u0442\u0432\u0430\u00bb"
    return "\u041a\u043d\u0438\u0433\u0430 \u00ab\u0418\u0437\u0431\u0440\u0430\u043d\u043d\u0430\u044f \u043f\u0440\u043e\u0437\u0430\u00bb"


def parse_portal_archive(author_url: str, output_dir: Path, json_name: str, book_limit=None, work_limit=None):
    domain = "https://stihi.ru" if "stihi.ru" in author_url else "https://proza.ru"
    print(f"[*] Author page: {author_url}", flush=True)
    author_urls = [author_url]
    if "stihi.ru" in author_url:
        author_urls = [f"{author_url}?s={offset}" for offset in (0, 50, 100)]
    author_soups = [fetch(url)[1] for url in author_urls]
    author_soup = author_soups[0]
    books = collect_book_links(domain, author_soup)
    if book_limit:
        books = books[:book_limit]
    print(f"[*] Books selected: {len(books)}", flush=True)
    queue = []
    assigned = set()
    for book, book_url in books:
        print(f"[*] Reading book: {book}", flush=True)
        _, book_soup = fetch(book_url, 12)
        for anchor in book_soup.find_all("a", class_="poemlink"):
            url = absolute_url(domain, anchor["href"])
            if url not in assigned:
                assigned.add(url)
                queue.append((url, book, anchor.get_text(" ", strip=True)))
    if not book_limit or not books:
        for page_soup in author_soups:
            for anchor in page_soup.find_all("a", class_="poemlink"):
                url = absolute_url(domain, anchor["href"])
                if url not in assigned:
                    assigned.add(url)
                    label = anchor.get_text(" ", strip=True)
                    book = classify_prose_book(label) if "proza.ru" in author_url else FAVORITES_BOOK
                    queue.append((url, book, label))
    if work_limit:
        queue = queue[:work_limit]
    print(f"[*] Works queued: {len(queue)}", flush=True)
    works = []
    for number, (url, book, label) in enumerate(queue, start=1):
        print(f"[{number}/{len(queue)}] Downloading: {label or url}", flush=True)
        work = parse_work_page(url, book)
        if work:
            works.append(work)
        time.sleep(0.4)
    save_archive_files(works, output_dir, DATA_DIR / json_name)
    return len(books), len(works)


def save_archive_files(works, content_dir: Path, json_path: Path):
    content_dir.mkdir(parents=True, exist_ok=True)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    # The archive content is generated output. Remove only old Markdown files
    # from this portal before writing the current authoritative snapshot.
    for old_file in content_dir.rglob("*.md"):
        old_file.unlink()
    for old_dir in sorted((path for path in content_dir.rglob("*") if path.is_dir()), key=lambda path: len(path.parts), reverse=True):
        try:
            old_dir.rmdir()
        except OSError:
            pass
    json_path.write_text(json.dumps(works, ensure_ascii=False, indent=2), encoding="utf-8")
    for work in works:
        folder = content_dir / slugify(work["book"])
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / f"{slugify(work['title'])}.md"
        path.write_text(f'''---\ntitle: "{work["title"]}"\nbook: "{work["book"]}"\ncontainer_type: "{work["container_type"]}"\ndate: "{work["date"]}"\ncopyright: "{work["copyright"]}"\ncertificate: "{work["certificate"]}"\nsource: "{work["url"]}"\n---\n\n# {work["title"]}\n\n{work["text"]}\n\n---\n\n<footer class="publication-certificate">\n  <p><em>{work["copyright"]}</em><br>\n  <em>{work["certificate"]}</em></p>\n</footer>\n''', encoding="utf-8")
    print(f"[*] Saved {len(works)} Markdown files in {content_dir}", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true", help="Process one book and five works only")
    parser.add_argument("--portal", choices=("poetry", "prose"), default="poetry")
    args = parser.parse_args()
    if args.test:
        if args.portal == "prose":
            parse_portal_archive(PROZA_AUTHOR_URL, ROOT_DIR / "content" / "prose-test", "prose-test.json", book_limit=1, work_limit=1)
        else:
            parse_portal_archive(STIHI_AUTHOR_URL, ROOT_DIR / "content" / "poetry-test", "poetry-test.json", book_limit=1, work_limit=5)
        print("Test complete; full archive was not downloaded.", flush=True)
    else:
        poetry_books, poetry_works = parse_portal_archive(STIHI_AUTHOR_URL, ROOT_DIR / "content" / "poetry", "poetry.json")
        prose_books, prose_works = parse_portal_archive(PROZA_AUTHOR_URL, ROOT_DIR / "content" / "prose", "prose.json")
        print(f"Total: books={poetry_books + prose_books}; works={poetry_works + prose_works}.", flush=True)
