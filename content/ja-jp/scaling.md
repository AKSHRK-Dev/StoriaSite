---
summary: まずは Storia サーバー 1 台で始め、プレイヤーが 1 台に収まらなくなったら Cluster に移ります。Worker は Storia Relay と組み合わせたときだけ動きます。
---
!!! warning "Worker は、単体の Storia サーバーにはつなげません"
    **Storia Worker** は **Storia Cluster** のサーバー 1 台分で、ワールドを保管する **Storia Relay** と組み合わせたときだけ
    動きます。単体の Storia サーバーに Worker を足すことはできません。サーバーを増やすときは、まずワールドを Relay に移します
    （下の手順）。いまのサーバーは、そのままワーカーの 1 台になります。

## どちらの構成にする？

| | 単体のサーバー | Cluster |
| --- | --- | --- |
| 使うソフト | Storia（必要なら Storia Proxy も） | Storia Relay ＋ Storia Worker 2 台以上 ＋ Storia Proxy |
| ワールドの場所 | サーバーの `world/` フォルダ | Storia Relay の `cluster-world/` |
| 向いている場合 | ほとんどのサーバー。マシン 1 台で足りる | 1 つのワールドが、マシン 1 台に収まらなくなった |
| RAM ワールド | 使える | 使わない（ワールドは Relay が保管） |
| プラグインのデータ | 各プラグインのファイル | [[plugin-api|プラグイン API]] で共有。プラグインのファイルはワーカーごとに別 |

まずは単体のサーバーで始めてください。Tick Guard・プレイヤーごとの予算・RAM ワールド・事前生成など
[[introduction|Storia]] の機能は、単体のサーバーで全部使えます。マシン 1 台では足りなくなったら Cluster に移ります。

```text
単体のサーバー：プレイヤー --> Storia（ワールドはここ）

Cluster：      プレイヤー --> Storia Proxy --> Storia Worker A（いままでのサーバー）
                                          \-> Storia Worker B（追加）      --> Storia Relay（ワールドはここ）
```

## 単体のサーバーから Cluster へ移る

!!! tip "先にバックアップ"
    始める前に、サーバーのフォルダを丸ごと安全な場所へコピーしてください。

1. **Storia サーバーを `stop` で止めます。** RAM ワールドの内容は、ここですべてディスクに書き出されます。
2. **Storia Relay を用意します**（[[relay]] を参照）。`storia-relay-{{VERSION}}.zip` を展開して一度起動し、
   `relay.properties` に `secret` を設定します。
3. **ワールドを Relay に移します。** `world/` フォルダを中身ごと、Relay の `cluster-world/` にコピーします。
   [[plugin-api|プラグイン API]] を使っているプラグインがあれば、`storia-shared/` も `cluster-world/storia-shared/` に
   コピーします。
4. **Relay を起動します。** これ以降、ワールドに書き込むのは Relay だけです。バックアップは `cluster-world/` から取ります。
5. **いままでのサーバーをワーカーにします。** `storia.yml` に次を設定します。

    ```yaml
    cluster:
      enabled: true
      coordinator: "relay-host:25590"
      node-name: worker-1
      secret: "Relay と同じ合言葉"
    ```

    古い `world/` フォルダは、今のワールドと間違えないように名前を変えておきます（例：`world-before-cluster/`）。
    次の起動時に、ワーカーは Relay からワールドの設定を取り寄せます。
6. **ワーカーを追加します。** `storia-worker-{{VERSION}}.zip` を使います（[[worker]] を参照）。ワールドのコピーは要りません。
7. **Storia Proxy を前に置きます**（[[proxy]] を参照）。`velocity.toml` に各ワーカーを node-name と同じ名前で登録し、
   `storia-proxy.toml` に `[cluster]` を設定します。ワーカーは Velocity のバックエンドとして設定します
   （`config/paper-global.yml` の `proxies.velocity`、`online-mode=false`）。
8. **プラグインと設定ファイルを、すべてのワーカーにコピーします。** 各ワーカーがそれぞれプラグインを動かします。

## プラグイン

- プレイヤーデータ（インベントリ・位置・効果・進捗・統計）は、Cluster が自動で共有します。
- プラグインが自分のファイルに保存しているデータ（残高・保護範囲・ホームなど）は、そのプラグインが Storia の
  [[plugin-api|プラグイン API]] に対応していない限り、**ワーカーごとに別々**になります。移る前に、大事なプラグインを
  確認してください。

## 単体のサーバーに戻す

Relay が保管しているのは普通の Minecraft のワールドです。プロキシ・ワーカー・Relay を止め、`cluster-world/` を
単体サーバーの `world/` に（`cluster-world/storia-shared/` を `storia-shared/` に）コピーし直し、`cluster.enabled` を
オフにすれば戻せます。

## よくある質問

**単体のサーバーに Storia Worker を足して、速くできますか？**
できません。ワーカーは共有するワールドの一部を動かすもので、Storia Relay が必要です。（26.2-2-beta までの
「Storia Worker」は単体サーバー用の地形生成の手伝い役でしたが、ワーカーが Cluster のサーバーになったときに削除されました。）

**Relay のために新しいマシンが要りますか？**
要りません。Relay は軽いので、ワーカーやプロキシと同じマシンで動かせます。ワールド分のディスクは必要です。

**止まる時間はありますか？**
サーバーを止めてワールドをコピーし、Relay とワーカーを起動するまでの間だけです。
