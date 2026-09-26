---
summary: Velocity プラグインから独自のプレースホルダーを登録し、テキストを表示する。
---
Storia Proxy は、プレースホルダーの登録先を `dev.storia.proxy.api.StoriaPlaceholders` としてプラグインに公開しています。
登録したプレースホルダーは、内蔵のものと同じく `storia-proxy.toml`・`/storiaproxy parse`・ほかのプラグインのどこでも使えます。

## 依存関係

Storia Proxy の API は、Velocity の API に `dev.storia.proxy.api` パッケージを加えたものです。Storia Proxy をビルドし（[[building]] を参照）、
`api/build/libs/velocity-api-<version>.jar` をプラグインのプロジェクトにコピーします。

```kotlin
dependencies {
    compileOnly(files("libs/velocity-api-4.2.1-SNAPSHOT.jar"))
    annotationProcessor(files("libs/velocity-api-4.2.1-SNAPSHOT.jar"))
}
```

普通の Velocity でも動くプラグインにしたい場合は、使う前にクラスがあるか確認してください（下記）。

## 登録する

```java
import dev.storia.proxy.api.StoriaPlaceholders;

@Subscribe
public void onProxyInitialize(ProxyInitializeEvent event) {
    StoriaPlaceholders placeholders = StoriaPlaceholders.get();

    // {coins}
    placeholders.register("coins", player -> player == null ? "0" : String.valueOf(coins(player)));

    // {team_red}、{team_blue} など：接頭辞より後ろが引数になります
    placeholders.registerPrefix("team_", (player, team) -> String.valueOf(teamSize(team)));
}
```

- 値を返す関数には **表示するプレイヤー** が渡されます。いない場合（サーバーリストの MOTD やコンソール）は `null` です。
- **プレーンテキスト** を返してください。値の中の MiniMessage タグはエスケープされるので、プレイヤーの入力で装飾を注入されることはありません。
- この関数は何度も呼ばれます（タブリストは毎秒更新されます）。速く終わるようにし、処理を止めないでください。

## 表示する

```java
Component line = StoriaPlaceholders.get().render("<gold>{coins} コイン</gold>（{player_server}）", player);
player.sendMessage(line);
```

| メソッド | 返すもの |
| --- | --- |
| `get()` | 登録先。プロキシの起動前は `IllegalStateException` を投げます。 |
| `register(key, resolver)` | `{key}` を追加します。 |
| `registerPrefix(prefix, resolver)` | `{prefix<引数>}` をまとめて追加します。 |
| `unregister(keyOrPrefix)` | 自分が登録したプレースホルダーや接頭辞を削除します。 |
| `apply(text, player)` | プレースホルダーを置き換えたテキスト（`String`。MiniMessage は解釈しません）。 |
| `render(text, player)` | プレースホルダーを置き換え、MiniMessage として解釈したもの（`Component`）。 |
| `describe()` | すべてのプレースホルダー名と説明。 |

## 任意の依存にする

```java
boolean storia;
try {
    Class.forName("dev.storia.proxy.api.StoriaPlaceholders");
    storia = true;
} catch (ClassNotFoundException e) {
    storia = false;
}
```

`StoriaPlaceholders` に触れるのは、`storia` が `true` のときに動くコードの中だけにしてください。

## 登録を外す

プラグインが無効になっても、プレースホルダーは自動では消えません。プラグインを再読み込みすることがあるなら、終了処理で `unregister` を呼んでください。
