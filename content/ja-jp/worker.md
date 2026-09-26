---
summary: 手伝う側のマシンに Storia Worker を用意して、メインサーバーの地形を生成してもらう。
---
**Storia Worker** は、Storia サーバーを特別なモード（`-Dstoria.worker=true`）で起動したもので、ほかの Storia サーバーのために地形を計算するだけです。
**プレイヤー用ポート・query・RCON は開かず**、**ワールドも変更しません**。同じ地形を作るのに必要なワールドの設定を読むだけです。

## 必要なもの

- **Java 25**
- CPU コアは多いほど良い（初期設定ではすべて使います：`offload.threads: -1`）
- メモリ：たいていのワールドならヒープ 2〜4 GB で十分です。`WORKER_MEMORY` で指定します。
- メインサーバー（またはリレー）とポート **25590/TCP** で通信できること

## インストール

1. [ダウンロードページ](/en-us/downloads/) から `storia-worker-{{VERSION}}.zip` を入手して展開します。

    ```text
    storia-worker-{{VERSION}}/
      storia.jar
      storia.yml
      start-worker.sh
      start-worker.bat
      README.md
    ```

2. **ワールドの設定をコピーします。** メインサーバーの `world/level.dat` と `world/datapacks/` フォルダを、`storia.jar` の隣に作った
   `world/` フォルダに入れます。必要なのはこれだけで、リージョンファイルは要りません。

    ```bash
    mkdir -p world
    scp main-server:/srv/storia/world/level.dat world/
    scp -r main-server:/srv/storia/world/datapacks world/
    ```

3. **EULA に同意します。** [Minecraft EULA](https://aka.ms/MinecraftEULA) を読み、同意する場合は：

    ```bash
    echo "eula=true" > eula.txt
    ```

4. `storia.yml` に、メインサーバーと同じ **合言葉を設定** します。

    ```yaml
    offload:
      mode: worker
      secret: "長くてランダムな合言葉"
      bind: 0.0.0.0
      port: 25590
      relay: ""
      threads: -1
      compress: true
    ```

5. **起動します。**

    ```bash
    ./start-worker.sh                    # Linux / macOS
    WORKER_MEMORY=6G ./start-worker.sh   # ヒープを 6 GB にする場合
    ```

    Windows では `start-worker.bat` を実行します。

6. **メインサーバー** の `offload.workers` にワーカーを追加し（[[offload]] を参照）、再起動します。

メインサーバーが接続すると、どのディメンションを受け付けたかがワーカーのログに出ます。ワーカーのコンソールで `/storia offload` を実行すると状態を見られます。

## 待ち受けるか、自分から接続するか

ワーカーの動き方は 2 通りあります。

| | 設定 | 誰が接続するか | ポートを開ける場所 |
| --- | --- | --- | --- |
| **待ち受け**（初期設定） | `relay: ""` | メインサーバーがワーカーに接続 | ワーカー |
| **リレー** | `relay: "relay-host:25590"` | ワーカーがリレーに接続 | リレー |

ワーカーが NAT の内側にある、よく入れ替わる、複数のサーバーでワーカーを共有する、といった場合はリレーを使います。[[relay]] を参照してください。

## ワーカーを同じ状態に保つ {#keeping-the-worker-in-sync}

ワーカーは、メインサーバーと **まったく同じ** 地形を作る必要があります。次のことをしたら、

- シードやワールド生成の設定を変えた
- ワールド生成に関わるデータパックを追加・削除・更新した
- メインサーバーの Storia を更新した

`level.dat` と `datapacks/` をもう一度コピーし、ワーカーの `storia.jar` も **同じバージョン** にしてください。違っていると、ワーカーは該当する
ディメンションを断り（ログに `terrain differs: check seed, datapacks and Storia build` と出ます）、メインサーバーが自分で生成します。
何も壊れませんが、分担されなくなります。

## サービスとして動かす（Linux）

```ini
# /etc/systemd/system/storia-worker.service
[Unit]
Description=Storia Worker
After=network-online.target

[Service]
User=minecraft
WorkingDirectory=/srv/storia-worker
Environment=WORKER_MEMORY=4G
ExecStart=/srv/storia-worker/start-worker.sh
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable --now storia-worker
journalctl -u storia-worker -f
```

## 止める

コンソールで `stop` と入力するか、サービスを止めます。処理中の依頼は返却され、そのチャンクはメインサーバーが自分で生成します。
