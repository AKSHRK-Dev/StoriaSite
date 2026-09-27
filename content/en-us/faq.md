---
summary: Answers to common questions and fixes for common problems.
---
## General

### Is Storia free?

Yes. Storia is open source, like Paper, Folia and Velocity, which it is built on. The source is on
[GitHub]({{GITHUB}}).

### Which Minecraft version does Storia support?

Minecraft **{{MC}}**, Java Edition. Storia follows Folia's supported versions.

### What do the version numbers mean?

Storia versions follow Minecraft. `26.2` is the first Storia release for Minecraft 26.2; later builds for the same
Minecraft version are `26.2-2`, `26.2-3`, and so on. Always run the **same version** on the workers, the relay and
Storia Proxy.

### Can I use Storia for a small server?

You can, but Folia's threading model mainly pays off with many players spread across the world. For a small
server, or one that depends on Paper-only plugins, Paper is simpler.

### Does Storia change vanilla behavior?

Storia's own changes keep vanilla results (terrain, entity physics, redstone). Folia, which Storia is built on,
does behave differently from single-threaded servers in some edge cases, for example contraptions that span
regions. See the [Folia README](https://github.com/PaperMC/Folia).

## RAM world

### The log says "Not enough space ... loading worlds from disk instead"

`/dev/shm` does not have room for the world plus `min-free-mb`. Check with `df -h /dev/shm`, and see
[[ram-world#how-much-ram-do-i-need]] to make it larger. The server works normally from disk meanwhile.

### The log says "Found RAM world left by a previous run"

The server process was killed without a clean shutdown. Storia is recovering the RAM copy to disk, which is
exactly what should happen. Nothing to do.

### How do I back up a server running from RAM?

Back up the disk copy, after `/storia sync` if you want the newest state. See [[ram-world#backups]].

## Performance

### Spawn is laggy because of someone else's farm. Will I be slowed down?

No. The [[tick-guard]] thins out the crowd's AI in the crowded chunks until the region is back under its target,
and players standing nearby are not limited. `/storia region` shows the crowded chunks, so you can find the farm.

### Players' view distance drops sometimes. Why?

The [[player-budget]] shortens the view distance of players who move very fast (elytra, ...) while their region
is over budget, and restores it when they slow down. `/storia budget` shows each player's speed. Players who
stand or walk are never limited. To disable it, set `player-budget.enabled: false`.

### Chunk generation is slow during normal play

Pregenerate with `/storia pregen` (see [[pregeneration]]), raise `chunk-system.worker-threads` in
`config/paper-global.yml`, or spread players over several machines with a [[cluster]].

## Storia Cluster

### A worker stops with "Cannot reach the cluster coordinator"

- Is the relay running, and is port 25590 reachable from the worker (`nc -zv relay-host 25590`)?
- Is the **secret identical** on the worker and the relay? A wrong secret is refused on the first message.
- Are both running the **same Storia release**? Different protocol versions are refused with a message saying so.

### The relay logs "an old Storia asked for terrain offload"

A server with an `offload:` section from 26.2-2-beta or earlier connected. Terrain offload was replaced by the
cluster: update Storia on that machine and set up `cluster:` instead (see [[worker]]).

### Players see a short loading screen when moving between workers

Seamless moves need Minecraft 26.1 or 26.2 clients. Older clients through ViaVersion get a normal server switch.

## Storia Proxy

### Placeholders show up as `{name}`

The name is unknown: check the spelling with `/storiaproxy placeholders`. For server placeholders, `<server>` must
match a name in `[servers]` in `velocity.toml` exactly.

### Player placeholders are empty in the MOTD

The server list is shown before a player joins, so there is no player to describe. Use proxy and server
placeholders there.

## Getting help

Open an issue on [GitHub]({{GITHUB}}/issues). Please include your Storia version (`/storia status`), the relevant
part of `logs/latest.log`, and your `storia.yml` **without the secret**.
