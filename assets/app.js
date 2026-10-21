/* Практикум по Си — клиентская логика: тема, меню, поиск, оглавление, копирование кода */
(function () {
  "use strict";

  /* ------------------------------------------------------------ тема */
  var root = document.documentElement;
  var saved = null;
  try { saved = localStorage.getItem("praktikum-theme"); } catch (e) {}
  if (!saved) {
    saved = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  }
  root.setAttribute("data-theme", saved);

  var themeBtn = document.getElementById("theme-btn");
  if (themeBtn) {
    themeBtn.addEventListener("click", function () {
      var next = root.getAttribute("data-theme") === "dark" ? "light" : "dark";
      root.setAttribute("data-theme", next);
      try { localStorage.setItem("praktikum-theme", next); } catch (e) {}
    });
  }

  /* ------------------------------------------------------------ мобильное меню */
  var burger = document.getElementById("burger");
  var backdrop = document.getElementById("backdrop");
  function closeNav() { document.body.classList.remove("nav-open"); if (burger) burger.setAttribute("aria-expanded", "false"); }
  if (burger) {
    burger.addEventListener("click", function () {
      var open = document.body.classList.toggle("nav-open");
      burger.setAttribute("aria-expanded", open ? "true" : "false");
    });
  }
  if (backdrop) backdrop.addEventListener("click", closeNav);

  /* ------------------------------------------------------------ раскрытие подменю */
  document.addEventListener("click", function (ev) {
    var tog = ev.target.closest(".nav-tog");
    if (!tog) return;
    var li = tog.closest(".nav-item");
    var sub = li && li.querySelector(".nav-sub");
    if (!sub) return;
    var hidden = sub.hasAttribute("hidden");
    if (hidden) { sub.removeAttribute("hidden"); tog.textContent = "\u25B4"; }
    else { sub.setAttribute("hidden", ""); tog.textContent = "\u25BE"; }
  });

  /* сворачивание/разворачивание всех групп */
  function setAll(open) {
    document.querySelectorAll(".nav-sub").forEach(function (sub) {
      if (open) sub.removeAttribute("hidden");
      else {
        var li = sub.parentElement;
        if (!li || !li.classList.contains("is-active")) sub.setAttribute("hidden", "");
      }
    });
    document.querySelectorAll(".nav-tog").forEach(function (t) { t.textContent = open ? "\u25B4" : "\u25BE"; });
  }
  var exp = document.getElementById("nav-expand"), col = document.getElementById("nav-collapse");
  if (exp) exp.addEventListener("click", function () { setAll(true); });
  if (col) col.addEventListener("click", function () { setAll(false); });

  /* ------------------------------------------------------------ поиск */
  var input = document.getElementById("search");
  var box = document.getElementById("search-box");
  var index = window.SEARCH_INDEX || [];
  var sel = -1, results = [];

  function esc(s) {
    return String(s).replace(/[&<>]/g, function (c) { return ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" })[c]; });
  }
  function normalize(s) { return String(s).toLowerCase().replace(/ё/g, "е"); }

  function excerpt(text, q) {
    var t = normalize(text), i = t.indexOf(q);
    if (i < 0) return text.slice(0, 140).trim() + "\u2026";
    var from = Math.max(0, i - 50);
    return (from ? "\u2026" : "") + text.slice(from, from + 190).trim() + "\u2026";
  }
  function mark(text, q) {
    var needle = normalize(q);
    if (!needle) return esc(text);
    var lower = normalize(text), out = "", i = 0;
    while (true) {
      var p = lower.indexOf(needle, i);
      if (p < 0) { out += esc(text.slice(i)); break; }
      out += esc(text.slice(i, p)) + "<mark>" + esc(text.slice(p, p + needle.length)) + "</mark>";
      i = p + needle.length;
    }
    return out;
  }

  function render(q) {
    if (!box) return;
    var query = normalize(q.trim());
    if (query.length < 2) { box.hidden = true; box.innerHTML = ""; return; }
    results = [];
    index.forEach(function (page) {
      var hay = normalize(page.title + " " + page.text);
      var pos = hay.indexOf(query);
      if (pos < 0) return;
      results.push({ page: page, score: pos < page.title.length ? 0 : 1, excerpt: excerpt(page.text, query) });
    });
    results.sort(function (a, b) { return a.score - b.score; });
    results = results.slice(0, 12);
    if (!results.length) {
      box.innerHTML = '<div class="sr-empty">Ничего не найдено</div>';
      box.hidden = false;
      return;
    }
    box.innerHTML = results.map(function (r, i) {
      return '<a class="sr-item" href="' + r.page.url + '" data-i="' + i + '">' +
             '<b>' + mark(r.page.title, q.trim()) + '</b>' +
             '<small>' + (r.page.section ? r.page.section + " \u00B7 " : "") + mark(r.excerpt, q.trim()) + "</small></a>";
    }).join("");
    box.hidden = false;
    sel = -1;
  }

  if (input) {
    input.addEventListener("input", function () { render(input.value); });
    input.addEventListener("keydown", function (ev) {
      if (ev.key === "Escape") { input.value = ""; box.hidden = true; input.blur(); return; }
      if (!results.length) return;
      if (ev.key === "ArrowDown" || ev.key === "ArrowUp") {
        ev.preventDefault();
        var items = box.querySelectorAll(".sr-item");
        if (!items.length) return;
        if (sel >= 0) items[sel].classList.remove("sel");
        sel = (sel + (ev.key === "ArrowDown" ? 1 : -1) + items.length) % items.length;
        items[sel].classList.add("sel");
        items[sel].scrollIntoView({ block: "nearest" });
      } else if (ev.key === "Enter") {
        ev.preventDefault();
        var it = box.querySelectorAll(".sr-item");
        if (sel >= 0 && it[sel]) window.location.href = it[sel].getAttribute("href");
        else if (it[0]) window.location.href = it[0].getAttribute("href");
      }
    });
    document.addEventListener("click", function (ev) {
      if (!ev.target.closest(".search-wrap")) box.hidden = true;
    });
  }
  document.addEventListener("keydown", function (ev) {
    if ((ev.ctrlKey || ev.metaKey) && ev.key.toLowerCase() === "k") {
      ev.preventDefault();
      if (input) { input.focus(); input.select(); }
    }
  });

  /* ------------------------------------------------------------ оглавление страницы */
  var tocList = document.getElementById("toc-list");
  var doc = document.querySelector(".doc");
  if (tocList && doc) {
    var heads = Array.prototype.slice.call(doc.querySelectorAll("h2, h3"))
      .filter(function (h) { return h.textContent.trim().length > 1; });
    if (heads.length) {
      heads.forEach(function (h, i) {
        h.id = "sec-" + i;
        var a = document.createElement("a");
        a.href = "#" + h.id;
        a.textContent = h.textContent.trim();
        a.className = h.tagName === "H3" ? "lvl-3" : "lvl-2";
        tocList.appendChild(a);
      });
      var links = tocList.querySelectorAll("a");
      if ("IntersectionObserver" in window) {
        var obs = new IntersectionObserver(function (entries) {
          entries.forEach(function (en) {
            if (!en.isIntersecting) return;
            links.forEach(function (l) { l.style.borderLeftColor = ""; l.style.color = ""; });
            var act = tocList.querySelector('a[href="#' + en.target.id + '"]');
            if (act) { act.style.borderLeftColor = "var(--accent)"; act.style.color = "var(--accent)"; }
          });
        }, { rootMargin: "-70px 0px -75% 0px" });
        heads.forEach(function (h) { obs.observe(h); });
      }
    } else {
      var toc = document.getElementById("toc");
      if (toc) toc.style.display = "none";
    }
  }

  /* ------------------------------------------------------------ копирование кода */
  document.querySelectorAll(".doc-body pre").forEach(function (pre) {
    var code = pre.querySelector("code");
    if (!code) return;
    var btn = document.createElement("button");
    btn.className = "copy-btn";
    btn.type = "button";
    btn.textContent = "Копировать";
    btn.addEventListener("click", function () {
      var text = code.innerText;
      var done = function () {
        btn.textContent = "Скопировано";
        btn.classList.add("done");
        setTimeout(function () { btn.textContent = "Копировать"; btn.classList.remove("done"); }, 1600);
      };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(done, function () {});
      } else {
        var ta = document.createElement("textarea");
        ta.value = text;
        document.body.appendChild(ta);
        ta.select();
        try { document.execCommand("copy"); done(); } catch (e) {}
        document.body.removeChild(ta);
      }
    });
    pre.appendChild(btn);
  });

  /* ------------------------------------------------------------ подсветка C */
  var KEYWORDS = ("auto|break|case|char|const|continue|default|do|double|else|enum|extern|float|for|goto|if|inline|" +
    "int|long|register|restrict|return|short|signed|sizeof|static|struct|switch|typedef|union|unsigned|void|" +
    "volatile|while|NULL|true|false|stdin|stdout|stderr|printf|scanf|sprintf|fprintf|malloc|calloc|free|realloc|" +
    "strlen|strcpy|strncpy|strcmp|strcat|fopen|fclose|fread|fwrite|fgets|fputs|rand|srand|exit|main|include|" +
    "define|ifdef|ifndef|endif|pragma|undef").split("|");
  var kwRe = new RegExp("\\b(" + KEYWORDS.join("|") + ")\\b", "g");
  var numRe = /\b(\d+\.?\d*([eE][+-]?\d+)?)\b/g;

  document.querySelectorAll(".doc-body pre code").forEach(function (code) {
    var text = code.textContent;
    if (!text) return;
    /* режем на куски: комментарии, строки, препроцессор, обычный текст */
    var parts = [], buf = "", i = 0;
    function flushPlain() { if (buf) { parts.push({ t: "plain", s: buf }); buf = ""; } }
    while (i < text.length) {
      var ch = text[i];
      if (ch === "/" && text[i + 1] === "/") {
        flushPlain();
        var e = text.indexOf("\n", i); if (e < 0) e = text.length;
        parts.push({ t: "com", s: text.slice(i, e) }); i = e; continue;
      }
      if (ch === "/" && text[i + 1] === "*") {
        flushPlain();
        var e2 = text.indexOf("*/", i + 2); e2 = e2 < 0 ? text.length : e2 + 2;
        parts.push({ t: "com", s: text.slice(i, e2) }); i = e2; continue;
      }
      if (ch === '"' || ch === "'") {
        flushPlain();
        var j = i + 1;
        while (j < text.length && text[j] !== ch) { if (text[j] === "\\") j++; j++; }
        j = Math.min(j + 1, text.length);
        parts.push({ t: "str", s: text.slice(i, j) }); i = j; continue;
      }
      if (ch === "#") {
        flushPlain();
        var k = text.indexOf("\n", i); if (k < 0) k = text.length;
        parts.push({ t: "pre", s: text.slice(i, k) }); i = k; continue;
      }
      buf += ch; i++;
    }
    flushPlain();

    var html = parts.map(function (p) {
      if (p.t === "plain") {
        var s = esc(p.s)
          .replace(kwRe, '<span class="tok-kw">$1</span>')
          .replace(numRe, '<span class="tok-num">$1</span>');
        return s;
      }
      if (p.t === "str") return '<span class="tok-str">' + esc(p.s) + "</span>";
      if (p.t === "com") return '<span class="tok-com">' + esc(p.s) + "</span>";
      return '<span class="tok-pre">' + esc(p.s) + "</span>";
    }).join("");
    code.innerHTML = html;
  });
})();
