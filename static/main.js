(() => {
  const store = {
    get(k) { try { return localStorage.getItem(k); } catch (e) { return null; } },
    set(k, v) { try { localStorage.setItem(k, v); } catch (e) { /* ignore */ } },
  };
  const root = document.documentElement;
  const lang = root.dataset.lang;
  const live = document.getElementById("live");
  const announce = (msg) => { if (live) { live.textContent = ""; setTimeout(() => (live.textContent = msg), 50); } };

  // ---- theme ----
  const themeBtn = document.getElementById("theme-toggle");
  const isDark = () => root.dataset.theme ? root.dataset.theme === "dark" : matchMedia("(prefers-color-scheme: dark)").matches;
  if (themeBtn) {
    themeBtn.setAttribute("aria-pressed", isDark());
    themeBtn.addEventListener("click", () => {
      root.dataset.theme = isDark() ? "light" : "dark";
      store.set("storia-theme", root.dataset.theme);
      themeBtn.setAttribute("aria-pressed", isDark());
    });
  }

  // ---- language: remember the choice so "/" sends the visitor back here ----
  document.querySelectorAll("[data-set-lang]").forEach((a) => {
    a.addEventListener("click", () => {
      document.cookie = "storia_lang=" + a.dataset.setLang + "; path=/; max-age=31536000; SameSite=Lax";
    });
  });
  const langBtn = document.getElementById("lang-toggle");
  const langMenu = document.getElementById("lang-menu");
  if (langBtn && langMenu) {
    const setOpen = (open, focus) => {
      langMenu.hidden = !open;
      langBtn.setAttribute("aria-expanded", open);
      if (open && focus) langMenu.querySelector("a").focus();
    };
    langBtn.addEventListener("click", () => setOpen(langMenu.hidden, false));
    langBtn.addEventListener("keydown", (e) => { if (e.key === "ArrowDown") { e.preventDefault(); setOpen(true, true); } });
    langMenu.querySelectorAll("a").forEach((a) => a.addEventListener("click", (e) => {
      // keep the part of the page the visitor was looking at
      if (location.hash) { e.preventDefault(); location.href = a.href + location.hash; }
    }));
    document.addEventListener("keydown", (e) => { if (e.key === "Escape" && !langMenu.hidden) { setOpen(false); langBtn.focus(); } });
    document.addEventListener("click", (e) => { if (!e.target.closest(".lang")) setOpen(false); });
    langMenu.addEventListener("focusout", (e) => { if (!e.relatedTarget || !e.relatedTarget.closest(".lang")) setOpen(false); });
  }

  // ---- skip link: move keyboard focus to the main content ----
  const skip = document.querySelector(".skip");
  const main = document.getElementById("main");
  if (skip && main) skip.addEventListener("click", (e) => { e.preventDefault(); main.focus(); main.scrollIntoView(); });

  // ---- mobile menus ----
  const menuBtn = document.getElementById("menu-toggle");
  const nav = document.getElementById("site-nav");
  if (menuBtn && nav) menuBtn.addEventListener("click", () => {
    const open = nav.classList.toggle("open");
    menuBtn.setAttribute("aria-expanded", open);
  });
  const docsBtn = document.getElementById("docs-menu");
  const sidebar = document.getElementById("sidebar");
  if (docsBtn && sidebar) docsBtn.addEventListener("click", () => {
    const open = sidebar.classList.toggle("open");
    docsBtn.setAttribute("aria-expanded", open);
  });

  // ---- copy buttons ----
  const copyLabel = lang === "ja-jp" ? ["コピー", "コピーしました"] : ["Copy", "Copied"];
  document.querySelectorAll(".doc pre, .codeblock pre").forEach((pre) => {
    let wrap = pre.closest(".codeblock");
    if (!wrap) {
      wrap = document.createElement("div");
      wrap.className = "codeblock";
      const host = pre.parentElement.classList.contains("hl") ? pre.parentElement : pre;
      host.parentNode.insertBefore(wrap, host);
      wrap.appendChild(host);
    }
    const btn = document.createElement("button");
    btn.className = "copy";
    btn.type = "button";
    btn.textContent = copyLabel[0];
    btn.addEventListener("click", async () => {
      try {
        await navigator.clipboard.writeText(pre.innerText.replace(/\n$/, ""));
        btn.textContent = copyLabel[1];
        announce(copyLabel[1]);
        setTimeout(() => (btn.textContent = copyLabel[0]), 1500);
      } catch (e) { /* clipboard unavailable */ }
    });
    wrap.appendChild(btn);
  });

  // ---- tables scroll on small screens ----
  document.querySelectorAll(".doc table").forEach((t) => {
    if (t.parentElement.classList.contains("table-wrap")) return;
    const w = document.createElement("div");
    w.className = "table-wrap";
    t.parentNode.insertBefore(w, t);
    w.appendChild(t);
  });

  // ---- "on this page" highlight ----
  const tocLinks = [...document.querySelectorAll(".toc a")];
  if (tocLinks.length && "IntersectionObserver" in window) {
    const byId = new Map(tocLinks.map((a) => [decodeURIComponent(a.hash.slice(1)), a]));
    const visible = new Set();
    const io = new IntersectionObserver((entries) => {
      entries.forEach((e) => (e.isIntersecting ? visible.add(e.target.id) : visible.delete(e.target.id)));
      const heads = [...byId.keys()].map((id) => document.getElementById(id)).filter(Boolean);
      const current = heads.find((h) => visible.has(h.id)) ||
        heads.filter((h) => h.getBoundingClientRect().top < 120).pop();
      tocLinks.forEach((a) => a.classList.toggle("active", current && byId.get(current.id) === a));
    }, { rootMargin: "-64px 0px -60% 0px" });
    byId.forEach((_, id) => { const el = document.getElementById(id); if (el) io.observe(el); });
  }

  // ---- docs search ----
  const input = document.getElementById("search");
  const results = document.getElementById("search-results");
  if (input && results) {
    let index = null;
    let active = -1;
    const load = () => index ? Promise.resolve(index) :
      fetch(input.dataset.index).then((r) => r.json()).then((j) => (index = j)).catch(() => (index = []));
    const esc = (s) => s.replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
    const mark = (s, terms) => {
      let out = esc(s);
      terms.forEach((t) => { out = out.replace(new RegExp("(" + t.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + ")", "gi"), "<mark>$1</mark>"); });
      return out;
    };
    results.setAttribute("role", "listbox");
    const close = () => {
      results.classList.remove("open");
      input.setAttribute("aria-expanded", "false");
      input.removeAttribute("aria-activedescendant");
    };
    const render = () => {
      const q = input.value.trim().toLowerCase();
      if (!q) { close(); return; }
      const terms = q.split(/\s+/).filter(Boolean);
      const hits = [];
      index.forEach((page) => {
        page.s.forEach((sec) => {
          const hay = (page.t + " " + sec.h + " " + sec.x).toLowerCase();
          if (!terms.every((t) => hay.includes(t))) return;
          let score = 0;
          terms.forEach((t) => {
            if (page.t.toLowerCase().includes(t)) score += 10;
            if (sec.h.toLowerCase().includes(t)) score += 6;
            if (sec.x.toLowerCase().includes(t)) score += 1;
          });
          const lower = sec.x.toLowerCase();
          const at = Math.max(0, lower.indexOf(terms[0]) - 40);
          const snippet = (at > 0 ? "…" : "") + sec.x.slice(at, at + 140) + (sec.x.length > at + 140 ? "…" : "");
          hits.push({ score, url: page.u + (sec.a ? "#" + sec.a : ""), title: sec.h || page.t, sec: page.g + " › " + page.t, snippet });
        });
      });
      hits.sort((a, b) => b.score - a.score);
      active = -1;
      input.removeAttribute("aria-activedescendant");
      results.innerHTML = hits.length
        ? hits.slice(0, 12).map((h, i) => `<a href="${h.url}" id="sr-${i}" role="option" aria-selected="false"><div class="r-title">${mark(h.title, terms)}</div><div class="r-sec">${esc(h.sec)}</div><div class="r-text">${mark(h.snippet, terms)}</div></a>`).join("")
        : `<div class="empty" role="option" aria-disabled="true">${esc(input.dataset.empty)}</div>`;
      results.classList.add("open");
      input.setAttribute("aria-expanded", "true");
      announce(hits.length ? input.dataset.results.replace("{n}", Math.min(hits.length, 12)) : input.dataset.empty);
    };
    input.addEventListener("focus", load);
    input.addEventListener("input", () => load().then(render));
    input.addEventListener("keydown", (e) => {
      const items = [...results.querySelectorAll("a")];
      if (e.key === "ArrowDown" || e.key === "ArrowUp") {
        e.preventDefault();
        if (!items.length) return;
        active = (active + (e.key === "ArrowDown" ? 1 : -1) + items.length) % items.length;
        items.forEach((a, i) => { a.classList.toggle("active", i === active); a.setAttribute("aria-selected", i === active); });
        input.setAttribute("aria-activedescendant", items[active].id);
        items[active].scrollIntoView({ block: "nearest" });
      } else if (e.key === "Enter" && items.length) {
        location.href = items[Math.max(0, active)].href;
      } else if (e.key === "Escape") {
        close();
      }
    });
    document.addEventListener("click", (e) => { if (!e.target.closest(".search")) close(); });
  }

  // ---- header border once scrolled ----
  const head = document.getElementById("site-header");
  if (head) {
    const onScroll = () => head.classList.toggle("scrolled", scrollY > 4);
    addEventListener("scroll", onScroll, { passive: true });
    onScroll();
  }

  // ---- hero terminal: type commands, then print output lines ----
  const term = document.getElementById("term");
  if (term && !matchMedia("(prefers-reduced-motion: reduce)").matches) {
    const lines = [...term.querySelectorAll(".ln")];
    const markup = lines.map((l) => l.innerHTML);
    lines.forEach((l) => (l.hidden = true));
    const cursor = document.createElement("span");
    cursor.className = "cursor";
    let n = 0;
    const next = () => {
      if (n >= lines.length) return;
      const el = lines[n], html = markup[n];
      n++;
      el.hidden = false;
      if (el.dataset.k !== "cmd") {
        el.innerHTML = html;
        el.appendChild(cursor);
        setTimeout(next, 250 + Math.random() * 250);
        return;
      }
      const text = new DOMParser().parseFromString(html, "text/html").body.textContent;
      let i = 0;
      const type = () => {
        el.textContent = text.slice(0, ++i);
        el.appendChild(cursor);
        if (i < text.length) setTimeout(type, 30 + Math.random() * 40);
        else setTimeout(() => { el.innerHTML = html; el.appendChild(cursor); setTimeout(next, 350); }, 200);
      };
      type();
    };
    setTimeout(next, 400);
  }

  // ---- relative dates ("2 days ago") ----
  if ("RelativeTimeFormat" in Intl) {
    const rtf = new Intl.RelativeTimeFormat(lang === "ja-jp" ? "ja" : "en", { numeric: "auto" });
    document.querySelectorAll("[data-time]").forEach((el) => {
      const days = Math.round((new Date(el.dataset.time) - Date.now()) / 86400000);
      if (days > -8) el.textContent = rtf.format(days, "day");
    });
  }

})();
