---
summary: Register your own placeholders from a Velocity plugin and render text with them.
---
Storia Proxy exposes its placeholder registry to plugins through `dev.storia.proxy.api.StoriaPlaceholders`.
Placeholders you register work everywhere the built-in ones do: `storia-proxy.toml`, `/storiaproxy parse` and
other plugins.

## Dependency

The Storia Proxy API is the Velocity API plus the `dev.storia.proxy.api` package. Build Storia Proxy
(see [[building]]) and copy `api/build/libs/velocity-api-<version>.jar` into your plugin project:

```kotlin
dependencies {
    compileOnly(files("libs/velocity-api-4.2.1-SNAPSHOT.jar"))
    annotationProcessor(files("libs/velocity-api-4.2.1-SNAPSHOT.jar"))
}
```

If your plugin should also run on plain Velocity, check that the class exists before using it (see below).

## Registering

```java
import dev.storia.proxy.api.StoriaPlaceholders;

@Subscribe
public void onProxyInitialize(ProxyInitializeEvent event) {
    StoriaPlaceholders placeholders = StoriaPlaceholders.get();

    // {coins}
    placeholders.register("coins", player -> player == null ? "0" : String.valueOf(coins(player)));

    // {team_red}, {team_blue}, ... : everything after the prefix is the argument
    placeholders.registerPrefix("team_", (player, team) -> String.valueOf(teamSize(team)));
}
```

- The resolver receives the **viewing player**, or `null` when there is none (the server list MOTD, the console).
- Return **plain text**. MiniMessage tags in the value are escaped, so player input cannot inject formatting.
- Resolvers may be called often (the tab list refreshes every second). Keep them fast and do not block.

## Rendering

```java
Component line = StoriaPlaceholders.get().render("<gold>{coins} coins</gold> on {player_server}", player);
player.sendMessage(line);
```

| Method | Returns |
| --- | --- |
| `get()` | The registry. Throws `IllegalStateException` before the proxy has started. |
| `register(key, resolver)` | Adds `{key}`. |
| `registerPrefix(prefix, resolver)` | Adds every `{prefix<argument>}`. |
| `unregister(keyOrPrefix)` | Removes a placeholder or prefix you registered. |
| `apply(text, player)` | The text with placeholders replaced, as a `String` (MiniMessage not parsed). |
| `render(text, player)` | The text with placeholders replaced and parsed as MiniMessage, as a `Component`. |
| `describe()` | Every placeholder name with its description. |

## Optional dependency

```java
boolean storia;
try {
    Class.forName("dev.storia.proxy.api.StoriaPlaceholders");
    storia = true;
} catch (ClassNotFoundException e) {
    storia = false;
}
```

Only touch `StoriaPlaceholders` in code that runs when `storia` is `true`.

## Unregistering

Placeholders are not removed automatically when a plugin is disabled. Call `unregister` in your shutdown
handler if your plugin can be reloaded.
