---
summary: Run Storia Proxy, a Velocity fork with built-in placeholders, a live tab list, MOTD and join messages.
---
**Storia Proxy** is a fork of [Velocity](https://papermc.io/software/velocity), the proxy from PaperMC. It
connects your players to several servers behind one address, like Velocity, and adds:

- **50 built-in placeholders** for the proxy, every backend server and the viewing player. See [[placeholders]].
- A **server list MOTD** with placeholders.
- A **tab list header and footer** that refreshes every second.
- **Join, leave and server switch messages** for the whole network.
- A **placeholder API** for your own Velocity plugins. See [[placeholder-api]].
- The `/storiaproxy` command to list, test and reload.

Everything else is Velocity: the same `velocity.toml`, the same plugins and the same forwarding.

## Install

Requires **Java 21** or newer.

1. Download `storia-proxy-{{VERSION}}.jar` from the [downloads page](/en-us/downloads/).
2. Start it:

    ```bash
    java -Xms512M -Xmx512M -jar storia-proxy-{{VERSION}}.jar
    ```

3. It creates `velocity.toml`, `forwarding.secret` and `storia-proxy.toml`. Stop it with `end`.

## Connect your Storia servers

Use **modern forwarding**, so player UUIDs and skins are passed on securely.

In the proxy's `velocity.toml`:

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

On **each Storia server**:

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
    secret: "<the contents of forwarding.secret>"
```

Restart the backend servers, then the proxy. Players connect to the proxy's address.

!!! warning
    Make sure backend servers cannot be reached directly from the internet (firewall), since they now trust the
    proxy for authentication.

## storia-proxy.toml

Text uses [MiniMessage](https://docs.advntr.dev/minimessage/format) with `{placeholders}`.

```toml
[motd]
# Replaces the server list description (two lines).
enabled = true
lines = [
  "<gradient:#bdbdbd:#ffffff><bold>{proxy_name}</bold></gradient> <dark_gray>|</dark_gray> <gray>{servers_online}/{server_count} servers up",
  "<gray>{online} players online <dark_gray>·</dark_gray> {time}"
]
# Max players shown in the server list; -1 keeps show-max-players from velocity.toml.
max-players = -1

[tablist]
enabled = true
# How often headers and footers are refreshed, in milliseconds.
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
# Broadcast to everyone. Leave empty ("") to disable.
join = "<dark_gray>[<green>+</green>]</dark_gray> <gray>{player}"
leave = "<dark_gray>[<red>-</red>]</dark_gray> <gray>{player}"
# Also has {previous_server}.
switch = "<dark_gray>[<aqua>»</aqua>]</dark_gray> <gray>{player}: {previous_server} → {player_server}"

[server-status]
# How often backend servers are pinged for {status_<server>}, {motd_<server>} and friends.
refresh-seconds = 10
```

| Option | Default | Description |
| --- | --- | --- |
| `motd.enabled` | `true` | Replace the server list description. |
| `motd.lines` | see above | Up to two lines. Player placeholders are empty here (there is no player yet). |
| `motd.max-players` | `-1` | Max players shown. `-1` = `show-max-players` from `velocity.toml`. |
| `tablist.enabled` | `true` | Show a header and footer in the tab list. |
| `tablist.interval-ms` | `1000` | Refresh interval, at least 250. |
| `tablist.header` / `footer` | see above | Lines of text. |
| `messages.join` / `leave` / `switch` | see above | Network-wide broadcasts. `""` disables one. |
| `server-status.refresh-seconds` | `10` | How often backends are pinged, at least 2. |

Apply changes with `/storiaproxy reload`, without a restart.

## /storiaproxy

Permission: **`storiaproxy.admin`** (the console always has it).

| Command | Description |
| --- | --- |
| `/storiaproxy placeholders` | Every placeholder with its description and current value for you. |
| `/storiaproxy parse <text>` | Render a line of MiniMessage with placeholders, to try it out. |
| `/storiaproxy reload` | Reload `storia-proxy.toml`. |

```text
/storiaproxy parse <green>{online_lobby}</green> in the lobby, you are on {player_server} ({player_ping}ms)
```

## Velocity plugins

Storia Proxy runs Velocity plugins unchanged. The Velocity documentation at
[docs.papermc.io/velocity](https://docs.papermc.io/velocity) applies to everything that is not specific to
Storia Proxy.
