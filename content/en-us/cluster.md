---
summary: Several Storia servers run one world together, each ticking a different part of it, and players move between them without a loading screen.
---
Running a single server today? See [[scaling|From one server to a cluster]] for when to move and how.

!!! note "Version"
    Storia Cluster is part of Storia **26.2-2** and later; the first 26.2 release does not include it. Back up your
    world before you move it into a cluster.

**Storia Cluster** splits one world over several Storia servers, the [[worker|Storia Workers]]. Each worker runs
the part of the world where its players are: chunks, mobs, redstone and the players themselves. When players come close to each other,
their areas are moved onto one worker before they could see each other's chunks, so nothing is ever split between
two machines. Players move between workers through Storia Proxy **without a loading screen**; their inventory,
advancements and statistics come with them.

```text
players --> Storia Proxy --> Storia Worker A --\
                         \-> Storia Worker B ---> Storia Relay: the world, who runs what
                          \-> Storia Worker C --/
```

## What each program does

| Program | Role in a cluster |
| --- | --- |
| **[[relay|Storia Relay]]** | The coordinator. Stores the world (normal Anvil region files), player data and shared data, decides which worker runs which part of the world, and balances players across workers. |
| **[[worker|Storia Worker]]** | Runs its part of the world. Keeps no world data of its own: chunks are read from and written to the relay. |
| **Storia Proxy** | The front door. Sends each player to the right worker and switches them to another worker when the relay says so. |

## How the world is split

- The world is divided into **cells** of 32 × 32 chunks (one region file each). Only one worker may run a cell at
  a time; the relay hands cells out.
- A worker reports every second which cells its players can see. Groups of players whose areas touch are always put
  on **the same worker**, together with everything they can see. In practice players about 1,000 blocks apart or
  closer share a worker.
- Every 10 seconds the relay moves a whole group from the busiest worker to the quietest one if that evens things
  out.
- **Contraptions are never split.** When redstone, pistons, hoppers, rails and similar blocks sit on the border
  between two cells in a place people have spent time (10 minutes or more), the two cells are linked and always
  run on the same worker. Links survive restarts.

## What is shared between workers

- Time, weather and game rules (one worker keeps the reference; changes on any worker reach all of them).
- The scoreboard (objectives, scores, teams), map ids and map contents, command storage.
- Player data, advancements and statistics: exactly one worker holds a player at a time, and the next worker reads
  them only after the previous one has saved.

## Setup

You need one [[relay|Storia Relay]], two or more [[worker|Storia Workers]] and one Storia Proxy, all from the
same release. Every worker needs the resources of a normal Storia server.

1. **Relay**: set a `secret` in `relay.properties` and put your world in `cluster-world/`. See [[relay]].
2. **Workers**: in each worker's `storia.yml` set `cluster.coordinator`, a unique `cluster.node-name` and the
   relay's `cluster.secret`. A new worker fetches the world settings from the relay on first start, so you do not
   copy the world. Workers are Velocity backends (`proxies.velocity` in `config/paper-global.yml`). See [[worker]].
3. **Storia Proxy**: list the workers in `velocity.toml` under their node names and use modern forwarding, then
   set `[cluster]` in `storia-proxy.toml`:

    ```toml
    [cluster]
    enabled = true
    coordinator = "relay-host:25590"
    secret = "choose-a-long-secret"
    ```

Start the relay first, then the workers, then the proxy. `status` in the relay console and `/storia cluster` on a
worker show who runs what; `/storiaproxy cluster` shows the proxy's view.

## Stopping and restarting

- `/stop` on a worker first moves its players to the other workers (no kick), then saves and stops.
- If the relay goes away for a while, workers keep running and keep their writes in `cluster-spool/` on local disk;
  they send them when the relay is back, also after a worker restart.
- If every worker stops, players are disconnected as on any server.

## Current limits

- Seamless switching needs **Minecraft 26.1 or 26.2** clients. Older clients through ViaVersion may see a
  normal server switch (a short loading screen) instead.
- Plugins run separately on each worker. Their own data (balances, claims, ...) can be shared with the
  [[plugin-api|plugin API]].
- Folia has no `/scoreboard` and `/team` commands; the shared scoreboard changes through criteria such as
  `deathCount` and a scoreboard carried over from another server.
- Tested with two workers and a few players so far. Please report problems on
  [GitHub]({{GITHUB}}/issues).
