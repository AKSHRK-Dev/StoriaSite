---
summary: Storia Proxy に内蔵された 50 個のプレースホルダー。MOTD・タブリスト・メッセージ・プラグインで使えます。
---
プレースホルダーは `{名前}` の形で、`storia-proxy.toml`、`/storiaproxy parse`、[[placeholder-api]] を通してプラグインが表示するテキストの
どこにでも書けます。知らない名前はそのまま残るので、打ち間違いにすぐ気づけます。

`/storiaproxy placeholders` を実行すると、すべてのプレースホルダーを **現在の値** つきで確認できます。

値はプレーンテキストとして入ります。値の中の MiniMessage タグ（たとえばプレイヤーが決めた名前の中のもの）はエスケープされます。
ただし `*_color` のプレースホルダーはタグとして使うためのものなので、例外です。

```text
<{player_ping_color}>{player_ping}ms</{player_ping_color}>
<{status_color_lobby}>lobby は {status_lobby}</{status_color_lobby}>
```

## プロキシ

| プレースホルダー | 値 |
| --- | --- |
| `{proxy_name}` | プロキシの名前 |
| `{proxy_version}` | プロキシのバージョン |
| `{online}` | プロキシにいるプレイヤー数 |
| `{max}` | 最大人数（`show-max-players`） |
| `{server_count}` | 登録されているサーバー数 |
| `{servers_online}` | ping に応答したサーバー数 |
| `{servers}` | サーバー名の一覧 |
| `{most_popular_server}` | 一番プレイヤーが多いサーバー |
| `{time}` | `HH:mm` |
| `{time_seconds}` | `HH:mm:ss` |
| `{date}` | `yyyy-MM-dd` |
| `{datetime}` | `yyyy-MM-dd HH:mm` |
| `{day_of_week}` | 曜日（わかる場合は見ている人の言語） |
| `{uptime}` | プロキシの稼働時間（例：`2d 3h 4m`） |
| `{uptime_seconds}` | プロキシの稼働時間（秒） |
| `{memory_used}` | 使用中のヒープ（MB） |
| `{memory_max}` | 最大ヒープ（MB） |
| `{memory_free}` | 空きヒープ（MB） |
| `{memory_percent}` | ヒープ使用率（%） |
| `{cpu_cores}` | CPU コア数 |
| `{cpu_load}` | プロキシのプロセスの CPU 使用率（%） |
| `{java_version}` | Java のバージョン |
| `{os}` | OS |
| `{plugin_count}` | 読み込まれたプラグイン数 |

## 各サーバー

`<server>` は `velocity.toml` の `[servers]` にあるサーバー名です。例：`{online_lobby}`

| プレースホルダー | 値 |
| --- | --- |
| `{online_<server>}` | そのサーバーにいるプレイヤー数（このプロキシ経由） |
| `{players_<server>}` | そのプレイヤーの名前 |
| `{status_<server>}` | `online` または `offline` |
| `{status_color_<server>}` | `green` または `red`（タグとして使います） |
| `{max_<server>}` | サーバーが返す最大人数 |
| `{motd_<server>}` | サーバーの MOTD（プレーンテキスト） |
| `{version_<server>}` | サーバーのバージョン名 |
| `{latency_<server>}` | プロキシからサーバーへの ping（ms） |
| `{address_<server>}` | `host:port` |

状態・MOTD・バージョン・最大人数・遅延は、`server-status.refresh-seconds` ごとの ping で取得します。

## 表示するプレイヤー

テキストを見ているプレイヤーの情報です。サーバーリストの MOTD の時点ではまだプレイヤーがいないので、空になります。

| プレースホルダー | 値 |
| --- | --- |
| `{player}` | 名前 |
| `{player_uuid}` | UUID |
| `{player_ping}` | ping（ms） |
| `{player_ping_color}` | `green`（80 ms 未満）、`yellow`（200 ms 未満）、`red` |
| `{player_server}` | 今いるサーバー |
| `{player_server_online}` | そのサーバーのプレイヤー数 |
| `{player_server_max}` | そのサーバーの最大人数 |
| `{player_server_motd}` | そのサーバーの MOTD |
| `{player_locale}` | ロケール（例：`ja_jp`） |
| `{player_language}` | 言語名（その言語で） |
| `{player_client_brand}` | `vanilla`、`fabric` など |
| `{player_protocol}` | プロトコル番号 |
| `{player_version}` | クライアントの Minecraft バージョン |
| `{player_virtual_host}` | 接続に使ったホスト名 |
| `{player_online_mode}` | 正規アカウントなら `true` |
| `{player_session}` | 参加してからの時間 |
| `{player_session_minutes}` | 参加してからの分数 |

`messages.switch` では `{previous_server}` も使えます。

## 例

全サーバーの状態を出すタブリストのフッター：

```toml
footer = [
  "<{status_color_lobby}>●</{status_color_lobby}> lobby {online_lobby}  <{status_color_survival}>●</{status_color_survival}> survival {online_survival}",
  "<gray>{player} · {player_version} · {player_client_brand}"
]
```

一番にぎわっているサーバーを出す MOTD：

```toml
lines = [
  "<white><bold>My Network</bold> <gray>· {online}/{max}",
  "<gray>いま一番人が多いサーバー：<white>{most_popular_server}"
]
```
