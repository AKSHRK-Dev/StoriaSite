---
summary: Start with one Storia server, and move to a cluster when your players outgrow it. Workers only work with Storia Relay.
---
!!! warning "Workers do not connect to a single Storia server"
    A **Storia Worker** is one server of a **Storia Cluster**. It works only with **Storia Relay**, which holds the
    world. You cannot add a worker to a single Storia server: to use more servers, move the world to a relay first
    (below). Your current server then becomes one of the workers.

## Which setup do I need?

| | Single server | Cluster |
| --- | --- | --- |
| Programs | Storia (plus Storia Proxy if you like) | Storia Relay + two or more Storia Workers + Storia Proxy |
| Where the world is | In the server's `world/` folder | In `cluster-world/` on Storia Relay |
| Good for | Most servers: one machine is enough | One world that has outgrown one machine |
| RAM world | Yes | Not used (the relay stores the world) |
| Plugin data | In each plugin's files | Shared with the [[plugin-api|plugin API]]; each worker has its own copy of plugin files |

Start with a single server. Everything in [[introduction|Storia]] (tick guard, player budget, RAM world,
pregeneration) works there. Move to a cluster when one machine is no longer enough for your players.

```text
Single server:  players --> Storia (the world is here)

Cluster:        players --> Storia Proxy --> Storia Worker A (your old server)
                                         \-> Storia Worker B (new)        --> Storia Relay (the world is here)
```

## Moving from one server to a cluster

!!! tip "Back up first"
    Copy your whole server folder somewhere safe before you start.

1. **Stop your Storia server** with `stop`. With the RAM world, this writes everything to disk.
2. **Set up Storia Relay** (see [[relay]]): unzip `storia-relay-{{VERSION}}.zip`, start it once and set a `secret`
   in `relay.properties`.
3. **Move the world to the relay**: copy your `world/` folder, with everything in it, to the relay's
   `cluster-world/`. If your plugins use the [[plugin-api|plugin API]], also copy `storia-shared/` to
   `cluster-world/storia-shared/`.
4. **Start the relay.** From now on, only the relay writes the world: back up `cluster-world/`.
5. **Turn your old server into a worker**: in its `storia.yml` set

    ```yaml
    cluster:
      enabled: true
      coordinator: "relay-host:25590"
      node-name: worker-1
      secret: "the relay's secret"
    ```

    Rename its old `world/` folder (for example to `world-before-cluster/`) so nobody mistakes it for the live world;
    on the next start the worker fetches the world settings from the relay.
6. **Add more workers** with `storia-worker-{{VERSION}}.zip` (see [[worker]]): no copy of the world is needed.
7. **Put Storia Proxy in front** (see [[proxy]]): list every worker in `velocity.toml` under its node name and set
   `[cluster]` in `storia-proxy.toml`. Workers are Velocity backends (`proxies.velocity` in
   `config/paper-global.yml`, `online-mode=false`).
8. **Copy your plugins and their configuration** to every worker. Each worker runs its own copy of every plugin.

## Plugins

- Player data (inventory, position, effects, advancements, statistics) is shared by the cluster automatically.
- Data that a plugin keeps in its own files (balances, claims, homes, ...) is **separate on each worker** unless the
  plugin uses Storia's [[plugin-api|plugin API]]. Check your important plugins before you move.

## Going back to one server

The relay stores a normal Minecraft world. Stop the proxy, the workers and the relay, then copy `cluster-world/`
back to a single server's `world/` (and `cluster-world/storia-shared/` to `storia-shared/`), and turn
`cluster.enabled` off.

## Common questions

**Can I add a Storia Worker to my single server to make it faster?**
No. A worker runs part of a shared world and needs Storia Relay. (Up to 26.2-2-beta, "Storia Worker" was a
terrain-only helper for a single server; that feature was removed when workers became cluster servers.)

**Do I need a new machine for the relay?**
No. The relay is small; it can run on the same machine as a worker or the proxy. It needs disk space for the world.

**Is there downtime?**
Only while you stop the server, copy the world and start the relay and workers.
