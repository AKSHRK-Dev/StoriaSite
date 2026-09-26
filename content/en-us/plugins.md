---
summary: Which plugins work on Storia, and what plugin developers need to know.
---
Storia uses Folia's threading model, so **only plugins that support Folia work**. A plugin declares support
with this line in its `plugin.yml`:

```yaml
folia-supported: true
```

Plugins without it are refused at startup, exactly as on Folia. This protects your server: a plugin written for
single-threaded Paper would corrupt data or crash on a multithreaded server.

## Finding compatible plugins

- Look for "Folia" in the plugin's description or supported platforms on [Hangar](https://hangar.papermc.io),
  [Modrinth](https://modrinth.com/plugins?g=categories:folia) or SpigotMC.
- Many popular plugins support Folia: LuckPerms, spark, Chunky, CoreProtect (recent versions), and others.
- Storia also reports itself as Folia-compatible: `ServerBuildInfo#isBrandCompatible(Key.key("papermc", "folia"))`
  returns `true`, so plugins that check for Folia behave as they would on Folia.

!!! tip "Chunky"
    Chunky works on Storia, but `/storia pregen` is usually faster, because it raises the chunk worker pool to all
    cores but one while it runs. See [[pregeneration]].

## For plugin developers

Build against the **Folia API** (or Paper API, avoiding what Folia does not support). Everything Folia requires
applies to Storia:

- Use the region-aware schedulers: `Bukkit.getRegionScheduler()`, `Bukkit.getGlobalRegionScheduler()`,
  `entity.getScheduler()` and `Bukkit.getAsyncScheduler()`, not `BukkitScheduler`.
- Only touch a chunk, block or entity from the thread that owns it. Use `Bukkit.isOwnedByCurrentRegion(...)` to check.
- Teleport with `teleportAsync`.

See [Folia's documentation](https://docs.papermc.io/folia) for the full guide.

### Detecting Storia

```java
ServerBuildInfo info = ServerBuildInfo.buildInfo();
boolean storia = info.brandId().equals(Key.key("storia", "storia"));
boolean foliaLike = info.isBrandCompatible(Key.key("papermc", "folia"));   // true on Folia and Storia
```

### Player view distance

The [[player-budget]] changes players' view distance (and, only if enabled, simulation distance) through the same
per-player mechanism as `Player#setViewDistance`. If your plugin sets per-player distances too, the two will
override each other. Disable the budget, or leave distances to Storia.
