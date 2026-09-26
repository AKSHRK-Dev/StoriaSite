#!/usr/bin/env python3
"""Builds the Storia website into dist/.

    python3 build.py

Languages live under /en-us/ and /ja-jp/. "/" is sent to one of them by the web server
(see deploy/nginx.conf), using the visitor's saved choice or Cloudflare's CF-IPCountry header.
Release data comes from the GitHub API (set GITHUB_TOKEN to raise the rate limit); if it cannot be
reached, the last copy in releases.json is used.
"""
import html
import json
import os
import re
import shutil
import subprocess
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"
CONTENT = ROOT / "content"
STATIC = ROOT / "static"

REPO = "AKSHRK-Dev/Storia"
PROXY_REPO = "AKSHRK-Dev/StoriaProxy"
SITE_REPO = "AKSHRK-Dev/StoriaSite"
GITHUB = f"https://github.com/{REPO}"
MC_VERSION = "26.2"
LANGS = ["en-us", "ja-jp"]
HTML_LANG = {"en-us": "en", "ja-jp": "ja"}
LANG_NAME = {"en-us": "English", "ja-jp": "日本語"}

# ---------------------------------------------------------------------------------------------
# Docs navigation: ((group_en, group_ja), [(slug, title_en, title_ja)])
# ---------------------------------------------------------------------------------------------
DOCS_NAV = [
    (("Storia", "Storia"), [
        ("introduction", "Introduction", "はじめに"),
        ("getting-started", "Getting started", "導入ガイド"),
        ("configuration", "Configuration", "設定 (storia.yml)"),
        ("commands", "Commands & permissions", "コマンドと権限"),
    ]),
    (("Features", "機能"), [
        ("ram-world", "RAM world", "RAM ワールド"),
        ("pregeneration", "Chunk pregeneration", "チャンクの事前生成"),
        ("player-budget", "Per-player budget", "プレイヤーごとの予算"),
        ("performance", "Performance & tuning", "パフォーマンスと調整"),
    ]),
    (("Offload", "処理の分担"), [
        ("offload", "Offloading terrain", "地形生成の分担"),
        ("worker", "Storia Worker", "Storia Worker"),
        ("relay", "Storia Relay", "Storia Relay"),
        ("security", "Encryption & security", "暗号化とセキュリティ"),
    ]),
    (("Storia Proxy", "Storia Proxy"), [
        ("proxy", "Proxy setup", "プロキシの導入"),
        ("placeholders", "Placeholders", "プレースホルダー一覧"),
        ("placeholder-api", "Placeholder API", "プレースホルダー API"),
    ]),
    (("Reference", "リファレンス"), [
        ("plugins", "Plugin compatibility", "プラグインの互換性"),
        ("building", "Building from source", "ソースからビルド"),
        ("faq", "FAQ & troubleshooting", "FAQ とトラブルシューティング"),
    ]),
]


def doc_title(slug, lang):
    return next(en if lang == "en-us" else ja for _, items in DOCS_NAV for s, en, ja in items if s == slug)


# ---------------------------------------------------------------------------------------------
# Icons
# ---------------------------------------------------------------------------------------------
def svg(body, fill=False, sw="2"):
    attrs = 'fill="currentColor"' if fill else f'fill="none" stroke="currentColor" stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round"'
    return f'<svg viewBox="0 0 24 24" {attrs} aria-hidden="true">{body}</svg>'


MARK = ('<svg viewBox="46 40 108 120" fill="currentColor" aria-hidden="true">'
        '<rect x="50" y="44" width="100" height="16" rx="3"/><rect x="62" y="68" width="20" height="64" rx="3"/>'
        '<rect x="90" y="68" width="20" height="64" rx="3"/><rect x="118" y="68" width="20" height="64" rx="3"/>'
        '<rect x="50" y="140" width="100" height="16" rx="3"/></svg>')
ICON = {
    "storia": MARK,
    "worker": svg('<rect x="6" y="6" width="12" height="12" rx="2"/><path d="M9 2v4M15 2v4M9 18v4M15 18v4M2 9h4M2 15h4M18 9h4M18 15h4"/><rect x="10" y="10" width="4" height="4" rx=".5" fill="currentColor"/>'),
    "relay": svg('<circle cx="12" cy="12" r="3"/><circle cx="4" cy="5" r="2"/><circle cx="4" cy="19" r="2"/><circle cx="20" cy="5" r="2"/><circle cx="20" cy="19" r="2"/><path d="m6 6.5 3.6 3.4M6 17.5l3.6-3.4M18 6.5l-3.6 3.4M18 17.5l-3.6-3.4"/>'),
    "proxy": svg('<path d="M12 3 4 6.5v5.2c0 4.6 3.4 8.3 8 9.3 4.6-1 8-4.7 8-9.3V6.5z"/><path d="M8.5 12h7M12 8.5v7"/>'),
    "sun": svg('<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>', sw="1.8"),
    "globe": svg('<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c2.5 2.6 3.8 5.6 3.8 9s-1.3 6.4-3.8 9c-2.5-2.6-3.8-5.6-3.8-9S9.5 5.6 12 3z"/>', sw="1.8"),
    "chev": svg('<path d="m6 9 6 6 6-6"/>').replace("<svg ", '<svg class="chev" '),
    "ext": svg('<path d="M14 4h6v6M20 4l-9 9M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5"/>').replace("<svg ", '<svg class="ext" '),
    "menu": svg('<path d="M4 7h16M4 12h16M4 17h16"/>', sw="1.8"),
    "dl": svg('<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5M12 11v6m0 0 3-3m-3 3-3-3"/>'),
    "file": svg('<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5M12 11v6m0 0 2.5-2.5M12 17l-2.5-2.5"/>'),
    "arrow": svg('<path d="M5 12h14m0 0-5-5m5 5-5 5"/>'),
    "search": svg('<circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/>'),
    "github": ('<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 .5A11.5 11.5 0 0 0 .5 12a11.5 11.5 0 0 0 7.86 10.92c.58.1.79-.25.79-.56v-2c-3.2.7-3.87-1.37-3.87-1.37-.52-1.33-1.28-1.69-1.28-1.69-1.04-.71.08-.7.08-.7 1.15.08 1.76 1.19 1.76 1.19 1.03 1.76 2.69 1.25 3.35.96.1-.75.4-1.25.73-1.54-2.55-.29-5.24-1.28-5.24-5.69 0-1.26.45-2.29 1.19-3.1-.12-.29-.52-1.46.11-3.05 0 0 .97-.31 3.17 1.18a11 11 0 0 1 5.77 0c2.2-1.49 3.17-1.18 3.17-1.18.63 1.59.23 2.76.11 3.05.74.81 1.19 1.84 1.19 3.1 0 4.42-2.7 5.39-5.26 5.68.41.36.78 1.06.78 2.14v3.17c0 .31.21.67.8.56A11.5 11.5 0 0 0 23.5 12 11.5 11.5 0 0 0 12 .5z"/></svg>'),
}


def logo(key, cls="logo"):
    return f'<span class="{cls}">{ICON[key]}</span>'


e = html.escape

# ---------------------------------------------------------------------------------------------
# Products
# ---------------------------------------------------------------------------------------------
# key, name, download path, asset pattern, docs slug
PRODUCTS = [
    ("storia", "Storia", "downloads/", r"storia-[0-9][0-9.]*(-[0-9]+)?\.jar", "getting-started"),
    ("worker", "Storia Worker", "downloads/worker/", r"storia-worker-.*\.zip", "worker"),
    ("relay", "Storia Relay", "downloads/relay/", r"storia-relay-.*\.zip", "relay"),
    ("proxy", "Storia Proxy", "downloads/proxy/", r"storia-proxy-.*\.jar", "proxy"),
]

# ---------------------------------------------------------------------------------------------
# UI strings
# ---------------------------------------------------------------------------------------------
T = {
    "en-us": {
        "software": "Software", "downloads": "Downloads", "docs": "Docs", "github": "GitHub",
        "theme": "Toggle theme", "menu": "Menu", "language": "Language",
        "desc": "Storia is a Folia-based Minecraft server with RAM-backed worlds, fast chunk pregeneration, a fair share of the server for every player, redstone-safe physics optimizations and encrypted terrain offloading to other machines.",
        "hero1": "Multithreaded Minecraft.", "hero2": "Fair for every player.",
        "hero_p": "Storia builds on Folia with worlds that live in RAM, five-times-faster pregeneration, a fair share of the CPU for every player and terrain generation spread across machines, all without ever stopping your redstone.",
        "documentation": "Documentation",
        "meta": [f"Minecraft {MC_VERSION}", "Java 25", "Based on Folia", "Open source"],
        "cards_title": 'Everything your server <span class="accent">needs.</span>',
        "product_text": {
            "storia": "The Minecraft server. Folia's regionised multithreading plus RAM worlds, fast pregeneration and a per-player budget.",
            "worker": "Generates terrain for your server on another machine. Opens no player port and never changes your world.",
            "relay": "A tiny program that shares terrain work between any number of workers. No Minecraft files needed.",
            "proxy": "A Velocity fork with 50 built-in placeholders, a live tab list, MOTD and network-wide messages.",
        },
        "get": "Download",
        "learn": "Learn more",
        "f_ram": ("Worlds that live in <span class=\"accent\">RAM.</span>",
                  "Storia copies your worlds into RAM when it starts and writes changes back to disk in the background. Disk I/O stops being your bottleneck.",
                  ["Only changed files are synced, at an interval you choose", "Atomic writes: the copy on disk is never half-written", "Survives a crash of the server process and recovers on the next start"]),
        "f_pregen": ("Pregeneration, <span class=\"accent\">5× faster.</span>",
                     "/storia pregen uses every core but one while it runs, keeps every thread busy and saves its progress, so a restart simply continues where it left off.",
                     ["3,721 chunks in 40 seconds instead of 3 minutes 21 on six cores", "Faster noise sampling, with terrain identical to vanilla", "Resume after a restart with /storia pregen resume"]),
        "bars": [("Folia default", "3m 21s", 100, False), ("Storia /storia pregen", "40s", 20, True)],
        "bars_t": "3,721 chunks · 6 cores", "bars_note": "Lower is better. Same seed, same machine.",
        "f_budget": ("A fair share for <span class=\"accent\">every player.</span>",
                     "Every player is entitled to an equal share of the tick threads. When one region lags or takes more than its share while the server is busy, only the players in that region get a shorter view distance, until it recovers.",
                     ["Nothing is limited while the server has headroom", "Simulation distance is untouched, so farms and redstone keep running", "Memory pressure lowers view distance for everyone, then restores it"]),
        "f_offload": ("Terrain on <span class=\"accent\">other machines.</span>",
                      "Send the heaviest step of terrain generation to Storia Workers on spare machines. Results are bit-for-bit identical, and the server falls back to generating locally the moment a worker is busy, slow or gone.",
                      ["AES-256-GCM encryption, keyed by a shared secret that never leaves the machine", "Probe chunks on connect: mismatching seeds or datapacks are refused", "Storia Relay lets workers join and leave at any time"]),
        "f_proxy": ("A proxy with <span class=\"accent\">50 placeholders.</span>",
                    "Storia Proxy is Velocity with a live tab list, a server list MOTD and join, leave and switch messages, all built from placeholders for the proxy, every backend and the viewing player.",
                    ["{online_lobby}, {status_survival}, {player_ping} and 47 more", "MiniMessage formatting, reloadable without a restart", "An API to register your own placeholders from plugins"]),
        "f_vanilla": ("The promise of <span class=\"accent\">vanilla.</span>",
                      "Every optimisation in Storia must produce exactly what vanilla would. Terrain and physics changes are checked against the original code, and redstone is never paused, slowed or skipped.",
                      []),
        "stats": [("0", "", "differences in 18M noise samples"), ("0", "", "differences in 500,000 entity pushes"), ("3", "×", "faster entity pushing"), ("0", "", "redstone changes")],
        # downloads
        "dl_desc": {
            "storia": "Download Storia, our Minecraft server software for large communities, built on Folia.",
            "worker": "Download Storia Worker to generate terrain for your Storia server on another machine.",
            "relay": "Download Storia Relay to share terrain work between any number of Storia Workers.",
            "proxy": "Download Storia Proxy, a Velocity fork with 50 built-in placeholders.",
        },
        "req": {"storia": "Java 25", "worker": "Java 25", "relay": "Java 21+", "proxy": "Java 21+"},
        "get_title": "Get {name}{ver}", "build": "Release", "older": "Older builds",
        "older_text": 'Looking for older builds or changelogs? Every release is on <a href="{url}">GitHub Releases</a>.',
        "dev_builds": "Development builds", "no_release": "No release yet", "other_software": "Other software",
        # docs
        "search": "Search docs", "search_empty": "No results", "on_page": "On this page", "prev": "Previous", "next": "Next",
        "docs_menu": "Documentation menu",
        # footer
        "f_start": "Getting Started", "f_soft": "Software", "f_comm": "Community", "f_res": "Resources",
        "issues": "Issues", "releases": "Releases", "website_src": "Website source",
        "legal": "This website is not an official Minecraft website and is not associated with Mojang Studios or Microsoft. All product and company names are trademarks or registered trademarks of their respective holders. Storia is built on the work of PaperMC (Paper, Folia, Velocity).",
        "nf_title": "Page not found", "nf_text": "The page you are looking for does not exist.", "nf_home": "Back home",
    },
    "ja-jp": {
        "software": "ソフトウェア", "downloads": "ダウンロード", "docs": "ドキュメント", "github": "GitHub",
        "theme": "テーマ切り替え", "menu": "メニュー", "language": "言語",
        "desc": "Storia は Folia ベースの Minecraft サーバーです。RAM 上のワールド、高速なチャンク事前生成、プレイヤーごとの公平な負荷分配、回路を止めない物理演算の最適化、暗号化された別マシンへの地形生成の分担を備えています。",
        "hero1": "マルチスレッドの Minecraft。", "hero2": "全員に公平なサーバーを。",
        "hero_p": "Storia は Folia をベースに、RAM 上で動くワールド、約 5 倍速い事前生成、プレイヤー全員への公平な CPU の割り当て、複数マシンでの地形生成を加えました。回路は一切止めません。",
        "documentation": "ドキュメント",
        "meta": [f"Minecraft {MC_VERSION}", "Java 25", "Folia ベース", "オープンソース"],
        "cards_title": 'サーバーに必要なものを、<span class="accent">すべて。</span>',
        "product_text": {
            "storia": "Minecraft サーバー本体。Folia のリージョン並列処理に、RAM ワールド・高速な事前生成・プレイヤーごとの予算を加えました。",
            "worker": "別のマシンでサーバーの地形を生成します。プレイヤー用ポートは開かず、ワールドも変更しません。",
            "relay": "何台ものワーカーに地形生成の仕事を配る小さなプログラム。Minecraft のファイルは不要です。",
            "proxy": "50 個のプレースホルダー、自動更新のタブリスト、MOTD、ネットワーク全体のメッセージを備えた Velocity のフォーク。",
        },
        "get": "ダウンロード",
        "learn": "詳しく見る",
        "f_ram": ("ワールドは <span class=\"accent\">RAM の上に。</span>",
                  "起動時にワールドを RAM にコピーし、変更はバックグラウンドでディスクに書き戻します。ディスク I/O がボトルネックになりません。",
                  ["変更されたファイルだけを、決めた間隔で同期", "原子的な書き込みで、ディスク上のワールドが書きかけになることはありません", "サーバーのプロセスが落ちても RAM 上のデータは残り、次の起動で復旧"]),
        "f_pregen": ("事前生成が <span class=\"accent\">約 5 倍速く。</span>",
                     "/storia pregen は実行中だけ CPU コアを 1 つ残してすべて使い、すべてのスレッドを休ませません。進み具合は保存されるので、再起動しても続きから再開できます。",
                     ["6 コアで 3,721 チャンクが 3 分 21 秒から 40 秒に", "ノイズ計算を高速化。地形はバニラとまったく同じ", "再起動後は /storia pregen resume で再開"]),
        "bars": [("Folia の初期設定", "3分21秒", 100, False), ("Storia /storia pregen", "40秒", 20, True)],
        "bars_t": "3,721 チャンク · 6 コア", "bars_note": "短いほど高速です。同じシード・同じマシンで計測。",
        "f_budget": ("すべてのプレイヤーに <span class=\"accent\">公平な割り当てを。</span>",
                     "プレイヤーは全員、ティックスレッドを同じだけ使う権利を持っています。サーバーが混んでいるときに、あるリージョンが重くなったり割り当て以上を使ったりすると、そのリージョンにいるプレイヤーだけ、回復するまで描画距離を短くします。",
                     ["サーバーに余裕があるうちは何も制限しません", "シミュレーション距離は変えないので、トラップも回路も動き続けます", "メモリが逼迫したら全員の描画距離を下げ、落ち着けば戻します"]),
        "f_offload": ("地形生成を <span class=\"accent\">別のマシンで。</span>",
                      "地形生成で一番重い処理を、空いているマシンの Storia Worker に任せます。結果はビット単位で同一で、ワーカーが忙しい・遅い・止まったときは、その場でサーバー自身の生成に戻ります。",
                      ["AES-256-GCM で暗号化。鍵のもとになる合言葉はマシンの外に出ません", "接続時に確認用チャンクを照合し、シードやデータパックの違いを拒否", "Storia Relay を使えば、ワーカーをいつでも追加・削除できます"]),
        "f_proxy": ("<span class=\"accent\">50 個のプレースホルダー</span>を持つプロキシ。",
                    "Storia Proxy は、自動更新のタブリスト、サーバーリストの MOTD、参加・退出・移動のメッセージを備えた Velocity です。どれもプロキシ・各サーバー・表示するプレイヤーのプレースホルダーで組み立てられます。",
                    ["{online_lobby}、{status_survival}、{player_ping} ほか 47 個", "MiniMessage で装飾でき、再起動なしで再読み込み", "プラグインから独自のプレースホルダーを登録できる API"]),
        "f_vanilla": ("<span class=\"accent\">バニラと同じ</span>、という約束。",
                      "Storia の最適化は、すべてバニラとまったく同じ結果を出さなければなりません。地形と物理演算の変更は元のコードと照合し、レッドストーンを止めたり遅らせたり飛ばしたりすることはありません。",
                      []),
        "stats": [("0", "件", "ノイズ 1,800 万件での差異"), ("0", "件", "押し合い 50 万回での差異"), ("3", "倍", "エンティティの押し合いの速さ"), ("0", "件", "レッドストーンへの変更")],
        "dl_desc": {
            "storia": "Folia をベースにした、大人数向けの Minecraft サーバーソフトウェア Storia をダウンロード。",
            "worker": "別のマシンで Storia サーバーの地形を生成する Storia Worker をダウンロード。",
            "relay": "何台もの Storia Worker に地形生成の仕事を配る Storia Relay をダウンロード。",
            "proxy": "50 個のプレースホルダーを内蔵した Velocity のフォーク、Storia Proxy をダウンロード。",
        },
        "req": {"storia": "Java 25", "worker": "Java 25", "relay": "Java 21 以上", "proxy": "Java 21 以上"},
        "get_title": "{name}{ver} を入手", "build": "リリース", "older": "過去のビルド",
        "older_text": '過去のビルドや変更履歴をお探しですか？すべてのリリースは <a href="{url}">GitHub Releases</a> にあります。',
        "dev_builds": "開発版のビルド", "no_release": "まだリリースがありません", "other_software": "ほかのソフトウェア",
        "search": "ドキュメントを検索", "search_empty": "見つかりませんでした", "on_page": "このページの内容", "prev": "前へ", "next": "次へ",
        "docs_menu": "ドキュメントのメニュー",
        "f_start": "はじめる", "f_soft": "ソフトウェア", "f_comm": "コミュニティ", "f_res": "リソース",
        "issues": "Issues", "releases": "Releases", "website_src": "このサイトのソース",
        "legal": "このサイトは Minecraft の公式サイトではなく、Mojang Studios や Microsoft とは関係ありません。製品名・会社名は各社の商標または登録商標です。Storia は PaperMC（Paper・Folia・Velocity）の成果をもとに作られています。",
        "nf_title": "ページが見つかりません", "nf_text": "お探しのページは存在しません。", "nf_home": "ホームに戻る",
    },
}


def url(lang, path=""):
    return f"/{lang}/{path}"


# ---------------------------------------------------------------------------------------------
# Page shell
# ---------------------------------------------------------------------------------------------
def header(lang, path, current):
    t = T[lang]
    items = "".join(
        f'<a href="{url(lang, p)}">{logo(k)}<div><strong>{e(n)}</strong><span>{e(t["product_text"][k])}</span></div></a>'
        for k, n, p, _, _ in PRODUCTS)
    cur = lambda k: ' aria-current="page"' if current == k else ""
    lang_opts = "".join(f'<option value="{l}" data-href="{url(l, path)}"{" selected" if l == lang else ""}>{LANG_NAME[l]}</option>' for l in LANGS)
    lang_links = " ".join(f'<a href="{url(l, path)}" hreflang="{HTML_LANG[l]}">{LANG_NAME[l]}</a>' for l in LANGS if l != lang)
    return f"""<header class="site-header" id="site-header">
  <div class="container">
    <a class="brand" href="{url(lang)}" aria-label="Storia">{logo("storia")}<span class="word">STORIA</span></a>
    <nav class="nav" id="site-nav" aria-label="Main">
      <div class="dd"><button type="button" aria-haspopup="true">{t['software']} {ICON['chev']}</button><div class="dd-menu">{items}</div></div>
      <a href="{url(lang, 'downloads/')}"{cur('downloads')}>{t['downloads']}</a>
      <a href="{url(lang, 'docs/')}"{cur('docs')}>{t['docs']}</a>
      <a href="{GITHUB}" rel="noopener">{t['github']} {ICON['ext']}</a>
    </nav>
    <div class="header-tools">
      <a class="icon-btn hide-sm" href="{GITHUB}" aria-label="GitHub">{ICON['github']}</a>
      <label class="lang">{ICON['globe'].replace('<svg ', '<svg class="globe" ')}<span class="sr-only">{t['language']}</span>
        <select id="lang-select" aria-label="{t['language']}">{lang_opts}</select>{ICON['chev']}</label>
      <noscript>{lang_links}</noscript>
      <button class="icon-btn" id="theme-toggle" type="button" title="{t['theme']}" aria-label="{t['theme']}">{ICON['sun']}</button>
      <button class="icon-btn menu-btn" id="menu-toggle" type="button" aria-label="{t['menu']}" aria-controls="site-nav" aria-expanded="false">{ICON['menu']}</button>
    </div>
  </div>
</header>"""


def footer(lang):
    t = T[lang]
    d = lambda slug: f'<li><a href="{url(lang, f"docs/{slug}/")}">{e(doc_title(slug, lang))}</a></li>'
    soft = "".join(f'<li><a href="{url(lang, p)}">{e(n)}</a></li>' for k, n, p, _, _ in PRODUCTS)
    return f"""<footer class="site-footer">
  <div class="container">
    <div class="cols">
      <div><h4>{t['f_start']}</h4><ul>
        <li><a href="{url(lang, 'downloads/')}">{t['downloads']}</a></li>
        <li><a href="{url(lang, 'docs/')}">{t['documentation']}</a></li>
        {d('getting-started')}{d('configuration')}
      </ul></div>
      <div><h4>{t['f_soft']}</h4><ul>{soft}</ul></div>
      <div><h4>{t['f_comm']}</h4><ul>
        <li><a href="{GITHUB}">GitHub</a></li>
        <li><a href="{GITHUB}/issues">{t['issues']}</a></li>
        <li><a href="{GITHUB}/releases">{t['releases']}</a></li>
        <li><a href="https://github.com/{PROXY_REPO}">Storia Proxy</a></li>
      </ul></div>
      <div><h4>{t['f_res']}</h4><ul>
        {d('placeholders')}{d('faq')}{d('building')}
        <li><a href="https://github.com/{SITE_REPO}">{t['website_src']}</a></li>
      </ul></div>
    </div>
    <div class="bottom">
      <a class="brand" href="{url(lang)}">{logo("storia")}<span class="word">STORIA</span></a>
      <div class="copyright">© {datetime.now().year} Storia<br><a href="https://github.com/{SITE_REPO}">{SITE_REPO}</a>{f' @ <a href="https://github.com/{SITE_REPO}/commit/{SITE_SHA}">{SITE_SHA[:7]}</a>' if SITE_SHA else ''}</div>
    </div>
    <p class="legal">{e(t['legal'])}</p>
  </div>
</footer>"""


def page(lang, path, title, description, body, current):
    full_title = f"{title} | Storia" if title else "Storia"
    alternates = "".join(f'<link rel="alternate" hreflang="{HTML_LANG[l]}" href="{url(l, path)}">' for l in LANGS)
    alternates += f'<link rel="alternate" hreflang="x-default" href="{url("en-us", path)}">'
    fonts = ("https://fonts.googleapis.com/css2?family=Poppins:ital,wght@0,400;0,500;0,600;0,700;0,800;1,800"
             "&family=JetBrains+Mono:wght@400;500"
             + ("&family=Noto+Sans+JP:wght@400;500;600;700" if lang == "ja-jp" else "") + "&display=swap")
    return f"""<!doctype html>
<html lang="{HTML_LANG[lang]}" data-lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(full_title)}</title>
<meta name="description" content="{e(description)}">
<meta property="og:title" content="{e(full_title)}">
<meta property="og:description" content="{e(description)}">
<meta property="og:type" content="website">
<meta property="og:image" content="/assets/storia.png">
<meta name="theme-color" content="#2f7bf5">
<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
<link rel="icon" href="/assets/storia.png" type="image/png">
{alternates}
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{fonts}">
<link rel="stylesheet" href="/assets/style.css?v={BUILD_ID}">
<script>try{{var s=localStorage.getItem("storia-theme");if(s)document.documentElement.dataset.theme=s}}catch(e){{}}</script>
</head>
<body>
{header(lang, path, current)}
<main>
{body}
</main>
{footer(lang)}
<script src="/assets/main.js?v={BUILD_ID}" defer></script>
</body>
</html>
"""


# ---------------------------------------------------------------------------------------------
# Home
# ---------------------------------------------------------------------------------------------
def terminal_lines(version):
    radius_chunks = (5000 + 15) >> 4
    side = 2 * radius_chunks + 1
    return [
        ("cmd", '<span class="p">$</span> <span class="c">java</span> -Xmx8G -jar storia-' + e(version) + '.jar nogui'),
        ("out", '<span class="d">[INFO]</span> Starting minecraft server version ' + MC_VERSION),
        ("out", '<span class="d">[INFO]</span> <span class="g">Loaded world (412 MB) into /dev/shm/storia in 830 ms</span>'),
        ("out", '<span class="d">[INFO]</span> Syncing to disk every 300 seconds.'),
        ("out", '<span class="d">[INFO]</span> Player budget enabled: checking every 100 ticks, region MSPT limit 45.0'),
        ("out", '<span class="d">[INFO]</span> <span class="a">Offloading noise generation to 192.168.0.20:25590 (6 threads, encrypted)</span>'),
        ("out", '<span class="d">[INFO]</span> <span class="w">Done (4.812s)! For help, type "help"</span>'),
        ("cmd", '<span class="p">&gt;</span> storia pregen start 5000'),
        ("out", f'<span class="g">Pregenerating {side * side} chunks in world with 11 worker threads.</span>'),
    ]


def feature(key, lang, visual, slug, flip=False, alt=False):
    t = T[lang]
    title, text, bullets = t[key]
    lis = "".join(f"<li>{e(b)}</li>" for b in bullets)
    return f"""<section class="feature{' flip' if flip else ''}{' band alt' if alt else ''}">
  <div class="container">
    <div class="text">
      <h2>{title}</h2>
      <p>{e(text)}</p>
      {f'<ul>{lis}</ul>' if lis else ''}
      <a class="btn secondary" href="{url(lang, f'docs/{slug}/')}">{t['learn']} {ICON['arrow']}</a>
    </div>
    <div class="visual">{visual}</div>
  </div>
</section>"""


def diagram(lang):
    ja = lang == "ja-jp"
    labels = ["プレイヤー" if ja else "Players", "Storia Proxy", "Storia", "Relay", "ワーカー" if ja else "Worker", "地形ノイズ" if ja else "terrain noise"]
    box = lambda x, y, w, h, title, sub="", strong=False: (
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{"#2f7bf5" if strong else "#1f2937"}" stroke="{"#2f7bf5" if strong else "#334155"}"/>'
        f'<text x="{x + w / 2}" y="{y + (h / 2 if not sub else h / 2 - 7)}" text-anchor="middle" dominant-baseline="middle" font-size="14" font-weight="600" fill="#fff">{e(title)}</text>'
        + (f'<text x="{x + w / 2}" y="{y + h / 2 + 11}" text-anchor="middle" dominant-baseline="middle" font-size="10" fill="#cbd5e1">{e(sub)}</text>' if sub else ""))
    line = lambda x1, y1, x2, y2, dash=False: (
        f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#64748b" stroke-width="1.5"{" stroke-dasharray=&quot;4 4&quot;" if dash else ""} marker-end="url(#arr)"/>')
    workers = "".join(box(440, 12 + i * 62, 118, 46, f"{labels[4]} {chr(65 + i)}", labels[5]) for i in range(3))
    wlines = "".join(line(404, 105, 438, 35 + i * 62, True) for i in range(3))
    return f"""<div class="panel"><div class="t">storia offload · AES-256-GCM</div>
<svg class="diagram" viewBox="0 0 570 210" role="img" aria-label="Storia offload">
<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M0 0 10 5 0 10z" fill="#64748b"/></marker></defs>
{box(0, 82, 84, 46, labels[0])}{line(86, 105, 104, 105)}
{box(106, 82, 104, 46, labels[1])}{line(212, 105, 230, 105)}
{box(232, 76, 90, 58, labels[2], "26.2", True)}{line(324, 105, 342, 105, True)}
{box(344, 82, 60, 46, labels[3])}
{wlines}{workers}
</svg></div>"""


def home(lang):
    t = T[lang]
    version = LATEST["version"]
    term = "".join(f'<span class="ln" data-k="{k}">{h}</span>' for k, h in terminal_lines(version))
    meta = "".join(f"<span>{e(m)}</span>" for m in t["meta"])
    cards = "".join(f"""<a class="card" href="{url(lang, p)}"><div class="top">{logo(k)}<h3>{e(n)}</h3></div>
      <p>{e(t['product_text'][k])}</p><span class="go">{t['get']} →</span></a>""" for k, n, p, _, _ in PRODUCTS)
    status = """<div class="panel"><div class="t">/storia status</div><pre><span style="color:#67e8f9">Storia 26.2</span>
<span style="color:#94a3b8">RAM world:</span> <span style="color:#4ade80">enabled</span>
<span style="color:#94a3b8">RAM path:</span> /dev/shm/storia/survival
<span style="color:#94a3b8">Disk path:</span> /srv/survival
<span style="color:#94a3b8">RAM used:</span> 3187 MB
<span style="color:#94a3b8">Sync interval:</span> 300 s
<span style="color:#94a3b8">Last sync:</span> 2m 14s ago (184 file(s))</pre></div>""".replace("26.2", e(version))
    bars = "".join(f"""<div class="bar-row{' win' if win else ''}"><div class="lbl"><span>{e(n)}</span><b>{e(v)}</b></div>
      <div class="track"><div class="fill" style="width:{w}%"></div></div></div>""" for n, v, w, win in t["bars"])
    pregen = f'<div class="panel"><div class="t">{e(t["bars_t"])}</div><div class="bars">{bars}</div><p class="bar-note">{e(t["bars_note"])}</p></div>'
    budget = """<div class="panel"><div class="t">/storia budget</div><pre><span style="color:#67e8f9">Player budget (checked every 5s)</span>
<span style="color:#94a3b8">Tick threads busy:</span> <span style="color:#f87171">91% (saturated: heavy regions are limited)</span>
<span style="color:#94a3b8">Share per player:</span> 40% of a thread
<span style="color:#94a3b8">Heap after GC:</span> <span style="color:#4ade80">52%</span>
 Alice: <span style="color:#94a3b8">region 38.2 MSPT, 20.0 TPS, 140% thread, 1 player(s)</span> <span style="color:#facc15">| sim default, view 9</span>
 Bob: <span style="color:#94a3b8">region 6.1 MSPT, 20.0 TPS, 20% thread, 2 player(s)</span> <span style="color:#4ade80">| sim default, view default</span>
 Carol: <span style="color:#94a3b8">region 4.8 MSPT, 20.0 TPS, 15% thread, 1 player(s)</span> <span style="color:#4ade80">| sim default, view default</span></pre></div>"""
    proxy = f"""<div class="panel"><div class="t">storia-proxy.toml · tablist</div>
<div class="mc-tab"><b style="color:#fff">My Network</b><br><span style="color:#aaa">42/200 online · 21:37</span>
<div class="rows"><span>Alice <i>12ms</i></span><span>Bob <i>34ms</i></span><span>Carol <i style="color:#facc15">96ms</i></span><span>Dave <i>18ms</i></span></div>
<span style="color:#aaa">survival <span style="color:#666">(28)</span> · ping <span style="color:#4ade80">12ms</span></span><br><span style="color:#666">uptime 3d 4h 12m</span></div>
<div class="mc-motd"><span class="ico">{MARK}</span><div><b style="color:#fff">My Network</b> <span style="color:#555">|</span> <span style="color:#aaa">3/3 servers up</span><br><span style="color:#aaa">42 players online · 21:37</span></div></div></div>"""
    stats = "".join(f"<div><b>{v}<small>{u}</small></b><span>{e(l)}</span></div>" for v, u, l in t["stats"])
    vanilla = f'<div class="panel"><div class="stats">{stats}</div></div>'
    body = f"""
<section class="hero">
  <div class="container">
    <div>
      <h1><span>{e(t['hero1'])}</span><span class="accent">{e(t['hero2'])}</span></h1>
      <p>{e(t['hero_p'])}</p>
      <div class="actions">
        <a class="btn primary" href="{url(lang, 'downloads/')}">{t['downloads']}</a>
        <a class="btn secondary" href="{url(lang, 'docs/')}">{t['documentation']}</a>
      </div>
      <div class="meta">{meta}</div>
    </div>
    <div class="terminal" aria-hidden="true"><div class="bar"><i></i><i></i><i></i><b>storia — bash</b></div><pre id="term">{term}</pre></div>
  </div>
</section>

<section class="band alt">
  <div class="container">
    <h2>{t['cards_title']}</h2>
    <div class="cards">{cards}</div>
  </div>
</section>

{feature('f_ram', lang, status, 'ram-world')}
{feature('f_pregen', lang, pregen, 'pregeneration', flip=True)}
{feature('f_budget', lang, budget, 'player-budget')}
{feature('f_offload', lang, diagram(lang), 'offload', flip=True)}
{feature('f_proxy', lang, proxy, 'placeholders')}
{feature('f_vanilla', lang, vanilla, 'performance', flip=True)}
<div style="height:48px"></div>"""
    return page(lang, "", "", t["desc"], body, "home")


# ---------------------------------------------------------------------------------------------
# Downloads
# ---------------------------------------------------------------------------------------------
def fmt_size(b):
    return f"{b / 1048576:.1f} MB" if b >= 1048576 else f"{max(1, round(b / 1024))} KB"


def fmt_date(s):
    return s[:10]


def downloads(lang, key):
    t = T[lang]
    _, name, path, pattern, doc = next(p for p in PRODUCTS if p[0] == key)
    rows = []
    for rel in RELEASES:
        asset = next((a for a in rel["assets"] if re.fullmatch(pattern, a["name"])), None)
        if asset:
            rows.append((rel, asset))
    if rows:
        rel, asset = rows[0]
        ver = rel["tag_name"].lstrip("v")
        sha = (asset.get("digest") or "").replace("sha256:", "")
        main_btn = f"""<a class="dl-main" href="{e(asset['browser_download_url'])}"><span class="ic">{ICON['dl']}</span>
  <span class="txt"><b>{e(name)} {e(ver)}</b><span>{e(asset['name'])} · {fmt_size(asset['size'])}</span></span></a>
<div class="dl-meta"><span>{e(t['req'][key])}</span><span>{t['build']} {e(rel['tag_name'])} · {fmt_date(rel['published_at'])}</span>{f'<span>SHA-256 <code>{e(sha)}</code></span>' if sha else ''}</div>"""
        title_ver = f' <span class="accent">{e(ver)}</span>'
    else:
        main_btn = f'<a class="dl-main" href="{GITHUB}/releases"><span class="ic">{ICON["dl"]}</span><span class="txt"><b>{t["no_release"]}</b><span>GitHub Releases</span></span></a>'
        title_ver = ""
    switch = "".join(f'<a href="{url(lang, p)}"{" aria-current=page" if k == key else ""}>{logo(k)}{e(n)}</a>' for k, n, p, _, _ in PRODUCTS)
    builds = []
    for rel, asset in rows:
        changes = rel.get("changes") or [{"sha": "", "message": rel.get("name") or rel["tag_name"]}]
        lines = "".join(
            f'<div class="change">{f"""<a href="{GITHUB}/commit/{c["sha"]}">{c["sha"][:7]}</a>""" if c["sha"] else ""}<span>{linkify(e(c["message"]))}</span></div>'
            for c in changes)
        builds.append(f"""<div class="build"><a class="badge" href="{e(asset['browser_download_url'])}">{ICON['file']}{e(rel['tag_name'].lstrip('v'))}</a>
  <div class="changes">{lines}<div class="files"><a href="{e(rel['html_url'])}">{t['releases']}</a>{e(asset['name'])} · {fmt_size(asset['size'])}</div></div>
  <span class="date" data-time="{e(rel['published_at'])}">{fmt_date(rel['published_at'])}</span></div>""")
    body = f"""
<section class="dl-head"><div class="container">
  <div class="dl-kicker">{logo(key)}{t['downloads']}</div>
  <h1>{t['get_title'].format(name=e(name), ver=title_ver)}</h1>
  <p>{e(t['dl_desc'][key])} <a href="{url(lang, f'docs/{doc}/')}" style="color:var(--accent);text-decoration:none">{t['documentation']} →</a></p>
  {main_btn}
  <div class="dl-switch" aria-label="{t['other_software']}">{switch}</div>
</div></section>
<section class="older"><div class="container">
  <div class="intro"><h2>{t['older']}</h2><p>{t['older_text'].format(url=GITHUB + '/releases')}</p>
    <p><a href="{GITHUB}/actions">{t['dev_builds']}</a></p></div>
  {''.join(builds)}
</div></section>"""
    return page(lang, path, f"{t['downloads']}: {name}", t["dl_desc"][key], body, "downloads")


def linkify(text):
    return re.sub(r"\(#(\d+)\)", lambda m: f'(<a href="{GITHUB}/pull/{m.group(1)}" style="color:var(--accent)">#{m.group(1)}</a>)', text)


# ---------------------------------------------------------------------------------------------
# Docs
# ---------------------------------------------------------------------------------------------
class Doc:
    pass


def slugify(value, separator="-"):
    value = re.sub(r"<[^>]+>", "", value)
    value = re.sub(r"[^\w\s\-぀-ヿ一-鿿]", "", value.lower(), flags=re.UNICODE).strip()
    return re.sub(r"[\s]+", separator, value)


def parse_front(text):
    meta = {}
    if text.startswith("---\n"):
        head, _, text = text[4:].partition("\n---\n")
        for line in head.splitlines():
            k, _, v = line.partition(":")
            meta[k.strip()] = v.strip()
    return meta, text


def render_markdown(src, lang):
    md = markdown.Markdown(extensions=[
        "fenced_code", "tables", "admonition", "attr_list", "md_in_html", "sane_lists", "codehilite", "toc"],
        extension_configs={
            "codehilite": {"css_class": "hl", "guess_lang": False},
            "toc": {"permalink": "#", "permalink_class": "headerlink", "slugify": slugify, "toc_depth": "2-3"},
        })

    def link(m):
        target, _, text = m.group(1).partition("|")
        slug, _, anchor = target.partition("#")
        try:
            title = doc_title(slug, lang)
        except StopIteration:
            raise SystemExit(f"unknown doc link [[{m.group(1)}]]")
        return f"[{text or title}]({url(lang, f'docs/{slug}/')}{'#' + anchor if anchor else ''})"
    src = re.sub(r"\[\[([^\]]+)\]\]", link, src)
    src = src.replace("](/en-us/", f"](/{lang}/")
    src = src.replace("{{VERSION}}", LATEST["version"]).replace("{{MC}}", MC_VERSION).replace("{{GITHUB}}", GITHUB)
    return md.convert(src), md.toc_tokens


def plain(html_text):
    txt = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html_text, flags=re.S)
    txt = re.sub(r'<a class="headerlink"[^>]*>.*?</a>', "", txt)
    txt = re.sub(r"<[^>]+>", " ", txt)
    return re.sub(r"\s+", " ", html.unescape(txt)).strip()


def search_sections(body):
    """Split rendered HTML at h2/h3 so search hits jump to the right heading."""
    parts = re.split(r'(<h[23] id="[^"]+">.*?</h[23]>)', body, flags=re.S)
    sections = [{"h": "", "a": "", "x": plain(parts[0])[:1500]}]
    for i in range(1, len(parts), 2):
        m = re.match(r'<h[23] id="([^"]+)">(.*?)</h[23]>', parts[i], re.S)
        sections.append({"h": plain(m.group(2)), "a": m.group(1), "x": plain(parts[i + 1])[:1500]})
    return [s for s in sections if s["h"] or s["x"]]


def docs(lang):
    t = T[lang]
    index, pages = [], {}
    for (g_en, g_ja), items in DOCS_NAV:
        for slug, en, ja in items:
            meta, src = parse_front((CONTENT / lang / f"{slug}.md").read_text(encoding="utf-8"))
            body, toc = render_markdown(src, lang)
            d = Doc()
            d.slug, d.title, d.group = slug, en if lang == "en-us" else ja, g_en if lang == "en-us" else g_ja
            d.summary, d.body, d.toc = meta.get("summary", ""), body, toc
            pages[slug] = d
            index.append({"t": d.title, "g": d.group, "u": url(lang, f"docs/{slug}/"), "s": search_sections(body)})
    (DIST / lang / "docs").mkdir(parents=True, exist_ok=True)
    (DIST / lang / "docs" / "search-index.json").write_text(json.dumps(index, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    flat = [slug for _, items in DOCS_NAV for slug, _, _ in items]
    for i, slug in enumerate(flat):
        d = pages[slug]
        side = []
        for (g_en, g_ja), items in DOCS_NAV:
            links = "".join(f'<a href="{url(lang, f"docs/{s}/")}"{" aria-current=page" if s == slug else ""}>{e(en if lang == "en-us" else ja)}</a>'
                            for s, en, ja in items)
            side.append(f'<div class="group"><p class="group-title">{e(g_en if lang == "en-us" else g_ja)}</p>{links}</div>')
        toc_items = []
        for h in d.toc:
            toc_items.append(f'<li><a href="#{h["id"]}">{h["name"]}</a></li>')
            for c in h.get("children", []):
                toc_items.append(f'<li class="l3"><a href="#{c["id"]}">{c["name"]}</a></li>')
        toc_html = f'<p class="title">{t["on_page"]}</p><ul>{"".join(toc_items)}</ul>' if toc_items else ""
        prev_html = next_html = ""
        if i > 0:
            p = pages[flat[i - 1]]
            prev_html = f'<a class="prev" href="{url(lang, f"docs/{p.slug}/")}"><span class="dir">{t["prev"]}</span><span class="t">« {e(p.title)}</span></a>'
        if i < len(flat) - 1:
            n = pages[flat[i + 1]]
            next_html = f'<a class="next" href="{url(lang, f"docs/{n.slug}/")}"><span class="dir">{t["next"]}</span><span class="t">{e(n.title)} »</span></a>'
        summary = f'<p class="summary">{e(d.summary)}</p>' if d.summary else ""
        body = f"""
<div class="docs">
  <button class="icon-btn docs-menu" id="docs-menu" type="button" aria-controls="sidebar" aria-expanded="false">{e(d.group)} › {e(d.title)} {ICON['menu']}</button>
  <aside class="sidebar" id="sidebar" aria-label="{t['docs_menu']}">
    <div class="search">{ICON['search']}
      <input id="search" type="search" placeholder="{t['search']}  /" aria-label="{t['search']}" autocomplete="off"
        data-index="{url(lang, 'docs/search-index.json')}?v={BUILD_ID}" data-empty="{t['search_empty']}">
      <div class="search-results" id="search-results" role="listbox"></div>
    </div>
    {''.join(side)}
  </aside>
  <article class="doc">
    <div class="crumbs"><a href="{url(lang, 'docs/')}">{t['docs']}</a> › {e(d.group)}</div>
    <h1>{e(d.title)}</h1>
    {summary}
    {d.body}
    <nav class="pager">{prev_html}{next_html}</nav>
  </article>
  <nav class="toc" aria-label="{t['on_page']}">{toc_html}</nav>
</div>"""
        write(lang, f"docs/{slug}/", page(lang, f"docs/{slug}/", d.title, d.summary or t["desc"], body, "docs"))
    write(lang, "docs/", redirect_page(url(lang, "docs/introduction/")))


def redirect_page(target):
    return f'<!doctype html><meta charset="utf-8"><title>Storia</title><meta http-equiv="refresh" content="0; url={target}"><link rel="canonical" href="{target}"><a href="{target}">{target}</a>'


def not_found(lang):
    t = T[lang]
    body = f"""<section class="notfound"><div class="container">
  <div class="code">404</div><h1>{e(t['nf_title'])}</h1><p>{e(t['nf_text'])}</p>
  <div class="actions" style="margin-top:28px"><a class="btn primary" href="{url(lang)}">{e(t['nf_home'])}</a>
  <a class="btn secondary" href="{url(lang, 'docs/')}">{t['documentation']}</a></div></div></section>"""
    return page(lang, "", t["nf_title"], t["nf_text"], body, "")


def write(lang, path, content):
    out = DIST / lang / path / "index.html" if path.endswith("/") or path == "" else DIST / lang / path
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(content, encoding="utf-8")


# ---------------------------------------------------------------------------------------------
# Releases (from the GitHub API, with the commits that went into each release)
# ---------------------------------------------------------------------------------------------
def api(path):
    req = urllib.request.Request(f"https://api.github.com/{path}", headers={"Accept": "application/vnd.github+json", "User-Agent": "storia-site"})
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=20) as res:
        return json.load(res)


def first_line(message):
    return message.strip().splitlines()[0] if message.strip() else ""


def load_releases():
    cache = ROOT / "releases.json"
    try:
        data = [r for r in api(f"repos/{REPO}/releases?per_page=30") if not r.get("draft")]
        for i, rel in enumerate(data):
            tag = rel["tag_name"]
            if i + 1 < len(data):
                commits = api(f"repos/{REPO}/compare/{data[i + 1]['tag_name']}...{tag}").get("commits", [])[::-1]
            else:
                commits = api(f"repos/{REPO}/commits?sha={tag}&per_page=5")
            rel["changes"] = [{"sha": c["sha"], "message": first_line(c["commit"]["message"])} for c in commits[:6]]
        cache.write_text(json.dumps(data, indent=1), encoding="utf-8")
    except Exception as ex:  # offline or rate limited: use the last copy
        print(f"warning: could not fetch releases ({ex}); using releases.json")
        data = json.loads(cache.read_text(encoding="utf-8")) if cache.exists() else []
    return data


RELEASES = []
LATEST = {"version": MC_VERSION}
BUILD_ID = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
SITE_SHA = ""


def main():
    global RELEASES, LATEST, SITE_SHA
    RELEASES = load_releases()
    if RELEASES:
        LATEST = {"version": RELEASES[0]["tag_name"].lstrip("v")}
    try:
        SITE_SHA = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    except Exception:
        SITE_SHA = ""
    if DIST.exists():
        shutil.rmtree(DIST)
    (DIST / "assets").mkdir(parents=True)
    for f in STATIC.iterdir():
        shutil.copy2(f, DIST / "assets" / f.name)
    for lang in LANGS:
        write(lang, "", home(lang))
        for key, *_ in PRODUCTS:
            _, _, path, _, _ = next(p for p in PRODUCTS if p[0] == key)
            write(lang, path, downloads(lang, key))
        docs(lang)
        write(lang, "404.html", not_found(lang))
    (DIST / "index.html").write_text(redirect_page(url("en-us")), encoding="utf-8")
    (DIST / "robots.txt").write_text("User-agent: *\nAllow: /\n", encoding="utf-8")
    print(f"built {sum(1 for _ in DIST.rglob('*.html'))} pages into {DIST} (latest release {LATEST['version']})")


if __name__ == "__main__":
    main()
