---
summary: Keep worlds in RAM so disk I/O never slows the server down, with background syncing and crash recovery.
---
Minecraft reads and writes region files constantly: every chunk that is loaded, generated or changed. On a busy
server, or one on a slow disk, this I/O becomes a bottleneck. With the RAM world, Storia copies your worlds into
RAM when it starts and works from there. The disk is only touched by a background thread that writes changed
files at a fixed interval.

## How it works

1. **Startup.** Storia checks that `ram-directory` (by default `/dev/shm/storia`) has room for all world
   folders plus `min-free-mb`. If it does, the worlds are copied there and the server loads them from RAM.
   If not, it logs an error and loads the worlds from disk, exactly like Paper.
2. **While running.** Every `sync-interval-seconds` (default 300), files that changed since the last sync are
   copied to disk. Each file is written to a temporary file first and then renamed over the old one, so the
   world on disk is never half-written.
3. **Stop.** `stop` saves the world as usual and then writes everything to disk. With `delete-on-shutdown: true`
   the RAM copy is then removed.
4. **Crash of the server process.** The RAM copy survives in `/dev/shm` as long as the machine stays on. On the
   next start Storia detects it (a marker file records the PID) and syncs it to disk before doing anything else.

The level folder (`level-name` in `server.properties`, which in Minecraft {{MC}} holds every dimension) is
handled, together with any older `<level-name>_*` sibling folders that still have a `level.dat`.

!!! warning "Power loss"
    If the **machine** loses power or the operating system crashes, RAM is gone. Changes made since the last
    sync are lost. Lower `sync-interval-seconds` if that matters more to you than disk load, run
    `/storia sync` before risky maintenance, and keep regular backups as always.

## How much RAM do I need?

Free space in `/dev/shm` at least as large as your world folders, **plus** `min-free-mb`, **plus** the Java heap
(`-Xmx`), plus the operating system. Check both:

```bash
du -sh world
df -h /dev/shm
```

On most Linux systems `/dev/shm` may use up to half of physical RAM. To allow more, remount it:

```bash
sudo mount -o remount,size=24G /dev/shm
```

Add a line to `/etc/fstab` to keep the size after a reboot:

```text
tmpfs /dev/shm tmpfs defaults,size=24G 0 0
```

## Windows and macOS

`/dev/shm` only exists on Linux. On other systems point `ram-directory` at a RAM disk you created
(for example with ImDisk on Windows), or set `ram-world.enabled: false`.

## Commands

| Command | Description |
| --- | --- |
| `/storia status` | Where the RAM copy lives, RAM used, time of the last sync. |
| `/storia sync` | Write changes to disk now (in the background). |

## Backups

Back up the **disk** copy, which is always a complete, consistent world as of the last sync. Run `/storia sync`
first if you want the latest state, and wait for the `Synced ... file(s)` message.

## Turning it off

```yaml
ram-world:
  enabled: false
```

Restart the server. The disk copy is up to date after a clean stop, so nothing else is needed.
