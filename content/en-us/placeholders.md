---
summary: All 50 placeholders built into Storia Proxy, for the MOTD, tab list, messages and plugins.
---
Write a placeholder as `{name}` anywhere in `storia-proxy.toml`, in `/storiaproxy parse`, or in text rendered by
a plugin through the [[placeholder-api]]. Unknown placeholders are left as they are, so a typo is easy to spot.

Run `/storiaproxy placeholders` to see every placeholder with its **current value**.

Values are inserted as plain text: MiniMessage tags inside a value (for example in a player-chosen name) are
escaped. The `*_color` placeholders are the exception, since they are meant to be used as tags:

```text
<{player_ping_color}>{player_ping}ms</{player_ping_color}>
<{status_color_lobby}>lobby is {status_lobby}</{status_color_lobby}>
```

## Proxy

| Placeholder | Value |
| --- | --- |
| `{proxy_name}` | Proxy name |
| `{proxy_version}` | Proxy version |
| `{online}` | Players on the proxy |
| `{max}` | Max players (`show-max-players`) |
| `{server_count}` | Registered backend servers |
| `{servers_online}` | Backend servers answering pings |
| `{servers}` | Backend server names |
| `{most_popular_server}` | Backend with the most players |
| `{time}` | `HH:mm` |
| `{time_seconds}` | `HH:mm:ss` |
| `{date}` | `yyyy-MM-dd` |
| `{datetime}` | `yyyy-MM-dd HH:mm` |
| `{day_of_week}` | Day of the week, in the viewer's language when known |
| `{uptime}` | Proxy uptime, e.g. `2d 3h 4m` |
| `{uptime_seconds}` | Proxy uptime in seconds |
| `{memory_used}` | Heap used (MB) |
| `{memory_max}` | Max heap (MB) |
| `{memory_free}` | Free heap (MB) |
| `{memory_percent}` | Heap used (%) |
| `{cpu_cores}` | CPU cores |
| `{cpu_load}` | Proxy process CPU (%) |
| `{java_version}` | Java version |
| `{os}` | Operating system |
| `{plugin_count}` | Loaded plugins |

## Backend servers

`<server>` is a server name from the `[servers]` section of `velocity.toml`, for example `{online_lobby}`.

| Placeholder | Value |
| --- | --- |
| `{online_<server>}` | Players on the server (connected through this proxy) |
| `{players_<server>}` | Names of those players |
| `{status_<server>}` | `online` or `offline` |
| `{status_color_<server>}` | `green` or `red`, for use as a tag |
| `{max_<server>}` | Max players the server reports |
| `{motd_<server>}` | The server's MOTD as plain text |
| `{version_<server>}` | The server's version name |
| `{latency_<server>}` | Ping from the proxy to the server (ms) |
| `{address_<server>}` | `host:port` |

Status, MOTD, version, max players and latency come from pings every `server-status.refresh-seconds`.

## Viewing player

These describe the player who sees the text. In the server list MOTD there is no player yet, so they are empty.

| Placeholder | Value |
| --- | --- |
| `{player}` | Name |
| `{player_uuid}` | UUID |
| `{player_ping}` | Ping (ms) |
| `{player_ping_color}` | `green` (< 80 ms), `yellow` (< 200 ms) or `red` |
| `{player_server}` | Current server |
| `{player_server_online}` | Players on that server |
| `{player_server_max}` | Max players of that server |
| `{player_server_motd}` | MOTD of that server |
| `{player_locale}` | Locale, e.g. `en_us` |
| `{player_language}` | Language name, in that language |
| `{player_client_brand}` | `vanilla`, `fabric`, ... |
| `{player_protocol}` | Protocol number |
| `{player_version}` | Client Minecraft version |
| `{player_virtual_host}` | Host name the player connected with |
| `{player_online_mode}` | `true` if the account is verified |
| `{player_session}` | Time since joining |
| `{player_session_minutes}` | Minutes since joining |

In `messages.switch` there is also `{previous_server}`.

## Examples

A tab list footer showing every server's state:

```toml
footer = [
  "<{status_color_lobby}>●</{status_color_lobby}> lobby {online_lobby}  <{status_color_survival}>●</{status_color_survival}> survival {online_survival}",
  "<gray>{player} · {player_version} · {player_client_brand}"
]
```

A MOTD with the busiest server:

```toml
lines = [
  "<white><bold>My Network</bold> <gray>· {online}/{max}",
  "<gray>Most players right now: <white>{most_popular_server}"
]
```
