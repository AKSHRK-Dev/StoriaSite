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
| `status` | Workers, the cells each one runs, players, moves, contraption links, reads and writes. |
| `stop` | Stops the relay. |

## When the relay is away

Workers keep running. Writes they cannot send are kept in `cluster-spool/` on their disk, in order, and sent
when the relay is back (also after a worker restart). Workers claim their parts of the world again when they
reconnect. New players cannot join and nobody is moved until the relay is back.

## Settings

| Key | Default | Meaning |
| --- | --- | --- |
| `bind` | `0.0.0.0` | Address to listen on. |
| `port` | `25590` | Port for workers and Storia Proxy. |
| `secret` | *(empty)* | Shared secret, at least 8 characters. Required. |
| `compress` | `true` | Deflate messages before encryption. |
| `cluster-world` | `cluster-world` | The shared world folder. |
