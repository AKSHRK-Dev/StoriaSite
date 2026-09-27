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
cluster:
  enabled: false
  coordinator: 127.0.0.1:25590
  node-name: ''
  secret: ''
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

## cluster

このサーバーを [[cluster|Storia Cluster]] の [[worker|Storia Worker]] にします。[[worker]] と [[relay]] を参照してください。

| 項目 | 初期値 | 説明 |
| --- | --- | --- |
| `enabled` | `false` | Cluster に参加します。ワールドは Relay に置かれ、このサーバーは自分のワールドを持ちません。 |
| `coordinator` | `127.0.0.1:25590` | [[relay|Storia Relay]] の `host:port`。 |
| `node-name` | `''` | このワーカーの名前。ワーカーごとに変え、プロキシの `velocity.toml` でも同じ名前にします。 |
| `secret` | `''` | Relay と同じ合言葉。8 文字以上。ネットワークには流れません。 |

古い `storia.yml` に `offload:` の項目が残っていても無視されます。消してかまいません。

## Java のシステムプロパティ

コマンドラインで `-jar` の前に `-D...` として指定します。

| プロパティ | 説明 |
| --- | --- |
| `-Dstoria.verifyPush=true` | エンティティの押し合いをバニラの方法でも計算して照合します。テスト用で、CPU を使います。 |
