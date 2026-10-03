---
summary: The coordinator of a Storia Cluster. Stores the shared world and decides which worker runs which part of it.
---
**Storia Relay** is the coordinator of a [[cluster|Storia Cluster]]. It:

- **stores the world** as a normal Minecraft world folder (Anvil region files), plus player data, advancements,
  statistics and shared data such as maps and the scoreboard;
- **hands out the world**: every cell (32 × 32 chunks) is run by one [[worker]] at a time;
- **places players**: players who come close go to the same worker, busy workers hand groups to quiet ones,
  and contraptions on a border keep their cells together;
- **tells Storia Proxy** when a player should move to another worker.

The relay needs **Java 21 or newer**, no Minecraft server, and disk space for the world. It is small; the work
of running the world happens on the workers.

## Install

1. Download `storia-relay-{{VERSION}}.zip` and unzip it.
2. Run it once. It creates `relay.properties` and exits:

    ```bash
    ./start-relay.sh        # Windows: start-relay.bat
    ```

3. Set a secret (see [[security]]) and put your world in `cluster-world/`:

    ```properties
    bind=0.0.0.0
    port=25590
    secret=choose-a-long-secret
    compress=true
    cluster-world=cluster-world
    ```

4. Start it again. From now on **only the relay writes to `cluster-world/`**: back it up from here.

## Console

| Command | What it does |
| --- | --- |
| `status` | Role (active or standby), workers, the cells each one runs, players, moves, contraption links, reads and writes, the standby's state. |
| `promote` | On a standby: take over from the active relay (see "Standby relay" below). |
| `stop` | Stops the relay. |

## When the relay is away

Workers keep running. Writes they cannot send are kept in `cluster-spool/` on their disk, in order, and sent
when the relay is back (also after a worker restart). Workers claim their parts of the world again when they
reconnect. New players cannot join and nobody is moved until the relay is back.

## Standby relay (beta) {#standby}

!!! note "Beta"
    The standby relay is part of Storia **26.2-8-beta** and later.

Run a second relay as a **standby** and it keeps a live copy of everything the active relay stores. If the active
relay's machine or disk is lost, the standby takes over and the world is not lost.

- **No write is lost**: while the standby is in sync, a worker is told "stored" only once the write is on **both**
  relays. A write the active relay never confirmed is sent again by the worker to the new active relay.
- **A standby never stops the active relay**: if it does not answer within 2 s, the active relay goes on without it
  (with a warning). When it is back, it copies the world again and is in sync once more.
- **Taking over is manual**: once you are sure the active relay is gone, type `promote` on the standby's console.
  Workers and Storia Proxy connect to the next relay in their list by themselves and send what they were holding.

### Settings

```properties
# relay.properties of the active relay (relay-a)
role=active
peer=relay-b:25590
```

```properties
# relay.properties of the standby (relay-b); its world can start empty: it gets a full copy first
role=standby
peer=relay-a:25590
```

In each worker's `storia.yml` and in Storia Proxy's `storia-proxy.toml`, list **both relays, in order**:

```yaml
cluster:
  coordinator: "relay-a:25590,relay-b:25590"
```

```toml
[cluster]
coordinator = "relay-a:25590,relay-b:25590"
```

Both relays use the same `secret`. The standby needs as much disk space as the active relay.

### When the active relay is gone

1. Make sure the active relay is really down (its machine is off, its disk failed, ...).
2. Type `promote` on the standby's console.
   - It refuses while the active relay is still running, so the world is never written in two places.
   - It also refuses if it was not in sync, since it might miss recent writes. `promote force` takes over anyway.
3. Workers and Storia Proxy connect to the new active relay within seconds.
4. When the old relay is fixed, just start it: it sees that the other one took over, **becomes the standby by
   itself** and copies the world back.

Each relay keeps its role and term in `relay-state.txt`. Do not edit it while the relay runs.

### Costs

- One extra round trip between the relays per write, and about twice the active relay's outgoing traffic for writes.
- Pregenerating 2,601 chunks on one machine took 59 s without a standby and 71 to 84 s with one, with the relays and
  the worker all sharing that machine's CPU.

## Settings

| Key | Default | Meaning |
| --- | --- | --- |
| `bind` | `0.0.0.0` | Address to listen on. |
| `port` | `25590` | Port for workers and Storia Proxy. |
| `secret` | *(empty)* | Shared secret, at least 8 characters. Required. |
| `compress` | `true` | Deflate messages before encryption. |
| `cluster-world` | `cluster-world` | The shared world folder. |
| `role` | `active` | `active` or `standby`. Once a relay has taken over or stepped down, `relay-state.txt` decides instead. |
| `peer` | *(empty)* | The other relay's `host:port`, when you run a standby. |
