---
summary: 何台もの Storia サーバーとワーカーの間で、地形生成の仕事を配る小さな単体プログラム。
---
**Storia Relay** は、Storia サーバーと Storia Worker の間に入るプログラムです。サーバーは地形生成の依頼をリレーに送り、リレーはそれを、
そのサーバーと同じ地形を作れるワーカーのうち一番空いているものに渡します。

```text
Storia サーバー --\                  /-- Storia Worker A
                   >-- Storia Relay <---- Storia Worker B
Storia サーバー --/                  \-- Storia Worker C   （いつでも追加・削除できる）
```

使う理由：

- **ワーカーをいつでも追加・削除できます。** サーバーの設定を変えたり再起動したりする必要はありません。
- **ポートを開けるのはリレーだけです。** ワーカーは自分から接続するので、NAT や家庭用ルーターの内側にあってもかまいません。
- **複数のサーバーで同じワーカーを共有できます。** 依頼は、そのサーバーと地形が完全に一致するワーカーにだけ渡ります。

リレーはとても小さく、**Java 21 以上**、RAM 256 MB ほどで動き、**Minecraft のファイルは不要** です。

## インストール

1. `storia-relay-{{VERSION}}.zip` をダウンロードして展開します。
2. 一度起動します。`relay.properties` を作って終了します。

    ```bash
    ./start-relay.sh        # Windows は start-relay.bat
    ```

3. `relay.properties` を開き、合言葉（8 文字以上、すべてのマシンで同じ）を設定します。

    ```properties
    bind=0.0.0.0
    port=25590
    secret=長くてランダムな合言葉
    compress=true
    in-flight-per-thread=4
    timeout-ms=20000
    ```

4. もう一度起動します。

## relay.properties

| 項目 | 初期値 | 説明 |
| --- | --- | --- |
| `bind` | `0.0.0.0` | 待ち受けるアドレス。 |
| `port` | `25590` | 待ち受けるポート。サーバーもワーカーもここに接続します。 |
| `secret` | （空） | 合言葉。8 文字未満だとリレーは起動しません。 |
| `compress` | `true` | 暗号化の前に通信を圧縮します。 |
| `in-flight-per-thread` | `4` | ワーカーのスレッド 1 本あたりに待たせる依頼の数。 |
| `timeout-ms` | `20000` | ワーカーの返事をこの時間待っても来なければ、別のワーカーに回すかサーバーに返します。 |

## サーバーとワーカーをつなぐ

Storia サーバー（`storia.yml`）：

```yaml
offload:
  mode: client
  secret: "長くてランダムな合言葉"
  workers:
  - relay.example.lan:25590
```

各 Storia Worker（`storia.yml`）：

```yaml
offload:
  mode: worker
  secret: "長くてランダムな合言葉"
  relay: "relay.example.lan:25590"
```

## コンソール

| コマンド | 説明 |
| --- | --- |
| `status` | 接続中のワーカーとサーバー、処理中の依頼、完了・失敗の件数。 |
| `stop` | リレーを終了します。 |

## 障害時の動き

- ワーカーの接続が切れたら、処理待ちの依頼は、地形が一致する別のワーカーに回し直します。
- 引き受けられるワーカーがほかになければ、依頼はサーバーに返され、サーバーがそのチャンクを自分で生成します。
- リレー自体が止まったら、サーバーはすべて自分で生成し、リレーが戻ると自動で接続し直します。

## サービスとして動かす

```ini
# /etc/systemd/system/storia-relay.service
[Unit]
Description=Storia Relay
After=network-online.target

[Service]
User=storia
WorkingDirectory=/srv/storia-relay
ExecStart=/usr/bin/java -Xmx256M -jar storia-relay.jar relay.properties
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

リレーはコマンドを標準入力から読むので、systemd で動かしているときは `systemctl stop` で止めてください。
