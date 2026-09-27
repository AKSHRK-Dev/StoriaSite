---
summary: Storia Cluster のサーバー 1 台分。ワーカーを足すと 1 つのワールドを複数のマシンで動かせ、プレイヤーは読み込み画面なしで移動します。
---
**Storia Worker** は [[cluster|Storia Cluster]] のサーバー 1 台分です。各ワーカーは、自分のプレイヤーがいる場所
（チャンク・モブ・回路・プレイヤー）を動かし、どのワーカーがどこを動かすかは [[relay|Storia Relay]] が決めます。
プレイヤーは Storia Proxy を通してワーカーに入り、読み込み画面なしでワーカー間を移動します。1 台で足りなくなったら、
ワーカーを足してください。

```text
プレイヤー --> Storia Proxy --> Storia Worker A --\
                            \-> Storia Worker B ---> Storia Relay：ワールドと、どこを誰が動かすか
                             \-> Storia Worker C --/
```

ワーカーは普通の Storia サーバーと同じものです。普通の Storia サーバーと同じくらいの CPU と RAM を用意してください。
ワーカーは**自分のワールドを持ちません**。チャンクは Relay から読み書きします。

## 導入

1. `storia-worker-{{VERSION}}.zip` をダウンロードして展開します。Java 25 が必要です。
2. [Minecraft EULA](https://aka.ms/MinecraftEULA) を読み、同意する場合は `eula=true` と書いた `eula.txt` を作ります。
3. `storia.yml` で Relay を指定します。

    ```yaml
    cluster:
      enabled: true
      coordinator: "relay-host:25590"
      node-name: worker-1        # ワーカーごとに別の名前。velocity.toml の名前と同じにする
      secret: "Relay と同じ合言葉"
    ```

4. 一度起動します：`./start-worker.sh`（Windows は `start-worker.bat`）。メモリは `WORKER_MEMORY=8G ./start-worker.sh`。
   初回起動時に、ワーカーは **Relay からワールドの設定を取り寄せます**（`level.dat`、ワールド生成の設定、データパック）。
   ワールドを自分でコピーする必要はありません。
5. ワーカーは Velocity のバックエンドです。`config/paper-global.yml` で `proxies.velocity.enabled: true` にし、
   `proxies.velocity.secret` をプロキシの `forwarding.secret` にして再起動します。同梱の `server.properties` は
   `online-mode=false` になっています。
6. Storia Proxy の `velocity.toml` に、ワーカーを node-name と同じ名前で登録し、`try` にも入れます。

    ```toml
    [servers]
    worker-1 = "10.0.0.11:25565"
    worker-2 = "10.0.0.12:25565"
    try = ["worker-1", "worker-2"]
    ```

ワーカーの `/storia cluster` で、そのワーカーが動かしている場所とプレイヤーが見られます。

## ワーカーの追加と削除

- **追加**：上と同じように新しいワーカーを用意して起動します。数秒で Relay がプレイヤーを割り当て始めます。
- **削除**：ワーカーで `stop` と入力します。先にプレイヤーをほかのワーカーへ移し（キックなし）、保存して止まります。
  そのあと `velocity.toml` から外してください。
- ワーカーが落ちた場合、その場所は Relay が気づくまで（15 秒）止まり、そのあとは最後に保存された状態から別のワーカーが
  動かします。

## 以前のバージョン

26.2-2-beta までの「Storia Worker」は、1 台のサーバーのために新しいチャンクのノイズの段階だけを計算する、地形専用の
手伝い役でした（`storia.yml` の `offload.*`）。このモードは Cluster に置き換わって削除されました。コードは GitHub の
`archive/terrain-offload` ブランチに残しています。
