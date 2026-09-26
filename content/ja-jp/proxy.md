---
summary: プレースホルダー・自動更新のタブリスト・MOTD・参加メッセージを内蔵した Velocity のフォーク、Storia Proxy を動かす。
---
**Storia Proxy** は、PaperMC のプロキシ [Velocity](https://papermc.io/software/velocity) のフォークです。Velocity と同じく、
1 つのアドレスでプレイヤーを複数のサーバーにつなぎます。さらに次の機能を加えています。

- プロキシ・各サーバー・表示するプレイヤーの情報を出せる **50 個のプレースホルダー**（[[placeholders]] を参照）
- プレースホルダーを使える **サーバーリストの MOTD**
- 毎秒更新される **タブリストのヘッダーとフッター**
- ネットワーク全体への **参加・退出・サーバー移動のメッセージ**
- 自作の Velocity プラグイン向けの **プレースホルダー API**（[[placeholder-api]] を参照）
- 一覧表示・試し表示・再読み込みができる `/storiaproxy` コマンド

それ以外は Velocity そのままです。`velocity.toml` もプラグインもフォワーディングも同じです。

## インストール

**Java 21** 以上が必要です。

1. [ダウンロードページ](/en-us/downloads/) から `storia-proxy-{{VERSION}}.jar` を入手します。
2. 起動します。

    ```bash
    java -Xms512M -Xmx512M -jar storia-proxy-{{VERSION}}.jar
    ```

3. `velocity.toml`、`forwarding.secret`、`storia-proxy.toml` が作られます。`end` で止めます。

## Storia サーバーをつなぐ

プレイヤーの UUID やスキンを安全に引き継げる **modern フォワーディング** を使います。

プロキシの `velocity.toml`：

```toml
bind = "0.0.0.0:25565"
online-mode = true
player-info-forwarding-mode = "modern"
forwarding-secret-file = "forwarding.secret"

[servers]
lobby = "127.0.0.1:30066"
survival = "192.168.0.10:30067"
try = ["lobby"]
```

**各 Storia サーバー** では：

```properties
# server.properties
server-port=30066
online-mode=false
```

```yaml
# config/paper-global.yml
proxies:
  velocity:
    enabled: true
    online-mode: true
    secret: "<forwarding.secret の中身>"
```

各サーバーを再起動してから、プロキシを再起動します。プレイヤーはプロキシのアドレスに接続します。

!!! warning "注意"
    各サーバーは認証をプロキシに任せるようになるので、インターネットから直接つながらないようにしてください（ファイアウォール）。

## storia-proxy.toml

文字列には [MiniMessage](https://docs.advntr.dev/minimessage/format) と `{プレースホルダー}` を使えます。

```toml
[motd]
# サーバーリストの説明文を置き換えます（2 行）。
enabled = true
lines = [
  "<gradient:#bdbdbd:#ffffff><bold>{proxy_name}</bold></gradient> <dark_gray>|</dark_gray> <gray>{servers_online}/{server_count} servers up",
  "<gray>{online} players online <dark_gray>·</dark_gray> {time}"
]
# サーバーリストに出す最大人数。-1 なら velocity.toml の show-max-players のまま。
max-players = -1

[tablist]
enabled = true
# ヘッダーとフッターの更新間隔（ミリ秒）。
interval-ms = 1000
header = [
  "",
  "<white><bold>{proxy_name}</bold>",
  "<gray>{online}/{max} online <dark_gray>·</dark_gray> {time}",
  ""
]
footer = [
  "",
  "<gray>{player_server} <dark_gray>({player_server_online})</dark_gray> <dark_gray>·</dark_gray> ping <{player_ping_color}>{player_ping}ms</{player_ping_color}>",
  "<dark_gray>uptime {uptime}",
  ""
]

[messages]
# 全員に送ります。空（""）にすると送りません。
join = "<dark_gray>[<green>+</green>]</dark_gray> <gray>{player}"
leave = "<dark_gray>[<red>-</red>]</dark_gray> <gray>{player}"
# {previous_server} も使えます。
switch = "<dark_gray>[<aqua>»</aqua>]</dark_gray> <gray>{player}: {previous_server} → {player_server}"

[server-status]
# {status_<server>} や {motd_<server>} などのために各サーバーへ ping する間隔。
refresh-seconds = 10
```

| 項目 | 初期値 | 説明 |
| --- | --- | --- |
| `motd.enabled` | `true` | サーバーリストの説明文を置き換えます。 |
| `motd.lines` | 上記 | 最大 2 行。まだプレイヤーがいないので、プレイヤーのプレースホルダーは空になります。 |
| `motd.max-players` | `-1` | 表示する最大人数。`-1` は `velocity.toml` の `show-max-players`。 |
| `tablist.enabled` | `true` | タブリストにヘッダーとフッターを表示します。 |
| `tablist.interval-ms` | `1000` | 更新間隔。最小 250。 |
| `tablist.header` / `footer` | 上記 | 表示する行。 |
| `messages.join` / `leave` / `switch` | 上記 | ネットワーク全体へのメッセージ。`""` で無効。 |
| `server-status.refresh-seconds` | `10` | 各サーバーに ping する間隔。最小 2。 |

変更は `/storiaproxy reload` で、再起動せずに反映できます。

## /storiaproxy

権限：**`storiaproxy.admin`**（コンソールは常に使えます）

| コマンド | 説明 |
| --- | --- |
| `/storiaproxy placeholders` | すべてのプレースホルダーと、その説明・自分にとっての現在の値。 |
| `/storiaproxy parse <テキスト>` | プレースホルダー入りの MiniMessage を 1 行表示して試せます。 |
| `/storiaproxy reload` | `storia-proxy.toml` を読み込み直します。 |

```text
/storiaproxy parse <green>{online_lobby}</green> 人がロビーにいます。あなたは {player_server} にいます（{player_ping}ms）
```

## Velocity のプラグイン

Storia Proxy では Velocity のプラグインがそのまま動きます。Storia Proxy 独自の部分以外は、
[docs.papermc.io/velocity](https://docs.papermc.io/velocity) の Velocity のドキュメントがそのまま当てはまります。
