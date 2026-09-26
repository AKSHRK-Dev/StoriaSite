---
summary: The physics and world generation optimizations in Storia, how they are verified, and settings worth tuning.
---
Storia's optimizations follow one rule: **the result must be exactly what vanilla would produce.** Each one is
checked against the original code, and none of them touches redstone.

## Entity pushing

When many mobs or items are crammed together, most of the tick is spent on *pushing*: every entity looks for the
entities it overlaps and pushes them away. Storia finds those entities with a faster query that skips work
vanilla repeats for every entity, while keeping:

- the **same entities**, in the **same order**, pushed with the same forces,
- the **same cramming damage** (`maxEntityCramming`), including its random roll.

| 2,000 crammed chickens + 2,000 spread out + 2,000 items, one region | MSPT |
| --- | --- |
| Folia | 750 |
| Storia | 252 |

Verified with `-Dstoria.verifyPush=true`, which also computes every push the vanilla way and compares:
500,000 checks with cramming on and off, 0 differences.

## World generation

Terrain generation spends most of its time sampling noise and counting blocks. Storia speeds up:

- **Perlin noise:** integer permutation tables and precomputed gradient tables, fewer divisions per sample.
- **Octave noise:** precomputed amplitudes and multiplication instead of division.
- **Block counting in chunk sections:** counts blocks by palette index in a tight loop instead of decoding every block state.

The terrain is **identical to vanilla** for the same seed: 18 million noise outputs were compared bit for bit with
the original code. Existing worlds and seed maps stay valid.

## Crowds

A crowded spot (a mob farm, a villager hall) used to slow down everyone in the same region. The [[tick-guard]]
now thins out the crowd's AI only while the region is overloaded, and never touches blocks or redstone.

## Redstone

Storia does **not** change redstone, pistons, hoppers or block updates. The [[player-budget]] never lowers
the simulation distance unless you ask it to. If a contraption behaves differently on Storia than on Folia,
please [open an issue]({{GITHUB}}/issues).

Folia itself behaves differently from single-threaded Paper in a few places (for example, contraptions that
span two regions tick independently). See the [Folia README](https://github.com/PaperMC/Folia) for details.

## Settings worth tuning

### Distances

In `server.properties`:

```properties
view-distance=12
simulation-distance=8
```

Simulation distance costs far more CPU than view distance. A gap between the two also gives the
[[player-budget]] room to work.

### Chunk worker threads

`/storia pregen` raises the chunk workers automatically, but during normal play Folia uses only about a quarter
of your cores for chunk generation and loading. If players explore a lot and your CPU has spare cores, raise it in
`config/paper-global.yml`:

```yaml
chunk-system:
  worker-threads: 4
```

### Region threads

Folia's region tick thread count is `threaded-regions.threads` in `config/paper-global.yml`. `-1` picks a
default from your core count. Tick threads and chunk worker threads share the same cores, so avoid giving both
all of them.

### Java flags

Aikar's flags work well with Storia. For heaps of 12 GB and above, consider ZGC:

```bash
java -Xms16G -Xmx16G -XX:+UseZGC -jar storia-{{VERSION}}.jar nogui
```

## Measuring

| Command | Shows |
| --- | --- |
| `/storia region` | Busiest regions: thread usage, MSPT, TPS, players, chunks. |
| `/storia budget` | Tick thread load per player. |
| `/tps`, `/mspt` | Folia's per-region numbers. |
| [spark](https://spark.lucko.me) | CPU profiles (use a Folia-compatible build). |
