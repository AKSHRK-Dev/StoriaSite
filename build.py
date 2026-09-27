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
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import TextLexer, get_lexer_by_name
from pygments.util import ClassNotFound

from site_how import HOW

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
        ("tick-guard", "Tick guard", "Tick Guard"),
        ("player-budget", "Per-player budget", "プレイヤーごとの予算"),
        ("performance", "Performance & tuning", "パフォーマンスと調整"),
    ]),
    (("Storia Cluster", "Storia Cluster"), [
        ("cluster", "One world on several servers", "複数サーバーで 1 つのワールド"),
        ("scaling", "From one server to a cluster", "1 台から Cluster へ"),
        ("worker", "Storia Worker", "Storia Worker"),
        ("relay", "Storia Relay", "Storia Relay"),
        ("security", "Encryption & security", "暗号化とセキュリティ"),
        ("plugin-api", "Plugin API (shared data)", "プラグイン API（共有データ）"),
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
    "info": svg('<circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7.5v.5"/>'),
    "warn": svg('<path d="M12 3 2 20h20z"/><path d="M12 10v4M12 17v.5"/>'),
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
# key, name, asset pattern, docs slug
PRODUCTS = [
    ("storia", "Storia", r"storia-[0-9][0-9.]*(-[0-9A-Za-z.]+)*\.jar", "getting-started"),
    ("worker", "Storia Worker", r"storia-worker-.*\.zip", "worker"),
    ("relay", "Storia Relay", r"storia-relay-.*\.zip", "relay"),
    ("proxy", "Storia Proxy", r"storia-proxy-.*\.jar", "proxy"),
]

ICON.update({
    "ram": svg('<rect x="3" y="7" width="18" height="10" rx="1.5"/><path d="M7 11v2M11 11v2M15 11v2M6 17v2M10 17v2M14 17v2M18 17v2"/>'),
    "bolt": svg('<path d="M13 2 4 14h7l-1 8 9-12h-7z"/>'),
    "users": svg('<circle cx="9" cy="8" r="3.5"/><path d="M2.5 20c.8-3.6 3.4-5.5 6.5-5.5s5.7 1.9 6.5 5.5"/><circle cx="17" cy="9" r="2.5"/><path d="M17 14.5c2.4 0 4 1.5 4.5 4.5"/>'),
    "net": ICON["relay"],
    "check": svg('<circle cx="12" cy="12" r="9"/><path d="m8 12.5 2.8 2.8L16.5 9.5"/>'),
    "java": svg('<path d="M8 3v4M12 3v4M16 3v4"/><path d="M4 9h14v5a5 5 0 0 1-5 5H9a5 5 0 0 1-5-5z"/><path d="M18 11h1.5a2 2 0 0 1 0 4H18"/>'),
    "code": svg('<path d="m8 8-4 4 4 4M16 8l4 4-4 4M13.5 5l-3 14"/>'),
    "layers": svg('<path d="m12 3 9 5-9 5-9-5z"/><path d="m3 13 9 5 9-5"/>'),
    "tag": svg('<path d="M3 12V4a1 1 0 0 1 1-1h8l9 9-9 9z"/><circle cx="8" cy="8" r="1.5"/>'),
})

# ---------------------------------------------------------------------------------------------
# UI strings
# ---------------------------------------------------------------------------------------------
T = {
    "en-us": {
        "features": "Features", "downloads": "Downloads", "docs": "Docs", "github": "GitHub",
        "theme": "Dark mode", "menu": "Menu", "skip": "Skip to main content", "title_tag": "The finest server software. Zero stutter.", "copied": "Copied to clipboard", "results": "{n} results", "language": "Language", "documentation": "Documentation",
        "desc": "Storia is a Minecraft server that runs one world on several machines at once: players move between servers without a loading screen. Built on Folia, with RAM worlds, fast pregeneration and a tick guard for busy spawns.",
        "pill": "Storia {v} is out", "pill_tag": "New",
        "hero": 'The finest server software. <span class="accent">Zero stutter.</span>',
        "hero_sub": "Storia is a Minecraft server that runs one world on several machines at once. Players cross from server to server without a loading screen, and redstone never stops.",
        "get": "Download {v}", "read": "Read the docs",
        "meta": [("layers", "Minecraft " + MC_VERSION), ("java", "Java 25"), ("code", "Open source")],
        "why_k": "On a single server, too", "why_t": "Fast even on one machine",
        "why_p": "Without a cluster, these still work on every Storia server. Each one keeps vanilla behavior: the same terrain for the same seed, the same physics, and redstone that never stops.",
        "more": "How it works",
        "t_ram": ("RAM world", "Worlds live in memory", "Worlds are copied into RAM at startup and synced back to disk in the background, so disk speed stops mattering."),
        "t_pregen": ("Pregeneration", "Five times faster pregen", "/storia pregen puts every spare core to work and picks up where it left off after a restart."),
        "t_budget": ("Tick guard", "A busy spawn, smooth for you", "When a farm or a crowd overloads an area, Storia thins out the crowd's thinking, not the players. People standing nearby are never limited."),
        "t_pbud": ("Player budget", "Only the fast flier waits", "While an area is busy, players flying faster than 12 blocks/s get a shorter view until they slow down. People who stand, build or walk there are never limited."),
        "pbud": [("Alice", "elytra · 38 b/s", "view 6", True), ("Bob", "building", "view 10", False), ("Carol", "walking", "view 10", False)],
        "pbud_note": "Region over its budget: only the fast mover is limited.",
        "t_proxy": ("Storia Proxy", "50 placeholders built in", "A Velocity fork with a live tab list, MOTD and join messages for the whole network."),
        "t_vanilla": ("Vanilla-exact", "Faster, never different", "Every change is checked against the original code, sample by sample and push by push."),
        "bars": [("Folia default", "3m 21s", 100, False), ("Storia", "40s", 20, True)],
        "bars_note": "3,721 chunks on 6 cores. Lower is better.",
        "people": [("Zombies", 100, 40, True, "AI 1/8"), ("Villagers", 60, 40, True, "AI 1/8"), ("Alice", 0, 40, False, "view 10"), ("Bob", 0, 40, False, "view 10")],
        "people_note": "Spawn with 1,400 mobs: 55 ms → 33 ms per tick, TPS 20. Nobody limited.",
        "facts": [("0", "", "differences in 18M noise samples"), ("0", "", "in 500k entity pushes"), ("3", "×", "faster entity pushing"), ("0", "", "redstone changes")],
        "prog_k": "The family", "prog_t": "Four programs, one release",
        "prog_p": "Run the server on its own, or add helpers when you need them. All four ship together in every release.",
        "products": {
            "storia": ("The server", "Folia's regionized multithreading plus RAM worlds, fast pregeneration and a per-player budget."),
            "worker": ("Cluster server", "Runs part of a shared world. Add workers when your players outgrow one machine."),
            "relay": ("Coordinator", "Keeps a cluster's world and decides which server runs which part. Also shares terrain work between workers."),
            "proxy": ("Network proxy", "Velocity with placeholders, a live tab list and network messages."),
        },
        "req": {"storia": "Java 25", "worker": "Java 25", "relay": "Java 21+", "proxy": "Java 21+"},
        "close_t": "Start with Storia in a minute.", "close_p": "Replace your Folia jar, accept the EULA and you are running. Folia plugins work as they are.",
        # downloads
        "dl_k": "Downloads", "dl_t": 'Get Storia <span class="accent">{v}</span>', "dl_p": "Every release contains the server and its three companions, built by GitHub Actions from the public source.",
        "release": "Storia {v}", "released": "Released {d}", "notes": "Release notes",
        "for_mc": "for Minecraft {mc}",
        "dl_btn": "Download", "dev": "Looking for the newest changes? Development builds are on", "history": "Release history",
        "no_release": "No release has been published yet.",
        "beta": "Beta", "beta_head": "Try the beta",
        "cl_nav": "Cluster", "cl_k": "Storia Cluster", "cl_t": "One world, many servers.",
        "cl_p": "Folia splits a world across the cores of one machine. Storia splits it across machines. When your players outgrow one server, add another: they keep playing in the same world.",
        "cl_try": "Download", "cl_guide": "Read the guide",
        "cl_points": [
            ("Automatic placement", "Every part of the world where people play is given to a server. Players who meet end up on the same one; busy servers hand work to quiet ones."),
            ("No loading screen", "Crossing to another server keeps the connection. Inventory, advancements and statistics come along."),
            ("Contraptions stay whole", "Redstone and machines on the border between two parts are found and always run on one server."),
            ("Stop a server, nobody is kicked", "/stop moves its players to the other servers first. If the coordinator blinks, writes wait on disk."),
        ],
        "cl_fig": "A world split between three servers. Each colored area is run by one server; a player flying from one area into another moves to that server without a loading screen.",
        "cl_legend": ["Server alpha", "Server beta", "Server gamma", "Not in use"],
        "cl_note": "Seamless moves need Minecraft 26.1 or 26.2 clients. Back up your world before you move it into a cluster.",
        "beta_note": "New features that are still being tested. Back up your server before trying it.",
        "pill_beta": "Beta {v}: tick guard keeps busy spawns smooth",
        "dl_count": "{n} downloads", "dl_total": "total downloads across all releases", "dl_total_short": "{n} downloads",
        "dl_which": "Running one server? You only need <b>storia-{v}.jar</b>. Storia Worker and Storia Relay are for a cluster (one world on several servers) and do not work with a single Storia server.",
        "dl_which_link": "From one server to a cluster",
        "cl_scale": "Running one server now? How to move to a cluster",
        # docs
        "search": "Search docs", "search_empty": "No results", "on_page": "On this page", "prev": "Previous", "next": "Next",
        "docs_menu": "Documentation menu",
        # footer
        "tagline": "A Minecraft server for big communities, built on Folia.",
        "f_use": "Use", "f_learn": "Learn", "f_source": "Source",
        "issues": "Report an issue", "releases": "All releases", "website_src": "This website",
        "legal": "Storia is not an official Minecraft product and is not affiliated with Mojang or Microsoft.",
        "thanks": "Built on Paper, Folia and Velocity by PaperMC.",
        "nf_title": "Page not found", "nf_text": "There is nothing here. It may have moved.", "nf_home": "Go home",
    },
    "ja-jp": {
        "features": "特長", "downloads": "ダウンロード", "docs": "ドキュメント", "github": "GitHub",
        "theme": "ダークモード", "menu": "メニュー", "skip": "本文へスキップ", "title_tag": "カクつかない、最高峰のサーバーソフトウェア", "copied": "クリップボードにコピーしました", "results": "{n} 件見つかりました", "language": "言語", "documentation": "ドキュメント",
        "desc": "Storia は、1 つのワールドを複数のサーバーで分担して動かせる Minecraft サーバーです。サーバー間の移動に読み込み画面は出ません。Folia ベースで、RAM ワールド、高速な事前生成、混んだ初期地点のための Tick Guard も備えています。",
        "pill": "Storia {v} を公開しました", "pill_tag": "New",
        "hero": '<span class="accent ph">カクつかない、</span><span class="ph">最高峰の</span><span class="ph">サーバー</span><span class="ph">ソフトウェア。</span>',
        "hero_sub": "Storia は、1 つのワールドを複数のサーバーで分担して動かせる Minecraft サーバーです。サーバーをまたいでも読み込み画面は出ず、回路も止まりません。",
        "get": "{v} をダウンロード", "read": "ドキュメントを読む",
        "meta": [("layers", "Minecraft " + MC_VERSION), ("java", "Java 25"), ("code", "Open source")],
        "why_k": "On a single server, too", "why_t": "1 台のサーバーでも、とことん軽く",
        "why_p": "Cluster を使わなくても、どの Storia サーバーでも効きます。どれもバニラと同じ動きです。同じシードなら同じ地形、同じ物理演算、そして回路は止まりません。",
        "more": "仕組みを見る",
        "t_ram": ("RAM world", "ワールドはメモリの上に", "起動時にワールドを RAM にコピーし、変更はバックグラウンドでディスクへ。ディスクの速さが気にならなくなります。"),
        "t_pregen": ("Pregeneration", "事前生成が約 5 倍速く", "/storia pregen は空いているコアをすべて使い、再起動しても続きから再開します。"),
        "t_budget": ("Tick Guard", "混んだ初期地点でも、快適に", "トラップや群れで場所が重くなったら、減らすのは群れの判断だけ。近くに立っている人は一切制限しません。"),
        "t_pbud": ("Player budget", "制限されるのは、飛ばしている人だけ", "場所が重い間、秒速 12 ブロックより速く飛んでいる人だけ描画距離を短くし、速度を落とせば戻します。立っている人・建築している人・歩いている人は制限しません。"),
        "pbud": [("Alice", "エリトラ · 秒速 38", "view 6", True), ("Bob", "建築中", "view 10", False), ("Carol", "歩き", "view 10", False)],
        "pbud_note": "予算を超えたリージョンでも、制限されるのは速く動く人だけ。",
        "t_proxy": ("Storia Proxy", "50 個のプレースホルダー", "自動更新のタブリスト、MOTD、ネットワーク全体の参加メッセージを備えた Velocity のフォーク。"),
        "t_vanilla": ("Vanilla-exact", "速く、でも違わない", "すべての変更を、元のコードと 1 件ずつ照合しています。"),
        "bars": [("Folia の初期設定", "3分21秒", 100, False), ("Storia", "40秒", 20, True)],
        "bars_note": "3,721 チャンク・6 コア。短いほど高速です。",
        "people": [("ゾンビ", 100, 40, True, "AI 1/8"), ("村人", 60, 40, True, "AI 1/8"), ("Alice", 0, 40, False, "view 10"), ("Bob", 0, 40, False, "view 10")],
        "people_note": "モブ 1,400 体の初期地点：1 ティック 55 ms → 33 ms、TPS 20。誰も制限されません。",
        "facts": [("0", "件", "ノイズ 1,800 万件での差異"), ("0", "件", "押し合い 50 万回での差異"), ("3", "倍", "押し合いの計算の速さ"), ("0", "件", "レッドストーンへの変更")],
        "prog_k": "The family", "prog_t": "4 つのソフトを、ひとつのリリースで",
        "prog_p": "サーバー単体でも動き、必要になったら手伝い役を足せます。4 つとも毎回のリリースにそろって入っています。",
        "products": {
            "storia": ("サーバー本体", "Folia のリージョン並列処理に、RAM ワールド・高速な事前生成・プレイヤーごとの予算を加えたもの。"),
            "worker": ("Cluster の 1 台", "共有するワールドの一部を動かします。1 台で足りなくなったら足します。"),
            "relay": ("まとめ役", "Cluster のワールドを保管し、どのサーバーがどこを動かすかを決めます。ワーカーへの地形生成の仕事も配ります。"),
            "proxy": ("ネットワーク用プロキシ", "プレースホルダー、自動更新のタブリスト、ネットワークのメッセージを備えた Velocity。"),
        },
        "req": {"storia": "Java 25", "worker": "Java 25", "relay": "Java 21 以上", "proxy": "Java 21 以上"},
        "close_t": "1 分で Storia を始めよう。", "close_p": "Folia の jar と入れ替えて、EULA に同意すれば動きます。Folia 対応のプラグインはそのまま使えます。",
        "dl_k": "Downloads", "dl_t": 'Storia <span class="accent">{v}</span> を入手', "dl_p": "各リリースには、サーバー本体と 3 つの関連ソフトが入っています。すべて公開されているソースから GitHub Actions でビルドしています。",
        "release": "Storia {v}", "released": "{d} 公開", "notes": "リリースノート",
        "for_mc": "Minecraft {mc} 向け",
        "dl_btn": "ダウンロード", "dev": "最新の変更を試したい場合は、開発版のビルドを入手できます：", "history": "リリース履歴",
        "no_release": "まだリリースがありません。",
        "beta": "Beta", "beta_head": "Beta 版を試す",
        "cl_nav": "Cluster", "cl_k": "Storia Cluster", "cl_t": "1 つのワールドを、何台ものサーバーで。",
        "cl_p": "Folia は 1 台のマシンの中で、ワールドを CPU コアごとに分けました。Storia はそれをマシンごとに分けます。プレイヤーが 1 台に収まらなくなったら、サーバーを足すだけ。みんな同じワールドで遊び続けられます。",
        "cl_try": "ダウンロード", "cl_guide": "ガイドを読む",
        "cl_points": [
            ("自動で振り分け", "人が遊んでいる場所ごとに、サーバーを自動で割り当てます。近づいたプレイヤーは同じサーバーにまとめ、忙しいサーバーの仕事は空いているサーバーへ移します。"),
            ("読み込み画面なしで移動", "別のサーバーへ移っても接続はそのまま。インベントリ・進捗・統計も一緒に移ります。"),
            ("回路は分けない", "サーバーの境目にあるレッドストーンや装置を見つけ、必ず 1 台で動かします。"),
            ("止めてもキックされない", "/stop すると、先にプレイヤーをほかのサーバーへ移します。まとめ役が一瞬止まっても、書き込みはディスクで待ちます。"),
        ],
        "cl_fig": "3 台のサーバーで分担しているワールド。色の付いた場所をそれぞれ 1 台が動かし、別の場所へ飛んでいったプレイヤーは、読み込み画面なしでそのサーバーへ移ります。",
        "cl_legend": ["Server alpha", "Server beta", "Server gamma", "Not in use"],
        "cl_note": "読み込み画面なしの移動は Minecraft 26.1・26.2 のクライアントが対象です。ワールドを Cluster に移す前に、バックアップを取ってください。",
        "beta_note": "テスト中の新機能が入っています。試す前にサーバーをバックアップしてください。",
        "pill_beta": "{v}：混んだ初期地点も快適にする Tick Guard",
        "dl_count": "{n} ダウンロード", "dl_total": "全リリースの累計ダウンロード数", "dl_total_short": "累計 {n} ダウンロード",
        "dl_which": "サーバー 1 台で動かすなら、必要なのは <b>storia-{v}.jar</b> だけです。Storia Worker と Storia Relay は Cluster（1 つのワールドを複数のサーバーで動かす構成）専用で、単体の Storia サーバーでは動きません。",
        "dl_which_link": "1 台から Cluster へ",
        "cl_scale": "いまは 1 台で動かしていますか？Cluster への移り方",
        "search": "ドキュメントを検索", "search_empty": "見つかりませんでした", "on_page": "このページの内容", "prev": "前へ", "next": "次へ",
        "docs_menu": "ドキュメントのメニュー",
        "tagline": "Folia をベースにした、大人数のコミュニティのための Minecraft サーバー。",
        "f_use": "使う", "f_learn": "学ぶ", "f_source": "ソース",
        "issues": "問題を報告", "releases": "すべてのリリース", "website_src": "このサイト",
        "legal": "Storia は Minecraft の公式製品ではなく、Mojang や Microsoft とは関係ありません。",
        "thanks": "PaperMC の Paper・Folia・Velocity をもとに作られています。",
        "nf_title": "ページが見つかりません", "nf_text": "ここには何もありません。移動した可能性があります。", "nf_home": "ホームへ",
    },
}


def url(lang, path=""):
    return f"/{lang}/{path}"


# ---------------------------------------------------------------------------------------------
# Page shell
# ---------------------------------------------------------------------------------------------
def header(lang, path, current):
    t = T[lang]
    cur = lambda k: ' aria-current="page"' if current == k else ""
    lang_items = "".join(
        f'<li><a href="{url(l, path)}" hreflang="{HTML_LANG[l]}" lang="{HTML_LANG[l]}" data-set-lang="{l}"{" aria-current=true" if l == lang else ""}>{LANG_NAME[l]}</a></li>'
        for l in LANGS)
    return f"""<header class="site-header" id="site-header">
  <div class="container">
    <a class="brand" href="{url(lang)}" aria-label="StoriaMC">{logo("storia")}<span class="word">StoriaMC</span></a>
    <nav class="nav" id="site-nav" aria-label="Main">
      <a href="{url(lang)}#cluster">{t['cl_nav']}</a>
      <a href="{url(lang)}#features">{t['features']}</a>
      <a href="{url(lang, 'how-it-works/')}"{cur('how')}>{HOW[lang]['nav']}</a>
      <a href="{url(lang, 'downloads/')}"{cur('downloads')}>{t['downloads']}</a>
      <a href="{url(lang, 'docs/')}"{cur('docs')}>{t['docs']}</a>
    </nav>
    <div class="header-tools">
      <a class="icon-btn hide-sm" href="{GITHUB}" aria-label="GitHub">{ICON['github']}</a>
      <div class="lang">
        <button type="button" id="lang-toggle" aria-expanded="false" aria-controls="lang-menu">{ICON['globe']}<span><span class="sr-only">{t['language']}: </span><span class="lang-long">{LANG_NAME[lang]}</span><span class="lang-short" aria-hidden="true">{HTML_LANG[lang].upper()}</span></span>{ICON['chev']}</button>
        <ul id="lang-menu" hidden>{lang_items}</ul>
      </div>
      <button class="icon-btn" id="theme-toggle" type="button" title="{t['theme']}" aria-label="{t['theme']}" aria-pressed="false">{ICON['sun']}</button>
      <button class="icon-btn menu-btn" id="menu-toggle" type="button" aria-label="{t['menu']}" aria-controls="site-nav" aria-expanded="false">{ICON['menu']}</button>
    </div>
  </div>
</header>"""


def footer(lang):
    t = T[lang]
    d = lambda slug: f'<li><a href="{url(lang, f"docs/{slug}/")}">{e(doc_title(slug, lang))}</a></li>'
    return f"""<footer class="site-footer" aria-labelledby="footer-title">
  <h2 id="footer-title" class="sr-only">StoriaMC</h2>
  <div class="container">
    <div class="top">
      <div class="about"><a class="brand" href="{url(lang)}" aria-label="StoriaMC">{logo("storia")}<span class="word" style="color:var(--ink)">StoriaMC</span></a><p>{e(t['tagline'])}</p></div>
      <div><h2>{t['f_use']}</h2><ul>
        <li><a href="{url(lang, 'downloads/')}">{t['downloads']}</a></li>
        {d('getting-started')}{d('configuration')}{d('commands')}
      </ul></div>
      <div><h2>{t['f_learn']}</h2><ul>
        <li><a href="{url(lang, 'how-it-works/')}">{e(HOW[lang]['nav'])}</a></li>
        {d('cluster')}{d('player-budget')}{d('placeholders')}{d('faq')}
      </ul></div>
      <div><h2>{t['f_source']}</h2><ul>
        <li><a href="{GITHUB}">Storia</a></li>
        <li><a href="https://github.com/{PROXY_REPO}">Storia Proxy</a></li>
        <li><a href="https://github.com/{SITE_REPO}">{t['website_src']}</a></li>
        <li><a href="{GITHUB}/issues">{t['issues']}</a></li>
      </ul></div>
    </div>
    <div class="bottom"><span>© {datetime.now().year} StoriaMC · {e(t['legal'])}</span><span>{e(t['thanks'])}</span></div>
  </div>
</footer>"""


def page(lang, path, title, description, body, current):
    full_title = f"{title} | StoriaMC" if title else "StoriaMC: " + T[lang]["title_tag"]
    alternates = "".join(f'<link rel="alternate" hreflang="{HTML_LANG[l]}" href="{url(l, path)}">' for l in LANGS)
    alternates += f'<link rel="alternate" hreflang="x-default" href="{url("en-us", path)}">'
    fonts = ("https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,500;0,9..144,600;1,9..144,500"
             "&family=Manrope:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500"
             + ("&family=Noto+Sans+JP:wght@400;500;700;800&family=Noto+Serif+JP:wght@500;600" if lang == "ja-jp" else "") + "&display=swap")
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
<meta property="og:site_name" content="StoriaMC">
<meta property="og:image" content="/assets/storia.png">
<meta name="theme-color" content="#c4552f">
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
<a class="skip" href="#main">{T[lang]['skip']}</a>
{header(lang, path, current)}
<main id="main" tabindex="-1">
{body}
</main>
{footer(lang)}
<div id="live" class="sr-only" aria-live="polite"></div>
<script src="/assets/main.js?v={BUILD_ID}" defer></script>
</body>
</html>
"""


# ---------------------------------------------------------------------------------------------
# Home
# ---------------------------------------------------------------------------------------------
def terminal_lines(version):
    d = '<span class="d">[INFO]</span> '
    return [
        ("cmd", '<span class="p">$</span> <span class="c">java</span> -jar storia-relay.jar'),
        ("out", d + 'Cluster mode on: storing the shared world in cluster-world'),
        ("out", d + '<span class="g">Node alpha joined the cluster</span>'),
        ("out", d + '<span class="g">Node beta joined the cluster</span>'),
        ("out", d + '<span class="g">Node gamma joined the cluster</span>'),
        ("out", d + '<span class="a">Storia Proxy connected to the cluster</span>'),
        ("out", d + 'Linked r.3.-1 and r.4.-1: redstone on the border stays on one node'),
        ("out", d + '<span class="w">Moving player Alice from alpha to beta (areas met)</span>'),
        ("cmd", '<span class="p">&gt;</span> status'),
        ("out", '<span class="g">3 node(s), 214 owned cell(s), 1 proxy, 38 player move(s)</span>'),
    ]


def cluster_map(lang):
    """A world split between three servers, as a grid of cells coloured by the server that runs them."""
    t = T[lang]
    cols, rows, w, h, x0, y0 = 10, 6, 58, 54, 10, 10
    owner = {}
    for c in range(0, 3):
        for r in range(0, 4):
            owner[(c, r)] = "a"
    owner[(3, 1)] = owner[(3, 2)] = "a"
    for c in range(5, 8):
        for r in range(0, 3):
            owner[(c, r)] = "b"
    for c in range(6, 10):
        for r in range(3, 6):
            owner[(c, r)] = "g"
    cells = "".join(f'<rect class="cell {owner.get((c, r), "n")}" x="{x0 + c * w}" y="{y0 + r * h}" width="{w}" height="{h}" rx="6"/>'
                    for c in range(cols) for r in range(rows))
    cx = lambda c: x0 + c * w + w / 2
    cy = lambda r: y0 + r * h + h / 2
    players = [("a", 0.6, 0.7), ("a", 1.5, 2.3), ("a", 1.1, 1.4), ("b", 6.2, 0.6), ("b", 5.7, 1.5), ("g", 7.4, 4.2), ("g", 8.6, 4.9), ("g", 8.1, 3.6)]
    dots = "".join(f'<circle class="p {k}" cx="{x0 + c * w}" cy="{y0 + r * h}" r="7"/>' for k, c, r in players)
    labels = "".join(f'<text class="lbl" x="{x}" y="{y}">{n}</text>' for n, x, y in
                     (("alpha", cx(1), cy(3) + 6), ("beta", cx(6), cy(2) + 6), ("gamma", cx(8), cy(5) + 6)))
    # a player flying from alpha into beta's area
    path = f'M{cx(3) + 6} {cy(2)} C {cx(4) - 4} {cy(2) + 10}, {cx(4) + 6} {cy(1) + 18}, {cx(5) - 6} {cy(1) + 4}'
    move = (f'<path class="mv" d="{path}" marker-end="url(#cm-arr)"/>'
            f'<circle class="p a mover" cx="{cx(3) + 2}" cy="{cy(2)}" r="7"/>'
            f'<text class="tag" x="{cx(4) + 2}" y="{cy(2) + 34}">seamless move</text>')
    # linked cells: a machine on the border between two of alpha's cells
    link = (f'<g class="link"><rect x="{x0 + 3 * w - 12}" y="{cy(1) - 11}" width="24" height="22" rx="5"/>'
            f'<path d="M{x0 + 3 * w - 6} {cy(1)}h12M{x0 + 3 * w - 3} {cy(1) - 5}v10M{x0 + 3 * w + 3} {cy(1) - 5}v10"/></g>'
            f'<text class="tag" x="{x0 + 3 * w}" y="{cy(0) + 6}">linked</text>')
    legend = "".join(f'<li><i class="sw {k}"></i>{e(n)}</li>' for k, n in zip(("a", "b", "g", "n"), t["cl_legend"]))
    return f"""<figure class="cmap">
  <svg viewBox="0 0 600 344" role="img" aria-label="{e(t['cl_fig'])}">
    <defs><marker id="cm-arr" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0 10 5 0 10z" class="ah"/></marker></defs>
    {cells}{labels}{link}{dots}{move}
  </svg>
  <figcaption><ul class="legend">{legend}</ul></figcaption>
</figure>"""


def cluster_section(lang):
    t = T[lang]
    points = "".join(f'<div class="cl-point"><h3>{e(h)}</h3><p>{e(p)}</p></div>' for h, p in t["cl_points"])
    return f"""<section class="section cluster" id="cluster" aria-labelledby="cl-title">
  <div class="container">
    <div class="cl-top">
      <div class="cl-text">
        <p class="kicker">{e(t['cl_k'])}</p>
        <h2 id="cl-title">{e(t['cl_t'])}</h2>
        <p class="cl-lede">{e(t['cl_p'])}</p>
        <div class="actions">
          <a class="btn primary" href="{url(lang, 'downloads/')}">{ICON['dl']}{e(t['cl_try'])}</a>
          <a class="btn secondary" href="{url(lang, 'docs/cluster/')}">{e(t['cl_guide'])}</a>
        </div>
        <p class="cl-note">{e(t['cl_note'])}</p>
        <p class="cl-scale"><a class="link" href="{url(lang, 'docs/scaling/')}">{e(t['cl_scale'])} {ICON['arrow']}</a></p>
      </div>
      {cluster_map(lang)}
    </div>
    <div class="cl-points">{points}</div>
  </div>
</section>"""


def pill(lang, v):
    t = T[lang]  # stable builds only; betas are announced on the downloads page
    return f'<a class="pill" href="{url(lang, "downloads/")}"><b>{t["pill_tag"]}</b>{e(t["pill"].format(v=v))}{ICON["arrow"]}</a>'


def tile(lang, key, icon, visual, slug, width=""):
    t = T[lang]
    tag, title, text = t[key]
    return f"""<article class="tile {width}">
  <div class="tag">{ICON[icon]}{e(tag)}</div>
  <h3>{e(title)}</h3>
  <p>{e(text)}</p>
  <a class="link" href="{url(lang, f'docs/{slug}/')}">{t['more']} {ICON['arrow']}</a>
  <div class="visual">{visual}</div>
</article>"""


def home(lang):
    t = T[lang]
    v = LATEST["version"]
    term = "".join(f'<span class="ln" data-k="{k}">{h}</span>' for k, h in terminal_lines(v))
    meta = "".join(f"<span>{ICON[i]}{e(m)}</span>" for i, m in t["meta"])
    if RELEASES:
        meta += f'<span>{ICON["dl"]}{e(t["dl_total_short"].format(n=f"{total_downloads():,}"))}</span>'

    status = f"""<div class="screen"><pre><span class="a">Storia {e(v)}</span>
<span class="k">RAM world:</span> <span class="g">enabled</span>
<span class="k">RAM used:</span> 3187 MB
<span class="k">Sync interval:</span> 300 s
<span class="k">Last sync:</span> 2m 14s ago (184 file(s))</pre></div>"""
    bars = "".join(f"""<div class="bar-row{' win' if win else ''}"><div class="lbl"><span>{e(n)}</span><b>{e(val)}</b></div>
      <div class="track"><div class="fill" style="width:{w}%"></div></div></div>""" for n, val, w, win in t["bars"])
    pregen = f'<div class="screen"><div class="bars">{bars}</div><p class="bar-note">{e(t["bars_note"])}</p></div>'
    people = "".join(f"""<div class="person{' over' if over else ''}"><span>{e(n)}</span>
      <div class="track"><i style="width:{min(use, 100)}%"></i><s style="left:{share}%"></s></div><em>{e(state)}</em></div>""" for n, use, share, over, state in t["people"])
    budget = f'<div class="screen"><div class="people">{people}</div><p class="bar-note">{e(t["people_note"])}</p></div>'
    pbud_rows = "".join(f"""<div class="pb-row{' over' if over else ''}"><b>{e(n)}</b><span>{e(what)}</span><em>{e(view)}</em></div>""" for n, what, view, over in t["pbud"])
    pbud = f'<div class="screen"><div class="pb">{pbud_rows}</div><p class="bar-note">{e(t["pbud_note"])}</p></div>'
    proxy = """<div class="screen" style="padding:14px"><div class="mc"><b style="color:#fff">My Network</b><br><span style="color:#aaa">42/200 online · 21:37</span>
<div class="rows"><span>Alice <i>12ms</i></span><span>Bob <i>34ms</i></span><span>Carol <i style="color:#f5c16c">96ms</i></span><span>Dave <i>18ms</i></span></div>
<span style="color:#aaa">survival (28) · ping <span style="color:#9bd49b">12ms</span></span></div></div>"""
    facts = "".join(f"<div><b>{val}<small>{u}</small></b><span>{e(l)}</span></div>" for val, u, l in t["facts"])
    vanilla = f'<div class="facts">{facts}</div>'
    programs = "".join(f"""<div class="program">{logo(k)}<h3>{e(n)}</h3><span class="req">{e(t['products'][k][0])} · {e(t['req'][k])}</span>
      <p>{e(t['products'][k][1])}</p><a class="link" href="{url(lang, 'downloads/')}#{k}">{t['dl_btn']} {ICON['arrow']}</a></div>""" for k, n, _, _ in PRODUCTS)
    body = f"""
<section class="hero">
  <div class="container">
    {pill(lang, v)}
    <h1>{t['hero']}</h1>
    <p class="sub">{e(t['hero_sub'])}</p>
    <div class="actions">
      <a class="btn primary" href="{url(lang, 'downloads/')}">{ICON['dl']}{e(t['get'].format(v=v))}</a>
      <a class="btn secondary" href="{url(lang, 'docs/')}">{t['read']}</a>
    </div>
    <div class="meta">{meta}</div>
    <div class="stage"><div class="terminal" aria-hidden="true"><div class="bar"><i></i><i></i><i></i><b>storia-relay</b></div><pre id="term">{term}</pre></div></div>
  </div>
</section>

{cluster_section(lang)}

<section class="section" id="features">
  <div class="container">
    <div class="head"><p class="kicker">{e(t['why_k'])}</p><h2>{e(t['why_t'])}</h2><p>{e(t['why_p'])}</p></div>
    <div class="bento">
      {tile(lang, 't_ram', 'ram', status, 'ram-world', 'w7')}
      {tile(lang, 't_pregen', 'bolt', pregen, 'pregeneration', 'w5')}
      {tile(lang, 't_budget', 'users', budget, 'tick-guard', 'w5')}
      {tile(lang, 't_pbud', 'users', pbud, 'player-budget', 'w7')}
      {tile(lang, 't_proxy', 'proxy', proxy, 'placeholders')}
      {tile(lang, 't_vanilla', 'check', vanilla, 'performance')}
    </div>
  </div>
</section>

<section class="section alt">
  <div class="container">
    <div class="head"><p class="kicker">{e(t['prog_k'])}</p><h2>{e(t['prog_t'])}</h2><p>{e(t['prog_p'])}</p></div>
    <div class="programs">{programs}</div>
    <p style="text-align:center;margin:28px 0 0"><a class="link" href="{url(lang, 'how-it-works/')}">{e(HOW[lang]['title'])} {ICON['arrow']}</a></p>
  </div>
</section>

<section class="section">
  <div class="container">
    <div class="closing">
      <div><h2>{e(t['close_t'])}</h2><p>{e(t['close_p'])}</p>
        <div class="actions"><a class="btn primary" href="{url(lang, 'downloads/')}">{ICON['dl']}{e(t['get'].format(v=v))}</a>
        <a class="btn secondary" href="{url(lang, 'docs/getting-started/')}">{e(doc_title('getting-started', lang))}</a></div></div>
      <pre><span style="color:#9c948b"># 1</span>
java -Xmx8G -jar storia-{e(v)}.jar nogui
<span style="color:#9c948b"># 2</span>
echo "eula=true" &gt; eula.txt
<span style="color:#9c948b"># 3</span>
java -Xmx8G -jar storia-{e(v)}.jar nogui</pre>
    </div>
  </div>
</section>"""
    return page(lang, "", "", t["desc"], body, "home")


# ---------------------------------------------------------------------------------------------
# How it works
# ---------------------------------------------------------------------------------------------
def arch_svg(lang, tall=False):
    """The cluster: players -> Storia Proxy -> workers -> Storia Relay. A wide version, and a tall one for phones."""
    h = HOW[lang]
    d = h["d"]
    uid = "t" if tall else "w"

    def node(x, y, w, label, sub="", main=False, hgt=56):
        cls = "n main" if main else "n"
        t = (f'<g class="{cls}"><rect x="{x}" y="{y}" width="{w}" height="{hgt}" rx="10"/>'
             f'<text x="{x + w / 2}" y="{y + (hgt / 2 if not sub else hgt / 2 - 8)}" class="nt">{e(label)}</text>')
        if sub:
            t += f'<text x="{x + w / 2}" y="{y + hgt / 2 + 12}" class="ns">{e(sub)}</text>'
        return t + "</g>"

    def edge(x1, y1, x2, y2, dash=False):
        return f'<line class="e{" dash" if dash else ""}" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" marker-end="url(#ah-{uid})"/>'

    def label(x, y, text, anchor="middle"):
        return f'<text class="el" x="{x}" y="{y}" text-anchor="{anchor}">{e(text)}</text>'

    head = (f'<title id="arch-title-{uid}">{e(h["diagram_label"])}</title><desc id="arch-desc-{uid}">{e(" ".join(h["diagram_desc"]))}</desc>'
            f'<defs><marker id="ah-{uid}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0 10 5 0 10z" class="ah"/></marker></defs>')
    names = [f"{d['worker']} {c}" for c in "ABC"]
    if not tall:
        ys = [96, 196, 296]
        workers = "".join(node(470, y, 180, n, d["wsub"], main=(k == 1)) for k, (y, n) in enumerate(zip(ys, names)))
        to_workers = "".join(edge(370, 220, 468, y + 28) for y in ys)
        to_relay = "".join(edge(650, y + 28, 818, 220, True) for y in ys)
        return f"""<svg class="arch arch-wide" viewBox="0 0 1090 400" role="img" aria-labelledby="arch-title-{uid} arch-desc-{uid}">{head}
<text class="gh" x="185" y="40">{e(d['net'])}</text><text class="gh" x="560" y="40">{e(d['game'])}</text><text class="gh" x="905" y="40">{e(d['help'])}</text>
<line class="sep" x1="410" y1="60" x2="410" y2="390"/><line class="sep" x1="770" y1="60" x2="770" y2="390"/>
{node(10, 192, 130, d['players'])}{edge(140, 220, 218, 220)}{label(179, 208, 'MC')}
{node(220, 192, 150, d['proxy'], ':25565')}{to_workers}{label(300, 300, d['fwd'])}
{workers}{to_relay}{label(735, 360, d['enc'])}
{node(820, 188, 170, d['relay'], d['rsub'], hgt=64)}
</svg>"""
    xs = [12, 128, 244]
    workers = "".join(node(x, 250, 104, n, main=(k == 1), hgt=60) for k, (x, n) in enumerate(zip(xs, names)))
    to_workers = "".join(edge(180, 176, x + 52, 248) for x in xs)
    to_relay = "".join(edge(x + 52, 310, 180, 388, True) for x in xs)
    return f"""<svg class="arch arch-tall" viewBox="0 0 360 470" role="img" aria-labelledby="arch-title-{uid} arch-desc-{uid}">{head}
{node(115, 10, 130, d['players'], hgt=48)}{edge(180, 58, 180, 118)}{label(190, 94, 'MC', 'start')}
{node(100, 120, 160, d['proxy'], ':25565')}{label(270, 214, d['fwd'], 'start')}
{to_workers}{workers}{to_relay}{label(270, 356, d['enc'], 'start')}
{node(90, 390, 180, d['relay'], d['rsub'], hgt=64)}
</svg>"""


def how_it_works(lang):
    t, h = T[lang], HOW[lang]
    L = h["labels"]
    order = [("storia", "Storia"), ("proxy", "Storia Proxy"), ("worker", "Storia Worker"), ("relay", "Storia Relay")]
    roles = "".join(f"""<article class="role" id="{k}">
  <div class="role-head">{logo(k)}<div><h3>{e(n)}</h3><p class="role-sub">{e(h['roles'][k]['role'])}</p></div></div>
  <dl>
    <dt>{L['does']}</dt><dd>{e(h['roles'][k]['does'])}</dd>
    <dt>{L['not']}</dt><dd>{e(h['roles'][k]['not'])}</dd>
    <dt>{L['runs']}</dt><dd>{e(h['roles'][k]['runs'])}</dd>
    <dt>{L['needs']}</dt><dd>{e(h['roles'][k]['needs'])}</dd>
    <dt>{L['ports']}</dt><dd>{e(h['roles'][k]['ports'])}</dd>
    <dt>{L['config']}</dt><dd>{e(h['roles'][k]['config'])}</dd>
  </dl>
  <a class="link" href="{url(lang, f"docs/{h['roles'][k]['docs']}/")}">{L['docs']} {ICON['arrow']}</a>
</article>""" for k, n in order)
    inside = "".join(f"""<a class="layer" href="{url(lang, f'docs/{slug}/')}"><h3>{e(name)}</h3><p>{e(text)}</p></a>""" for name, text, slug in h["inside"])
    chunk = "".join(f"""<li><span class="who who-{who}">{e(h['who'][who])}</span><p>{e(text)}</p></li>""" for who, text in h["chunk"])
    join = "".join(f"""<li><h3>{e(title)}</h3><p>{e(text)}</p></li>""" for title, text in h["join"])

    def table(head, rows, cls=""):
        th = "".join(f'<th scope="col">{e(x)}</th>' for x in head)
        trs = "".join("<tr>" + f'<th scope="row">{e(r[0])}</th>' + "".join(f"<td>{e(c)}</td>" for c in r[1:]) + "</tr>" for r in rows)
        return f'<div class="table-wrap"><table class="plain {cls}"><thead><tr>{th}</tr></thead><tbody>{trs}</tbody></table></div>'

    def chips(items):
        out = []
        for i, it in enumerate(items):
            key, _, mult = it.partition("×")
            label = h["chips"][key] + (f" ×{mult}" if mult else "")
            out.append(f'<span class="chip chip-{key}">{e(label)}</span>')
        return '<span class="arrow" aria-hidden="true">→</span>'.join(out)

    setups = "".join(f"""<article class="setup"><span class="setup-n">{i + 1}</span><h3>{e(name)}</h3><p>{e(text)}</p>
  <div class="flow" aria-label="{e(' → '.join(h['chips'][x.partition('×')[0]] for x in items))}">{chips(items)}</div><p class="uses">{e(uses)}</p></article>"""
                     for i, (name, text, items, uses) in enumerate(h["setups"]))
    desc = "".join(f"<li>{e(x)}</li>" for x in h["diagram_desc"])
    body = f"""
<section class="page-head"><div class="container">
  <p class="kicker">{e(h['kicker'])}</p>
  <h1>{e(h['title'])}</h1>
  <p>{e(h['lede'])}</p>
</div></section>

<div class="container">
  <figure class="arch-fig">
    <div class="arch-wrap">{arch_svg(lang)}{arch_svg(lang, tall=True)}</div>
    <figcaption><ol class="arch-steps">{desc}</ol></figcaption>
  </figure>
</div>

<section class="section"><div class="container">
  <div class="head"><h2>{e(h['roles_t'])}</h2><p>{e(h['roles_p'])}</p></div>
  <div class="roles">{roles}</div>
</div></section>

<section class="section alt"><div class="container">
  <div class="head"><h2>{e(h['inside_t'])}</h2><p>{e(h['inside_p'])}</p></div>
  <div class="layers">{inside}</div>
</div></section>

<section class="section"><div class="container two">
  <div><h2 class="sub-h">{e(h['chunk_t'])}</h2><p class="sub-p">{e(h['chunk_p'])}</p><ol class="journey">{chunk}</ol></div>
  <div><h2 class="sub-h">{e(h['join_t'])}</h2><ol class="steps-list">{join}</ol></div>
</div></section>

<section class="section alt"><div class="container">
  <div class="head"><h2>{e(h['wire_t'])}</h2></div>
  {table(h['wire_h'], h['wire'])}
  <div class="head" style="margin-top:72px"><h2>{e(h['fail_t'])}</h2></div>
  {table(h['fail_h'], h['fail'])}
</div></section>

<section class="section"><div class="container">
  <div class="head"><h2>{e(h['setups_t'])}</h2><p>{e(h['setups_p'])}</p></div>
  <div class="setups">{setups}</div>
  <div class="head" style="margin-top:72px"><h2>{e(h['req_t'])}</h2></div>
  {table(h['req_h'], h['req'])}
  <p class="dl-note">{e(h['req_note'])}</p>
  <p style="text-align:center;margin-top:28px"><a class="btn primary" href="{url(lang, 'downloads/')}">{ICON['dl']}{e(h['cta'])}</a></p>
</div></section>"""
    return page(lang, "how-it-works/", h["title"], h["lede"], body, "how")


# ---------------------------------------------------------------------------------------------
# Downloads
# ---------------------------------------------------------------------------------------------
def fmt_size(b):
    return f"{b / 1048576:.1f} MB" if b >= 1048576 else f"{max(1, round(b / 1024))} KB"


def fmt_date(s, lang="en-us"):
    d = datetime.strptime(s[:10], "%Y-%m-%d")
    return d.strftime("%b %-d, %Y") if lang == "en-us" else f"{d.year}年{d.month}月{d.day}日"


def downloads_of(rel):
    return sum(a.get("download_count", 0) for a in rel["assets"])


def total_downloads():
    return sum(downloads_of(r) for r in RELEASES)


def fmt_count(n, lang):
    return T[lang]["dl_count"].format(n=f"{n:,}")


def release_card(lang, rel, beta=False):
    t = T[lang]
    v = rel["tag_name"].lstrip("v")
    files = []
    for k, name, pattern, doc in PRODUCTS:
        asset = next((a for a in rel["assets"] if re.fullmatch(pattern, a["name"])), None)
        if not asset:
            continue
        sha = (asset.get("digest") or "").replace("sha256:", "")
        files.append(f"""<div class="file" id="{'beta-' if beta else ''}{k}">{logo(k)}
  <div><h3>{e(name)}</h3><p>{e(t['products'][k][1])}</p>
    <div class="meta"><span>{e(asset['name'])}</span><span>{fmt_size(asset['size'])}</span><span>{e(t['req'][k])}</span><span>{e(fmt_count(asset.get('download_count', 0), lang))}</span>{f'<span title="SHA-256 {e(sha)}">SHA-256 <code class="sha">{e(sha)}</code></span>' if sha else ''}<a href="{url(lang, f'docs/{doc}/')}" style="color:var(--accent);text-decoration:none;font-weight:700">{t['docs']}</a></div></div>
  <a class="btn {'secondary' if beta else 'primary'} small" href="{e(asset['browser_download_url'])}">{ICON['dl']}{t['dl_btn']}</a></div>""")
    badge = f' <span class="beta">{t["beta"]}</span>' if beta else ""
    note = f'<p class="beta-note">{e(t["beta_note"])}</p>' if beta else ""
    return f"""<div class="release{' is-beta' if beta else ''}" id="{'beta' if beta else 'stable'}">
  <div class="rhead"><div><h2>{e(t['release'].format(v=v))}{badge}</h2><span>{e(t['for_mc'].format(mc=MC_VERSION))} · {e(t['released'].format(d=fmt_date(rel['published_at'], lang)))}</span>{note}</div>
    <a class="link" href="{e(rel['html_url'])}">{t['notes']} {ICON['arrow']}</a></div>
  {''.join(files)}
</div>"""


def downloads(lang):
    t = T[lang]
    stable = next((r for r in RELEASES if not r.get("prerelease")), None)
    beta = RELEASES[0] if RELEASES and RELEASES[0].get("prerelease") else None
    v = stable["tag_name"].lstrip("v") if stable else MC_VERSION
    release = release_card(lang, stable) if stable else f'<div class="release"><div class="rhead"><span>{t["no_release"]}</span></div></div>'
    if beta:
        release += f'<h2 class="beta-head">{e(t["beta_head"])}</h2>' + release_card(lang, beta, True)
    entries = []
    for rel in RELEASES:
        changes = rel.get("changes") or []
        lis = "".join(f'<li><a href="{GITHUB}/commit/{c["sha"]}">{c["sha"][:7]}</a><span>{linkify(e(c["message"]))}</span></li>' for c in changes)
        links = "".join(f'<a href="{e(a["browser_download_url"])}">{e(a["name"])}</a>' for a in rel["assets"])
        tag = f' <span class="beta">{t["beta"]}</span>' if rel.get("prerelease") else ""
        entries.append(f"""<div class="entry"><div class="when"><b>{e(rel['tag_name'].lstrip('v'))}</b>{tag}<time datetime="{e(rel['published_at'])}" data-time="{e(rel['published_at'])}">{fmt_date(rel['published_at'], lang)}</time><span class="dl-total">{e(fmt_count(downloads_of(rel), lang))}</span></div>
  {f'<ul>{lis}</ul>' if lis else ''}<div class="files">{links}</div></div>""")
    body = f"""
<section class="page-head"><div class="container">
  <p class="kicker">{e(t['dl_k'])}</p>
  <h1>{t['dl_t'].format(v=e(v))}</h1>
  <p>{e(t['dl_p'])}</p>
  <p class="stat"><b>{total_downloads():,}</b><span>{e(t['dl_total'])}</span></p>
</div></section>
<div class="container">
  <p class="dl-which" role="note">{ICON['info']}<span>{t['dl_which'].format(v=e(v))} <a href="{url(lang, 'docs/scaling/')}">{e(t['dl_which_link'])}</a></span></p>
  {release}
  <p class="dl-note">{e(t['dev'])} <a href="{GITHUB}/actions">GitHub Actions</a>.</p>
</div>
<section class="section"><div class="container"><div class="history"><h2>{t['history']}</h2>{''.join(entries)}</div></div></section>"""
    return page(lang, "downloads/", t["downloads"], t["dl_p"], body, "downloads")


def linkify(text):
    return re.sub(r"\(#(\d+)\)", lambda m: f'(<a href="{GITHUB}/pull/{m.group(1)}">#{m.group(1)}</a>)', text)

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
    # Python-Markdown's fenced_code ignores fences indented inside list items; render those here and put them back afterwards
    stash = []

    def nested_fence(m):
        indent, lang_name, code = m.group(1), m.group(2), m.group(3)
        code = "\n".join(line[len(indent):] if line.startswith(indent) else line.lstrip() for line in code.split("\n"))
        try:
            lexer = get_lexer_by_name(lang_name) if lang_name else TextLexer()
        except ClassNotFound:
            lexer = TextLexer()
        stash.append(highlight(code + "\n", lexer, HtmlFormatter(cssclass="hl", wrapcode=True)))
        return f"{indent}STORIACODE{len(stash) - 1}X"
    src = re.sub(r"^([ \t]+)```([\w+-]*)[ \t]*\n(.*?)\n\1```[ \t]*$", nested_fence, src, flags=re.M | re.S)
    out = md.convert(src)
    out = re.sub(r"(?:<p>)?STORIACODE(\d+)X(?:</p>)?", lambda m: stash[int(m.group(1))], out)
    # tabindex lets keyboard users scroll long code blocks (WCAG 2.1.1)
    return out.replace("<pre>", '<pre tabindex="0">'), md.toc_tokens


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
  <button class="icon-btn docs-menu" id="docs-menu" type="button" aria-controls="sidebar" aria-expanded="false"><span class="dm-label">{e(d.group)} › {e(d.title)}</span>{ICON['menu']}</button>
  <aside class="sidebar" id="sidebar" aria-label="{t['docs_menu']}">
    <div class="search">{ICON['search']}
      <input id="search" type="search" placeholder="{t['search']}" aria-label="{t['search']}" autocomplete="off"
        role="combobox" aria-expanded="false" aria-controls="search-results" aria-autocomplete="list" data-results="{t['results']}"
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
    return f'<!doctype html><meta charset="utf-8"><title>StoriaMC</title><meta http-equiv="refresh" content="0; url={target}"><link rel="canonical" href="{target}"><a href="{target}">{target}</a>'


def not_found(lang):
    t = T[lang]
    body = f"""<section class="notfound"><div class="container">
  <div class="code">404</div><h1>{e(t['nf_title'])}</h1><p>{e(t['nf_text'])}</p>
  <div class="actions" style="margin-top:28px"><a class="btn primary" href="{url(lang)}">{e(t['nf_home'])}</a>
  <a class="btn secondary" href="{url(lang, 'docs/')}">{t['documentation']}</a></div></div></section>"""
    return page(lang, "", t["nf_title"], t["nf_text"], body, "")


def keep_phrases(content):
    """Japanese headings: a space next to a Latin word or number must not become a line break (e.g. "6 / つのこと")."""
    def fix(m):
        return re.sub(r">([^<]*)<", lambda t: ">" + re.sub(r"(?<=\S) (?=\S)", "\u00a0", t.group(1)) + "<", m.group(0))
    return re.sub(r"<(h[1-3]|b|button)\b[^>]*>.*?</\1>", fix, content, flags=re.S)


def write(lang, path, content):
    if lang == "ja-jp":
        content = keep_phrases(content)
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
        data.sort(key=lambda r: r.get("published_at") or "", reverse=True)  # the API does not sort by date
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
        stable = next((r for r in RELEASES if not r.get("prerelease")), RELEASES[0])
        LATEST = {"version": stable["tag_name"].lstrip("v")}
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
        write(lang, "downloads/", downloads(lang))
        write(lang, "how-it-works/", how_it_works(lang))
        for key in ("worker", "relay", "proxy"):  # old per-product pages
            write(lang, f"downloads/{key}/", redirect_page(url(lang, f"downloads/#{key}")))
        docs(lang)
        write(lang, "docs/offload/", redirect_page(url(lang, "docs/cluster/")))  # terrain offload was replaced by the cluster
        write(lang, "404.html", not_found(lang))
    (DIST / "index.html").write_text(redirect_page(url("en-us")), encoding="utf-8")
    (DIST / "robots.txt").write_text("User-agent: *\nAllow: /\n", encoding="utf-8")
    print(f"built {sum(1 for _ in DIST.rglob('*.html'))} pages into {DIST} (latest release {LATEST['version']})")


if __name__ == "__main__":
    main()
