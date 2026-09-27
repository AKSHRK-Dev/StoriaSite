---
summary: /storia コマンドのサブコマンドと権限。
---
Storia のコマンドはすべて `/storia` のサブコマンドで、権限 **`storia.command.storia`** が必要です（初期状態では OP が持っています）。
ゲーム内でもサーバーのコンソールでも使えます。

| コマンド | 説明 |
| --- | --- |
| `/storia` または `/storia status` | Storia のバージョンと RAM ワールドの状態（場所、RAM 使用量、最後の同期）。 |
| `/storia sync` | RAM ワールドを今すぐディスクに書き込みます。バックグラウンドで行うので、サーバーは止まりません。 |
| `/storia pregen start <半径> [ワールド] [x z]` | ワールドのスポーン（または `x z`）を中心に、`半径` ブロックの正方形を事前生成します。 |
| `/storia pregen status` | 進み具合、速度、残り時間の目安。 |
| `/storia pregen stop` | 止めます。進み具合は保存されます。 |
| `/storia pregen resume` | 止めた・中断された続きから再開します。再起動後でも使えます。 |
| `/storia budget` | ティックスレッドの使用率、GC 後のヒープ、1 人あたりの割り当て、プレイヤーごとのリージョン負荷、移動速度、現在の描画・シミュレーション距離。 |
| `/storia region` | 負荷の高いリージョン：スレッド使用率、MSPT、TPS、プレイヤー数、チャンク数。加えて [[tick-guard]] の状態と、最も密集したチャンク。 |
| `/storia cluster` | Cluster との接続、このワーカーが動かしているセル、プレイヤー、共有している時刻とスコアボード。 |

## 例

```text
/storia pregen start 5000
/storia pregen start 1500 world 10000 -4000
/storia sync
```

## 権限

| 権限 | 初期値 | 内容 |
| --- | --- | --- |
| `storia.command.storia` | OP | `/storia` のすべてのサブコマンド。 |

OP 以外に与えるには、Folia 対応の権限プラグインを使います。たとえば LuckPerms なら：

```text
/lp group admin permission set storia.command.storia true
```

## Paper・Folia のコマンド

`/tps`、`/mspt`、`/paper` など、いつものコマンドも使えます。Folia の TPS は **リージョンごと** なので、
`/tps` は自分がいるリージョンの値を表示します。全リージョンの概要は `/storia region` で見られます。

Storia Proxy の `/storiaproxy` コマンドは [[proxy]] を参照してください。
