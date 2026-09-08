import html
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"

BRAND = "\u0411\u0438\u0431\u043b\u0438\u043e\u0442\u0435\u043a\u0430"
POETRY = "\u041f\u043e\u044d\u0437\u0438\u044f"
PROSE = "\u041f\u0440\u043e\u0437\u0430"
ABOUT = "\u041e\u0431 \u0430\u0432\u0442\u043e\u0440\u0435"


def generate_vignette(output_path: Path) -> Path:
    """Write a compact brass ink-style divider SVG and return its path."""
    source_path = ROOT / "assets" / "images" / "vignette.svg"
    if source_path.exists() and source_path.resolve() != output_path.resolve():
        output_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, output_path)
        return output_path
    svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 32" role="img" aria-label="Декоративный разделитель">
  <g fill="none" stroke="#C5A059" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round">
    <path d="M12 16h54c9 0 15-3 22-9"/>
    <path d="M228 16h-54c-9 0-15-3-22-9"/>
    <path d="M20 13c3-3 7-3 10 0s7 3 10 0"/>
    <path d="M220 13c-3-3-7-3-10 0s-7 3-10 0"/>
    <path d="M88 7c5 5 9 8 16 9-7 1-11 4-16 9-1-7-4-11-9-14 5-1 8-2 9-4z"/>
    <path d="M152 7c-5 5-9 8-16 9 7 1 11 4 16 9 1-7 4-11 9-14-5-1-8-2-9-4z"/>
    <path d="M120 4c-5 5-6 9 0 14 6-5 5-9 0-14z"/>
    <path d="M120 18c-7-5-12-5-16-1 5 4 10 5 16 1zM120 18c7-5 12-5 16-1-5 4-10 5-16 1z"/>
  </g>
  <circle cx="120" cy="18" r="1.7" fill="#C5A059"/>
</svg>
'''
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(svg, encoding="utf-8")
    return output_path


def slugify(value: str) -> str:
    value = re.sub(r"[^\w\s-]", "", value, flags=re.UNICODE).strip().lower()
    return re.sub(r"[-\s]+", "-", value) or "untitled"


def illustration_markup(work: dict) -> str:
    """Return an illustration tag when a matching work image exists."""
    slug = slugify(work.get("title", "untitled"))
    for extension in (".png", ".jpg", ".jpeg"):
        source = ROOT / "assets" / "images" / "works" / f"{slug}{extension}"
        if source.exists():
            return f'<img src="../../assets/images/works/{slug}{extension}" class="work-illustration" alt="Иллюстрация" loading="lazy">'
    return ""


def load_archive(name: str):
    path = ROOT / "data" / f"{name}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def group_works(works):
    groups = {}
    for work in works:
        groups.setdefault(work["book"], []).append(work)
    for book_works in groups.values():
        for index, work in enumerate(book_works):
            if "эпилог" in work.get("title", "").lower():
                book_works.append(book_works.pop(index))
                break
    return groups


POETRY_COLLECTIONS = {
    "Книга «О любви»",
    "Книга «Потерянные годы»",
    "Книга «Сквозь ад»",
    "Книга «Избранное»",
}


def display_book_name(book: str, kind: str) -> str:
    """Use collection terminology for the four poetry sections only."""
    if kind == "poetry" and book in POETRY_COLLECTIONS:
        return f"Сборник {book.removeprefix('Книга ')}"
    return book


def poetry_stanzas(text: str) -> list[str]:
    """Preserve real stanzas and normalize line-per-paragraph source exports."""
    parts = [part.strip() for part in re.split(r"\n[ \t]*\n", text) if part.strip()]
    if len(parts) > 1 and all("\n" not in part for part in parts):
        return ["\n".join(parts[index:index + 4]) for index in range(0, len(parts), 4)]
    return parts


def poetry_intro_and_stanzas(text: str, intro_blocks: int | None = None) -> tuple[list[str], list[str]]:
    """Separate leading prose paragraphs from a sustained four-line poem block."""
    parts = [part.strip() for part in re.split(r"\n[ \t]*\n", text) if part.strip()]
    if intro_blocks is not None:
        return parts[:intro_blocks], poetry_stanzas("\n\n".join(parts[intro_blocks:]))
    start = 0
    for index in range(max(0, len(parts) - 3)):
        candidate = parts[index:index + 4]
        if all(len(line) <= 80 for line in candidate) and sum(len(line) for line in candidate) <= 300:
            start = index
            break
    return parts[:start], poetry_stanzas("\n\n".join(parts[start:]))


def intro_blocks_for(work: dict, kind: str) -> int | None:
    """Read an explicit intro block count from the source Markdown front matter."""
    path = ROOT / "content" / kind / slugify(work.get("book", "")) / f"{slugify(work.get('title', ''))}.md"
    if not path.is_file():
        return None
    front_matter = path.read_text(encoding="utf-8").split("---", 2)
    if len(front_matter) < 2:
        return None
    match = re.search(r"^intro_blocks:\s*(\d+)\s*$", front_matter[1], re.MULTILINE)
    return int(match.group(1)) if match else None


def year_for(work: dict) -> str:
    match = re.search(r"\b(?:19|20)\d{2}\b", work.get("date", "") or work.get("url", ""))
    return match.group(0) if match else "2026"


def book_markup(groups: dict, kind: str) -> str:
    cards = []
    for book, works in groups.items():
        links = []
        for number, work in enumerate(works, 1):
            reader_path = f"reader/{kind}/{slugify(book)}-{slugify(work['title'])}-{number}.html?hall={kind}&book={slugify(book)}"
            links.append(f'<li><a href="{reader_path}">{html.escape(work["title"])}</a></li>')
        display_name = display_book_name(book, kind)
        cards.append(f'''<details class="book-card" data-book="{html.escape(slugify(book), quote=True)}">
  <summary class="book-summary">
    <span class="book-name">{html.escape(display_name)}</span>
    <span class="book-meta">{year_for(works[0])} · {len(works)} произведений</span>
  </summary>
  <ol class="work-list">{"".join(links)}</ol>
</details>''')
    return "\n".join(cards)


def navigation(active: str = "hall", prefix: str = "") -> str:
    home_class = ' class="active"' if active == "hall" else ""
    about_class = ' class="active"' if active == "about" else ""
    return f'''<nav class="top-nav" aria-label="Основная навигация">
      <a href="{prefix}index.html"{home_class}>Главная</a>
      <a href="{prefix}about.html"{about_class}>{ABOUT}</a>
    </nav>'''


def page_head(title: str, content: str, active: str = "hall") -> str:
    return f'''<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)} — {BRAND}</title>
  <link rel="stylesheet" href="css/site.css">
  <link rel="icon" type="image/svg+xml" href="favicon.svg">
</head>
<body>
{content}
<script src="js/site.js"></script>
</body>
</html>'''


def reader_page(work: dict, kind: str, book: str) -> str:
    if kind == "poetry":
        text = html.escape(work["text"]).replace("\n", "<br>\n")
        body = f'<div class="poem-text">{text}</div>'
    else:
        paragraphs = [part.strip() for part in re.split(r"\n\s*\n", work["text"]) if part.strip()]
        body = "".join(f'<p>{html.escape(part).replace(chr(10), "<br>")}</p>' for part in paragraphs)
    header = f'''<header class="site-header reader-header">
  {navigation("reader", "../../")}
  <a class="reader-back" href="../../index.html">← К списку книг</a>
</header>'''
    return f'''<!doctype html>
<html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{html.escape(work["title"])} — {BRAND}</title><link rel="stylesheet" href="../../css/site.css"><link rel="icon" type="image/svg+xml" href="../../favicon.svg"></head>
<body>{header}<main class="reader-content"><p class="reader-book">{html.escape(book)}</p><h1>{html.escape(work["title"])}</h1><div class="reader-text">{body}</div><footer class="publication-footer"><p>{html.escape(work["copyright"])}</p><p>{html.escape(work["certificate"])}</p></footer><a class="reader-back button" href="../../index.html">← К списку книг</a></main><script src="../../js/site.js"></script></body></html>'''


def write_assets():
    (SITE / "css").mkdir(parents=True, exist_ok=True)
    (SITE / "js").mkdir(parents=True, exist_ok=True)
    (SITE / "favicon.svg").write_text('''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" role="img" aria-labelledby="title desc">
  <title id="title">Библиотека</title>
  <desc id="desc">Стилизованный книжный переплёт</desc>
  <rect width="64" height="64" rx="10" fill="#121316"/>
  <path d="M11 14h18c4 0 7 3 7 7v31c-2-2-4-3-7-3H11z" fill="#252932" stroke="#c5a059" stroke-width="2"/>
  <path d="M53 14H35c-4 0-7 3-7 7v31c2-2 4-3 7-3h18z" fill="#1b1d22" stroke="#c5a059" stroke-width="2"/>
  <path d="M32 20v31M17 22h10M17 28h10M37 22h10M37 28h10" fill="none" stroke="#c5a059" stroke-width="2" stroke-linecap="round"/>
  <path d="M20 38h8M36 38h8" stroke="#c5a059" stroke-width="1.5" stroke-linecap="round"/>
</svg>
''', encoding="utf-8")
    vignette_source = ROOT / "assets" / "images" / "vignette.svg"
    vignette_target = SITE / "assets" / "images" / "vignette.svg"
    vignette_target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(vignette_source, vignette_target)
    portrait_source = ROOT / "assets" / "images" / "avtor.jpg"
    portrait_target = SITE / "assets" / "images" / "avtor.jpg"
    portrait_target.parent.mkdir(parents=True, exist_ok=True)
    if portrait_source.exists():
        shutil.copy2(portrait_source, portrait_target)
    works_source = ROOT / "assets" / "images" / "works"
    works_target = SITE / "assets" / "images" / "works"
    if works_source.exists():
        works_target.mkdir(parents=True, exist_ok=True)
        for image in works_source.iterdir():
            if image.is_file() and image.suffix.lower() in {".png", ".jpg", ".jpeg"}:
                shutil.copy2(image, works_target / image.name)
    (SITE / "css" / "site.css").write_text('''@import url("https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;500;600;700&family=Montserrat:wght@400;500;600&display=swap");
:root{--ink:#121316;--surface:#1b1d22;--paper:#e6e4df;--muted:#a9a69e;--brass:#c8a261;--line:rgba(230,228,223,.17);--serif:"Cormorant Garamond",Georgia,serif;--sans:"Montserrat",Arial,sans-serif}*{box-sizing:border-box}body{background:var(--ink);color:var(--paper);font:1.15rem/1.55 var(--serif);margin:0}a{color:inherit;text-decoration:none}.site-header{border-bottom:1px solid var(--line);margin:auto;max-width:76rem;padding:1.25rem clamp(1rem,5vw,4rem)}.top-nav{display:flex;flex-wrap:wrap;gap:1.25rem}.top-nav a,.reader-back,.reader-book,.book-meta,.site-footer,.tab-btn{font:500 .7rem/1.4 var(--sans);letter-spacing:.1em;text-transform:uppercase}.top-nav a{color:var(--muted)}.top-nav a:hover,.top-nav a.active{color:var(--brass)}.hero-section{align-items:start;display:grid;grid-template-columns:1fr 300px;gap:4rem;margin:3rem 0 5rem}.hero-content{max-width:600px;text-align:left}.hero-title{font-size:clamp(3rem,9vw,7rem);font-weight:500;line-height:1;letter-spacing:-.05em;margin:0 0 1.5rem}.hero-subtitle{color:var(--muted);font-size:clamp(1.25rem,2.5vw,1.7rem);margin:0}.hero-author-frame{flex-shrink:0}.author-portrait{width:300px;height:400px;object-fit:cover;border-radius:0;border:1px solid rgba(212,175,55,.25);box-shadow:0 20px 40px rgba(0,0,0,.7);display:block}.main-content{margin:auto;max-width:76rem;padding:0 clamp(1rem,5vw,4rem) 5rem}.hall-tabs{border-bottom:1px solid var(--line);display:flex;gap:1rem;margin-bottom:1.5rem}.tab-btn{background:none;border:0;border-bottom:2px solid transparent;color:var(--muted);cursor:pointer;padding:.9rem 0}.tab-btn.active{border-color:var(--brass);color:var(--brass)}.hall-section{display:block}.hall-section[style*="none"]{display:none}.book-card{background:var(--surface);border:1px solid var(--line);margin:.8rem 0}.book-summary{align-items:center;cursor:pointer;display:flex;gap:1rem;justify-content:space-between;list-style:none;padding:1.1rem 1.25rem}.book-summary::-webkit-details-marker{display:none}.book-name{font-size:1.45rem}.book-meta{color:var(--brass);white-space:nowrap}.work-list{border-top:1px solid var(--line);display:grid;gap:.25rem 1.5rem;grid-template-columns:1fr;margin:0;padding:.75rem 1.25rem .9rem 2.75rem}.work-list li{padding:.35rem 0}.work-list a:hover{color:var(--brass)}.site-footer{border-top:1px solid var(--brass);color:var(--muted);margin:2rem auto 0;max-width:76rem;padding:1.5rem clamp(1rem,5vw,4rem)}.site-footer p{margin:0}.reader-header{align-items:center;display:flex;gap:1.5rem;justify-content:space-between}.reader-content{margin:auto;max-width:52rem;padding:clamp(3rem,8vw,7rem) 1rem}.reader-content h1{font-size:clamp(2.8rem,7vw,5.5rem);line-height:1}.reader-book{color:var(--brass)}.reader-text{font-size:1.3rem;margin-top:3rem}.poem-text{line-height:1.8}.reader-text p{margin:0 0 1.5rem}.publication-footer{border-top:1px solid var(--brass);color:var(--muted);font:.72rem/1.6 var(--sans);margin-top:4rem;padding-top:1rem}.button{border:1px solid var(--brass);display:inline-block;margin-top:2rem;padding:.8rem 1rem}@media(min-width:48rem){.work-list{grid-template-columns:repeat(2,minmax(0,1fr))}.reader-content{padding-left:2rem;padding-right:2rem}}@media(max-width:768px){.hero-section{grid-template-columns:1fr;gap:2rem;text-align:center}.hero-content{text-align:center}.author-portrait{width:160px;height:200px;margin:0 auto}}
''', encoding="utf-8")
    with (SITE / "css" / "site.css").open("a", encoding="utf-8") as css:
        css.write("@media(max-width:768px){.book-summary{flex-wrap:wrap;align-items:flex-start;gap:8px}.book-name{overflow-wrap:break-word;word-break:break-word}.book-meta{white-space:normal}}")
        css.write(".reader-controls{display:flex;flex-wrap:wrap;gap:.75rem;justify-content:space-between;margin-top:2rem}.reader-control{border:1px solid var(--brass);font:500 .7rem/1.4 var(--sans);letter-spacing:.06em;padding:.75rem 1rem}.reader-control.is-disabled{border-color:var(--line);color:var(--muted)}.reader-home{background:var(--surface)}.reader-vignette{margin:3rem auto 2rem;max-width:15rem}.reader-vignette img{display:block;height:auto;max-width:100%;width:100%}.work-illustration{display:block;max-width:100%;height:auto;margin:2rem auto;border-radius:4px;opacity:.9}@media(min-width:48rem){.reader-vignette{max-width:20rem}}")
        css.write(".poem-text{line-height:1.4;white-space:pre-line}.poem-text>.poem-stanza{display:block;line-height:1.4;margin:0;padding:0 0 1.6em}.poem-text>.poem-stanza+.poem-stanza{margin-top:0}.poem-text>.poem-stanza:last-child{padding-bottom:0}")
        css.write(".poem-text{line-height:1.2;white-space:normal}.poem-text>.poem-stanza{line-height:1.2}")
        css.write(".poem-intro{font-style:italic;margin:0 0 2rem}")
    (SITE / "js" / "site.js").write_text('''function showHall(name) { const poetry = document.getElementById("poetry-hall"); const prose = document.getElementById("prose-hall"); const poetryButton = document.getElementById("btn-poetry"); const proseButton = document.getElementById("btn-prose"); const showPoetry = name === "poetry"; poetry.style.display = showPoetry ? "block" : "none"; prose.style.display = showPoetry ? "none" : "block"; poetryButton.classList.toggle("active", showPoetry); proseButton.classList.toggle("active", !showPoetry); }
''', encoding="utf-8")


def reader_page(work: dict, kind: str, book: str, previous_path: str | None = None, next_path: str | None = None) -> str:
    if kind == "poetry":
        intro_blocks, stanzas = poetry_intro_and_stanzas(work["text"], work.get("intro_blocks"))
        stanza_markup = []
        for stanza in stanzas:
            lines = html.escape(stanza).replace("\n", "<br>")
            stanza_markup.append(f'<div class="poem-stanza">{lines}</div>')
        intro_markup = "".join(f'<p class="poem-intro">{html.escape(block)}</p>' for block in intro_blocks)
        body = f'{intro_markup}<div class="poem-text">{"".join(stanza_markup)}</div>'
    else:
        paragraphs = [part.strip() for part in re.split(r"\n\s*\n", work["text"]) if part.strip()]
        body = "".join(f'<p>{html.escape(part).replace(chr(10), "<br>")}</p>' for part in paragraphs)
    previous = f'<a class="reader-control" href="{previous_path}">← Назад</a>' if previous_path else '<span class="reader-control is-disabled">← Назад</span>'
    following = f'<a class="reader-control" href="{next_path}">Вперёд →</a>' if next_path else '<span class="reader-control is-disabled">Вперёд →</span>'
    header = f'''<header class="site-header reader-header">
  {navigation("reader", "../../")}
  <a class="reader-back" href="../../index.html">К списку книг</a>
</header>'''
    controls = f'<nav class="reader-controls" aria-label="Навигация по книге">{previous}<a class="reader-control reader-home" href="../../index.html">К списку книг</a>{following}</nav>'
    return f'''<!doctype html>
<html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{html.escape(work["title"])} — {BRAND}</title><link rel="stylesheet" href="../../css/site.css?v=poetry-spacing-2"><link rel="icon" type="image/svg+xml" href="../../favicon.svg"></head>
<body>{header}<main class="reader-content"><p class="reader-book">{html.escape(book)}</p><h1>{html.escape(work["title"])}</h1><div class="reader-text">{body}</div><footer class="publication-footer"><p>{html.escape(work["copyright"])}</p><p>{html.escape(work["certificate"])}</p></footer>{controls}</main><script src="../../js/site.js"></script></body></html>'''


def add_reader_decorations(page: str, work: dict) -> str:
    """Insert the shared vignette and an available work illustration."""
    illustration = illustration_markup(work)
    if illustration:
        page = page.replace('<div class="reader-text">', f'<div class="reader-text">{illustration}', 1)
    decoration = '<div class="reader-vignette"><img src="../../assets/images/vignette.svg" alt="Декоративный разделитель"></div>'
    return page.replace('<footer class="publication-footer">', f'{decoration}<footer class="publication-footer">', 1)


def build():
    if SITE.exists():
        shutil.rmtree(SITE)
    write_assets()
    site_js = SITE / "js" / "site.js"
    site_js.write_text(site_js.read_text(encoding="utf-8") + 'const contextParams = new URLSearchParams(window.location.search); const requestedHall = contextParams.get("hall"); const requestedBook = contextParams.get("book"); showHall(requestedHall === "poetry" ? "poetry" : "prose"); if (requestedBook) { const card = Array.from(document.querySelectorAll("details.book-card")).find(item => item.dataset.book === requestedBook); if (card) card.open = true; }\n', encoding="utf-8")
    poetry = load_archive("poetry")
    prose = load_archive("prose")
    poetry_groups = group_works(poetry)
    prose_groups = group_works(prose)
    portrait_markup = ''
    if (ROOT / "assets" / "images" / "avtor.jpg").exists():
        portrait_markup = '<img src="assets/images/avtor.jpg" alt="Чернышев Евгений Александрович" class="author-portrait">'
    header = f'''<header class="site-header">
  {navigation("hall")}
  <section class="hero-section">
    <div class="hero-content">
      <h1 class="hero-title">\u0421\u043b\u043e\u0432\u0430, \u0445\u0440\u0430\u043d\u044f\u0449\u0438\u0435 \u0441\u043e\u0431\u0441\u0442\u0432\u0435\u043d\u043d\u044b\u0439 \u0441\u0432\u0435\u0442.</h1>
      <p class="hero-subtitle">\u0410\u0432\u0442\u043e\u0440\u0441\u043a\u0438\u0439 \u0430\u0440\u0445\u0438\u0432 \u043f\u0440\u043e\u0437\u044b \u0438 \u043f\u043e\u044d\u0437\u0438\u0438: \u043f\u0440\u043e\u0441\u0442\u0440\u0430\u043d\u0441\u0442\u0432\u043e \u0434\u043b\u044f \u0441\u043c\u044b\u0441\u043b\u043e\u0432, \u0442\u0440\u0435\u0431\u0443\u044e\u0449\u0438\u0445 \u0432\u0434\u0443\u043c\u0447\u0438\u0432\u043e\u0433\u043e \u0447\u0442\u0435\u043d\u0438\u044f.</p>
    </div>
    <div class="hero-author-frame">{portrait_markup}</div>
  </section>
</header>'''
    main = f'''<main class="main-content">
  <div class="hall-tabs" role="tablist">
    <button id="btn-prose" class="tab-btn active" onclick="showHall('prose')" role="tab">{PROSE}</button>
    <button id="btn-poetry" class="tab-btn" onclick="showHall('poetry')" role="tab">{POETRY}</button>
  </div>
  <section id="prose-hall" class="hall-section">{book_markup(prose_groups, "prose")}</section>
  <section id="poetry-hall" class="hall-section" style="display: none;">{book_markup(poetry_groups, "poetry")}</section>
</main>'''
    footer = '<footer class="site-footer"><p>2026 Евгений Чернышев · Литературный архив</p></footer>'
    index = f'''<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{BRAND}</title><link rel="stylesheet" href="css/site.css"><link rel="icon" type="image/svg+xml" href="favicon.svg"></head><body>{header}{main}{footer}<script src="js/site.js"></script></body></html>'''
    (SITE / "index.html").write_text(index, encoding="utf-8")
    about_header = f'''<header class="site-header">
  {navigation("about")}
  <div class="hero-block">
    <h1 class="site-title">\u0421\u043b\u043e\u0432\u043e \u0430\u0432\u0442\u043e\u0440\u0430</h1>
    <p class="site-subtitle">\u041c\u0430\u043d\u0438\u0444\u0435\u0441\u0442 \u043f\u0440\u043e\u0441\u0442\u0440\u0430\u043d\u0441\u0442\u0432\u0430</p>
  </div>
</header>'''
    about_main = '''<main class="main-content about-content"><article class="manifesto"><p>Библиотека — это форма внимания. Этот архив даёт каждому тексту пространство, чтобы продолжать звучать после первой публикации.</p><p>«Библиотека» — тихое место для произведений, которые связаны единой внутренней логикой, но не теряют своей индивидуальности. Она собирает прозу и поэзию в их собственные залы, сохраняя автономность каждой работы и нити, связывающие их воедино.</p><p>Это собрание создано для вдумчивого чтения и перечитывания: в размеренном темпе, на чистой академической полосе, без суеты перед тем, что требует времени и мысли.</p></article></main>'''
    about = f'''<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Слово автора — {BRAND}</title><link rel="stylesheet" href="css/site.css"><link rel="icon" type="image/svg+xml" href="favicon.svg"></head><body>{about_header}{about_main}{footer}<script src="js/site.js"></script></body></html>'''
    (SITE / "about.html").write_text(about, encoding="utf-8")
    for kind, works in (("poetry", poetry), ("prose", prose)):
        for book, book_works in group_works(works).items():
            for number, work in enumerate(book_works, 1):
                work = dict(work)
                if kind == "poetry":
                    work["intro_blocks"] = intro_blocks_for(work, kind)
                path = SITE / "reader" / kind / f"{slugify(book)}-{slugify(work['title'])}-{number}.html"
                path.parent.mkdir(parents=True, exist_ok=True)
                previous_path = None
                next_path = None
                if number > 1:
                    previous = book_works[number - 2]
                    previous_path = f"{slugify(book)}-{slugify(previous['title'])}-{number - 1}.html"
                if number < len(book_works):
                    following = book_works[number]
                    next_path = f"{slugify(book)}-{slugify(following['title'])}-{number + 1}.html"
                page = reader_page(work, kind, display_book_name(book, kind), previous_path, next_path)
                page = page.replace('href="../../index.html"', f'href="../../index.html?hall={kind}&book={slugify(book)}"')
                path.write_text(add_reader_decorations(page, work), encoding="utf-8")
    print(f"Built site: {len(poetry)} poetry works, {len(prose)} prose works.")


if __name__ == "__main__":
    build()
