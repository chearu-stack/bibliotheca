Делегировать сборку файловой структуры и рутинную верстку кодовому агенту — максимально прагматичный инженерный ход.

Ниже подготовлен полная спецификация для **`README.md`**, которую поймет любой кодовый агент (Codex, Cursor, Claude Code), и отдельная пошаговая команда для привязки к GitHub.

---

### 1. Текст файла `README.md` (Инструкция для Агента)

Создай в корне проекта файл `README.md` и помести туда следующий текст:

```markdown
# Bibliotheca Architecture & Automated Build Specification

## System Overview
Automated build instruction for generating a status-driven, academic-style digital library.
Theme: Deep dark library, graphite background (`#121316`), aged brass accents (`#c8a261`), parchment typography (`#e6e4df`).
Typography: `Cormorant Garamond` (Serif for headings and content) + `Montserrat` (Sans-serif for metadata and interface UI).

## Required Directory Structure
Create the following modular architecture:

```text
/
├── index.html              # Main Hall (Entry, Manifesto, Hall Selector)
├── about.html              # Author Statement & Philosophy
├── prose/
│   └── index.html          # Prose Gallery (Proza.ru cycles)
├── poetry/
│   └── index.html          # Poetry Gallery (Stihi.ru cycles)
├── css/
│   ├── variables.css       # Design tokens (colors, typography, grid)
│   ├── reset.css           # CSS Reset
│   ├── typography.css      # Academic publisher-grade typography
│   └── layout.css          # Grid, cards, navigation bar, reader containers
├── js/
│   └── main.js             # Minimalistic page transitions
└── assets/
    ├── images/
    └── fonts/

```

## CSS Tokens & Styles Implementation

### 1. `css/variables.css`

```css
@import url('[https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,600;0,700;1,400&family=Montserrat:wght@300;400;500&display=swap](https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,600;0,700;1,400&family=Montserrat:wght@300;400;500&display=swap)');

:root {
    --bg-primary: #121316;
    --bg-surface: #1a1c23;
    --bg-elevated: #22252e;
    --border-color: #2d313e;
    --border-accent: #3a3f50;
    --text-primary: #e6e4df;
    --text-secondary: #9ea3b0;
    --text-muted: #626775;
    --accent-brass: #c8a261;
    --accent-brass-hover: #e0b875;
    --font-serif: 'Cormorant Garamond', Georgia, serif;
    --font-sans: 'Montserrat', -apple-system, sans-serif;
    --max-width-site: 1080px;
    --max-width-text: 720px;
}

```

### 2. `css/reset.css`

Standard reset for box-sizing, margins, reset lists, and anchor defaults.

### 3. `css/typography.css`

Set `font-family: var(--font-serif)` for headers (`h1`-`h4`) and literary text. Set line-height to 1.7. Set `font-family: var(--font-sans)` for navigation links, buttons, and system metadata.

### 4. `css/layout.css`

Build responsive layout with centered containers (`max-width: var(--max-width-site)`), top navigation header, dark cards for book cycles, and brass hover transitions.

## Content Mapping for `prose/index.html`

Generate clean, structured literary blocks using direct links to Proza.ru:

1. **Пять вопросов к безмолвию**
* Эпилог, который должен быть Прологом (`https://proza.ru/2026/02/02/914`)
* Книга первая. Зарождение (`https://proza.ru/2026/01/18/2039`)
* Книга вторая. Исполины (`https://proza.ru/2026/02/01/2207`)
* Книга третья. Просеивание (`https://proza.ru/2026/01/25/1248`)
* Книга четвёртая. Предшественники (`https://proza.ru/2026/01/30/1869`)
* Книга пятая. Пробуждение (`https://proza.ru/2026/01/15/1565`)


2. **Путь Дурака**
* О чём эта книга (`https://proza.ru/2026/03/03/1599`)
* Вступление, которое не просили (`https://proza.ru/2026/03/03/1606`)
* Глава 1. О деньгах (`https://proza.ru/2026/03/03/1611`)
* Глава 2. О возрасте (Молодость: `1616`, Середина: `1619`, Зрелость: `1625`)
* Глава 3. О самообмане (`1642`), Глава 4. О зависимости (`1658`), Глава 5. О детях (`1663`), Глава 6. О дураке (`1684`)


3. **Слово**
* Глава 1–4 (`190`, `1791`, `1960`, `1847`)
* Глава 5. Изгнанный (Часть 1: `1289`, Часть 2: `1097`, Часть 3: `1719`)


4. **Фугу для человечества**
* От автора (`1506`), Глава 1 (`1510`), Глава 2 (`1355`), Глава 3 (`1413`)


5. **Цивилизация глазами здравого смысла**
* Пять процентов (`69`), Ковчег непуганых идиотов (`150`), Эволюция фаянсового престола (`142`), Привет от динозавров (`2063`)


6. **Отдельные рассказы**
* Железный конь (`51`), РомАнтика vs РомантИк (`1614`), Монахи на колёсах (`894`)



## Execution Command for Agent

`Please execute this specification. Create all directories, CSS files, JavaScript entry points, and HTML templates strictly following the provided layout and styling instructions.`

```

---

### 2. Связывание с GitHub и отправка первой сборки

После того как агент сформирует файлы в твоей локальной папке, выполни в терминале эти команды для инициализации и отправки кода в репозиторий:

```bash
# 1. Инициализация локального репозитория
git init

# 2. Добавление всех созданных файлов
git add .

# 3. Фиксация первого коммита
git commit -m "feat: initial academic library structure via agent"

# 4. Установка главной ветки
git branch -M main

# 5. Связывание с созданным репозиторием на GitHub
git remote add origin https://github.com/chearu-stack/bibliotheca.git

# 6. Отправка кода на GitHub
git push -u origin main

```

Запускай агента с этим `README.md` — он сделает всю рутинную раскладку за минуты.