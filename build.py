#!/usr/bin/env python3
"""Builds the Storia website into dist/.

    python3 build.py            # uses the release list baked from GitHub (via `gh`, if available)

Languages live under /en-us/ and /ja-jp/. "/" is sent to one of them by the web server
(see deploy/nginx.conf), using the visitor's saved choice or Cloudflare's CF-IPCountry header.
"""
import html
import json
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"
CONTENT = ROOT / "content"
STATIC = ROOT / "static"

REPO = "AKSHRK-Dev/Storia"
PROXY_REPO = "AKSHRK-Dev/StoriaProxy"
GITHUB = f"https://github.com/{REPO}"
MC_VERSION = "26.2"
LANGS = ["en-us", "ja-jp"]
HTML_LANG = {"en-us": "en", "ja-jp": "ja"}
LANG_NAME = {"en-us": "English", "ja-jp": "日本語"}

# ---------------------------------------------------------------------------------------------
# Docs navigation: (group, [(slug, title_en, title_ja)])
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
DOC_ORDER = [(g, item) for g, items in DOCS_NAV for item in items]

# ---------------------------------------------------------------------------------------------
# UI strings
# ---------------------------------------------------------------------------------------------
T = {
    "en-us": {
        "nav_home": "Home", "nav_downloads": "Downloads", "nav_docs": "Docs", "nav_github": "GitHub",
        "theme": "Toggle theme", "menu": "Menu", "language": "Language",
        "tagline": "A high-performance Minecraft server for large communities, built on Folia.",
        "desc": "Storia is a Folia-based Minecraft server with RAM-backed worlds, fast chunk pregeneration, per-player fairness, redstone-safe physics optimizations and encrypted terrain offloading to other machines.",
        "etym": "storia — Italian for “history”",
        "hero_lede": "Storia keeps your worlds in RAM, pregenerates terrain five times faster, gives every player a fair share of the server and can hand terrain generation to other machines. Your redstone keeps running.",
        "get": "Download Storia", "read_docs": "Read the docs",
        "meta": [f"Minecraft {MC_VERSION}", "Java 25", "Based on Folia"],
        "col_eyebrow": "The collection", "col_title": "Six exhibits of performance",
        "col_text": "Every Storia feature is built on Folia's regionised multithreading and keeps vanilla behaviour: the same terrain for the same seed, the same entity physics, and redstone that is never paused.",
        "more": "Learn more",
        "exhibits": [
            ("RAM world", "Worlds are copied into RAM at startup and written back in the background. Disk I/O stops being your bottleneck, and a crash of the server process never loses the RAM copy.", "ram-world"),
            ("Fast pregeneration", "/storia pregen uses every core but one while it runs, survives restarts and generated 3,721 chunks in 40 seconds instead of 3 minutes 21.", "pregeneration"),
            ("Per-player budget", "Each player gets a fair share of the tick threads. Only the region that is actually lagging is limited, and simulation distance is left alone so farms keep working.", "player-budget"),
            ("Redstone-safe physics", "Entity pushing is about three times faster with identical results. Redstone is never modified or slowed down.", "performance"),
            ("Terrain offload", "Send the heaviest step of terrain generation to other machines. Results are bit-for-bit identical, and the server falls back to local generation at any time.", "offload"),
            ("Storia Proxy", "A Velocity fork with 50 built-in placeholders for the MOTD, tab list and chat, plus an API for your own plugins.", "proxy"),
        ],
        "num_eyebrow": "By the numbers", "num_title": "Measured, not promised",
        "num_text": "Benchmarks from our test machines. Terrain and physics results are verified against the original code on every run.",
        "figures": [
            ("5.1", "×", "Faster pregeneration", "3,721 chunks: 3m 21s → 40s on 6 cores"),
            ("3", "×", "Faster entity pushing", "6,000 crammed entities: 750 → 252 MSPT"),
            ("0", "", "Differences", "18M noise samples and 500,000 pushes checked against vanilla"),
            ("50", "", "Proxy placeholders", "Proxy, backend server and player values"),
        ],
        "fine": "Offload: server on 3 cores + one worker on 3 cores pregenerated the same area in 1m 6s instead of 1m 35s.",
        "wings_eyebrow": "The wings", "wings_title": "One server, four programs",
        "wings_text": "Run Storia on its own, or spread the work: workers compute terrain on spare machines, a relay hands out the work, and Storia Proxy connects your players.",
        "wings": [
            ("Server", "Storia", "The Minecraft server. Folia's regionised threading plus everything on this page.", "storia", "getting-started"),
            ("Helper", "Storia Worker", "Generates terrain for your server on another machine. No player port, no world changes.", "worker", "worker"),
            ("Router", "Storia Relay", "A tiny program that shares terrain work between any number of workers. No Minecraft files needed.", "relay", "relay"),
            ("Proxy", "Storia Proxy", "Velocity with 50 placeholders, a live tab list, MOTD and join messages.", "proxy", "proxy"),
        ],
        "download": "Download", "docs": "Docs",
        "diagram": ["Players", "Storia Proxy", "Storia server", "worlds · structures · light", "Storia Relay", "Worker", "terrain noise", "encrypted"],
        "qs_title": "Up and running in a minute",
        "qs_text": "Storia is a drop-in replacement for a Folia server. Plugins that support Folia work unchanged.",
        "qs_steps": [
            ("Install Java 25", "Any Java 25 distribution, such as Eclipse Temurin."),
            ("Download Storia", "Get the latest storia jar from the downloads page."),
            ("Start the server", "Accept the EULA, start it again, and storia.yml is created next to server.properties."),
        ],
        "cta_title": "Write your server's history.", "cta_text": "Free and open source under the GPLv3, like Paper and Folia.",
        "footer_about": "A high-performance Minecraft server based on Folia.",
        "f_project": "Project", "f_docs": "Documentation", "f_source": "Source",
        "legal": "Storia is not an official Minecraft product and is not associated with Mojang or Microsoft.",
        "legal2": "Built on the work of PaperMC (Paper, Folia, Velocity).",
        # downloads
        "dl_title": "Downloads", "dl_text": "Every release contains the server, the worker and relay for offloading, and Storia Proxy. All files are built by GitHub Actions from the public source.",
        "latest": "Latest release", "version": "Version", "file": "File", "size": "Size", "released": "Released", "sha": "SHA-256",
        "notes": "Release notes", "all": "All releases", "dev": "Development builds are available from GitHub Actions.",
        "products": [
            ("storia", "Storia", "Server", r"storia-[0-9][0-9.]*(-[0-9]+)?\.jar", "The Storia server. Replace your Folia or Paper jar with it.", "Requires Java 25.", "getting-started"),
            ("worker", "Storia Worker", "Offload", r"storia-worker-.*\.zip", "A ready-to-run package that generates terrain for your server on another machine.", "Requires Java 25 and a copy of your world's level.dat and datapacks.", "worker"),
            ("relay", "Storia Relay", "Offload", r"storia-relay-.*\.zip", "Shares terrain work between any number of Storia Workers.", "Requires Java 21 or newer. No Minecraft files.", "relay"),
            ("proxy", "Storia Proxy", "Proxy", r"storia-proxy-.*\.jar", "A Velocity fork with 50 built-in placeholders.", "Requires Java 21 or newer.", "proxy"),
        ],
        # docs
        "search": "Search docs", "search_empty": "No results", "on_page": "On this page", "prev": "Previous", "next": "Next",
        "docs_menu": "Documentation menu",
        "nf_title": "Page not found", "nf_text": "This room of the museum does not exist.", "nf_home": "Back to the entrance",
    },
    "ja-jp": {
        "nav_home": "ホーム", "nav_downloads": "ダウンロード", "nav_docs": "ドキュメント", "nav_github": "GitHub",
        "theme": "テーマ切り替え", "menu": "メニュー", "language": "言語",
        "tagline": "Folia をベースにした、大人数向けの高性能 Minecraft サーバー。",
        "desc": "Storia は Folia ベースの Minecraft サーバーです。RAM 上のワールド、高速なチャンク事前生成、プレイヤーごとの公平な負荷分配、回路を止めない物理演算の最適化、暗号化された別マシンへの地形生成の分担を備えています。",
        "etym": "storia ― イタリア語で「歴史」",
        "hero_lede": "ワールドを RAM に置き、チャンクの事前生成は約 5 倍速。プレイヤー一人ひとりに公平に CPU を割り当て、地形生成を別のマシンに任せることもできます。回路は止まりません。",
        "get": "Storia をダウンロード", "read_docs": "ドキュメントを読む",
        "meta": [f"Minecraft {MC_VERSION}", "Java 25", "Folia ベース"],
        "col_eyebrow": "コレクション", "col_title": "性能を支える 6 つの展示",
        "col_text": "すべての機能は Folia のリージョン並列処理の上に作られ、バニラと同じ動作を保ちます。同じシードなら同じ地形、同じ物理演算、そして回路は止まりません。",
        "more": "詳しく見る",
        "exhibits": [
            ("RAM ワールド", "起動時にワールドを RAM にコピーし、変更はバックグラウンドでディスクに書き戻します。ディスク I/O がボトルネックにならず、サーバーのプロセスが落ちても RAM 上のデータは残ります。", "ram-world"),
            ("高速な事前生成", "/storia pregen は実行中だけ CPU コアを 1 つ残してすべて使い、再起動しても続きから再開できます。3,721 チャンクが 3 分 21 秒から 40 秒になりました。", "pregeneration"),
            ("プレイヤーごとの予算", "プレイヤー一人ひとりにティックスレッドを公平に割り当てます。制限されるのは実際に重いリージョンだけで、シミュレーション距離は変えないのでトラップも動き続けます。", "player-budget"),
            ("回路を止めない物理演算", "エンティティの押し合いの計算が約 3 倍速くなり、結果はまったく同じです。レッドストーンには一切手を加えていません。", "performance"),
            ("地形生成の分担", "地形生成で一番重い処理を別のマシンに任せます。結果はビット単位で同一で、いつでもメインサーバーでの生成に戻れます。", "offload"),
            ("Storia Proxy", "50 個のプレースホルダーを内蔵した Velocity のフォーク。MOTD・タブリスト・チャットに使え、プラグイン用の API もあります。", "proxy"),
        ],
        "num_eyebrow": "数字で見る", "num_title": "約束ではなく、計測値",
        "num_text": "テスト環境でのベンチマークです。地形と物理演算の結果は、元のコードと毎回照合して同一であることを確認しています。",
        "figures": [
            ("5.1", "倍", "事前生成が高速化", "3,721 チャンク：3分21秒 → 40秒（6 コア）"),
            ("3", "倍", "押し合いの計算が高速化", "6,000 体の密集：750 → 252 MSPT"),
            ("0", "件", "バニラとの差異", "ノイズ 1,800 万件・押し合い 50 万回を照合"),
            ("50", "個", "プロキシのプレースホルダー", "プロキシ・各サーバー・プレイヤーの情報"),
        ],
        "fine": "分担：サーバー 3 コア＋ワーカー 3 コアで、同じ範囲の事前生成が 1分35秒 から 1分6秒 になりました。",
        "wings_eyebrow": "展示棟", "wings_title": "ひとつのサーバー、4 つのソフト",
        "wings_text": "Storia 単体でも動きますし、処理を分散することもできます。ワーカーが空いているマシンで地形を計算し、リレーが仕事を配り、Storia Proxy がプレイヤーをつなぎます。",
        "wings": [
            ("サーバー", "Storia", "Minecraft サーバー本体。Folia のリージョン並列処理に、このページの機能をすべて加えたものです。", "storia", "getting-started"),
            ("ヘルパー", "Storia Worker", "別のマシンでメインサーバーの地形を生成します。プレイヤー用ポートは開かず、ワールドも変更しません。", "worker", "worker"),
            ("中継", "Storia Relay", "何台ものワーカーに地形生成の仕事を配る小さなプログラム。Minecraft のファイルは不要です。", "relay", "relay"),
            ("プロキシ", "Storia Proxy", "50 個のプレースホルダー、自動更新のタブリスト、MOTD、参加メッセージを備えた Velocity。", "proxy", "proxy"),
        ],
        "download": "ダウンロード", "docs": "ドキュメント",
        "diagram": ["プレイヤー", "Storia Proxy", "Storia サーバー", "ワールド・構造物・光", "Storia Relay", "ワーカー", "地形ノイズ", "暗号化"],
        "qs_title": "1 分で起動",
        "qs_text": "Storia は Folia サーバーとそのまま置き換えられます。Folia 対応のプラグインはそのまま動きます。",
        "qs_steps": [
            ("Java 25 をインストール", "Eclipse Temurin など、Java 25 ならどれでも使えます。"),
            ("Storia をダウンロード", "ダウンロードページから最新の jar を入手します。"),
            ("サーバーを起動", "EULA に同意してもう一度起動すると、server.properties の隣に storia.yml が作られます。"),
        ],
        "cta_title": "あなたのサーバーの歴史を。", "cta_text": "Paper や Folia と同じく GPLv3 の無料オープンソースです。",
        "footer_about": "Folia をベースにした高性能 Minecraft サーバー。",
        "f_project": "プロジェクト", "f_docs": "ドキュメント", "f_source": "ソースコード",
        "legal": "Storia は Minecraft の公式製品ではなく、Mojang や Microsoft とは関係ありません。",
        "legal2": "PaperMC（Paper・Folia・Velocity）の成果をもとに作られています。",
        "dl_title": "ダウンロード", "dl_text": "各リリースには、サーバー本体、処理分担用のワーカーとリレー、Storia Proxy が含まれます。すべて公開されているソースから GitHub Actions でビルドしています。",
        "latest": "最新リリース", "version": "バージョン", "file": "ファイル", "size": "サイズ", "released": "公開日", "sha": "SHA-256",
        "notes": "リリースノート", "all": "すべてのリリース", "dev": "開発版のビルドは GitHub Actions から入手できます。",
        "products": [
            ("storia", "Storia", "サーバー", r"storia-[0-9][0-9.]*(-[0-9]+)?\.jar", "Storia サーバー本体です。Folia や Paper の jar と置き換えて使います。", "Java 25 が必要です。", "getting-started"),
            ("worker", "Storia Worker", "処理の分担", r"storia-worker-.*\.zip", "別のマシンでメインサーバーの地形を生成する、すぐに使えるパッケージです。", "Java 25 と、ワールドの level.dat・データパックのコピーが必要です。", "worker"),
            ("relay", "Storia Relay", "処理の分担", r"storia-relay-.*\.zip", "何台もの Storia Worker に地形生成の仕事を配ります。", "Java 21 以上が必要です。Minecraft のファイルは不要です。", "relay"),
            ("proxy", "Storia Proxy", "プロキシ", r"storia-proxy-.*\.jar", "50 個のプレースホルダーを内蔵した Velocity のフォークです。", "Java 21 以上が必要です。", "proxy"),
        ],
        "search": "ドキュメントを検索", "search_empty": "見つかりませんでした", "on_page": "このページの内容", "prev": "前へ", "next": "次へ",
        "docs_menu": "ドキュメントのメニュー",
        "nf_title": "ページが見つかりません", "nf_text": "この展示室は存在しないようです。", "nf_home": "入口に戻る",
    },
}

# ---------------------------------------------------------------------------------------------
# Icons
# ---------------------------------------------------------------------------------------------
MARK = ('<svg class="{cls}" viewBox="46 40 108 120" fill="currentColor" aria-hidden="true">'
        '<rect x="50" y="44" width="100" height="16" rx="3"/><rect x="62" y="68" width="20" height="64" rx="3"/>'
        '<rect x="90" y="68" width="20" height="64" rx="3"/><rect x="118" y="68" width="20" height="64" rx="3"/>'
        '<rect x="50" y="140" width="100" height="16" rx="3"/></svg>')
ICON_SUN = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>'
ICON_GLOBE = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c2.5 2.6 3.8 5.6 3.8 9s-1.3 6.4-3.8 9c-2.5-2.6-3.8-5.6-3.8-9S9.5 5.6 12 3z"/></svg>'
ICON_GH = '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 .5A11.5 11.5 0 0 0 .5 12a11.5 11.5 0 0 0 7.86 10.92c.58.1.79-.25.79-.56v-2c-3.2.7-3.87-1.37-3.87-1.37-.52-1.33-1.28-1.69-1.28-1.69-1.04-.71.08-.7.08-.7 1.15.08 1.76 1.19 1.76 1.19 1.03 1.76 2.69 1.25 3.35.96.1-.75.4-1.25.73-1.54-2.55-.29-5.24-1.28-5.24-5.69 0-1.26.45-2.29 1.19-3.1-.12-.29-.52-1.46.11-3.05 0 0 .97-.31 3.17 1.18a11 11 0 0 1 5.77 0c2.2-1.49 3.17-1.18 3.17-1.18.63 1.59.23 2.76.11 3.05.74.81 1.19 1.84 1.19 3.1 0 4.42-2.7 5.39-5.26 5.68.41.36.78 1.06.78 2.14v3.17c0 .31.21.67.8.56A11.5 11.5 0 0 0 23.5 12 11.5 11.5 0 0 0 12 .5z"/></svg>'
ICON_MENU = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M4 7h16M4 12h16M4 17h16"/></svg>'
ICON_DL = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 4v11m0 0 4.5-4.5M12 15l-4.5-4.5M5 20h14"/></svg>'
ICON_ARROW = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14m0 0-5-5m5 5-5 5"/></svg>'
ICON_SEARCH = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>'

ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII"]
e = html.escape


def url(lang, path=""):
    return f"/{lang}/{path}"


# ---------------------------------------------------------------------------------------------
# Page shell
# ---------------------------------------------------------------------------------------------
def page(lang, path, title, description, body, current, extra_head=""):
    t = T[lang]
    full_title = f"{title} | Storia" if title != "Storia" else "Storia — " + t["tagline"].rstrip("。.")
    alternates = "".join(f'<link rel="alternate" hreflang="{HTML_LANG[l]}" href="{url(l, path)}">' for l in LANGS)
    alternates += f'<link rel="alternate" hreflang="x-default" href="{url("en-us", path)}">'
    nav_items = [("", t["nav_home"], "home"), ("downloads/", t["nav_downloads"], "downloads"), ("docs/", t["nav_docs"], "docs")]
    nav = "".join(f'<a href="{url(lang, p)}"{" aria-current=page" if current == k else ""}>{e(label)}</a>' for p, label, k in nav_items)
    nav += f'<a href="{GITHUB}" rel="noopener">{t["nav_github"]}</a>'
    lang_opts = "".join(
        f'<option value="{l}" data-href="{url(l, path)}"{" selected" if l == lang else ""}>{LANG_NAME[l]}</option>' for l in LANGS)
    lang_links = "".join(f'<a href="{url(l, path)}" data-set-lang="{l}" hreflang="{HTML_LANG[l]}">{LANG_NAME[l]}</a>' for l in LANGS if l != lang)
    fonts = ("https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,500;0,600;1,500"
             "&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600"
             + ("&family=Noto+Sans+JP:wght@400;500;700&family=Noto+Serif+JP:wght@500;600" if lang == "ja-jp" else "")
             + "&display=swap")
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
<meta name="theme-color" content="#151515">
<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
<link rel="icon" href="/assets/storia.png" type="image/png">
{alternates}
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{fonts}">
<link rel="stylesheet" href="/assets/style.css?v={BUILD_ID}">
<script>try{{var s=localStorage.getItem("storia-theme");if(s)document.documentElement.dataset.theme=s}}catch(e){{}}</script>
{extra_head}
</head>
<body>
<header class="site-header">
  <div class="container">
    <a class="brand" href="{url(lang)}" aria-label="Storia">{MARK.format(cls="mark")}<span class="word">Storia</span></a>
    <nav class="nav" id="site-nav" aria-label="Main">{nav}</nav>
    <div class="header-tools">
      <label class="tool" title="{t['language']}">{ICON_GLOBE}<span class="sr-only">{t['language']}</span>
        <select id="lang-select" aria-label="{t['language']}" style="border:0;background:transparent;color:inherit;font:inherit;cursor:pointer">{lang_opts}</select>
      </label>
      <noscript>{lang_links}</noscript>
      <button class="tool" id="theme-toggle" type="button" title="{t['theme']}" aria-label="{t['theme']}">{ICON_SUN}</button>
      <button class="tool menu-btn" id="menu-toggle" type="button" aria-label="{t['menu']}" aria-controls="site-nav" aria-expanded="false">{ICON_MENU}</button>
    </div>
  </div>
</header>
<main>
{body}
</main>
{footer(lang)}
<script src="/assets/main.js?v={BUILD_ID}" defer></script>
</body>
</html>
"""


def footer(lang):
    t = T[lang]
    d = lambda slug: url(lang, f"docs/{slug}/")
    title = {slug: (en if lang == "en-us" else ja) for _, items in DOCS_NAV for slug, en, ja in items}
    return f"""<footer class="site-footer">
  <div class="container">
    <div class="cols">
      <div>
        <a class="brand" href="{url(lang)}">{MARK.format(cls="mark")}<span class="word">Storia</span></a>
        <p>{e(t['footer_about'])}</p>
      </div>
      <div><h4>{t['f_project']}</h4><ul>
        <li><a href="{url(lang, 'downloads/')}">{t['nav_downloads']}</a></li>
        <li><a href="{GITHUB}/releases">Releases</a></li>
        <li><a href="{GITHUB}/issues">Issues</a></li>
      </ul></div>
      <div><h4>{t['f_docs']}</h4><ul>
        <li><a href="{d('getting-started')}">{e(title['getting-started'])}</a></li>
        <li><a href="{d('configuration')}">{e(title['configuration'])}</a></li>
        <li><a href="{d('offload')}">{e(title['offload'])}</a></li>
        <li><a href="{d('placeholders')}">{e(title['placeholders'])}</a></li>
      </ul></div>
      <div><h4>{t['f_source']}</h4><ul>
        <li><a href="{GITHUB}">Storia</a></li>
        <li><a href="https://github.com/{PROXY_REPO}">Storia Proxy</a></li>
        <li><a href="https://github.com/PaperMC/Folia">Folia</a></li>
      </ul></div>
    </div>
    <div class="legal"><span>{e(t['legal'])}</span><span>{e(t['legal2'])}</span></div>
  </div>
</footer>"""


# ---------------------------------------------------------------------------------------------
# Home
# ---------------------------------------------------------------------------------------------
def diagram(lang):
    d = T[lang]["diagram"]
    box = lambda x, y, w, h, title, sub="", strong=False: (
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="4" fill="{"currentColor" if strong else "none"}" stroke="currentColor" stroke-width="1.5"/>'
        f'<text x="{x + w / 2}" y="{y + (h / 2 if not sub else h / 2 - 6)}" text-anchor="middle" dominant-baseline="middle" '
        f'font-family="var(--serif)" font-size="19" font-weight="600" fill="{"var(--bg)" if strong else "currentColor"}">{e(title)}</text>'
        + (f'<text x="{x + w / 2}" y="{y + h / 2 + 14}" text-anchor="middle" dominant-baseline="middle" font-size="11" '
           f'fill="{"var(--bg)" if strong else "currentColor"}" opacity=".75">{e(sub)}</text>' if sub else ""))
    line = lambda x1, y1, x2, y2, dash=False: (
        f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="currentColor" stroke-width="1.5"'
        f'{" stroke-dasharray=&quot;5 5&quot;" if dash else ""} marker-end="url(#arr)"/>')
    workers = "".join(box(700, 20 + i * 70, 150, 50, f"{d[5]} {chr(65 + i)}", d[6]) for i in range(3))
    wlines = "".join(line(660, 115, 698, 45 + i * 70, True) for i in range(3))
    return f"""<div class="diagram"><svg viewBox="0 0 870 230" role="img" aria-label="Storia architecture">
<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0 10 5 0 10z" fill="currentColor"/></marker></defs>
{box(10, 90, 110, 50, d[0])}
{line(122, 115, 158, 115)}
{box(160, 90, 130, 50, d[1])}
{line(292, 115, 328, 115)}
{box(330, 80, 170, 70, d[2], d[3], True)}
{line(502, 115, 538, 115, True)}
{box(540, 90, 120, 50, d[4])}
{wlines}
{workers}
<text x="520" y="170" text-anchor="middle" font-size="11" letter-spacing="2" fill="currentColor" opacity=".7">AES-256-GCM · {e(d[7])}</text>
</svg></div>"""


def home(lang):
    t = T[lang]
    exhibits = "".join(f"""<a class="exhibit" href="{url(lang, f'docs/{slug}/')}">
      <span class="num">{ROMAN[i]}.</span><h3>{e(title)}</h3><p>{e(text)}</p><span class="more">{t['more']} →</span></a>"""
                       for i, (title, text, slug) in enumerate(t["exhibits"]))
    figures = "".join(f"""<div class="figure"><div class="value">{v}<small>{u}</small></div>
      <div class="label">{e(label)}</div><div class="detail">{e(detail)}</div></div>""" for v, u, label, detail in t["figures"])
    wings = "".join(f"""<div class="wing"><span class="kind">{e(kind)}</span><h3>{e(name)}</h3><p>{e(text)}</p>
      <div class="links"><a href="{url(lang, 'downloads/')}#{product}">{t['download']}</a><a href="{url(lang, f'docs/{doc}/')}">{t['docs']}</a></div></div>"""
                    for kind, name, text, product, doc in t["wings"])
    steps = "".join(f"<li><strong>{e(a)}</strong>{e(b)}</li>" for a, b in t["qs_steps"])
    meta = "".join(f"<span>{e(m)}</span>" for m in t["meta"])
    body = f"""
<section class="hero">
  <div class="container">
    {MARK.format(cls="emblem")}
    <p class="eyebrow">Minecraft server software</p>
    <h1>Storia</h1>
    <p class="etym">{e(t['etym'])}</p>
    <p class="lede">{e(t['hero_lede'])}</p>
    <div class="actions">
      <a class="btn primary" href="{url(lang, 'downloads/')}">{ICON_DL}{e(t['get'])}</a>
      <a class="btn ghost" href="{url(lang, 'docs/')}">{e(t['read_docs'])}{ICON_ARROW}</a>
    </div>
    <div class="meta">{meta}</div>
  </div>
</section>

<section class="band">
  <div class="container">
    <div class="section-head"><div><p class="eyebrow">{e(t['col_eyebrow'])}</p><h2>{e(t['col_title'])}</h2></div><p>{e(t['col_text'])}</p></div>
    <div class="exhibits">{exhibits}</div>
  </div>
</section>

<section class="band">
  <div class="container">
    <div class="section-head"><div><p class="eyebrow">{e(t['num_eyebrow'])}</p><h2>{e(t['num_title'])}</h2></div><p>{e(t['num_text'])}</p></div>
    <div class="figures">{figures}</div>
    <p class="fineprint">{e(t['fine'])}</p>
  </div>
</section>

<section class="band">
  <div class="container">
    <div class="section-head"><div><p class="eyebrow">{e(t['wings_eyebrow'])}</p><h2>{e(t['wings_title'])}</h2></div><p>{e(t['wings_text'])}</p></div>
    <div class="wings">{wings}</div>
    {diagram(lang)}
  </div>
</section>

<section class="band">
  <div class="container split">
    <div><h2>{e(t['qs_title'])}</h2><p>{e(t['qs_text'])}</p><ol class="steps">{steps}</ol></div>
    <div>
      <div class="codeblock"><pre class="plain"><code><span style="color:var(--muted)"># Linux / macOS / Windows</span>
java -Xms4G -Xmx8G -jar storia-{LATEST['version']}.jar nogui

<span style="color:var(--muted)"># eula.txt</span>
eula=true</code></pre></div>
      <div class="codeblock"><pre class="plain"><code><span style="color:var(--muted)"># In game or in the console</span>
/storia status
/storia pregen start 3000
/storia budget</code></pre></div>
    </div>
  </div>
</section>

<section class="cta">
  <div class="container">
    <h2>{e(t['cta_title'])}</h2>
    <p>{e(t['cta_text'])}</p>
    <div class="actions">
      <a class="btn primary" href="{url(lang, 'downloads/')}">{ICON_DL}{e(t['get'])}</a>
      <a class="btn ghost" href="{GITHUB}">{ICON_GH}GitHub</a>
    </div>
  </div>
</section>"""
    return page(lang, "", "Storia", t["desc"], body, "home")


# ---------------------------------------------------------------------------------------------
# Downloads
# ---------------------------------------------------------------------------------------------
def fmt_size(b):
    return f"{b / 1048576:.1f} MB" if b >= 1048576 else f"{max(1, round(b / 1024))} KB"


def fmt_date(s, lang):
    d = datetime.strptime(s[:10], "%Y-%m-%d")
    return f"{d.year}年{d.month}月{d.day}日" if lang == "ja-jp" else d.strftime("%b %-d, %Y")


def downloads(lang):
    t = T[lang]
    tabs, panels = [], []
    for i, (key, name, kind, pattern, text, req, doc) in enumerate(t["products"]):
        rows = []
        for rel in RELEASES:
            asset = next((a for a in rel["assets"] if re.fullmatch(pattern, a["name"])), None)
            if asset:
                rows.append((rel, asset))
        if rows:
            rel, asset = rows[0]
            ver = rel["tag_name"].lstrip("v")
            href, fname, size, date = asset["browser_download_url"], asset["name"], fmt_size(asset["size"]), fmt_date(rel["published_at"], lang)
            sha = (asset.get("digest") or "").replace("sha256:", "") or "—"
            notes = rel["html_url"]
        else:
            ver, href, fname, size, date, sha, notes = "—", f"{GITHUB}/releases/latest", "—", "—", "—", "—", f"{GITHUB}/releases"
        list_html = "".join(
            f'<div class="build-row"><span class="ver">{e(r["tag_name"].lstrip("v"))}</span><span class="date">{fmt_date(r["published_at"], lang)}</span>'
            f'<span class="size">{fmt_size(a["size"])}</span><a href="{e(a["browser_download_url"])}">{e(a["name"])}</a></div>' for r, a in rows)
        tabs.append(f'<button role="tab" id="tab-{key}" data-product="{key}" aria-controls="panel-{key}" aria-selected="{str(i == 0).lower()}">{e(name)}</button>')
        panels.append(f"""<div class="panel" role="tabpanel" id="panel-{key}" aria-labelledby="tab-{key}" data-product-panel="{key}" data-pattern="{e(pattern)}"{"" if i == 0 else " hidden"}>
  <div class="latest">
    <div>
      <span class="kind">{e(kind)} · {t['latest']}</span>
      <h2>{e(name)} <span data-f="version">{e(ver)}</span></h2>
      <p>{e(text)}</p>
      <div class="actions">
        <a class="btn primary" data-f="download" href="{e(href)}">{ICON_DL}<span>{t['download']} {e(ver)}</span></a>
        <a class="btn ghost" href="{url(lang, f'docs/{doc}/')}">{t['docs']}{ICON_ARROW}</a>
      </div>
      <p class="req">{e(req)} <a data-f="notes" href="{e(notes)}">{t['notes']}</a></p>
    </div>
    <dl>
      <dt>{t['version']}</dt><dd data-f="version">{e(ver)}</dd>
      <dt>{t['file']}</dt><dd data-f="file">{e(fname)}</dd>
      <dt>{t['size']}</dt><dd data-f="size">{e(size)}</dd>
      <dt>{t['released']}</dt><dd data-f="date">{e(date)}</dd>
      <dt>{t['sha']}</dt><dd data-f="sha" style="font-family:var(--mono);font-size:12px">{e(sha)}</dd>
    </dl>
  </div>
  <div class="builds"><h3>{t['all']}</h3><div data-f="list">{list_html}</div></div>
</div>""")
    body = f"""
<section class="page-head"><div class="container">
  <p class="eyebrow">Minecraft {MC_VERSION}</p>
  <h1>{e(t['dl_title'])}</h1>
  <p>{e(t['dl_text'])}</p>
  <div class="tabs" role="tablist">{''.join(tabs)}</div>
</div></section>
<div class="container">{''.join(panels)}
  <p class="req" style="margin:-48px 0 88px"><a href="{GITHUB}/actions">{e(t['dev'])}</a></p>
</div>
<script type="application/json" id="dl-i18n">{json.dumps({"download": t["download"]})}</script>"""
    # The version appears twice (heading + table); JS updates every [data-f=version] via querySelector on the first one,
    # so keep the heading's span in sync by mirroring it.
    body = body.replace('<h2>', '<h2>', 1)
    return page(lang, "downloads/", t["dl_title"], t["dl_text"], body, "downloads")


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
        "fenced_code", "tables", "admonition", "attr_list", "md_in_html", "sane_lists",
        "codehilite", "toc"],
        extension_configs={
            "codehilite": {"css_class": "hl", "guess_lang": False},
            "toc": {"permalink": "#", "permalink_class": "headerlink", "slugify": slugify, "toc_depth": "2-3"},
        })
    # Link helper: [[slug]] -> link to that doc in this language; [[slug#anchor|text]]
    def link(m):
        target, _, text = m.group(1).partition("|")
        slug, _, anchor = target.partition("#")
        title = next((en if lang == "en-us" else ja for _, items in DOCS_NAV for s, en, ja in items if s == slug), None)
        if title is None:
            raise SystemExit(f"unknown doc link [[{m.group(1)}]]")
        return f"[{text or title}]({url(lang, f'docs/{slug}/')}{'#' + anchor if anchor else ''})"
    src = re.sub(r"\[\[([^\]]+)\]\]", link, src)
    src = src.replace("](/en-us/", f"](/{lang}/")
    src = src.replace("{{VERSION}}", LATEST["version"]).replace("{{MC}}", MC_VERSION).replace("{{GITHUB}}", GITHUB)
    out = md.convert(src)
    return out, md.toc_tokens


def plain(html_text):
    txt = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html_text, flags=re.S)
    txt = re.sub(r'<a class="headerlink"[^>]*>.*?</a>', "", txt)
    txt = re.sub(r"<[^>]+>", " ", txt)
    return re.sub(r"\s+", " ", html.unescape(txt)).strip()


def search_sections(body, title):
    """Split rendered HTML at h2/h3 so search hits jump to the right heading."""
    parts = re.split(r'(<h[23] id="[^"]+">.*?</h[23]>)', body, flags=re.S)
    sections = [{"h": "", "a": "", "x": plain(parts[0])[:1500]}]
    for i in range(1, len(parts), 2):
        m = re.match(r'<h[23] id="([^"]+)">(.*?)</h[23]>', parts[i], re.S)
        sections.append({"h": plain(m.group(2)), "a": m.group(1), "x": plain(parts[i + 1])[:1500]})
    return [s for s in sections if s["h"] or s["x"]]


def docs(lang):
    t = T[lang]
    index = []
    pages = {}
    for gi, ((g_en, g_ja), items) in enumerate(DOCS_NAV):
        for slug, en, ja in items:
            src = (CONTENT / lang / f"{slug}.md").read_text(encoding="utf-8")
            meta, src = parse_front(src)
            body, toc = render_markdown(src, lang)
            d = Doc()
            d.slug, d.title, d.group = slug, en if lang == "en-us" else ja, g_en if lang == "en-us" else g_ja
            d.summary, d.body, d.toc = meta.get("summary", ""), body, toc
            pages[slug] = d
            index.append({"t": d.title, "g": d.group, "u": url(lang, f"docs/{slug}/"),
                          "s": search_sections(body, d.title)})
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
            prev_html = f'<a class="prev" href="{url(lang, f"docs/{p.slug}/")}"><span class="dir">← {t["prev"]}</span><span class="t">{e(p.title)}</span></a>'
        if i < len(flat) - 1:
            n = pages[flat[i + 1]]
            next_html = f'<a class="next" href="{url(lang, f"docs/{n.slug}/")}"><span class="dir">{t["next"]} →</span><span class="t">{e(n.title)}</span></a>'
        summary = f'<p class="summary">{e(d.summary)}</p>' if d.summary else ""
        body = f"""
<div class="docs">
  <button class="tool docs-menu" id="docs-menu" type="button" aria-controls="sidebar" aria-expanded="false">{e(d.group)} › {e(d.title)} {ICON_MENU}</button>
  <aside class="sidebar" id="sidebar" aria-label="{t['docs_menu']}">
    <div class="search">{ICON_SEARCH}
      <input id="search" type="search" placeholder="{t['search']}  /" aria-label="{t['search']}" autocomplete="off"
        data-index="{url(lang, 'docs/search-index.json')}?v={BUILD_ID}" data-empty="{t['search_empty']}">
      <div class="search-results" id="search-results" role="listbox"></div>
    </div>
    {''.join(side)}
  </aside>
  <article class="doc">
    <div class="crumbs">{e(d.group)}</div>
    <h1>{e(d.title)}</h1>
    {summary}
    {d.body}
    <nav class="pager">{prev_html}{next_html}</nav>
  </article>
  <nav class="toc" aria-label="{t['on_page']}">{toc_html}</nav>
</div>"""
        write(lang, f"docs/{slug}/", page(lang, f"docs/{slug}/", d.title, d.summary or t["desc"], body, "docs"))
    # /docs/ -> introduction
    write(lang, "docs/", redirect_page(url(lang, "docs/introduction/")))


def redirect_page(target):
    return f'<!doctype html><meta charset="utf-8"><title>Storia</title><meta http-equiv="refresh" content="0; url={target}"><link rel="canonical" href="{target}"><a href="{target}">{target}</a>'


def not_found(lang):
    t = T[lang]
    body = f"""<section class="notfound"><div class="container">
  {MARK.format(cls="emblem").replace('class="emblem"', 'class="emblem" style="width:72px;height:72px;margin:0 auto 24px"')}
  <div class="code">404</div><h1 style="font-family:var(--serif);font-weight:500">{e(t['nf_title'])}</h1><p>{e(t['nf_text'])}</p>
  <p style="margin-top:28px"><a class="btn ghost" href="{url(lang)}">{e(t['nf_home'])}</a></p></div></section>"""
    return page(lang, "", t["nf_title"], t["nf_text"], body, "")


def write(lang, path, content):
    out = DIST / lang / path / "index.html" if path.endswith("/") or path == "" else DIST / lang / path
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(content, encoding="utf-8")


# ---------------------------------------------------------------------------------------------
# Releases (baked in; the downloads page refreshes them from the GitHub API in the browser)
# ---------------------------------------------------------------------------------------------
def load_releases():
    cache = ROOT / "releases.json"
    try:
        out = subprocess.run(["gh", "api", f"repos/{REPO}/releases?per_page=30"], capture_output=True, text=True, timeout=30, check=True).stdout
        data = [r for r in json.loads(out) if not r.get("draft")]
        cache.write_text(json.dumps(data, indent=1), encoding="utf-8")
    except Exception as ex:  # offline or no gh: use the last copy
        print(f"warning: could not fetch releases ({ex}); using releases.json")
        data = json.loads(cache.read_text(encoding="utf-8")) if cache.exists() else []
    return data


RELEASES = []
LATEST = {"version": "1.0.0"}
BUILD_ID = datetime.now().strftime("%Y%m%d%H%M%S")


def main():
    global RELEASES, LATEST
    RELEASES = load_releases()
    if RELEASES:
        LATEST = {"version": RELEASES[0]["tag_name"].lstrip("v")}
    if DIST.exists():
        shutil.rmtree(DIST)
    (DIST / "assets").mkdir(parents=True)
    for f in STATIC.iterdir():
        shutil.copy2(f, DIST / "assets" / f.name)
    for lang in LANGS:
        write(lang, "", home(lang))
        write(lang, "downloads/", downloads(lang))
        docs(lang)
        write(lang, "404.html", not_found(lang))
    # Fallback for "/" when the web server does not redirect (e.g. opened as plain files).
    (DIST / "index.html").write_text(redirect_page(url("en-us")), encoding="utf-8")
    (DIST / "robots.txt").write_text("User-agent: *\nAllow: /\n", encoding="utf-8")
    count = sum(1 for _ in DIST.rglob("*.html"))
    print(f"built {count} pages into {DIST}")


if __name__ == "__main__":
    main()
