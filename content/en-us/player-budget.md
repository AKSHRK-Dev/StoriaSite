---
summary: Give every player a fair share of the server's CPU, so one player's lag machine never slows down everyone else.
---
Folia already runs each region of the world on its own thread. The **player budget** adds fairness on top:
every player is entitled to an equal share of the region tick threads. If a region's players use much more
than their share, or their region cannot keep up, only **those** players get a lower view distance until the
region recovers. Everyone else keeps playing as if they had the server to themselves.

## When is a player limited?

The budget checks every player every `check-interval-ticks` (5 seconds by default), on that player's own region
thread. A player's region is **over budget** when either:

1. **The region itself lags:** its tick takes longer than `max-region-mspt` (45 ms; a tick has 50 ms), or
2. **The server is full and the region takes more than its share:** the tick threads are more than
   `pool-saturated-percent` (85%) busy, *and* the region uses more of a thread than its players' fair share.

TPS is deliberately **not** used: a region can show low TPS because *other* regions are busy, and punishing it for
that would be unfair.

While the server has headroom, nothing is ever limited, however much a single region uses.

## What happens

For an over-budget region, each check lowers the view distance of the players in it by one chunk, down to the
limit. When the region is back below `recover-below-percent` (70%) of its limits, it is raised one step per check
until it is back at the world's setting.

!!! note "Redstone keeps running"
    By default the **simulation distance is never changed**, so redstone, farms and mobs around players keep
    ticking exactly as before. The view distance is never lowered below the simulation distance, because that
    would stop chunks from ticking too.

This means the budget needs some room between the two distances to work. In `server.properties`:

```properties
view-distance=12
simulation-distance=8
```

With these settings the budget can lower a lagging region's view distance from 12 to 8 and back.

### lower-simulation-distance

```yaml
player-budget:
  lower-simulation-distance: true
  min-simulation-distance: 4
```

This also lowers the simulation distance, **first**, down to `min-simulation-distance`. It saves far more CPU,
but machines and farms further away from the player than the new distance **stop** while it is lowered. Only use
it if your players accept that.

## Memory

Separately from CPU, the budget watches the Java heap **after garbage collection** (not the momentary usage,
which always looks high). Above `memory-high-percent` (85%) everyone's view distance is lowered one step per
check; below `memory-low-percent` (70%) it is raised again. Fewer chunks sent to clients means less memory.

## Inspecting it

```text
/storia budget
```

```text
Player budget (checked every 5s)
Tick threads busy: 91% (saturated: heavy regions are limited)
Share per player: 40% of a thread
Heap after GC: 52%
 Alice: region 38.2 MSPT, 20.0 TPS, 140% thread, 1 player(s) | sim default, view 9
 Bob: region 6.1 MSPT, 20.0 TPS, 20% thread, 2 player(s) | sim default, view default
```

Here Alice's region uses 140% of a thread while each player's share is 40%, and the tick threads are saturated,
so her view distance has been lowered to 9. Bob's region is within its share and keeps the world's settings
(`default`).

`/storia region` lists the busiest regions if you want to find out *what* is using the CPU.

## Settings

See the [player-budget table](/en-us/docs/configuration/#player-budget) in [[configuration]].
To turn it off:

```yaml
player-budget:
  enabled: false
```
