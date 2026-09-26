---
summary: Keep a crowded area like spawn smooth for everyone in it, by thinning out the crowd's thinking instead of limiting the players.
---
Players who stand in the same place share the same region, and a region is ticked by one CPU core. When
someone's mob farm or a crowded villager hall at spawn takes more than a tick's worth of time, everyone nearby
used to feel it, even players who had nothing to do with it.

The **tick guard** fixes the cause instead of the symptom. When a region gets too slow, it thins out the most
expensive part of the crowd, the mobs' *decisions*, only where the crowd is. The players in the region are
never limited for it.

## How it works

1. Every region measures its own tick time, continuously.
2. Once a second it counts mobs per chunk. A chunk with at least `crowd-threshold` (16) mobs is **crowded**.
3. If the region's average tick time is above `target-mspt` (40 ms, of the 50 ms a tick may take), mobs in
   crowded chunks re-plan only every 2nd tick. If that is not enough, every 4th, then every 8th tick
   (`max-level`).
4. When the region has headroom again (below 60% of the target), it steps back down to normal.

On the ticks in between, a crowded mob keeps doing what it already decided:

| Every tick (unchanged) | Only on full ticks |
| --- | --- |
| Movement, gravity, water flow, collisions and pushing | Sensing (who can I see?) |
| Walking along the current path | Choosing targets and goals |
| Looking, jumping, running goals already started | Brain updates (villagers, piglins, ...) |

**Blocks are never touched**: redstone, pistons, hoppers, crops and block entities run exactly as before.

### Who is never thinned out

- Mobs within `player-radius` (8) blocks of any player, so fights feel normal.
- Mobs that are targeting a player.
- Pets and other owned animals, and leashed mobs.
- The Ender Dragon and the Wither.

## What it changes, honestly

Only while a region is overloaded, and only in crowded chunks:

- Crowded mobs react a little later: a zombie in a packed pen may notice a new target a few ticks later.
- Farms that depend on mob decisions (for example villager breeding or iron farms) produce somewhat less
  **during** the overload. Farms driven by physics (water streams, drops, crushers) are unaffected.

When the region is not overloaded, nothing is changed at all.

## Measured

A laggy spawn: 600 zombies, 300 villagers and 500 cows in pens, two players standing nearby and one far away.

| | Spawn region | TPS | Players standing nearby |
| --- | --- | --- | --- |
| Without the tick guard | 50–55 ms per tick | 18 | view distance cut to 6 by the old player budget |
| With the tick guard | 32–35 ms per tick | 20.0 | not limited |

The player far away was unaffected in both cases (about 1 ms per tick).

## Finding the cause

```text
/storia region
```

```text
2 region(s), busiest first (last 5s):
 world -329, 71: 66% thread, 32.8 MSPT, 20.0 TPS, 2 player(s), 766 chunks
   tick guard: crowded mobs re-plan every 8 ticks (23993 AI updates skipped/s)
   crowd at 8, 8: 572 mobs, mostly zombie
   crowd at 8, 24: 460 mobs, mostly cow
   crowd at 24, 8: 300 mobs, mostly villager
```

The crowd lines are block coordinates of the chunk center, so you can go and look at what is there.

## Settings

```yaml
tick-guard:
  enabled: true
  target-mspt: 40.0      # keep regions below this (a tick has 50 ms)
  crowd-threshold: 16    # mobs per chunk that count as a crowd
  player-radius: 8.0     # mobs this close to a player always think every tick
  max-level: 3           # thin out down to 1/2^max-level (3 = every 8th tick)
```

When the server's tick threads are saturated and a region uses more than its players' fair share, the target
for that region is lowered to 60%, so one busy area cannot starve everyone else.

See also [[player-budget]] and [[performance]].
