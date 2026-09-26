---
summary: Every option in storia.yml, with its default and what it does.
---
`storia.yml` is created in the server folder on first start. Missing options are added with their defaults
on the next start, so you can delete a line to reset it. Changes take effect after a **restart**.

Paper's and Folia's own settings stay where they always were (`config/paper-global.yml`,
`config/paper-world-defaults.yml`, `server.properties`).

## Full default file

```yaml
ram-world:
  enabled: true
  ram-directory: /dev/shm/storia
  sync-interval-seconds: 300
  min-free-mb: 512
  delete-on-shutdown: true
pregen:
  worker-threads: -1
  max-in-flight: -1
tick-guard:
  enabled: true
  target-mspt: 40.0
  crowd-threshold: 16
  player-radius: 8.0
  max-level: 3
player-budget:
  enabled: true
  check-interval-ticks: 100
  max-region-mspt: 45.0
  pool-saturated-percent: 85
  recover-below-percent: 70
  lower-simulation-distance: false
  min-simulation-distance: 4
  min-view-distance: 6
  memory-high-percent: 85
  memory-low-percent: 70
  fast-mover-speed: 12.0
offload:
  mode: 'off'
  secret: ''
  workers:
  - 127.0.0.1:25590
  max-in-flight: -1
  timeout-ms: 10000
  compress: true
  bind: 0.0.0.0
  port: 25590
  threads: -1
  relay: ''
```

## ram-world

See [[ram-world]].

| Option | Default | Description |
| --- | --- | --- |
| `enabled` | `true` | Keep worlds in RAM. `false` runs from disk like Paper. |
| `ram-directory` | `/dev/shm/storia` | Where the RAM copy lives. Must be a RAM-backed file system (tmpfs). |
| `sync-interval-seconds` | `300` | How often changed files are written to disk. Minimum 10. Shorter is safer, longer is lighter. |
| `min-free-mb` | `512` | If loading the world would leave less free RAM than this, worlds are loaded from disk instead. |
| `delete-on-shutdown` | `true` | Delete the RAM copy after a clean shutdown (it has been written to disk). |

## pregen

See [[pregeneration]].

| Option | Default | Description |
| --- | --- | --- |
| `worker-threads` | `-1` | Chunk worker threads while `/storia pregen` runs. `-1` = CPU cores − 1. Restored when it finishes. |
| `max-in-flight` | `-1` | Chunks queued at once. `-1` = worker threads × 16. |

## tick-guard

See [[tick-guard]].

| Option | Default | Description |
| --- | --- | --- |
| `enabled` | `true` | Thin out crowded mobs' AI when a region is overloaded. |
| `target-mspt` | `40.0` | Keep each region's tick time below this (milliseconds; a tick has 50). |
| `crowd-threshold` | `16` | Mobs in one chunk that count as a crowd. Only crowds are thinned out. |
| `player-radius` | `8.0` | Mobs within this many blocks of a player always think every tick. |
| `max-level` | `3` | How far to thin out: 1 = every 2nd tick, 2 = every 4th, 3 = every 8th. |

## player-budget

See [[player-budget]].

| Option | Default | Description |
| --- | --- | --- |
| `enabled` | `true` | Turn the budget on or off. |
| `check-interval-ticks` | `100` | How often each player is checked (100 ticks = 5 seconds). |
| `max-region-mspt` | `45.0` | A region whose tick takes longer than this (milliseconds) is over budget. Only fast movers in it are limited. |
| `pool-saturated-percent` | `85` | When the tick threads are this busy, fair shares are enforced. |
| `recover-below-percent` | `70` | A limited region is restored once it is below this percentage of its limits. |
| `fast-mover-speed` | `12.0` | Only players moving faster than this (blocks per second, on two checks in a row) are limited. |
| `lower-simulation-distance` | `false` | Also lower the fast mover's simulation distance. **Leave `false` to keep farms and redstone running.** |
| `min-simulation-distance` | `4` | Lowest simulation distance, only used when the option above is `true`. |
| `min-view-distance` | `6` | Lowest view distance the budget will set. |
| `memory-high-percent` | `85` | Heap usage after GC above this lowers everyone's view distance. |
| `memory-low-percent` | `70` | Heap usage after GC below this restores it. |

## offload

See [[offload]], [[worker]] and [[relay]].

| Option | Default | Used by | Description |
| --- | --- | --- | --- |
| `mode` | `off` | all | `off`, `client` (the main server) or `worker` (a helper). |
| `secret` | `''` | all | Shared secret, at least 8 characters, identical on every machine. Never sent over the network. |
| `workers` | `[127.0.0.1:25590]` | client | Workers or relays to use, as `host:port`. |
| `max-in-flight` | `-1` | client | Requests waiting per connection. `-1` = the worker's threads × 4. |
| `timeout-ms` | `10000` | client | Give up on an answer after this long and generate the chunk locally. |
| `compress` | `true` | all | Compress traffic (deflate) before encryption. Turn off on very fast networks to save CPU. |
| `bind` | `0.0.0.0` | worker | Address a worker listens on. |
| `port` | `25590` | worker | Port a worker listens on. |
| `threads` | `-1` | worker | Threads for terrain computation. `-1` = all cores. |
| `relay` | `''` | worker | If set (`host:port`), the worker connects out to this relay instead of listening. |

Any `mode` other than `client` or `worker` means off (a bare `off` is read by YAML as `false`, which is also off).

## Java system properties

These are set on the command line with `-D...` before `-jar`:

| Property | Description |
| --- | --- |
| `-Dstoria.worker=true` | Start as a dedicated worker: no player port, no query or RCON. Used by the [[worker]] package. |
| `-Dstoria.verifyOffload=true` | Also generate every offloaded chunk locally and compare. For testing; costs CPU. |
| `-Dstoria.verifyPush=true` | Also compute every entity push the vanilla way and compare. For testing; costs CPU. |
