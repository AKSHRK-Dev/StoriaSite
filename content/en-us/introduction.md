---
summary: What Storia is, what it adds to Folia, and which parts make up the project.
---
Storia is Minecraft server software for large communities. It is a fork of
[Folia](https://github.com/PaperMC/Folia), which is itself built on [Paper](https://papermc.io), so it keeps
Folia's **regionized multithreading**: nearby chunks are grouped into independent regions that tick in
parallel on different CPU cores. On top of that, Storia adds features aimed at making a busy server feel like
single player for everyone on it.

*Storia* is Italian for "history". The logo is a row of columns, like the entrance of a museum.

## What Storia adds

| Feature | In one sentence | Docs |
| --- | --- | --- |
| RAM world | Worlds live in RAM and are written to disk in the background. | [[ram-world]] |
| Fast pregeneration | `/storia pregen` uses every core but one and can be resumed. | [[pregeneration]] |
| Tick guard | A crowded spot like spawn stays smooth: the crowd thinks less, the players are not limited. | [[tick-guard]] |
| Per-player budget | Only players who add load themselves (flying fast) get a shorter view distance while it is busy. | [[player-budget]] |
| Faster physics | Entity pushing is about 3× faster with identical results. Redstone is untouched. | [[performance]] |
| Faster world generation | Optimized noise sampling; terrain is identical to vanilla for the same seed. | [[performance]] |
| Storia Cluster (beta) | One world on several servers; players move between them without a loading screen. | [[cluster]] |
| Storia Proxy | A Velocity fork with 50 placeholders for MOTD, tab list and messages. | [[proxy]] |

## Design rules

Everything in Storia follows three rules:

1. **Vanilla results.** The same seed produces the same terrain, and entities are pushed in the same order with
   the same random rolls. Changes to terrain and physics are verified bit for bit against the original code.
2. **Redstone never stops.** No optimization pauses, slows or skips redstone, and by default nothing lowers the
   simulation distance, so farms and machines near players keep running.
3. **Safe fallbacks.** If RAM is short, worlds load from disk. If the cluster's relay is briefly away, workers keep
   running and keep their writes on disk. A feature failing never takes the server down with it.

## The programs

For the full picture of how they connect, see [How Storia works](/en-us/how-it-works/).

| Program | What it does | Java |
| --- | --- | --- |
| **Storia** | The Minecraft server. | 25 |
| **Storia Worker** | One server of a Storia Cluster: runs the part of the world where its players are. | 25 |
| **Storia Relay** | The cluster's coordinator: stores the world and decides which worker runs which part. | 21+ |
| **Storia Proxy** | Velocity with built-in placeholders, tab list and MOTD. | 21+ |

All four are published on the [downloads page](/en-us/downloads/) and on
[GitHub Releases]({{GITHUB}}/releases).

## Is Storia right for my server?

Storia is a good fit when:

- you have many players who spread out (survival, SMP, large towns, skyblock islands),
- your machine has several CPU cores, and
- your plugins support Folia (see [[plugins]]).

If your server is small, or relies on plugins that only support Paper, Paper is the simpler choice. Folia's
threading model changes how plugins must schedule work, and Storia inherits that.

Next: [[getting-started]].
