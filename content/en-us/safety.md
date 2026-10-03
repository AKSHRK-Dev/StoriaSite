---
summary: What changes when you install Storia and what does not, covering how your data is handled, the effect on players, and compatibility with vanilla and plugins.
---
This page collects what you may want to know before installing Storia. In short: Storia's own features are built
to give **the same results as vanilla**, and your world stays in the **normal Minecraft format**. You can go back
to Paper or Folia at any time.

## At a glance

| Question | Answer |
| --- | --- |
| Is the world stored in a custom format? | No. It stays in the normal Anvil format (region files). |
| Can I go back to Paper, Folia or vanilla? | Yes. Use the world folder as it is. |
| Does terrain change? | No. The same seed gives exactly the same terrain as vanilla. |
| What about redstone and mobs? | Storia's own changes keep vanilla results. Differences come from Folia, which Storia is based on. |
| Is player data sent anywhere? | No. Only anonymous statistics such as the server count are sent (bStats), and you can turn them off. |
| Do my plugins work? | Only **Folia-compatible plugins** work. |

## How your data is handled

### World and player data

- The world, player data, advancements and statistics are saved **in the normal Minecraft format and places**.
  If you stop using Storia, take the world folder to Paper or any other server as it is.
- In a [[cluster|Storia Cluster]] the world lives in the relay's `cluster-world/`, also in the normal format. To
  leave the cluster, put that folder on a single Storia server.
- Files are written to a temporary file first and then swapped in, so a crash never leaves a **half-written file**.

### What is sent to the internet

Player names, IP addresses, chat and world contents are **never sent anywhere**. Only these two are sent:

| What | Contents | How to turn it off |
| --- | --- | --- |
| [bStats](https://bstats.org) statistics | Server and player counts, Storia, Minecraft and Java versions, OS, CPU core count, single server or cluster, and whether the RAM world is on. All **anonymous**, sent every 30 minutes | Server: `enabled: false` in `plugins/bStats/config.yml`. Proxy: `enabled=false` in `plugins/bStats/config.txt` |
| Version check | Only when you run `/version`, asks GitHub whether a newer release exists | Nothing is sent unless you run it |

The statistics are public: [Storia](https://bstats.org/plugin/bukkit/Storia/34364) and
[Storia Proxy](https://bstats.org/plugin/velocity/StoriaProxy/34365). Up to 26.2-4 they were reported as Folia and
Velocity. Storia Relay sends nothing.

### Cluster traffic

- All traffic between workers, the relay and the proxy is **encrypted and authenticated** with your `secret`
  (AES-256-GCM). The secret itself is never sent. See [[security]].
- This traffic carries the whole world, including chunks, inventories and positions. Run the relay and the workers on
  **machines you control**.

### Shared plugin data

Data shared through the [[plugin-api|plugin API]] is stored as plain files on the relay (or in `storia-shared/` on a
single server), **not encrypted**. Plugins should encrypt secrets such as passwords themselves.

## When something fails

| What happened | What you get |
| --- | --- |
| The server process crashed | Changes since the last autosave are lost, as on any server. A RAM world is recovered from the copy in RAM on the next start. |
| **The machine lost power** (with RAM world) | RAM is cleared and changes **since the last sync** are lost. The sync interval is `ram-world.sync-interval-seconds` (5 minutes by default). |
| The relay stopped (cluster) | Workers keep running, keep their writes in `cluster-spool/` and send them when the relay is back. New players cannot log in meanwhile. |
| The relay's machine or disk failed (cluster) | With a [[relay#standby|standby relay]], `promote` takes over; every write that was confirmed is on the standby too. Without one, restore from a backup. |
| One worker stopped (cluster) | Its players are disconnected. The world is on the relay, so they can rejoin on another worker. `/stop` moves players to other workers first, so they are not disconnected. |
| Player data could not be read from the relay (cluster) | The login is refused. Storia never overwrites the player with empty data and loses their items. |

In every case you still need **regular backups**. Back up the world on disk (the relay's `cluster-world/` in a
cluster).

## Effect on players

### What does not change

- **No client mods are needed.** Players join with a normal Minecraft {{MC}} client.
- **Terrain, blocks, items, combat and crafting** are the same as vanilla. The faster world generation has been
  checked to give bit-for-bit the same results as vanilla.
- In a cluster, players close to each other always run on **the same server**. People playing together are never
  split between servers.

### What changes (only when busy)

| Feature | When | What players notice | To turn it off |
| --- | --- | --- | --- |
| [[tick-guard]] | One place is too busy | Crowded mobs (16 or more in a chunk) react a little later. Mobs within 8 blocks of a player are unchanged. | `tick-guard.enabled: false` |
| [[player-budget]] | Moving fast (elytra and so on) in a busy place | That player's view distance gets shorter and comes back when they slow down. | `player-budget.enabled: false` |
| Memory guard ([[player-budget]]) | Java heap above 85% | Everyone's view distance goes down one step at a time. | `player-budget.enabled: false` |
| Cluster moves | Moving between workers | Nothing on 26.1 and 26.2 clients. Older clients through ViaVersion may see a short loading screen. | Do not use the cluster |

When the server has room to spare, none of these do anything.

## Compatibility with vanilla

### Storia's own changes

Every change Storia adds is built to keep **vanilla results**:

- **Faster world generation**: the same seed gives the same terrain and structures.
- **Faster entity pushing**: pushing gives the same results.
- **Tick Guard**: never touches blocks (redstone, pistons, hoppers, crops). When a place is too busy it only makes
  crowded mobs rethink their next action less often. Movement, gravity, water flow and collisions run every tick.

### Differences inherited from Folia

Storia is a fork of Folia, so it keeps Folia's differences from vanilla. The main ones:

- The world is split into "regions" that run in parallel, so **the order of work in distant places** may differ
  from vanilla. You will rarely notice this in normal play, but very long contraptions that span distant places may
  behave differently.
- Some commands, such as `/scoreboard` and `/team`, are not available.
- See [Folia's README](https://github.com/PaperMC/Folia) for details.

### Differences in a cluster

- Plugins run separately on each worker. Use the [[plugin-api|plugin API]] to share their data.
- Time, weather, game rules, the scoreboard and maps are shared by all workers. See [[cluster]].

## Compatibility with plugins

- Only **Folia-compatible plugins** (`folia-supported: true` in `plugin.yml`) work. Paper-only plugins do not.
- A Folia-compatible plugin needs no changes for Storia.
- See [[plugins]].

## Trying Storia safely

1. **Back up** your current world.
2. Start Storia on a copy of the world and check that your plugins and contraptions work.
3. If all is well, move to production. If not, take the world back to your old server as it is.

If you find anything odd, please tell us on [GitHub]({{GITHUB}}/issues).
