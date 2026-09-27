---
summary: Beta. Several Storia servers run one world together, each ticking a different part of it, and players move between them without a loading screen.
---
!!! warning "Beta"
    Storia Cluster is new in **26.2-2-beta** and still being tested. Releases before it (26.2, 26.2-1-beta)
    do not include it. Back up your world before you try it, and do not run it on your only copy.

**Storia Cluster** splits one world over several Storia servers ("nodes"). Each node runs the part of the world
where its players are: chunks, mobs, redstone and the players themselves. When players come close to each other,
their areas are moved onto one node before they could see each other's chunks, so nothing is ever split between
two machines. Players move between nodes through Storia Proxy **without a loading screen**; their inventory,
advancements and statistics come with them.

```text
players --> Storia Proxy --> node alpha --\
                         \-> node beta  ---> Storia Relay (cluster=true): the world, who runs what
                          \-> node gamma --/
```

## What each program does

| Program | Role in a cluster |
| --- | --- |
| **Storia Relay** with `cluster=true` | The coordinator. Stores the world (normal Anvil region files), player data and shared data, decides which node runs which part of the world, and balances players across nodes. |
| **Storia** (each node) | Runs its part of the world. Keeps no world data of its own: chunks are read from and written to the relay. |
| **Storia Proxy** | The front door. Sends each player to the right node and switches them to another node when the relay says so. |

## How the world is split

- The world is divided into **cells** of 32 × 32 chunks (one region file each). Only one node may run a cell at
  a time; the relay hands cells out.
- A node reports every second which cells its players can see. Groups of players whose areas touch are always put
  on **the same node**, together with everything they can see. In practice players about 1,000 blocks apart or
  closer share a node.
- Every 10 seconds the relay moves a whole group from the busiest node to the quietest one if that evens things
  out.
- **Contraptions are never split.** When redstone, pistons, hoppers, rails and similar blocks sit on the border
  between two cells in a place people have spent time (10 minutes or more), the two cells are linked and always
  run on the same node. Links survive restarts.

## What is shared between nodes

- Time, weather and game rules (one node keeps the reference; changes on any node reach all of them).
- The scoreboard (objectives, scores, teams), map ids and map contents, command storage.
- Player data, advancements and statistics: exactly one node holds a player at a time, and the next node reads
  them only after the previous one has saved.

## Setup

You need: one Storia Relay, two or more Storia servers (nodes) and one Storia Proxy, all from the same release.
Every node needs the resources of a normal Storia server.

### 1. Relay (the coordinator)

In `relay.properties`:

```properties
port=25590
secret=choose-a-long-secret
cluster=true
cluster-world=cluster-world
```

Put your world in `cluster-world` (a normal world folder: `level.dat`, `dimensions/`, `players/`, ...). This is
now the only copy the cluster writes to.

### 2. Each node

Copy the world to every node **without** its `region`, `entities` and `poi` folders (the node needs `level.dat`,
the world generation settings and data packs, but reads chunks from the relay). Then add to `storia.yml`:

```yaml
cluster:
  enabled: true
  coordinator: "relay-host:25590"
  node-name: alpha        # unique per node, and the same name as in velocity.toml
  secret: choose-a-long-secret
```

Set up the node for the proxy as for any Velocity backend: `online-mode=false` in `server.properties`, and in
`config/paper-global.yml` `proxies.velocity.enabled: true` with the proxy's forwarding secret.

### 3. Storia Proxy

In `velocity.toml`, list every node under the same name as its `cluster.node-name` and use modern forwarding:

```toml
player-info-forwarding-mode = "modern"

[servers]
alpha = "10.0.0.11:25565"
beta = "10.0.0.12:25565"
try = ["alpha", "beta"]
```

In `storia-proxy.toml`:

```toml
[cluster]
enabled = true
coordinator = "relay-host:25590"
secret = "choose-a-long-secret"
```

Start the relay first, then the nodes, then the proxy. `status` in the relay console and `/storia cluster` on a
node show who runs what; `/storiaproxy cluster` shows the proxy's view.

## Stopping and restarting

- `/stop` on a node first moves its players to the other nodes (no kick), then saves and stops.
- If the relay goes away for a while, nodes keep running and keep their writes in `cluster-spool/` on local disk;
  they send them when the relay is back, also after a node restart.
- If every node stops, players are disconnected as on any server.

## Limits in this beta

- Seamless switching needs **Minecraft 26.1 or 26.2** clients. Older clients through ViaVersion may see a
  normal server switch (a short loading screen) instead.
- Plugins run separately on each node: their own data is not shared yet.
- Folia has no `/scoreboard` and `/team` commands; the shared scoreboard changes through criteria such as
  `deathCount` and a scoreboard carried over from another server.
- Tested with two nodes and a few players so far. Please report problems on
  [GitHub]({{GITHUB}}/issues).
