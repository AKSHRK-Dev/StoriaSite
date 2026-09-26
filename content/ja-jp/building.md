---
summary: Storia・Storia Relay・Storia Proxy をソースからビルドする方法と、パッチ形式のプロジェクトの構成。
---
## Storia サーバー

**Java 25**（ビルドでは Java 21 も使います）、Git、数 GB のディスクが必要です。

```bash
git clone {{GITHUB}}.git
cd Storia
./gradlew applyAllPatches
./gradlew createPaperclipJar
```

サーバーの jar は `folia-server/build/libs/folia-paperclip-*.jar` にできます。初回は Minecraft のダウンロードと逆コンパイルがあるので時間がかかります。

### プロジェクトの構成

Storia は、Paper のフォークである Folia を、[paperweight](https://github.com/PaperMC/paperweight) でさらにフォークしたものです。変更はパッチとして管理しています。

| 場所 | 中身 |
| --- | --- |
| `folia-server/src/main/java/dev/storia/` | Storia 独自のクラス（RAM ワールド、事前生成、予算、分担、コマンド）。 |
| `folia-server/minecraft-patches/features/` | Minecraft のコードへのパッチ（`0012-Storia-...`）。 |
| `folia-server/paper-patches/features/` | Paper のコードへのパッチ。 |
| `storia-relay/` | Storia Relay。 |
| `packaging/` | ワーカーとリレーのダウンロードに入れるファイル。 |

### 変更の仕方

- **Storia 独自のクラス：** `folia-server/src/main/java/dev/storia/` を直接編集します。
- **Minecraft のコード：** `folia-server/src/minecraft/java` の中を編集してそこでコミットし、次を実行します。

    ```bash
    ./gradlew rebuildMinecraftFeaturePatches
    ```

- **Paper のコード：** `paper-server` の中を編集してそこでコミットし、次を実行します。

    ```bash
    ./gradlew rebuildPaperServerFeaturePatches
    ```

更新されたパッチファイルを、メインのリポジトリにコミットします。

## Storia Relay

```bash
./gradlew -p storia-relay jar
# storia-relay/build/libs/storia-relay-*.jar
```

リレーは、サーバーと共通の `dev/storia/offload/protocol/` のクラスを使い、ほかに依存するものはありません。

## Storia Proxy

```bash
git clone https://github.com/AKSHRK-Dev/StoriaProxy.git
cd StoriaProxy
./gradlew :velocity-proxy:shadowJar
# proxy/build/libs/storia-proxy-*.jar
```

Storia Proxy で追加した部分は `proxy/src/main/java/com/velocitypowered/proxy/storia/` と `api/src/main/java/dev/storia/proxy/api/` にあります。

## リリース

`v*` のタグを push すると GitHub Actions のリリース用ワークフローが動き、4 つのソフトをすべてビルドして
[GitHub Releases]({{GITHUB}}/releases) に公開します。また push のたびに開発版の jar がビルドされ、[Actions]({{GITHUB}}/actions) のページから入手できます。
