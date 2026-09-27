---
summary: The /storia command, its subcommands and permissions.
---
All Storia commands are subcommands of `/storia` and need the permission **`storia.command.storia`**, which
operators have by default. They work in game and in the server console.

| Command | Description |
| --- | --- |
| `/storia` or `/storia status` | Storia version, RAM world state: paths, RAM used, last sync. |
| `/storia sync` | Write the RAM world to disk now. Runs in the background; the server does not pause. |
| `/storia pregen start <radius> [world] [x z]` | Pregenerate a square of `radius` blocks around the world spawn, or around `x z`. |
| `/storia pregen status` | Progress, speed and estimated time left. |
| `/storia pregen stop` | Stop. Progress is saved. |
| `/storia pregen resume` | Continue a stopped or interrupted run, also after a restart. |
| `/storia budget` | Tick thread usage, heap after GC, share per player, and for each player: region load, speed and current view and simulation distance. |
| `/storia region` | The busiest regions: thread usage, MSPT, TPS, players and chunks, plus the [[tick-guard]] state and the most crowded chunks. |
| `/storia cluster` | Cluster connection, the cells this worker runs, players, shared time and scoreboard. |

## Examples

```text
/storia pregen start 5000
/storia pregen start 1500 world 10000 -4000
/storia sync
```

## Permissions

| Permission | Default | Grants |
| --- | --- | --- |
| `storia.command.storia` | op | All `/storia` subcommands. |

Give it to non-operators with any permissions plugin that supports Folia, for example LuckPerms:

```text
/lp group admin permission set storia.command.storia true
```

## Paper and Folia commands

The usual commands are still there: `/tps`, `/mspt` and `/paper`. Folia reports TPS **per region**, so
`/tps` shows the region you are standing in. `/storia region` gives the overview across all regions.

For Storia Proxy's `/storiaproxy` command, see [[proxy]].
