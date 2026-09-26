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
Minecraft version are `26.2-2`, `26.2-3`, and so on. Always run the **same version** on the server, the workers and
the relay.

### Can I use Storia for a small server?

You can, but Folia's threading model mainly pays off with many players spread across the world. For a small
server, or one that depends on Paper-only plugins, Paper is simpler.

### Does Storia change vanilla behaviour?

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

### Players' view distance drops sometimes. Why?

That is the [[player-budget]] limiting a region that is lagging or using more than its share while the server is
busy. `/storia budget` shows which region and why. The simulation distance is not changed, so farms keep
working. To disable it, set `player-budget.enabled: false`.

### Chunk generation is slow during normal play

Pregenerate with `/storia pregen` (see [[pregeneration]]), raise `chunk-system.worker-threads` in
`config/paper-global.yml`, or add [[worker]]s.

## Offload

### `/storia offload` shows "disconnected"

- Is the worker running, and is its port reachable from the server (`nc -zv worker-host 25590`, with your port)?
- Is the **secret identical** on both sides? A wrong secret is refused on the first message and logged.
- Are both running the **same Storia release**? Different protocol versions are refused with a message saying so.

### The worker refuses a dimension: "terrain differs"

The worker's `level.dat`, datapacks or Storia version do not match the server. Copy `level.dat` and `datapacks/`
again and use the same Storia release. See [[worker#keeping-the-worker-in-sync]].

### The worker refuses a dimension: "no such dimension here"

The server has a dimension (for example from a datapack or a plugin-created world) that the worker does not.
Chunks in it are generated locally.

### Most chunks are "generated locally (workers busy)"

Your workers are at capacity. Add workers, give them more threads, or raise `offload.max-in-flight`.

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
