---
summary: storia.yml のすべての項目と、その初期値・意味。
---
`storia.yml` は初回起動時にサーバーフォルダに作られます。足りない項目は次の起動時に初期値で追加されるので、
行を消せばその項目を初期値に戻せます。変更は **再起動** で反映されます。

Paper や Folia の設定は今までどおりの場所にあります（`config/paper-global.yml`、`config/paper-world-defaults.yml`、
`server.properties`）。

## 初期状態のファイル

```yaml
ram-world:
  enabled: true
  ram-directory: /dev/shm/storia
  sync-interval-seconds: 300
  min-free-mb: 512
  delete-on-shutdown: true
pregen:
  worker-threads: -1
  max-in-flight: -1
tick-guard:
  enabled: true
  target-mspt: 40.0
  crowd-threshold: 16
  player-radius: 8.0
  max-level: 3
player-budget:
  enabled: true
  check-interval-ticks: 100
  max-region-mspt: 45.0
  pool-saturated-percent: 85
  recover-below-percent: 70
  lower-simulation-distance: false
  min-simulation-distance: 4
  min-view-distance: 6
  memory-high-percent: 85
  memory-low-percent: 70
  fast-mover-speed: 12.0
offload:
  mode: 'off'
  secret: ''
  workers:
  - 127.0.0.1:25590
  max-in-flight: -1
  timeout-ms: 10000
  compress: true
  bind: 0.0.0.0
  port: 25590
  threads: -1
  relay: ''
```

## ram-world

[[ram-world]] を参照してください。

| 項目 | 初期値 | 説明 |
| --- | --- | --- |
| `enabled` | `true` | ワールドを RAM に置きます。`false` にすると Paper と同じくディスクから動きます。 |
| `ram-directory` | `/dev/shm/storia` | RAM 上のコピーを置く場所。RAM を使うファイルシステム（tmpfs）である必要があります。 |
| `sync-interval-seconds` | `300` | 変更をディスクに書き込む間隔（秒）。最小 10。短いほど安全、長いほど軽くなります。 |
| `min-free-mb` | `512` | 読み込むと空き RAM がこれより少なくなる場合は、ディスクから読み込みます。 |
| `delete-on-shutdown` | `true` | 正常終了したら RAM 上のコピーを消します（ディスクには書き込み済みです）。 |

## pregen

[[pregeneration]] を参照してください。

| 項目 | 初期値 | 説明 |
| --- | --- | --- |
| `worker-threads` | `-1` | `/storia pregen` の実行中に使うチャンク生成スレッド数。`-1` は CPU コア数 − 1。終わると元に戻ります。 |
| `max-in-flight` | `-1` | 同時に待機させるチャンク数。`-1` はスレッド数 × 16。 |

## tick-guard

[[tick-guard]] を参照してください。

| 項目 | 初期値 | 説明 |
| --- | --- | --- |
| `enabled` | `true` | リージョンが重すぎるときに、密集したモブの AI を間引きます。 |
| `target-mspt` | `40.0` | 各リージョンの処理時間をこの値（ミリ秒。1 ティックは 50）より下に保ちます。 |
| `crowd-threshold` | `16` | 1 チャンクにこの数以上のモブがいると密集とみなします。間引くのは密集だけです。 |
| `player-radius` | `8.0` | プレイヤーからこのブロック数以内のモブは、常に毎ティック判断します。 |
| `max-level` | `3` | どこまで間引くか。1 = 2 ティックに 1 回、2 = 4 回に 1 回、3 = 8 回に 1 回。 |

## player-budget

[[player-budget]] を参照してください。

| 項目 | 初期値 | 説明 |
| --- | --- | --- |
| `enabled` | `true` | 予算機能のオン・オフ。 |
| `check-interval-ticks` | `100` | 各プレイヤーを確認する間隔（100 ティック = 5 秒）。 |
| `max-region-mspt` | `45.0` | 1 ティックの処理にこれ以上（ミリ秒）かかるリージョンは予算オーバーです。制限されるのはその中の高速移動中の人だけです。 |
| `pool-saturated-percent` | `85` | ティックスレッドの使用率がこれを超えると、公平な割り当てを適用します。 |
| `recover-below-percent` | `70` | 制限中のリージョンは、上限のこの割合を下回ると元に戻ります。 |
| `fast-mover-speed` | `12.0` | 制限するのは、この速度（毎秒のブロック数。2 回続けて）より速く移動している人だけです。 |
| `lower-simulation-distance` | `false` | 高速で移動している人のシミュレーション距離も下げます。**トラップや回路を動かし続けるには `false` のままにしてください。** |
| `min-simulation-distance` | `4` | シミュレーション距離の下限。上の項目が `true` のときだけ使います。 |
| `min-view-distance` | `6` | 予算機能が設定する描画距離の下限。 |
| `memory-high-percent` | `85` | GC 後のヒープ使用率がこれを超えると、全員の描画距離を下げます。 |
| `memory-low-percent` | `70` | GC 後のヒープ使用率がこれを下回ると元に戻します。 |

## offload

[[offload]]、[[worker]]、[[relay]] を参照してください。

| 項目 | 初期値 | 使う側 | 説明 |
| --- | --- | --- | --- |
| `mode` | `off` | 全員 | `off`、`client`（メインサーバー）、`worker`（手伝う側）。 |
| `secret` | `''` | 全員 | 合言葉。8 文字以上で、すべてのマシンで同じにします。ネットワークには送られません。 |
| `workers` | `[127.0.0.1:25590]` | client | 使うワーカーまたはリレー（`host:port`）。 |
| `max-in-flight` | `-1` | client | 接続ごとに待たせるリクエスト数。`-1` はワーカーのスレッド数 × 4。 |
| `timeout-ms` | `10000` | client | この時間内に返事がなければ、そのチャンクは自分で生成します。 |
| `compress` | `true` | 全員 | 暗号化の前に通信を圧縮（deflate）します。とても速いネットワークでは切ると CPU を節約できます。 |
| `bind` | `0.0.0.0` | worker | ワーカーが待ち受けるアドレス。 |
| `port` | `25590` | worker | ワーカーが待ち受けるポート。 |
| `threads` | `-1` | worker | 地形計算に使うスレッド数。`-1` は全コア。 |
| `relay` | `''` | worker | 設定すると（`host:port`）、待ち受けずにそのリレーへ自分から接続します。 |

`mode` が `client` と `worker` 以外なら、すべてオフの扱いです（引用符なしの `off` は YAML では `false` と読まれますが、これもオフです）。

## Java のシステムプロパティ

コマンドラインで `-jar` の前に `-D...` として指定します。

| プロパティ | 説明 |
| --- | --- |
| `-Dstoria.worker=true` | 専用ワーカーとして起動します。プレイヤー用ポート・query・RCON は開きません。[[worker]] のパッケージで使っています。 |
| `-Dstoria.verifyOffload=true` | 分担したチャンクを自分でも生成して照合します。テスト用で、CPU を使います。 |
| `-Dstoria.verifyPush=true` | エンティティの押し合いをバニラの方法でも計算して照合します。テスト用で、CPU を使います。 |
