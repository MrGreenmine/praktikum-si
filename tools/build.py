#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Сборка статического сайта «практикум по Си» из выгруженного контента."""
import os, re, json, html as ihtml, shutil, sys
BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
from codefmt import mark_code

SRC = BASE + "/clean"
# Куда собирать сайт. По умолчанию — папка site/ рядом с tools/,
# можно переопределить аргументом командной строки или переменной окружения:
#   python3 build.py /путь/к/папке
#   PRAKTIKUM_OUT=/путь/к/папке python3 build.py
DST = os.environ.get("PRAKTIKUM_OUT") or (sys.argv[1] if len(sys.argv) > 1 else os.path.join(BASE, os.pardir, "site"))
DST = os.path.abspath(DST)

# ---------------------------------------------------------------- структура
# (чистый ключ, новый путь, заголовок, короткое описание для меню)
WORKS = [
    # №, тема из рабочего плана, старая страница, неделя, ключ clean
    (1,  "Написание и компиляция консольного приложения",        "работа-1",   1,  "rabota-1"),
    (2,  "Работа с функцией printf",                            "работа-2",   2,  "rabota-2"),
    (3,  "Форматированный ввод/вывод",                          "работа-3",   3,  "rabota-3"),
    (4,  "Особенности использования данных различного типа",    "работа-4",   3,  "rabota-4"),
    (5,  "Использование функций стандартной библиотеки языка Си","работа-5",  4,  "rabota-5"),
    (6,  "Реализация разветвляющихся алгоритмов",              "работа-6",   5,  "rabota-6"),
    (7,  "Многоальтернативная обработка данных",                "работа-7",   5,  "rabota-7"),
    (8,  "Организация цикла с параметрами",                    "работа-8",   6,  "rabota-8"),
    (9,  "Реализация циклических алгоритмов",                   "работа-9",   7,  "rabota-9"),
    (10, "Конструирование функций",                            "работа-10",  8,  "rabota-10"),
    (11, "Структуры данных",                                   "работа-18",  9,  "rabota-18"),
    (12, "Запись в файл",                                      "работа-19",  9,  "rabota-19"),
    (13, "Чтение из файла",                                    "работа-20",  10, "rabota-20"),
    (15, "Работа с одномерными массивами",                      "работа-11",  11, "rabota-11"),
    (16, "Генерация случайных чисел",                          "работа-25",  11, "rabota-25"),
    (17, "Работа с указателями",                               "работа-12",  11, "rabota-12"),
    (18, "Передача массива в функцию",                         "работа-14",  12, "rabota-14"),
    (19, "Динамические массивы",                               "работа-16",  13, "rabota-16"),
    (20, "Работа со строками",                                 "работа-13",  14, "rabota-13"),
    (21, "Алгоритмы сортировки",                               "работа-17",  15, "rabota-17"),
    (22, "Рекурсия",                                           "работа-27",  16, "rabota-27-rekursiya"),
    (23, "Передача функции по указателю",                      "работа-22",  17, "rabota-22"),
    (24, "Многомерные статистические массивы",                 "работа-15",  17, "rabota-15"),
    (25, "Массивы указателей",                                 "работа-26",  17, "rabota-26-massivy-ukazateley"),
    (26, "Массив записей",                                     "работа-21",  18, "rabota-21-zapisi"),
]
# работы вне рабочего плана
EXTRA_WORKS = [
    (27, "Связанный список", "работа-23", "rabota-23"),
    (28, "Стеки и очереди",   "работа-24", "rabota-24"),
]

def wfile(n):   return f"praktika/rabota-{n:02d}.html"

# slug оригинала -> новый путь
SLUG2NEW = {
    "": "index.html",
    "главная": "index.html",
    "главная/источники": "istochniki.html",
    "главная/справочник-по-языку-си": "spravochnik/index.html",
    "главная/справочник-по-языку-си/алфавит": "spravochnik/alfavit.html",
    "главная/справочник-по-языку-си/ввод-вывод": "spravochnik/vvod-vyvod.html",
    "главная/примеры": "spravochnik/primery.html",
    "главная/инструменты-разработки": "instrumenty/index.html",
    "главная/инструменты-разработки/создание-проекта": "instrumenty/sozdanie-proekta.html",
    "главная/инструменты-разработки/настройки-проекта": "instrumenty/nastroyki-proekta.html",
    "главная/инструменты-разработки/работа-с-git": "instrumenty/git.html",
    "главная/инструменты-разработки/работа-с-git/работа-с-github": "instrumenty/git/github.html",
    "главная/инструменты-разработки/языковые-настройки-и-локализация": "instrumenty/lokalizaciya.html",
    "главная/инструменты-разработки/помощник-по-ide-mvs": "instrumenty/ide-mvs.html",
    "шкала-прогресса": "praktika/shkala.html",
    "кп": "kp/index.html",
    "кп/содержание-пояснительной-записки": "kp/soderzhanie.html",
    "кп/оформление-пояснительной-записки": "kp/oformlenie.html",
    "кп/codestyle": "kp/codestyle.html",
    "практика": "praktika/index.html",
}
for n, _t, old, _w, key in WORKS:
    SLUG2NEW[f"практика/{old}"] = wfile(n)
for n, _t, old, key in EXTRA_WORKS:
    SLUG2NEW[f"практика/{old}"] = f"praktika/dop/rabota-{n}.html"
SLUG2NEW["практика/работа-14-модули"] = "praktika/rabota-14.html"

# ---------------------------------------------------------------- меню
def wmenu(n, title):
    d = {"title": f"Работа {n}. {title}", "file": wfile(n), "num": n}
    if n in (23, 24, 25):
        d["note"] = "вне темы КП"
    return d

def emenu(n, title):
    return {"title": f"Работа {n}. {title}", "file": f"praktika/dop/rabota-{n}.html",
            "num": n, "note": "вне рабочего плана"}

# полный порядок работ в меню (1…26, включая отсутствовавшую на сайте № 14)
NAV_WORKS = []
for _n, _t, _o, _w, _k in WORKS:
    NAV_WORKS.append((_n, _t))
NAV_WORKS.insert([x[0] for x in NAV_WORKS].index(15), (14, "Модульное построение программ"))

NAV = [
    {"title": "Главная", "file": "index.html"},
    {"title": "Практика", "children": [
        {"title": "Организация лабораторных работ", "file": "praktika/index.html"},
        {"sep": True},
        *[wmenu(n, t) for n, t in NAV_WORKS[:9]],
        {"title": "Контрольная работа", "file": "kp/index.html", "note": "промежуточная аттестация"},
        {"sep": True},
        *[wmenu(n, t) for n, t in NAV_WORKS[9:]],
        {"sep": True},
        {"title": "Дополнительные работы", "note": "сверх рабочего плана", "children": [
            *[emenu(n, t) for n, t, _o, _k in EXTRA_WORKS],
        ]},
        {"sep": True},
        {"title": "Шкала прогресса", "file": "praktika/shkala.html"},
    ]},
    {"title": "Справочник по языку Си", "children": [
        {"title": "Обзор раздела", "file": "spravochnik/index.html"},
        {"title": "Алфавит", "file": "spravochnik/alfavit.html"},
        {"title": "Ввод и вывод", "file": "spravochnik/vvod-vyvod.html"},
        {"title": "Примеры", "file": "spravochnik/primery.html"},
    ]},
    {"title": "Инструменты разработки", "children": [
        {"title": "Обзор раздела", "file": "instrumenty/index.html"},
        {"title": "Создание проекта", "file": "instrumenty/sozdanie-proekta.html"},
        {"title": "Настройки проекта", "file": "instrumenty/nastroyki-proekta.html"},
        {"title": "Работа с Git", "children": [
            {"title": "Работа с GitHub", "file": "instrumenty/git/github.html"},
        ]},
        {"title": "Языковые настройки и локализация", "file": "instrumenty/lokalizaciya.html"},
        {"title": "Помощник по IDE MVS", "file": "instrumenty/ide-mvs.html"},
    ]},
    {"title": "Контрольная работа", "children": [
        {"title": "Обзор раздела", "file": "kp/index.html"},
        {"title": "Содержание пояснительной записки", "file": "kp/soderzhanie.html"},
        {"title": "Оформление пояснительной записки", "file": "kp/oformlenie.html"},
        {"title": "CodeStyle", "file": "kp/codestyle.html"},
    ]},
    {"title": "Источники", "file": "istochniki.html"},
]

# плоский список страниц для prev/next и поиска
def flatten(nav, parent=None):
    out = []
    for it in nav:
        if it.get("sep"): continue
        if it.get("file"):
            out.append({"title": it["title"], "file": it["file"],
                        "parent": parent, "note": it.get("note"), "num": it.get("num")})
        if it.get("children"):
            out += flatten(it["children"], it["title"])
    return out

PAGES = flatten(NAV)
PAGEMAP = {p["file"]: p for p in PAGES}

# ---------------------------------------------------------------- утилиты
def relpath(target, from_file):
    d = os.path.dirname(from_file)
    return os.path.relpath(target, d).replace("\\", "/")

def strip_footer(h):
    """Убирает подвал «Авторы курса …» (на части страниц он разорван на узлы)."""
    cut = len(h)
    for marker in ("Авторы курса", '<a href="mailto:ominakova', "Курипта О.В."):
        p = h.rfind(marker)
        if p >= 0 and p >= len(h) - 600:
            cut = min(cut, p)
    return h[:cut].rstrip()

def drop_h1(h):
    m = re.match(r"\s*<h1[^>]*>.*?</h1>", h, re.S)
    if m: h = h[m.end():]
    return h.lstrip()

def get_text(h):
    t = re.sub(r"<[^>]+>", " ", h)
    return re.sub(r"\s+", " ", t).strip()

def fix_links(h, cur_file):
    """Переписывает внутренние ссылки Google Sites на относительные пути нового сайта."""
    def rep(m):
        pre, href = m.group(1), m.group(2)
        if href.startswith("/view/course-of-study1-c/"):
            slug = urllib_unquote(href[len("/view/course-of-study1-c/"):].strip("/"))
            new = SLUG2NEW.get(slug)
            if new:
                return pre + ihtml.escape(relpath(new, cur_file), quote=True) + '"'
        return m.group(0)
    return re.sub(r'(<a[ >][^>]*?href=")([^"]*)"', rep, h, flags=re.S)

def urllib_unquote(s):
    from urllib.parse import unquote
    return unquote(s)

def clean_html(h):
    """Убирает мусор Google Sites, приводит к аккуратному виду."""
    h = re.sub(r"<br\s*/?>\s*</br>", "<br>", h)
    h = re.sub(r"</p>\s*<p>", "</p><p>", h)
    h = re.sub(r"</li>\s*</ul>", "</li></ul>", h)
    h = re.sub(r"<p>(\s*)</p>", "", h)
    h = re.sub(r"<li>(\s*)</li>", r"<li>\1</li>", h)
    # пустые <p> с пробелами
    h = re.sub(r"<p>\s*</p>", "", h)
    # ссылки на mailto без текста
    h = re.sub(r"<a href=\"mailto:[^\"]*\"></a>", "", h)
    # абзацы с исходным кодом -> блоки <pre><code>
    h = mark_code(h)
    return h.strip()

def balance(h):
    """Проставляет недостающие закрывающие теги."""
    VOID = {"br","hr","img","meta","link","input","source","col","area","base","embed","param"}
    stack = []
    for m in re.finditer(r"<(/?)([a-zA-Z][\w:-]*)([^>]*)>", h):
        close, tag, attrs = m.group(1), m.group(2), m.group(3)
        if tag in VOID or attrs.endswith("/"): continue
        if close:
            if tag in stack:
                while stack:
                    t = stack.pop()
                    if t == tag: break
        else:
            stack.append(tag)
    return h + "".join(f"</{t}>" for t in reversed(stack))

# ---------------------------------------------------------------- страницы
def read(key):
    p = os.path.join(SRC, key + ".html")
    if not os.path.exists(p): return ""
    return open(p, encoding="utf-8").read()

def page_title_orig(h):
    m = re.search(r"<h1[^>]*>(.*?)</h1>", h, re.S)
    if not m: return ""
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", m.group(1))).strip()

def build_page(file, title, body, desc="", badges="", toc=True, extra_class=""):
    """Собирает HTML-страницу по общему шаблону."""
    idx = PAGES.index(PAGEMAP[file]) if file in PAGEMAP else None
    prev_p = PAGES[idx - 1] if idx and idx > 0 else None
    next_p = PAGES[idx + 1] if idx is not None and idx + 1 < len(PAGES) else None
    # хлебные крошки
    crumbs = []
    p = PAGEMAP.get(file)
    if p:
        par = p["parent"]
        crumbs.append(("Главная", relpath("index.html", file)))
        if par:
            crumbs.append((par, None))
        crumbs.append((title, None))
    crumb_html = "".join(
        f'<li><a href="{ihtml.escape(h, quote=True)}">{ihtml.escape(t)}</a></li>' if h
        else f'<li aria-current="page">{ihtml.escape(t)}</li>'
        for t, h in crumbs)

    nav_html = render_nav(NAV, file, relpath("index.html", file))
    pn = ""
    if prev_p or next_p:
        pn = '<nav class="pager">'
        if prev_p:
            pn += (f'<a class="pager-prev" href="{ihtml.escape(relpath(prev_p["file"], file), quote=True)}">'
                   f'<span class="pager-dir">← предыдущая</span>'
                   f'<span class="pager-title">{ihtml.escape(prev_p["title"])}</span></a>')
        if next_p:
            pn += (f'<a class="pager-next" href="{ihtml.escape(relpath(next_p["file"], file), quote=True)}">'
                   f'<span class="pager-dir">следующая →</span>'
                   f'<span class="pager-title">{ihtml.escape(next_p["title"])}</span></a>')
        pn += "</nav>"

    toc_html = ""
    if toc:
        toc_html = '<aside class="toc" id="toc"><div class="toc-title">На странице</div><nav id="toc-list"></nav></aside>'

    return f"""<!DOCTYPE html>
<html lang="ru" data-theme="light">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{ihtml.escape(title)} — практикум по Си</title>
<meta name="description" content="{ihtml.escape(desc or title)}">
<link rel="stylesheet" href="{relpath('assets/style.css', file)}">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='14' fill='%231f6feb'/%3E%3Ctext x='32' y='45' font-size='36' font-family='monospace' font-weight='bold' fill='white' text-anchor='middle'%3EC%3C/text%3E%3C/svg%3E">
</head>
<body class="{extra_class}">
<a class="skip" href="#main">К содержанию</a>
<header class="topbar">
  <button class="burger" id="burger" aria-label="Меню" aria-expanded="false"><span></span><span></span><span></span></button>
  <a class="brand" href="{relpath('index.html', file)}"><span class="brand-mark">C</span><span class="brand-text">практикум<br><b>по Си</b></span></a>
  <div class="search-wrap">
    <input type="search" id="search" placeholder="Поиск по сайту…" autocomplete="off" aria-label="Поиск по сайту">
    <div class="search-box" id="search-box" hidden></div>
  </div>
  <button class="theme-btn" id="theme-btn" aria-label="Сменить тему"><span class="ico-sun">☀</span><span class="ico-moon">☾</span></button>
</header>
<div class="layout">
  <nav class="sidebar" id="sidebar" aria-label="Навигация по сайту"><div class="nav-tools">
      <button type="button" id="nav-expand">Развернуть</button>
      <button type="button" id="nav-collapse">Свернуть</button>
    </div><ul class="nav-root">{nav_html}</ul></nav>
  <div class="backdrop" id="backdrop"></div>
  <main class="content" id="main">
    <ol class="crumbs">{crumb_html}</ol>
    <article class="doc">
      <h1 class="doc-title">{title}</h1>
      {badges}
      {body}
    </article>
    {pn}
    <footer class="site-foot">
      <div class="foot-cols">
        <div><b>Кафедра систем управления и информационных технологий</b><br>
             Строительство ВГТУ · курс «Основы программирования и алгоритмизация»</div>
        <div><b>Авторы курса</b><br>
             О.В. Минакова — <a href="mailto:ominakova@vgasu.vrn.ru">ominakova@vgasu.vrn.ru</a><br>
             О.В. Курипта — <a href="mailto:okuripta@cchgeu.ru">okuripta@cchgeu.ru</a></div>
        <div><b>Материалы</b><br>
             Стандарт C89/C99 · Visual Studio 2017/2022 · MVS</div>
      </div>
      <div class="foot-note">Страница переработана: единая нумерация лабораторных работ по рабочему плану,
      исправлены битые таблицы и ссылки, меню приведено к логическому порядку.</div>
    </footer>
  </main>
  {toc_html}
</div>
<script src="{relpath('assets/search-index.js', file)}"></script>
<script src="{relpath('assets/app.js', file)}"></script>
</body>
</html>"""

def render_nav(items, cur_file, base):
    out = []
    def walk(items, depth):
        for it in items:
            if it.get("sep"):
                out.append('<li class="nav-sep" role="separator"></li>'); continue
            f = it.get("file")
            title = it["title"]
            active = f and relpath(f, cur_file) == cur_file
            cls = "nav-item" + (" is-active" if active else "")
            if f:
                href = relpath(f, cur_file)
                label = f'<a href="{ihtml.escape(href, quote=True)}">{ihtml.escape(title)}</a>'
                if it.get("num"):
                    short = title.split(". ", 1)[1] if title.startswith("Работа ") and ". " in title else title
                    label = (f'<a href="{ihtml.escape(href, quote=True)}">'
                             f'<span class="nav-num">{it["num"]}</span>'
                             f'<span class="nav-txt">{ihtml.escape(short)}</span></a>')
            else:
                label = f'<span class="nav-group">{ihtml.escape(title)}</span>'
            note = f'<span class="nav-note">{ihtml.escape(it["note"])}</span>' if it.get("note") else ""
            has_kids = bool(it.get("children"))
            tog = ('<button class="nav-tog" aria-label="Развернуть">▾</button>' if has_kids else "")
            out.append(f'<li class="{cls}" data-depth="{depth}">{tog}{label}{note}')
            if has_kids:
                out.append(f'<ul class="nav-sub"{" open" if active or _any_active(it, cur_file) else ""}>')
                walk(it["children"], depth + 1)
                out.append("</ul>")
            out.append("</li>")
    walk(items, 0)
    return "\n".join(out)

def _any_active(it, cur_file):
    for c in it.get("children", []):
        if c.get("file") and relpath(c["file"], cur_file) == cur_file: return True
        if c.get("children") and _any_active(c, cur_file): return True
    return False

# ---------------------------------------------------------------- главная
def plan_rows():
    """Строки рабочего плана в порядке выполнения (включая КП после 9-й работы)."""
    rows = []
    for n, title, old, week, key in WORKS:
        rows.append((n, title, old, week))
    # № 14 — страницы на оригинале не было, но в плане она значится
    rows.insert([r[0] for r in rows].index(15), (14, "Модульное построение программ", None, 10))
    return rows

def plan_table():
    rows = []
    for n, title, old, week in plan_rows():
        if old:
            oldnum = int(re.sub(r"\D", "", old) or 0)
            badge = (f'<span class="badge badge-old">прежняя № {oldnum}</span>' if oldnum != n
                     else '<span class="badge badge-same">без изменений</span>')
        else:
            badge = '<span class="badge badge-new">страница создана</span>'
        star = ' <span class="badge badge-star" title="вне темы курсового проекта">*</span>' if n in (23, 24, 25) else ""
        link = f"praktika/rabota-{n:02d}.html"
        rows.append(f"""      <tr>
        <td class="num"><a href="{link}">{n}</a></td>
        <td class="week">{week}</td>
        <td class="topic"><a href="{link}">{ihtml.escape(title)}</a>{star}</td>
        <td class="old">{badge}</td>
      </tr>""")
        if n == 9:
            rows.append("""      <tr class="row-kp">
        <td class="num">КП</td><td class="week">—</td>
        <td class="topic"><a href="kp/index.html">Контрольная работа (промежуточная аттестация)</a></td>
        <td class="old">—</td>
      </tr>""")
    return "\n".join(rows)

def extra_table():
    rows = []
    for n, title, old, key in EXTRA_WORKS:
        oldnum = int(re.sub(r"\D", "", old) or 0)
        rows.append(f"""      <tr>
        <td class="num"><a href="praktika/dop/rabota-{n}.html">{n}</a></td>
        <td class="week">—</td>
        <td class="topic"><a href="praktika/dop/rabota-{n}.html">{ihtml.escape(title)}</a></td>
        <td class="old"><span class="badge badge-old">прежняя № {oldnum}</span></td>
      </tr>""")
    return "\n".join(rows)

# ---------------------------------------------------------------- сборка
def main():
    if os.path.exists(DST): shutil.rmtree(DST)
    os.makedirs(DST)
    os.makedirs(f"{DST}/assets")
    for sub in ("praktika", "praktika/dop", "spravochnik", "instrumenty", "instrumenty/git", "kp"):
        os.makedirs(f"{DST}/{sub}", exist_ok=True)

    search = []

    def add(file, title, body, desc="", badges="", toc=True, idx=None):
        html_out = page_title = build_page(file, title, body, desc, badges, toc)
        path = os.path.join(DST, file)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        open(path, "w", encoding="utf-8").write(html_out)
        search.append({"url": relpath(file, "index.html"), "title": title,
                       "section": PAGEMAP.get(file, {}).get("parent", "") or "Главная",
                       "text": get_text(body)[:1800]})

    # ---------- Главная ----------
    idx_body = read("index")
    idx_body = strip_footer(idx_body)
    # убираем битый markdown-план (он заменяется настоящей таблицей)
    i = idx_body.find("Рабочий план лабораторных занятий")
    intro = idx_body[:i] if i > 0 else idx_body
    intro = drop_h1(intro)
    intro = re.sub(r"<h2[^>]*>\s*</h2>", "", intro)
    intro = clean_html(balance(fix_links(intro, "index.html")))
    # заголовок раздела
    intro = intro.replace("<h3>", "<h2>").replace("</h3>", "</h2>")
    main_body = f"""{intro}

<h2 id="plan">Рабочий план лабораторных занятий</h2>
<p class="lead">План на осень 2026 года. Номера лабораторных работ приведены в соответствие
с рабочим планом — именно в этом порядке работы и выполняются. В колонке «прежняя нумерация»
указано, под каким номером работа была размещена на старой версии сайта.</p>

<div class="table-wrap">
<table class="plan">
  <thead>
    <tr><th>№</th><th>Неделя</th><th>Тема лабораторной работы</th><th>Прежняя нумерация</th></tr>
  </thead>
  <tbody>
{plan_table()}
  </tbody>
</table>
</div>
<p class="note"><b>*)</b> работы № 23, 24 и 25 отмечены в плане знаком «*» — они идут
после модуля по указателям и <b>не входят в тему курсового проекта</b>.
Контрольная работа (КП) стоит в плане между 9-й и 10-й работами.</p>

<h2 id="dop">Работы сверх рабочего плана</h2>
<p class="lead">Эти работы есть на сайте, но в рабочем плане не значатся. Их можно выполнять
по желанию — они не входят в тему курсового проекта.</p>
<div class="table-wrap">
<table class="plan">
  <thead><tr><th>№</th><th>Неделя</th><th>Тема</th><th>Прежняя нумерация</th></tr></thead>
  <tbody>
{extra_table()}
  </tbody>
</table>
</div>

<h2 id="how">Как пользоваться сайтом</h2>
<ul class="cards">
  <li><b>Меню слева</b> — разделы в логическом порядке: практика, справочник, инструменты, контрольная работа, источники.</li>
  <li><b>Поиск</b> — поле в верхней панели ищет по всем страницам сразу (Ctrl&nbsp;+&nbsp;K).</li>
  <li><b>Тёмная тема</b> — кнопка ☀/☾ в правом верхнем углу, выбор сохраняется в браузере.</li>
  <li><b>Код</b> — блоки с исходниками можно копировать кнопкой «Копировать».</li>
  <li><b>Печать</b> — Ctrl&nbsp;+&nbsp;P: скрываются меню и панели, остаётся только текст работы.</li>
</ul>

<div class="note note-info">
  <b>Про нумерацию.</b> На старой версии сайта работы шли вразнобой: «Работа 22» стояла рядом
  с «Работой 10», а пункт «Работа 25.Работа 16» вообще назывался двумя номерами сразу.
  Теперь номер каждой работы совпадает с её местом в рабочем плане, а старый номер сохранён
  в подписи <span class="badge badge-old">прежняя № N</span> — чтобы старые ссылки и записи
  в электронном журнале оставались понятными.
</div>
"""
    add("index.html", "Основы программирования и алгоритмизация", main_body,
        desc="Практикум по языку Си: рабочий план лабораторных работ, справочник, инструменты разработки.")

    # ---------- Источники ----------
    s = strip_footer(read("istochniki"))
    s = drop_h1(s)
    s = clean_html(balance(fix_links(s, "istochniki.html")))
    add("istochniki.html", "Источники", f'<div class="doc-body">{s}</div>')

    # ---------- Практика: обзор ----------
    pr = strip_footer(read("praktika"))
    pr = drop_h1(pr)
    pr = clean_html(balance(fix_links(pr, "praktika/index.html")))
    pr_body = f"""<p class="lead">Ниже — порядок выполнения лабораторных работ и краткие
указания по оформлению отчётов. Полный план с темами — на <a href="../index.html#plan">главной</a>.</p>
<div class="doc-body">{pr}</div>"""
    add("praktika/index.html", "Организация лабораторных работ", pr_body)

    # ---------- Работы ----------
    for n, title, old, week, key in WORKS:
        h = strip_footer(read(key))
        orig = page_title_orig(h)
        body = drop_h1(h)
        body = clean_html(balance(fix_links(body, wfile(n))))
        oldnum = int(re.sub(r"\D", "", old) or 0)
        badges = ""
        if oldnum != n:
            badges = (f'<p class="badges"><span class="badge badge-old">прежняя нумерация: Работа {oldnum}</span>'
                      f'<span class="badge badge-week">неделя {week}</span></p>')
        else:
            badges = f'<p class="badges"><span class="badge badge-week">неделя {week}</span></p>'
        if week == 17:
            badges += '<p class="note note-warn"><b>Работа вне темы курсового проекта</b> — она идёт '\
                      'в плане со знаком «*» и не входит в тему КП.</p>'
        if n == 16:
            badges += '<p class="note note-info">Нумерация этой работы на старом сайте была сбита: '\
                      'в меню значилось «Работа 25.Работа 16». Здесь номер приведён к плану.</p>'
        body_html = f'{badges}<div class="doc-body">{body}</div>'
        add(wfile(n), f"Работа {n}. {title}", body_html,
            desc=f"Лабораторная работа {n}: {title}. Неделя {week}.")

    # ---------- Работа 14 (модульное построение) — страницы на сайте не было ----------
    mod_body = """<p class="lead">На старой версии сайта эта строка рабочего плана вела в никуда:
отдельной страницы с заданием не существовало. Здесь собраны требования к модульному
построению программы — они же изложены в разделе <a href="../kp/codestyle.html#modules">CodeStyle</a>.</p>

<h2 id="modules">Зачем нужно модульное построение</h2>
<p>Модульный код с чётким разделением меньше подвержен ошибкам, проще сопровождается
и легче расширяется. В языке Си нет встроенного механизма модулей, но разделение достигается
методами и соглашениями, описанными ниже.</p>
<p><b>Модуль</b> — это группа процедур и данных, совместно реализующих некую абстракцию:
например, организацию стека или задачу управления памятью.</p>
<div class="note">
  <b>Интерфейсная часть.</b> Роль интерфейса играют заголовочные файлы (с расширением <code>.h</code>)
  с объявлениями функций, определениями констант и типов. Реализация помещается в файлы
  с расширением <code>.c</code>.
</div>

<h2 id="rules">Основные правила</h2>
<ol>
  <li>Разделяйте программы на модули. Степень модульности определяется сложностью задачи
      и требованиями к производительности обмена между модулями.</li>
  <li>Заголовочный файл (<code>.h</code>) содержит объявления функций и типы; он не должен
      содержать реализаций.</li>
  <li>Файл реализации (<code>.c</code>) подключает свой заголовочный файл и реализует
      объявленные в нём функции.</li>
  <li>Порядок разделов в <code>.h</code>: комментарий-шапка → <code>#include</code> →
      <code>#define</code> → объявления типов и функций.</li>
  <li>Используйте осмысленные имена функций: функция должна делать что-то полезное и возвращать значение.</li>
  <li>Все объявления комментируются; избегайте «магических чисел».</li>
  <li>Используйте только функции стандартной библиотеки (стандарт C99).</li>
</ol>

<h2 id="example">Пример разделения на модули</h2>
<div class="doc-body">
<pre><code>/* circle.h — интерфейс модуля */
#ifndef CIRCLE_H
#define CIRCLE_H

typedef struct {
    double x;   /* центр окружности */
    double y;
    double r;   /* радиус */
} circle_t;

double circle_area(circle_t c);
circle_t circle_make(double x, double y, double r);

#endif /* CIRCLE_H */
</code></pre>
<pre><code>/* circle.c — реализация модуля */
#include &lt;stdio.h&gt;
#include "circle.h"

#define PI 3.14159265358979

double circle_area(circle_t c)
{
    return PI * c.r * c.r;
}

circle_t circle_make(double x, double y, double r)
{
    circle_t c;
    c.x = x;
    c.y = y;
    c.r = r;
    return c;
}
</code></pre>
<pre><code>/* main.c — программа */
#include &lt;stdio.h&gt;
#include "circle.h"

int main(void)
{
    circle_t c = circle_make(0.0, 0.0, 2.5);
    printf("Площадь круга = %lf\n", circle_area(c));
    return 0;
}
</code></pre>
</div>

<p class="note note-info">Полные требования к оформлению кода и структуре файлов —
в разделе <a href="../kp/codestyle.html#modules">CodeStyle → Организация программы</a>.</p>
"""
    add("praktika/rabota-14.html", "Работа 14. Модульное построение программ", mod_body,
        desc="Лабораторная работа 14: модульное построение программ. Неделя 10.",
        badges='<p class="badges"><span class="badge badge-week">неделя 10</span>'
               '<span class="badge badge-new">страница создана при переработке сайта</span></p>')

    # ---------- Дополнительные работы ----------
    for n, title, old, key in EXTRA_WORKS:
        h = strip_footer(read(key))
        orig = page_title_orig(h)
        body = drop_h1(h)
        body = clean_html(balance(fix_links(body, f"praktika/dop/rabota-{n}.html")))
        oldnum = int(re.sub(r"\D", "", old) or 0)
        badges = (f'<p class="badges"><span class="badge badge-old">прежняя нумерация: Работа {oldnum}</span>'
                  f'<span class="badge badge-star">вне рабочего плана</span></p>')
        body_html = f'{badges}<div class="doc-body">{body}</div>'
        add(f"praktika/dop/rabota-{n}.html", f"Работа {n}. {title}", body_html,
            desc=f"Дополнительная работа {n}: {title}.")

    # ---------- Шкала прогресса ----------
    sh = strip_footer(read("shkala"))
    sh = drop_h1(sh)
    sh = clean_html(balance(fix_links(sh, "praktika/shkala.html")))
    add("praktika/shkala.html", "Шкала прогресса", f'<div class="doc-body">{sh}</div>')

    # ---------- Справочник ----------
    LEAD = {
        "alfavit": '<p class="lead">Полный перечень символов, которые можно использовать '
                   'в программе на языке Си, — в таблице ниже (PDF).</p>',
        "vvod-vyvod": '<p class="lead">Функции стандартной библиотеки для ввода и вывода: '
                      'форматированный вывод <code>printf</code>, ввод <code>scanf</code>, '
                      'посимвольный ввод <code>getchar</code>, работа с файлами.</p>',
        "primery": '<p class="lead">Разобранные примеры программ на Си — от простых '
                   'вычислений до работы со структурами, массивами и файлами.</p>',
        "ide-mvs": '<p class="lead">Горячие клавиши среды разработки MVS 2022 — '
                   'таблица в PDF-файле ниже.</p>',
    }
    SPRAVO_LEAD = """<p class="lead">Справочные материалы по языку Си: набор символов,
ввод и вывод, примеры программ. Всё, что нужно под рукой, пока пишется код.</p>
<ul class="cards">
  <li><b><a href="alfavit.html">Алфавит</a></b><br>Набор символов, допустимых в программе на Си
      (таблица используемых символов в PDF).</li>
  <li><b><a href="vvod-vyvod.html">Ввод и вывод</a></b><br>Функции стандартной библиотеки
      для ввода и вывода: <code>printf</code>, <code>scanf</code>, <code>getchar</code>,
      работа с файлами и потоками.</li>
  <li><b><a href="primery.html">Примеры</a></b><br>Готовые программы-примеры с разбором:
      от простых вычислений до работы со структурами и файлами.</li>
</ul>
"""
    for key, file, title in [
        ("spravochnik", "spravochnik/index.html", "Справочник по языку Си"),
        ("alfavit", "spravochnik/alfavit.html", "Алфавит"),
        ("vvod-vyvod", "spravochnik/vvod-vyvod.html", "Ввод и вывод"),
        ("primery", "spravochnik/primery.html", "Примеры"),
    ]:
        h = strip_footer(read(key))
        h = drop_h1(h)
        h = clean_html(balance(fix_links(h, file)))
        lead = SPRAVO_LEAD if key == "spravochnik" else LEAD.get(key, "")
        add(file, title, f'{lead}<div class="doc-body">{h}</div>')

    # ---------- Инструменты ----------
    for key, file, title in [
        ("instrumenty", "instrumenty/index.html", "Инструменты разработки"),
        ("sozdanie-proekta", "instrumenty/sozdanie-proekta.html", "Создание проекта"),
        ("nastroyki-proekta", "instrumenty/nastroyki-proekta.html", "Настройки проекта"),
        ("git", "instrumenty/git.html", "Работа с Git"),
        ("github", "instrumenty/git/github.html", "Работа с GitHub"),
        ("lokalizaciya", "instrumenty/lokalizaciya.html", "Языковые настройки и локализация"),
        ("ide-mvs", "instrumenty/ide-mvs.html", "Помощник по IDE MVS"),
    ]:
        h = strip_footer(read(key))
        h = drop_h1(h)
        h = clean_html(balance(fix_links(h, file)))
        lead = LEAD.get(key, "")
        add(file, title, f'{lead}<div class="doc-body">{h}</div>')

    # ---------- КП ----------
    for key, file, title in [
        ("kp", "kp/index.html", "Контрольная работа"),
        ("kp-soderzhanie", "kp/soderzhanie.html", "Содержание пояснительной записки"),
        ("kp-oformlenie", "kp/oformlenie.html", "Оформление пояснительной записки"),
        ("kp-codestyle", "kp/codestyle.html", "CodeStyle"),
    ]:
        h = strip_footer(read(key))
        h = drop_h1(h)
        h = clean_html(balance(fix_links(h, file)))
        if key == "kp-codestyle":
            # якорь для раздела «Организация программы»
            h = h.replace("2. Организация программы.",
                          '<span id="modules"></span>2. Организация программы.', 1)
        add(file, title, f'<div class="doc-body">{h}</div>')

    # ---------- поисковый индекс ----------
    idx_js = "window.SEARCH_INDEX = " + json.dumps(search, ensure_ascii=False) + ";\n"
    open(f"{DST}/assets/search-index.js", "w", encoding="utf-8").write(idx_js)

    # ---------- оформление и скрипты ----------
    for f in ("style.css", "app.js"):
        shutil.copyfile(f"{BASE}/assets/{f}", f"{DST}/assets/{f}")

    # ---------- документация ----------
    for f in ("README.md", "MIGRATION.md"):
        p = f"{BASE}/docs/{f}"
        if os.path.exists(p):
            shutil.copyfile(p, f"{DST}/{f}")

    print("Страниц:", len(search))
    print("Папка:", DST)

if __name__ == "__main__":
    main()
