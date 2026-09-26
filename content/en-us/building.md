---
summary: Build Storia, Storia Relay and Storia Proxy from source, and how the patch-based project is organized.
---
## Storia server

Requires **Java 25** (and Java 21, which the build also uses), Git, and a few GB of disk.

```bash
git clone {{GITHUB}}.git
cd Storia
./gradlew applyAllPatches
./gradlew createPaperclipJar
```

The server jar is `folia-server/build/libs/folia-paperclip-*.jar`. The first build downloads and decompiles
Minecraft, which takes a while.

### Project layout

Storia is a [paperweight](https://github.com/PaperMC/paperweight) fork of Folia, which is itself a fork of Paper.
Changes are kept as patches:

| Path | Contents |
| --- | --- |
| `folia-server/src/main/java/dev/storia/` | Storia's own classes (RAM world, pregen, budget, offload, command). |
| `folia-server/minecraft-patches/features/` | Patches to Minecraft's code (`0012-Storia-...`). |
| `folia-server/paper-patches/features/` | Patches to Paper's code. |
| `storia-relay/` | Storia Relay. |
| `packaging/` | Files that go into the worker and relay downloads. |

### Making changes

- **Storia's own classes:** edit `folia-server/src/main/java/dev/storia/` directly.
- **Minecraft code:** edit under `folia-server/src/minecraft/java`, commit there, then:

    ```bash
    ./gradlew rebuildMinecraftFeaturePatches
    ```

- **Paper code:** edit under `paper-server`, commit there, then:

    ```bash
    ./gradlew rebuildPaperServerFeaturePatches
    ```

Commit the updated patch files in the main repository.

## Storia Relay

```bash
./gradlew -p storia-relay jar
# storia-relay/build/libs/storia-relay-*.jar
```

The relay shares the protocol classes in `dev/storia/offload/protocol/` with the server and has no other
dependencies.

## Storia Proxy

```bash
git clone https://github.com/AKSHRK-Dev/StoriaProxy.git
cd StoriaProxy
./gradlew :velocity-proxy:shadowJar
# proxy/build/libs/storia-proxy-*.jar
```

Storia Proxy's additions are in `proxy/src/main/java/com/velocitypowered/proxy/storia/` and
`api/src/main/java/dev/storia/proxy/api/`.

## Releases

Pushing a tag `v*` runs the release workflow on GitHub Actions, which builds all four programs and publishes
them to [GitHub Releases]({{GITHUB}}/releases). Every push also builds a development jar, available as an
artifact on the [Actions]({{GITHUB}}/actions) page.
