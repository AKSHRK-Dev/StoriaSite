---
summary: Minimum and recommended hardware for Storia, Storia Worker, Storia Relay and Storia Proxy, and how to check that yours is enough.
---
These are **starting points**, not guarantees: what a server needs depends mostly on how many players are online,
how spread out they are, and how many mobs and machines they build. Start with the recommended column, watch the
numbers described at the end, and adjust.

All programs need a **64-bit** OS: Linux (recommended), Windows or macOS.

## At a glance

| Program | Java | CPU (min / recommended) | Memory (min / recommended) | Disk | Network |
| --- | --- | --- | --- | --- | --- |
| **Storia** (single server) | 25 | 4 / 8+ cores | 4 / 8–16 GB heap, plus the world size for the RAM world | SSD, 2× the world size | Players' traffic |
| **Storia Worker** | 25 | 4 / 8+ cores | 4 / 8–16 GB heap | A few GB (logs, write queue) | Close to the relay: LAN, 1 Gbps |
| **Storia Relay** | 21+ | 2 / 4 cores | 512 MB / 1–2 GB heap | SSD, 2× the world size | 1 Gbps to the workers |
| **Storia Proxy** | 21+ | 1 / 2 cores | 512 MB / 1 GB heap | Under 1 GB | All players' traffic |

## Storia (single server)

- **CPU**: Folia runs separate areas of the world on separate cores, so **more cores help as players spread out**.
  4 cores run a small server; 8 or more are recommended for a busy one. A high clock speed helps a crowded spawn,
  which runs on one core.
- **Memory**: set the heap with `-Xmx`. 4 GB is enough for a few players; 8–16 GB for a busy server. Leave 1–2 GB
  for the operating system.
- **RAM world**: needs free RAM (in `/dev/shm`) at least as large as the world folder, **in addition to** the heap,
  plus `ram-world.min-free-mb` (512 MB by default). If there is not enough, Storia loads the world from disk instead.
  See [[ram-world]].
- **Disk**: an SSD. Keep room for twice the world size (the world and a backup).

## Storia Worker (cluster)

- A worker runs part of the world, so size it like a **Storia server without the RAM world**: 4 cores and a 4 GB
  heap at least, 8+ cores and 8–16 GB for a busy area.
- **Network**: every chunk a worker loads or saves goes to the relay. Put workers and the relay on the same LAN
  (about 1 ms apart; 1 Gbps). A far-away relay makes chunk loading slower.
- **Disk**: the world lives on the relay; a worker needs space only for its jar, logs and `cluster-spool/` (writes
  kept while the relay is away).
- See [[worker]] and [[scaling|From one server to a cluster]].

## Storia Relay (cluster)

- The relay stores the world and coordinates the workers; it does no game work. 2 cores and a 512 MB heap are
  enough to start; give it 4 cores and 1–2 GB with many workers.
- **Disk**: this is where the world is. Use an SSD with room for **twice the world size** and plan backups of
  `cluster-world/` from here.
- **Network**: 1 Gbps to the workers. It can share a machine with the proxy or a worker.
- See [[relay]].

## Storia Proxy

- The proxy passes players' traffic through and runs no world. 1–2 cores and a 512 MB–1 GB heap handle hundreds of
  players.
- **Network**: all player traffic goes through it. Plan roughly **0.1–1 Mbit/s per player** (more while they explore
  or fly, less while they stand).
- See [[proxy]].

## Is it enough? How to check

| Look at | Where | Healthy |
| --- | --- | --- |
| Tick time per region | `/tps`, `/storia region` | Under 50 ms (20 TPS) |
| Tick guard level | `/storia region` | 0 most of the time; if it is often above 0, add cores or look at the crowded chunks it lists |
| Player budget | `/storia budget` | Few players limited, and only while flying fast |
| Heap after GC | `/storia budget` (heap) | Below 85%; above it, raise `-Xmx` |
| Cluster | `/storia cluster`, `status` on the relay | Workers connected, no writes waiting |

If one machine is consistently at its limit with many players spread over the world, it is time to move to a
[[cluster]].
