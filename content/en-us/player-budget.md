---
summary: Players who add load by themselves get a shorter view distance while their region is busy. Everyone else is never limited.
---
The player budget decides **who** should give something back when a region is over budget. Since Storia
26.2-1-beta, the answer is: only the players who are adding load themselves. Players who simply stand, build or
walk in a busy place, like spawn, are never limited.

Load that comes from the place itself (farms, crowds of mobs) is handled by the [[tick-guard]], which thins out
the crowd instead of touching the players.

## Who is limited

A player's view distance is lowered one step per check when **both** are true:

1. **Their region is over budget.** Its tick takes longer than `max-region-mspt` (45 ms), or the server's tick
   threads are saturated (`pool-saturated-percent`, 85%) and the region uses more than its players' fair share.
2. **They are moving fast.** Faster than `fast-mover-speed` (12 blocks per second, above sprinting) on two checks
   in a row: flying with elytra, riding fast, and so on. Moving fast makes the server load, generate and send
   many new chunks.

It is raised again one step per check as soon as they slow down or the region recovers. A single teleport does
not count, because the speed has to hold for two checks.

!!! note "Redstone keeps running"
    By default the **simulation distance is never changed**, so redstone, farms and mobs around players keep
    ticking. The view distance is never lowered below the simulation distance either.

The view distance can only shrink if there is room above the simulation distance. In `server.properties`:

```properties
view-distance=10
simulation-distance=6
```

### lower-simulation-distance

```yaml
player-budget:
  lower-simulation-distance: true
  min-simulation-distance: 4
```

This also lowers the fast mover's simulation distance, **first**. It saves more CPU, but machines further away
from that player than the new distance stop while it is lowered.

## Memory

Separately, the budget watches the Java heap **after garbage collection**. Above `memory-high-percent` (85%)
everyone's view distance is lowered one step per check; below `memory-low-percent` (70%) it is raised again.
Memory is shared by the whole server, so this is the one case where everyone is affected.

## Measured

A laggy spawn with the tick guard switched off, so the region stays over budget. Alice stands still; Bob moves
20 blocks per second.

| Player | Speed | View distance |
| --- | --- | --- |
| Alice | 0 blocks/s | 10, not limited |
| Bob | 20 blocks/s | 10 → 9 → 7 while moving |

## Inspecting it

```text
/storia budget
```

```text
Player budget (checked every 5s)
Tick threads busy: 100% (saturated: busy regions thin out crowds more)
Share per player: 33% of a thread
Heap after GC: 9%
 Alice: region 60.6 MSPT, 16.1 TPS, 98% thread, 2 player(s) | 0 blocks/s | sim default, view default
 Bob: region 60.6 MSPT, 16.1 TPS, 98% thread, 2 player(s) | 20 blocks/s | sim default, view 9
```

## Settings

See the [player-budget table](/en-us/docs/configuration/#player-budget) in [[configuration]]. To turn it off:

```yaml
player-budget:
  enabled: false
```
