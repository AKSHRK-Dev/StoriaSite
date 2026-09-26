---
summary: 自分で負荷を増やしている人だけ、混雑中は描画距離を短くします。それ以外の人は一切制限しません。
---
プレイヤーごとの予算は、リージョンが重すぎるときに **誰が** 譲るべきかを決める仕組みです。Storia 26.2-1-beta からは、
「自分で負荷を増やしている人だけ」になりました。初期地点のような混み合った場所で、立っている・建築している・歩いている
だけの人は、一切制限されません。

その場所自体の重さ（トラップやモブの群れ）は [[tick-guard]] が受け持ち、プレイヤーではなく群れの処理を減らします。

## 制限される人

次の **両方** に当てはまるとき、確認のたびに描画距離を 1 段階ずつ下げます。

1. **そのリージョンが予算オーバー。** 1 ティックの処理が `max-region-mspt`（45 ms）を超えている。または、サーバーの
   ティックスレッドが満杯（`pool-saturated-percent`、85%）で、そのリージョンがプレイヤーの人数分の取り分より多く使っている。
2. **本人が高速で移動している。** `fast-mover-speed`（毎秒 12 ブロック。ダッシュより速い）を 2 回続けて超えている。
   エリトラでの飛行や、速い乗り物などです。高速で移動すると、サーバーは新しいチャンクを大量に読み込み、生成し、送ることになります。

速度が落ちるか、リージョンが回復すれば、確認のたびに 1 段階ずつ戻します。2 回続けて速い必要があるので、1 回のテレポートでは制限されません。

!!! note "回路は動き続けます"
    初期設定では **シミュレーション距離は一切変えない** ので、プレイヤーの周りのレッドストーン、トラップ、モブは動き続けます。
    描画距離もシミュレーション距離より下げることはありません。

描画距離を下げられるのは、シミュレーション距離との間に余裕がある場合だけです。`server.properties` で：

```properties
view-distance=10
simulation-distance=6
```

### lower-simulation-distance

```yaml
player-budget:
  lower-simulation-distance: true
  min-simulation-distance: 4
```

高速で移動している人のシミュレーション距離も、**先に** 下げるようになります。CPU をより多く節約できますが、下げている間は、
その人から新しい距離より遠くにある装置は止まります。

## メモリ

CPU とは別に、Java のヒープを **GC の後の値** で見ています。`memory-high-percent`（85%）を超えると全員の描画距離を
1 段階ずつ下げ、`memory-low-percent`（70%）を下回ると戻します。メモリはサーバー全体で共有しているので、全員が対象になるのはこの場合だけです。

## 計測結果

Tick Guard を切って、リージョンが重い状態を保ったまま計測しました。Alice は止まっていて、Bob は毎秒 20 ブロックで移動しています。

| プレイヤー | 速度 | 描画距離 |
| --- | --- | --- |
| Alice | 毎秒 0 ブロック | 10 のまま（制限なし） |
| Bob | 毎秒 20 ブロック | 移動中に 10 → 9 → 7 |

## 状態を見る

```text
/storia budget
```

```text
Player budget (checked every 5s)
Tick threads busy: 100% (saturated: busy regions thin out crowds more)
Share per player: 33% of a thread
Heap after GC: 9%
 Alice: region 60.6 MSPT, 16.1 TPS, 98% thread, 2 player(s) | 0 blocks/s | sim default, view default
 Bob: region 60.6 MSPT, 16.1 TPS, 98% thread, 2 player(s) | 20 blocks/s | sim default, view 9
```

## 設定

[[configuration]] の [player-budget の表](/en-us/docs/configuration/#player-budget) を参照してください。オフにするには：

```yaml
player-budget:
  enabled: false
```
