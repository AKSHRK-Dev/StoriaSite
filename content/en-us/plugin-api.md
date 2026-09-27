---
summary: Data and messages shared by every worker of a Storia Cluster, for plugin developers. Also works on a single server.
---
In a [[cluster|Storia Cluster]], every [[worker]] runs its own copy of each plugin, so a plugin's files and memory
are separate on each worker. **Storia's plugin API** gives plugins what must be the same everywhere:

- a **key-value store** per plugin, kept by Storia Relay, with compare-and-set, counters and change notifications
  on every worker;
- **messages** to the same plugin on every worker.

On a **single Storia server** (no cluster) the same API works locally: data is kept in `storia-shared/` in the
server folder and messages reach this server. A plugin needs no second code path.

Player data (inventory, position, effects, `PersistentDataContainer` on players), advancements, statistics,
maps and the scoreboard are already shared by the cluster; use the API for the plugin's own data.

## Add the API

Download `storia-api-{{VERSION}}.jar` from the [release]({{GITHUB}}/releases) and add it as a
**compile-only** dependency (the classes are part of the Storia server at runtime):

```kotlin
// build.gradle.kts
dependencies {
    compileOnly("io.papermc.paper:paper-api:{{MC}}.build.+")   // or the Folia API
    compileOnly(files("libs/storia-api-{{VERSION}}.jar"))
}
```

Set `folia-supported: true` in `plugin.yml`, as for any Folia plugin.

## Shared data

```java
import dev.storia.api.SharedStore;
import dev.storia.api.StoriaShared;

SharedStore coins = StoriaShared.get().store("myplugin");   // one namespace per plugin

coins.increment("coins." + uuid, 50)                        // atomic on every worker
     .thenAccept(total -> player.getScheduler().run(this,
         task -> player.sendMessage("You have " + total + " coins"), null));

coins.setString("motd", "Welcome!");
coins.getString("motd").thenAccept(text -> getLogger().info(text));
```

| Method | What it does |
| --- | --- |
| `get(key)` / `getString(key)` | Reads a value (`null` if there is none). |
| `set(key, value)` / `setString(key, text)` | Stores a value; `null` deletes the key. |
| `delete(key)` | Deletes the key. |
| `compareAndSet(key, expected, value)` | Changes the key only if it holds `expected` (`null` = absent). Only one worker can win. |
| `increment(key, delta)` | Adds to a counter kept as decimal text (missing = 0) and returns the new value. |
| `keys(prefix)` | The keys starting with `prefix`, sorted. |
| `listen(listener)` | Called whenever a key of this namespace changes on any worker, including this one. |

- Namespaces: 1 to 64 characters of `a-z 0-9 _ . -`. Use your plugin's name.
- Keys: 1 to 100 bytes of UTF-8. Values: up to 1 MiB.
- Changes are applied in the order the relay receives them, and every worker sees the notifications in that
  order.

### A lock that only one worker gets

```java
store.compareAndSet("event-running", null, nodeName.getBytes())
     .thenAccept(won -> { if (won) startEvent(); });
// ... later
store.delete("event-running");
```

## Messages

```java
StoriaShared shared = StoriaShared.get();
shared.subscribe("myplugin:announce", message ->
    Bukkit.getGlobalRegionScheduler().run(this, task ->
        Bukkit.broadcast(Component.text(message.text()))));

shared.publish("myplugin:announce", "The event starts in 5 minutes!");
```

A message reaches every subscriber of the channel on every worker, **including the one that sent it**, in the order
the relay received it. Channels: 1 to 64 characters of `a-z 0-9 _ . : -`. `message.node()` is the sender.

## Threads

Every call returns a `CompletableFuture` and never blocks. Results, listeners and message handlers run on a Storia
thread, not on a region thread: to touch the world or a player, schedule the work on the right region
(`player.getScheduler()`, `Bukkit.getRegionScheduler()` or `Bukkit.getGlobalRegionScheduler()`). Never call
`join()` on a region thread.

An invalid namespace, key or value throws `IllegalArgumentException` at once. If the relay cannot be reached, the
future completes exceptionally; nothing is queued, so handle the failure (retry, or tell the player).

## Where the data is

| Setup | Stored in |
| --- | --- |
| Cluster | `cluster-world/storia-shared/<namespace>/` on Storia Relay (back it up with the world). |
| Single server | `storia-shared/<namespace>/` in the server folder. |

Each key is one file whose name is the key in hex. To move a single server's data into a cluster, copy its
`storia-shared/` folder into the relay's `cluster-world/`.
