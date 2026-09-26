---
summary: Storia で動くプラグインと、プラグイン開発者が知っておくべきこと。
---
Storia は Folia の並列処理を使っているので、**Folia に対応したプラグインだけが動きます**。プラグインは `plugin.yml` の次の 1 行で対応を示します。

```yaml
folia-supported: true
```

これがないプラグインは、Folia と同じく起動時に読み込まれません。シングルスレッドの Paper 向けに書かれたプラグインは、並列処理のサーバーでは
データを壊したりクラッシュしたりするので、これはサーバーを守るための仕組みです。

## 対応プラグインの探し方

- [Hangar](https://hangar.papermc.io)、[Modrinth](https://modrinth.com/plugins?g=categories:folia)、SpigotMC で、説明や対応プラットフォームに「Folia」とあるものを探します。
- LuckPerms、spark、Chunky、CoreProtect（最近のバージョン）など、多くの有名プラグインが Folia に対応しています。
- Storia は自分を Folia 互換として報告します。`ServerBuildInfo#isBrandCompatible(Key.key("papermc", "folia"))` は `true` を返すので、
  Folia かどうかを確認するプラグインも、Folia 上と同じように動きます。

!!! tip "Chunky"
    Chunky も Storia で動きますが、たいていは `/storia pregen` のほうが速く終わります。実行中はチャンク生成スレッドをコア 1 つを残して
    すべてに増やすからです。[[pregeneration]] を参照してください。

## プラグイン開発者の方へ

**Folia API**（または Paper API のうち Folia が対応している部分）に対してビルドしてください。Folia で必要なことは Storia でもすべて必要です。

- `BukkitScheduler` ではなく、リージョン対応のスケジューラーを使います：`Bukkit.getRegionScheduler()`、`Bukkit.getGlobalRegionScheduler()`、
  `entity.getScheduler()`、`Bukkit.getAsyncScheduler()`。
- チャンク・ブロック・エンティティは、それを担当しているスレッドからだけ触ります。確認には `Bukkit.isOwnedByCurrentRegion(...)` を使います。
- テレポートは `teleportAsync` を使います。

詳しくは [Folia のドキュメント](https://docs.papermc.io/folia) を参照してください。

### Storia かどうかを判定する

```java
ServerBuildInfo info = ServerBuildInfo.buildInfo();
boolean storia = info.brandId().equals(Key.key("storia", "storia"));
boolean foliaLike = info.isBrandCompatible(Key.key("papermc", "folia"));   // Folia でも Storia でも true
```

### プレイヤーの描画距離

[[player-budget]] は、`Player#setViewDistance` と同じプレイヤーごとの仕組みで描画距離（有効にした場合はシミュレーション距離も）を変えます。
プラグインでもプレイヤーごとに距離を設定していると、お互いに上書きし合います。予算機能をオフにするか、距離の管理を Storia に任せてください。
