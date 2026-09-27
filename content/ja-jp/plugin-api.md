---
summary: Storia Cluster のすべてのワーカーで共有するデータとメッセージ。プラグイン開発者向け。単体のサーバーでも動きます。
---
[[cluster|Storia Cluster]] では、各 [[worker]] がそれぞれプラグインを動かすので、プラグインのファイルやメモリは
ワーカーごとに別々です。**Storia のプラグイン API** は、どのワーカーでも同じであるべきものを扱います。

- プラグインごとの **キーと値のストア**。Storia Relay が保管し、比較して入れ替え（CAS）、カウンター、すべてのワーカーへの
  変更通知があります。
- すべてのワーカーの同じプラグインへの **メッセージ**。

**単体の Storia サーバー**（Cluster なし）でも同じ API が動きます。データはサーバーフォルダの `storia-shared/` に保存され、
メッセージはそのサーバーに届きます。プラグインを 2 通り書き分ける必要はありません。

プレイヤーデータ（インベントリ・位置・効果・プレイヤーの `PersistentDataContainer`）、進捗、統計、地図、スコアボードは、
すでに Cluster が共有しています。API はプラグイン自身のデータに使ってください。

## API を追加する

[リリース]({{GITHUB}}/releases) から `storia-api-{{VERSION}}.jar` をダウンロードし、**compileOnly** の依存に
追加します（実行時のクラスは Storia サーバーに入っています）。

```kotlin
// build.gradle.kts
dependencies {
    compileOnly("io.papermc.paper:paper-api:{{MC}}.build.+")   // または Folia の API
    compileOnly(files("libs/storia-api-{{VERSION}}.jar"))
}
```

ほかの Folia 用プラグインと同じく、`plugin.yml` に `folia-supported: true` を書きます。

## 共有データ

```java
import dev.storia.api.SharedStore;
import dev.storia.api.StoriaShared;

SharedStore coins = StoriaShared.get().store("myplugin");   // プラグインごとに 1 つの名前空間

coins.increment("coins." + uuid, 50)                        // どのワーカーからでも正確に加算
     .thenAccept(total -> player.getScheduler().run(this,
         task -> player.sendMessage("所持コイン：" + total), null));

coins.setString("motd", "ようこそ！");
coins.getString("motd").thenAccept(text -> getLogger().info(text));
```

| メソッド | 内容 |
| --- | --- |
| `get(key)` / `getString(key)` | 値を読みます（なければ `null`）。 |
| `set(key, value)` / `setString(key, text)` | 値を保存します。`null` ならキーを削除します。 |
| `delete(key)` | キーを削除します。 |
| `compareAndSet(key, expected, value)` | キーが `expected`（`null` = 存在しない）のときだけ変更します。成功するのは 1 台だけです。 |
| `increment(key, delta)` | 10 進数の文字列で保存したカウンター（なければ 0）に加算し、新しい値を返します。 |
| `keys(prefix)` | `prefix` で始まるキーを並べて返します。 |
| `listen(listener)` | この名前空間のキーが、どのワーカーで（自分も含めて）変わっても呼ばれます。 |

- 名前空間：`a-z 0-9 _ . -` の 1〜64 文字。プラグイン名を使ってください。
- キー：UTF-8 で 1〜100 バイト。値：1 MiB まで。
- 変更は Relay が受け取った順に反映され、通知もどのワーカーでもその順に届きます。

### 1 台だけが取れるロック

```java
store.compareAndSet("event-running", null, nodeName.getBytes())
     .thenAccept(won -> { if (won) startEvent(); });
// ... あとで
store.delete("event-running");
```

## メッセージ

```java
StoriaShared shared = StoriaShared.get();
shared.subscribe("myplugin:announce", message ->
    Bukkit.getGlobalRegionScheduler().run(this, task ->
        Bukkit.broadcast(Component.text(message.text()))));

shared.publish("myplugin:announce", "5 分後にイベントが始まります！");
```

メッセージは、すべてのワーカーのそのチャンネルの購読者に、**送ったワーカー自身も含めて**、Relay が受け取った順に届きます。
チャンネルは `a-z 0-9 _ . : -` の 1〜64 文字。`message.node()` は送り主です。

## スレッド

どの呼び出しも `CompletableFuture` を返し、待たされることはありません。結果・リスナー・メッセージの処理は Storia の
スレッドで動き、リージョンのスレッドではありません。ワールドやプレイヤーを触るときは、正しいリージョンに処理を
予約してください（`player.getScheduler()`、`Bukkit.getRegionScheduler()`、`Bukkit.getGlobalRegionScheduler()`）。
リージョンのスレッドで `join()` を呼ばないでください。

名前空間・キー・値が不正なときは、その場で `IllegalArgumentException` になります。Relay に届かないときは future が
失敗で終わります。自動で溜めて送り直すことはしないので、失敗を扱ってください（再試行やプレイヤーへの案内など）。

## データの保存場所

| 構成 | 保存場所 |
| --- | --- |
| Cluster | Storia Relay の `cluster-world/storia-shared/<名前空間>/`（ワールドと一緒にバックアップ）。 |
| 単体のサーバー | サーバーフォルダの `storia-shared/<名前空間>/`。 |

キー 1 つが 1 ファイルで、ファイル名はキーを 16 進数にしたものです。単体サーバーのデータを Cluster に移すときは、
`storia-shared/` フォルダを Relay の `cluster-world/` にコピーしてください。
