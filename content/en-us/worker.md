---
summary: Set up Storia Worker on a helper machine to generate terrain for your main server.
---
**Storia Worker** is the Storia server started in a special mode (`-Dstoria.worker=true`) that only computes
terrain for other Storia servers. It opens **no player port**, no query and no RCON, and it **never changes your
world**: it only reads the world settings needed to produce the same terrain.

## Requirements

- **Java 25**.
- CPU cores: the more, the better. By default the worker uses all of them (`offload.threads: -1`).
- Memory: 2–4 GB of heap is plenty for most worlds. Set it with `WORKER_MEMORY`.
- A TCP connection between the worker and the main server (or the relay). The port is **25590** by default and can
  be any port you like (see [[offload#ports]]).

## Install

1. Download `storia-worker-{{VERSION}}.zip` from the [downloads page](/en-us/downloads/) and unzip it:

    ```text
    storia-worker-{{VERSION}}/
      storia.jar
      storia.yml
      start-worker.sh
      start-worker.bat
      README.md
    ```

2. **Copy the world settings.** Copy the main server's world folder into a `world/` folder next to
   `storia.jar`, **without** the chunk folders (`region`, `entities`, `poi`). What is left is small: `level.dat`,
   `datapacks/` and the `data/` folders, which in Minecraft {{MC}} hold the seed and world generation settings.

    ```bash
    rsync -a --exclude region --exclude entities --exclude poi \
      main-server:/srv/storia/world/ world/
    ```

    On Windows, copy the whole world folder and delete the `region`, `entities` and `poi` folders inside
    `world/dimensions/*/*/`.

    !!! warning "Copy the data folders too"
        Copying only `level.dat` is not enough in Minecraft {{MC}}: the seed lives in
        `dimensions/minecraft/overworld/data/minecraft/world_gen_settings.dat`. Without it the worker cannot start.

3. **Accept the EULA.** Read the [Minecraft EULA](https://aka.ms/MinecraftEULA) and, if you agree:

    ```bash
    echo "eula=true" > eula.txt
    ```

4. **Set the secret** in `storia.yml`, identical to the main server's:

    ```yaml
    offload:
      mode: worker
      secret: "a long random secret"
      bind: 0.0.0.0
      port: 25590
      relay: ""
      threads: -1
      compress: true
    ```

5. **Start it:**

    ```bash
    ./start-worker.sh                    # Linux / macOS
    WORKER_MEMORY=6G ./start-worker.sh   # with a 6 GB heap
    ```

    On Windows, run `start-worker.bat`.

6. On the **main server**, add the worker to `offload.workers` (see [[offload]]) and restart it.

When the main server connects, the worker log shows which dimensions were accepted. Run `/storia offload` in the
worker console to see its state.

## Listening or connecting out

A worker works in one of two ways:

| | Setting | Who connects | Open port on |
| --- | --- | --- | --- |
| **Listen** (default) | `relay: ""` | The main server connects to the worker | the worker |
| **Relay** | `relay: "relay-host:25590"` | The worker connects to the relay | the relay |

Use a relay when workers are behind NAT, change often, or when several servers share workers. See [[relay]].

## Keeping the worker in sync

The worker must produce **exactly** the same terrain as the main server. After you:

- change the seed or world generation settings,
- add, remove or update a datapack that affects world generation,
- update Storia on the main server,

copy the world settings again (step 2) and update the worker's `storia.jar` to the **same version**. If they
differ, the worker refuses the affected dimensions (the log says `terrain differs: check seed, datapacks and
Storia build`), and the main server generates them locally. Nothing breaks, it is just not offloaded.

## Running as a service (Linux)

```ini
# /etc/systemd/system/storia-worker.service
[Unit]
Description=Storia Worker
After=network-online.target

[Service]
User=minecraft
WorkingDirectory=/srv/storia-worker
Environment=WORKER_MEMORY=4G
ExecStart=/srv/storia-worker/start-worker.sh
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable --now storia-worker
journalctl -u storia-worker -f
```

## Stopping

Type `stop` in the console or stop the service. Requests in progress are handed back and the main server
generates those chunks itself.
