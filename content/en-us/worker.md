---
summary: One server of a Storia Cluster. Add workers to run one world on several machines; players move between them without a loading screen.
---
!!! warning "Not for a single Storia server"
    A worker works only together with Storia Relay; it cannot be added to a single Storia server. To grow from one
    server to several, see [[scaling|From one server to a cluster]].

A **Storia Worker** is one server of a [[cluster|Storia Cluster]]. Each worker runs the part of the world where
its players are (chunks, mobs, redstone and the players themselves), and [[relay|Storia Relay]] decides which
worker runs which part. Players reach the workers through Storia Proxy and move between them without a loading
screen. When your players outgrow one machine, add a worker.

```text
players --> Storia Proxy --> Storia Worker A --\
                         \-> Storia Worker B ---> Storia Relay: the world, who runs what
                          \-> Storia Worker C --/
```

A worker is a full Storia server: give it about the CPU and RAM you would give a normal Storia server. It keeps
**no world of its own**: chunks are read from and written to the relay.

## Install

1. Download `storia-worker-{{VERSION}}.zip` and unzip it. Java 25 is required.
2. Read the [Minecraft EULA](https://aka.ms/MinecraftEULA) and, if you agree, create `eula.txt` with `eula=true`.
3. In `storia.yml`, point the worker at your relay:

    ```yaml
    cluster:
      enabled: true
      coordinator: "relay-host:25590"
      node-name: worker-1        # unique per worker; the same name as in velocity.toml
      secret: "the relay's secret"
    ```

4. Start it once: `./start-worker.sh` (Windows: `start-worker.bat`). Memory: `WORKER_MEMORY=8G ./start-worker.sh`.
   On the first start the worker **fetches the world settings from the relay** (`level.dat`, world generation
   settings, data packs), so you do not copy the world yourself.
5. Workers are Velocity backends: in `config/paper-global.yml` set `proxies.velocity.enabled: true` and
   `proxies.velocity.secret` to the proxy's `forwarding.secret`, then restart. `server.properties` in the package
   already has `online-mode=false`.
6. Add the worker to Storia Proxy's `velocity.toml` under its node name, and to `try`:

    ```toml
    [servers]
    worker-1 = "10.0.0.11:25565"
    worker-2 = "10.0.0.12:25565"
    try = ["worker-1", "worker-2"]
    ```

`/storia cluster` on the worker shows the parts of the world it runs and its players.

## Adding and removing workers

- **Adding**: set up a new worker as above and start it. The relay starts giving it players within seconds.
- **Removing**: type `stop` on the worker. It first moves its players to the other workers (nobody is kicked),
  saves and stops. Remove it from `velocity.toml` afterwards.
- A worker that crashes loses its part of the world only until the relay notices (15 seconds); the part is then
  given to another worker, starting from the last saved state.

## Earlier versions

Up to 26.2-2-beta, "Storia Worker" was a terrain-only helper that computed the noise step of new chunks for one
server (`offload.*` in `storia.yml`). That mode was replaced by the cluster and removed; its code is kept in the
`archive/terrain-offload` branch on GitHub.
