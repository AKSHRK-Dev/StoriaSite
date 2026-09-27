---
summary: Install Java, download Storia and start your first server, or switch an existing Paper or Folia server.
---
## Requirements

- **Java 25** or newer. Any distribution works; [Eclipse Temurin](https://adoptium.net) is a good default.
- A 64-bit OS: Linux (recommended), Windows or macOS.
- For the [[ram-world]]: free RAM at least as large as your world folder, **in addition to** the Java heap.

Check your Java version:

```bash
java -version
```

## Install

1. Create an empty folder for the server.
2. Download `storia-{{VERSION}}.jar` from the [downloads page](/en-us/downloads/) into it.
3. Start it once:

    ```bash
    java -Xms4G -Xmx8G -jar storia-{{VERSION}}.jar nogui
    ```

4. The server stops and asks you to accept the [Minecraft EULA](https://aka.ms/MinecraftEULA). If you agree,
   open `eula.txt` and change it to `eula=true`.
5. Start it again. When you see `Done`, the server is ready on port 25565.

On first start, Storia creates the usual Paper and Folia files (`server.properties`, `config/paper-global.yml`,
`config/paper-world-defaults.yml`) plus **`storia.yml`**, described in [[configuration]].

!!! tip "Heap size"
    Give the server as much heap as you can spare with `-Xmx`, but leave room for the RAM world
    (it lives outside the heap in `/dev/shm`) and the operating system.

## A start script

For Linux or macOS:

```bash
#!/bin/sh
cd "$(dirname "$0")"
exec java -Xms4G -Xmx8G -jar storia-{{VERSION}}.jar nogui
```

Save it as `start.sh`, then run `chmod +x start.sh` and `./start.sh`.

For Windows, save this as `start.bat`:

```bat
@echo off
java -Xms4G -Xmx8G -jar storia-{{VERSION}}.jar nogui
pause
```

## Switching from Paper or Folia

Storia reads the same world format and config files, so you can switch in place:

1. **Back up the server folder.**
2. Stop the server and replace the Paper or Folia jar with the Storia jar.
3. Make sure every plugin supports Folia (`folia-supported: true` in its `plugin.yml`). Plugins that do not
   are refused at startup. See [[plugins]].
4. Start the server. `storia.yml` is created and the world is copied into RAM.

Going back is just as easy: stop Storia (this writes the RAM world to disk), and start your old jar.

## First steps after starting

```text
/storia status              RAM world state and last sync
/storia pregen start 3000   pregenerate 3000 blocks around spawn
/storia budget              how busy the tick threads are, per player
```

Recommended next reads:

- [[configuration]] for every option in `storia.yml`.
- [[pregeneration]] to generate terrain before players arrive.
- [[cluster]] when your players outgrow one machine.
- [[proxy]] if you run several servers behind one address.

!!! tip "One server is enough to start"
    Everything above is a single Storia server. Storia Worker and Storia Relay are only for a cluster (one world on
    several servers); see [[scaling|From one server to a cluster]] when you need more than one machine.
