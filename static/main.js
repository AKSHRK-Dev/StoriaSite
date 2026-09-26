(() => {
  const store = {
    get(k) { try { return localStorage.getItem(k); } catch (e) { return null; } },
    set(k, v) { try { localStorage.setItem(k, v); } catch (e) { /* ignore */ } },
  };
  const root = document.documentElement;
  const lang = root.dataset.lang;

  // ---- theme ----
  const themeBtn = document.getElementById("theme-toggle");
  if (themeBtn) {
    themeBtn.addEventListener("click", () => {
      const dark = root.dataset.theme ? root.dataset.theme === "dark" : matchMedia("(prefers-color-scheme: dark)").matches;
      root.dataset.theme = dark ? "light" : "dark";
      store.set("storia-theme", root.dataset.theme);
    });
  }

  // ---- language: remember the choice so "/" sends the visitor back here ----
  document.querySelectorAll("[data-set-lang]").forEach((a) => {
    a.addEventListener("click", () => {
      document.cookie = "storia_lang=" + a.dataset.setLang + "; path=/; max-age=31536000; SameSite=Lax";
    });
  });
  const langSel = document.getElementById("lang-select");
  if (langSel) {
    langSel.addEventListener("change", () => {
      const opt = langSel.selectedOptions[0];
      document.cookie = "storia_lang=" + opt.value + "; path=/; max-age=31536000; SameSite=Lax";
      location.href = opt.dataset.href + location.hash;
    });
  }

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
    const render = () => {
      const q = input.value.trim().toLowerCase();
      if (!q) { results.classList.remove("open"); return; }
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
      results.innerHTML = hits.length
        ? hits.slice(0, 12).map((h) => `<a href="${h.url}"><div class="r-title">${mark(h.title, terms)}</div><div class="r-sec">${esc(h.sec)}</div><div class="r-text">${mark(h.snippet, terms)}</div></a>`).join("")
        : `<div class="empty">${esc(input.dataset.empty)}</div>`;
      results.classList.add("open");
    };
    input.addEventListener("focus", load);
    input.addEventListener("input", () => load().then(render));
    input.addEventListener("keydown", (e) => {
      const items = [...results.querySelectorAll("a")];
      if (e.key === "ArrowDown" || e.key === "ArrowUp") {
        e.preventDefault();
        if (!items.length) return;
        active = (active + (e.key === "ArrowDown" ? 1 : -1) + items.length) % items.length;
        items.forEach((a, i) => a.classList.toggle("active", i === active));
        items[active].scrollIntoView({ block: "nearest" });
      } else if (e.key === "Enter" && items.length) {
        location.href = items[Math.max(0, active)].href;
      } else if (e.key === "Escape") {
        results.classList.remove("open");
        input.blur();
      }
    });
    document.addEventListener("click", (e) => { if (!e.target.closest(".search")) results.classList.remove("open"); });
    document.addEventListener("keydown", (e) => {
      if (e.key === "/" && document.activeElement !== input && !/INPUT|TEXTAREA/.test(document.activeElement.tagName)) {
        e.preventDefault();
        input.focus();
      }
    });
  }

  // ---- downloads: tabs + live release list from GitHub ----
  const tabs = [...document.querySelectorAll(".tabs [role=tab]")];
  if (tabs.length) {
    const select = (tab, push) => {
      tabs.forEach((t) => {
        const on = t === tab;
        t.setAttribute("aria-selected", on);
        document.getElementById(t.getAttribute("aria-controls")).hidden = !on;
      });
      if (push) history.replaceState(null, "", "#" + tab.dataset.product);
    };
    tabs.forEach((t) => t.addEventListener("click", () => select(t, true)));
    const fromHash = tabs.find((t) => "#" + t.dataset.product === location.hash);
    if (fromHash) select(fromHash, false);

    const i18n = JSON.parse(document.getElementById("dl-i18n").textContent);
    const fmtSize = (b) => b >= 1048576 ? (b / 1048576).toFixed(1) + " MB" : Math.max(1, Math.round(b / 1024)) + " KB";
    const fmtDate = (s) => new Date(s).toLocaleDateString(lang === "ja-jp" ? "ja-JP" : "en-US", { year: "numeric", month: "short", day: "numeric" });
    fetch("https://api.github.com/repos/AKSHRK-Dev/Storia/releases?per_page=30")
      .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
      .then((releases) => {
        releases = releases.filter((r) => !r.draft);
        if (!releases.length) return;
        document.querySelectorAll("[data-product-panel]").forEach((panel) => {
          const product = panel.dataset.productPanel;
          const re = new RegExp("^" + panel.dataset.pattern + "$");
          const rows = [];
          releases.forEach((rel) => {
            const asset = rel.assets.find((a) => re.test(a.name));
            if (asset) rows.push({ rel, asset });
          });
          if (!rows.length) return;
          const { rel, asset } = rows[0];
          panel.querySelector("[data-f=version]").textContent = rel.tag_name.replace(/^v/, "");
          panel.querySelector("[data-f=file]").textContent = asset.name;
          panel.querySelector("[data-f=size]").textContent = fmtSize(asset.size);
          panel.querySelector("[data-f=date]").textContent = fmtDate(rel.published_at);
          const sha = panel.querySelector("[data-f=sha]");
          if (sha) sha.textContent = asset.digest ? asset.digest.replace(/^sha256:/, "") : "—";
          const dl = panel.querySelector("[data-f=download]");
          dl.href = asset.browser_download_url;
          dl.querySelector("span").textContent = i18n.download + " " + rel.tag_name.replace(/^v/, "");
          panel.querySelector("[data-f=notes]").href = rel.html_url;
          const list = panel.querySelector("[data-f=list]");
          list.innerHTML = "";
          rows.forEach(({ rel: r, asset: a }) => {
            const row = document.createElement("div");
            row.className = "build-row";
            row.innerHTML = `<span class="ver"></span><span class="date"></span><span class="size"></span><a></a>`;
            row.children[0].textContent = r.tag_name.replace(/^v/, "") + (r.prerelease ? " (pre)" : "");
            row.children[1].textContent = fmtDate(r.published_at);
            row.children[2].textContent = fmtSize(a.size);
            row.children[3].textContent = a.name;
            row.children[3].href = a.browser_download_url;
            list.appendChild(row);
          });
          panel.dataset.live = product;
        });
      })
      .catch(() => { /* keep the list baked in at build time */ });
  }
})();
