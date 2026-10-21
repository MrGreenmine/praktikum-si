#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Финальная выгрузка Google Sites -> чистый HTML + метаданные (JSON)."""
import os, re, subprocess, urllib.parse, html as ihtml, json
from html.parser import HTMLParser

TOOLS = os.path.dirname(os.path.abspath(__file__))
BASE  = "https://sites.google.com/view/course-of-study1-c"
OUT   = TOOLS + "/clean"
os.makedirs(OUT, exist_ok=True)

PAGES = [
 ("index", "", "Главная"),
 ("istochniki", "главная/источники", "Источники"),
 ("spravochnik", "главная/справочник-по-языку-си", "Справочник по языку Си"),
 ("alfavit", "главная/справочник-по-языку-си/алфавит", "Алфавит"),
 ("vvod-vyvod", "главная/справочник-по-языку-си/ввод-вывод", "Ввод и вывод"),
 ("instrumenty", "главная/инструменты-разработки", "Инструменты разработки"),
 ("sozdanie-proekta", "главная/инструменты-разработки/создание-проекта", "Создание проекта"),
 ("nastroyki-proekta", "главная/инструменты-разработки/настройки-проекта", "Настройки проекта"),
 ("git", "главная/инструменты-разработки/работа-с-git", "Работа с Git"),
 ("github", "главная/инструменты-разработки/работа-с-git/работа-с-github", "Работа с GitHub"),
 ("lokalizaciya", "главная/инструменты-разработки/языковые-настройки-и-локализация", "Языковые настройки и локализация"),
 ("ide-mvs", "главная/инструменты-разработки/помощник-по-ide-mvs", "Помощник по IDE MVS"),
 ("primery", "главная/примеры", "Примеры"),
 ("shkala", "шкала-прогресса", "Шкала прогресса"),
 ("kp", "кп", "Контрольная работа"),
 ("kp-soderzhanie", "кп/содержание-пояснительной-записки", "Содержание пояснительной записки"),
 ("kp-oformlenie", "кп/оформление-пояснительной-записки", "Оформление пояснительной записки"),
 ("kp-codestyle", "кп/codestyle", "CodeStyle"),
 ("praktika", "практика", "Практика"),
]
for i in list(range(1, 22)) + [23, 24, 25, 26, 27]:
    if i == 21:   PAGES.append(("rabota-21-zapisi", "практика/работа-21-записи", "Массив структур"))
    elif i == 26: PAGES.append(("rabota-26-massivy-ukazateley", "практика/работа-26-массив-указателей", "Массив указателей"))
    elif i == 27: PAGES.append(("rabota-27-rekursiya", "практика/работа-27-рекурсия", "Рекурсия"))
    else:         PAGES.append((f"rabota-{i}", f"практика/работа-{i}", ""))

UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")

def fetch(url):
    for _ in range(3):
        p = subprocess.run(["curl","-sL","--compressed","-A",UA,url], capture_output=True)
        if p.stdout: return p.stdout.decode("utf-8","replace")
    return ""

class El:
    __slots__ = ("tag","attrs","kids")
    def __init__(self, tag, attrs=None): self.tag=tag; self.attrs=attrs or {}; self.kids=[]
class Txt:
    __slots__=("s",)
    def __init__(self,s): self.s=s

SKIP = {"script","style","noscript","svg"}
VOID = {"br","hr","img","meta","link","source","wbr","col","area","base","embed","param"}
KEEP = {"h1","h2","h3","h4","h5","h6","p","ul","ol","li","table","thead","tbody","tfoot",
        "tr","td","th","caption","pre","code","a","blockquote","strong","em","b","i","u","s",
        "sup","sub","img","br","hr","dl","dt","dd","figure","figcaption","mark","colgroup","col"}

class Dom(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = El("#root"); self.stack=[self.root]; self.skip=0
        self.drive_icon=0            # счётчик иконок Drive
    @property
    def cur(self): return self.stack[-1]
    def handle_starttag(self, tag, attrs):
        if tag in SKIP: self.skip+=1; return
        if self.skip: return
        if tag in VOID:
            if tag=="img":
                a=dict(attrs)
                src=a.get("src") or a.get("data-src") or ""
                if "drive_2026_32dp" in src:
                    self.cur.kids.append(El("@drive", {"idx":self.drive_icon})); self.drive_icon+=1
                else:
                    self.cur.kids.append(El("img",{"src":src,"alt":a.get("alt") or ""}))
            elif tag in ("br","hr"): self.cur.kids.append(El(tag))
            return
        if tag not in KEEP: return
        a={k:v for k,v in attrs if k in ("href","src","alt","colspan","rowspan","title","target","rel")}
        if tag=="a" and (a.get("href") or "").startswith("#h."): a["_drop"]="1"
        e=El(tag,a); self.cur.kids.append(e); self.stack.append(e)
    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag,attrs)
        if tag not in VOID and tag in KEEP and self.stack[-1].tag==tag: self.stack.pop()
    def handle_endtag(self, tag):
        if tag in SKIP: self.skip=max(0,self.skip-1); return
        if self.skip: return
        if tag in VOID or tag not in KEEP: return
        if not any(n.tag==tag for n in self.stack): return
        while len(self.stack)>1:
            if self.stack.pop().tag==tag: break
    def handle_data(self, data):
        if self.skip: return
        self.cur.kids.append(Txt(data))

def serialize(nodes, out):
    for n in nodes:
        if isinstance(n, Txt):
            t=re.sub(r"[ \t\xa0]+"," ",n.s)
            t=re.sub(r"\n{3,}","\n\n",t)
            if t.strip(): out.append(ihtml.escape(t,quote=False))
            continue
        tag=n.tag
        if tag=="@drive":
            out.append(f"@@FILE{n.attrs['idx']}@@"); continue
        if tag=="img":
            out.append(f'<img src="{ihtml.escape(n.attrs.get("src",""),quote=True)}" '
                       f'alt="{ihtml.escape(n.attrs.get("alt",""),quote=True)}" loading="lazy">'); continue
        if tag=="a":
            if n.attrs.get("_drop"): continue
            out.append(f'<a href="{ihtml.escape(n.attrs.get("href",""),quote=True)}">')
            serialize(n.kids,out); out.append("</a>"); continue
        if tag=="pre":
            inner=[]; serialize(n.kids,inner)
            code=re.sub(r"\n{3,}","\n\n","".join(inner)).strip("\n")
            out.append("<pre><code>"+ihtml.escape(code,quote=False)+"</code></pre>"); continue
        if tag=="code":
            inner=[]; serialize(n.kids,inner)
            out.append("<code>"+"".join(inner)+"</code>"); continue
        attrs=""
        for k in ("colspan","rowspan"):
            if n.attrs.get(k): attrs+=f' {k}="{ihtml.escape(n.attrs[k],quote=True)}"'
        out.append(f"<{tag}{attrs}>"); serialize(n.kids,out); out.append(f"</{tag}>")

def get_content(html):
    """Контент между </header> (шапка+меню) и </footer> (копирайт)."""
    m=re.search(r"</header>(.*)</footer>",html,re.S)
    if m: return m.group(1)
    # на части страниц </footer> отсутствует -> режем по концу последнего <section>
    m=re.search(r"</header>(.*)",html,re.S)
    if not m: return html
    body=m.group(1)
    ends=[mm.end() for mm in re.finditer(r"</section>",body)]
    return body[:ends[-1]] if ends else body

def find_files(body):
    """Сопоставляем иконки Drive с вложенными документами (по порядку в документе)."""
    icons=[m.start() for m in re.finditer(r"drive_2026_32dp",body)]
    embeds=list(re.finditer(r'data-embed-open-url="([^"]+)"',body))
    files=[]
    for pos in icons:
        prev=None
        for em in embeds:
            if em.end()<pos: prev=em
        if prev is None:
            files.append(("","")); continue
        url=prev.group(1).replace("&amp;","&")
        tail=body[prev.end():pos]
        lb=re.search(r'aria-label="Drive, ([^"]*)"',tail)
        label=lb.group(1) if lb else ""
        files.append((label,url))
    return files

meta={}
for key,slug,title in PAGES:
    url=f"{BASE}/{urllib.parse.quote(slug)}" if slug else BASE
    h=fetch(url)
    if not h: print("FAIL",slug); continue
    body=get_content(h)
    banner=re.search(r"background-image:\s*url\(([^)]+)\)",body)
    banner=banner.group(1).replace("&amp;","&") if banner else ""
    files=find_files(body)
    d=Dom(); d.feed(body)
    out=[]; serialize(d.root.kids,out)
    res="".join(out)
    # карточки файлов
    def repl(m):
        i=int(m.group(1)); tail=m.group(2) or ""
        if i>=len(files): return ""
        label,url2=files[i]
        nm=label or tail.strip()
        nm=re.sub(r"^Drive,\s*","",nm)
        if not nm: nm="Материалы"
        return (f'<p class="file-card"><a class="file" href="{ihtml.escape(url2,quote=True)}" '
                f'target="_blank" rel="noopener"><span class="file-ic">PDF</span>'
                f'<span class="file-nm">{ihtml.escape(nm)}</span></a></p>')
    res=re.sub(r"@@FILE(\d+)@@([^<]{0,140})", repl, res)
    res=re.sub(r"<p>\s*</p>","",res)
    res=re.sub(r"\n{3,}","\n\n",res)
    open(os.path.join(OUT,key+".html"),"w",encoding="utf-8").write(res)
    meta[key]={"slug":slug,"title":title,"banner":banner,"files":files}
    print(f"{key:28s} {len(res)//1024:4d} KB  файлов:{len(files)}")

json.dump(meta,open(TOOLS + "/meta.json","w",encoding="utf-8"),ensure_ascii=False,indent=1)
print("meta ok")
