---
summary: A small standalone program that shares terrain work between any number of Storia servers and workers.
---
**Storia Relay** sits between Storia servers and Storia Workers. Servers send their terrain requests to the
relay, and the relay hands each one to the least busy worker that can produce matching terrain.

```text
Storia server --\                  /-- Storia Worker A
                 >-- Storia Relay <---- Storia Worker B
Storia server --/                  \-- Storia Worker C   (join / leave any time)
```

Why use one:

- **Workers can join and leave at any time** without changing or restarting the server.
- **Only the relay needs an open port.** Workers connect out, so they can sit behind NAT or a home router.
- **Several servers can share the same workers.** Each request only goes to a worker whose terrain matches that
  server exactly.

The relay is tiny: it needs **Java 21 or newer**, about 256 MB of RAM and **no Minecraft files**.

## Install

1. Download `storia-relay-{{VERSION}}.zip` and unzip it.
2. Run it once. It creates `relay.properties` and exits:

    ```bash
    ./start-relay.sh        # Windows: start-relay.bat
    ```

3. Edit `relay.properties` and set a secret (at least 8 characters, the same everywhere):

    ```properties
    bind=0.0.0.0
    port=25590
    secret=a long random secret
    compress=true
    in-flight-per-thread=4
    timeout-ms=20000
    ```

4. Start it again.

## relay.properties

| Key | Default | Description |
| --- | --- | --- |
| `bind` | `0.0.0.0` | Address to listen on. |
| `port` | `25590` | Port to listen on, for servers and workers alike. |
| `secret` | *(empty)* | Shared secret. The relay refuses to start with fewer than 8 characters. |
| `compress` | `true` | Compress traffic before encryption. |
| `in-flight-per-thread` | `4` | Requests queued per worker thread. |
| `timeout-ms` | `20000` | Give up on a worker's answer after this long and retry elsewhere or return it. |

## Connecting servers and workers

Storia server (`storia.yml`):

```yaml
offload:
  mode: client
  secret: "a long random secret"
  workers:
  - relay.example.lan:25590
```

Each Storia Worker (`storia.yml`):

```yaml
offload:
  mode: worker
  secret: "a long random secret"
  relay: "relay.example.lan:25590"
```

## Console

| Command | Description |
| --- | --- |
| `status` | Connected workers and servers, requests in flight, completed and failed counts. |
| `stop` | Shut the relay down. |

## Failure handling

- If a worker disconnects, its pending requests are retried on another worker with matching terrain.
- If no other worker can take them, they are returned to the server, which generates those chunks itself.
- If the relay itself goes down, servers generate everything locally and reconnect automatically when it is back.

## Running as a service

```ini
# /etc/systemd/system/storia-relay.service
[Unit]
Description=Storia Relay
After=network-online.target

[Service]
User=storia
WorkingDirectory=/srv/storia-relay
ExecStart=/usr/bin/java -Xmx256M -jar storia-relay.jar relay.properties
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

The relay reads commands from standard input, so under systemd use `systemctl stop` to stop it.
