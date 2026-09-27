---
summary: Generate terrain before players get there, using every core, with progress that survives restarts.
---
Generating new terrain is the most expensive thing a Minecraft server does. When players explore, the server
has to generate chunks while they wait. Pregeneration does that work ahead of time, so exploring only loads
chunks that already exist.

## Usage

```text
/storia pregen start <radius> [world] [x z]
```

- `radius`: in **blocks**. The square from −radius to +radius around the center is generated.
- `world`: the world's name. Defaults to the main world (the first one loaded, usually `world`).
- `x z`: the center in block coordinates. Defaults to the world spawn.

```text
/storia pregen start 5000                 5000 blocks around spawn
/storia pregen start 2000 world 8000 0    around x=8000 z=0
/storia pregen status                     progress, chunks/s, ETA
/storia pregen stop                       stop, keep progress
/storia pregen resume                     continue, also after a restart
```

Chunks are generated in a spiral from the center outwards, so the area closest to spawn is ready first.

## Why it is faster

Folia generates chunks on a worker pool that by default uses only about a quarter of your CPU cores, to leave
room for the region tick threads. While `/storia pregen` runs, Storia raises the pool to **all cores but one**
(`pregen.worker-threads: -1`) and keeps enough chunks queued to keep every thread busy
(`pregen.max-in-flight`). When the run finishes or stops, the pool is restored.

| 3,721 chunks (radius 480) on 6 cores | Time | Chunks/s |
| --- | --- | --- |
| Folia default (1 worker thread) | 3m 21s | 18.5 |
| Storia `/storia pregen` (5 worker threads) | 40s | 94 |

Terrain generation itself is also faster in Storia (see [[performance]]).

## Progress and restarts

Progress is saved to `storia-pregen.yml` in the server folder while it runs. If the server stops or crashes,
run `/storia pregen resume` after starting it again. Chunks that were already generated are skipped quickly.

## Tips

- Pregenerate **before** opening the server, or at a quiet time: while it runs, generation uses most of the CPU.
- Set a [world border](https://minecraft.wiki/w/World_border) the same size, so players never leave the
  pregenerated area.
- A radius of 5,000 blocks is about 390,000 chunks, and 10,000 blocks is about 1.56 million. Check disk space
  (and RAM if the [[ram-world]] is on): a generated chunk takes very roughly 5–10 KB.
- For normal play (not pregen), you can raise `chunk-system.worker-threads` in `config/paper-global.yml` if
  your CPU has spare capacity.
