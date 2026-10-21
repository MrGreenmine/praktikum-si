#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Превращает абзацы с исходным кодом в настоящие блоки <pre><code>."""
import re, html

P_RE = re.compile(r'<p(?:\s[^>]*)?>(.*?)</p>', re.S)

STRONG = re.compile(r'^\s*(?:#\s*(?:include|define|ifndef|ifdef|endif|pragma|undef|error)\b|'
                    r'//|/\*|\*/|\*(?!\*)\s|'
                    r'\}|\{|\)|;|'
                    r'(?:int|double|float|char|void|short|long|unsigned|signed|const|static|'
                    r'struct|typedef|enum|union|register|volatile|extern|size_t|TYPE)\s+\w|'
                    r'(?:return|break|continue|goto|sizeof|else|case|default)\b|'
                    r'(?:if|for|while|switch|do)\s*[\(\{]|'
                    r'(?:printf|scanf|sprintf|fprintf|puts|putchar|getchar|malloc|calloc|realloc|free|'
                    r'strlen|strcpy|strncpy|strcmp|strcat|fopen|fclose|fgets|fputs|fread|fwrite|'
                    r'exit|rand|srand|time|localtime|system|push|pop)\s*\()')

SIGNALS = re.compile(r'[;{}()\[\]]|->|==|<=|>=|&&|\|\||\+=|-=|\*=|/=|%=|<<|>>|\bprintf\b|\bscanf\b')
CYR = re.compile(r'[а-яёА-Я]')

CODEISH = re.compile(r'^\s*(?:[A-Za-z_]\w*\s*\([^()]*\)\s*;?|[A-Za-z_]\w*\s*=\s*[^;]+;|'
                     r'[A-Za-z_]\w*\s+[A-Za-z_]\w*\s*(\[[^\]]*\])?\s*;|'
                     r'[{}]\s*|;|[A-Za-z_]\w*\s*\[|&\w+|\*\w+\s*[,;)])')

def text_of(inner):
    s = re.sub(r'<br\s*/?>', '\n', inner)
    s = re.sub(r'<[^>]+>', '', s)
    return html.unescape(s).replace('\xa0', ' ').strip()

def strip_code_noise(t):
    """Убирает строки и комментарии — остаётся «программная» часть."""
    t = re.sub(r'"(?:[^"\\]|\\.)*"', '""', t)
    t = re.sub(r"'(?:[^'\\]|\\.)*'", "''", t)
    t = re.sub(r'//.*', '', t)
    t = re.sub(r'/\*.*?\*/', '', t, flags=re.S)
    return t

def is_strong(t):
    if not t or len(t) > 500: return False
    if re.match(r'^\s*\*\s', t):          # продолжение комментария
        return True
    if not STRONG.match(t): return False
    if CYR.search(strip_code_noise(t)):   # смесь кода и русского текста
        return False
    return True

def is_weak(t):
    """Похоже на продолжение кода: короткая строка с программными знаками."""
    if not t or len(t) > 220: return False
    if CYR.search(strip_code_noise(t)) and not STRONG.match(t):
        return False
    n = len(SIGNALS.findall(t))
    if n >= 2 and CODEISH.match(t): return True
    if n >= 3: return True
    return False

def mark_code(body):
    """Заменяет группы «кодовых» абзацев на <pre><code>…</code></pre>."""
    blocks = []
    for m in P_RE.finditer(body):
        blocks.append((m.start(), m.end(), text_of(m.group(1))))

    kinds = []
    for _s, _e, t in blocks:
        kinds.append("code" if is_strong(t) else ("weak" if is_weak(t) else "prose"))

    out, pos, i, n = [], 0, 0, len(blocks)
    while i < n:
        if kinds[i] == "prose" or (kinds[i] == "weak" and (i + 1 >= n or kinds[i + 1] != "code")):
            i += 1
            continue
        group, k = [], i
        while k < n and kinds[k] in ("code", "weak"):
            group.append(blocks[k]); k += 1
        out.append(body[pos:group[0][0]])
        code = "\n".join(t for _s, _e, t in group).strip("\n")
        out.append("<pre><code>" + html.escape(code, quote=False) + "</code></pre>")
        pos = group[-1][1]
        i = k
    out.append(body[pos:])
    return "".join(out)

if __name__ == "__main__":
    import sys
    for f in sys.argv[1:]:
        h = open(f, encoding="utf-8").read()
        open(f, "w", encoding="utf-8").write(mark_code(h))
        print("ok", f)
