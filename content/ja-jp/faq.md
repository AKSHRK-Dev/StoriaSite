---
summary: よくある質問と、よくあるトラブルの解決方法。
---
## 全般

### Storia は無料ですか？

はい。Storia は、もとになった Paper・Folia・Velocity と同じくオープンソースです。ソースコードは [GitHub]({{GITHUB}}) にあります。

### 対応している Minecraft のバージョンは？

Minecraft Java Edition の **{{MC}}** です。Storia は Folia の対応バージョンに合わせています。

### バージョン番号の意味は？

Storia のバージョンは Minecraft に合わせています。`26.2` は Minecraft 26.2 向けの最初のリリースで、同じ Minecraft バージョンの
2 回目以降は `26.2-2`、`26.2-3` … となります。ワーカー・Relay・Storia Proxy は必ず **同じバージョン** にそろえてください。

### 小さなサーバーでも使えますか？

使えますが、Folia の並列処理が効果を発揮するのは、主にプレイヤーが多くワールドに散らばっている場合です。小さなサーバーや、
Paper 専用のプラグインに頼っているサーバーなら、Paper のほうが手軽です。

### Storia はバニラの動きを変えますか？

Storia 独自の変更は、バニラと同じ結果を保ちます（地形、エンティティの物理演算、レッドストーン）。ただしもとになっている Folia は、
リージョンをまたぐ装置など一部の特殊なケースで、シングルスレッドのサーバーと動きが異なります。[Folia の README](https://github.com/PaperMC/Folia) を参照してください。

## RAM ワールド

### ログに「Not enough space ... loading worlds from disk instead」と出る

`/dev/shm` に、ワールドと `min-free-mb` が入るだけの空きがありません。`df -h /dev/shm` で確認し、
[[ram-world#how-much-ram-do-i-need|必要な RAM の量]] を参考に増やしてください。その間も、サーバーはディスクから普通に動きます。

### ログに「Found RAM world left by a previous run」と出る

サーバーのプロセスが正常終了せずに止まりました。Storia が RAM 上のコピーをディスクに戻しているところで、正しい動作です。何もする必要はありません。

### RAM で動いているサーバーのバックアップは？

ディスク上のコピーを保存します。最新の状態が欲しければ、先に `/storia sync` を実行します。[[ram-world#backups|バックアップ]] を参照してください。

## パフォーマンス

### 初期地点がほかの人のトラップで重い。自分まで遅くなる？

なりません。[[tick-guard]] が、リージョンが目標の処理時間に戻るまで、密集チャンクの群れの AI を間引きます。近くに立っている
プレイヤーは制限されません。`/storia region` で密集チャンクが表示されるので、原因のトラップも見つけられます。

### ときどきプレイヤーの描画距離が下がるのはなぜ？

[[player-budget]] が、リージョンが重いときに、とても速く移動している人（エリトラなど）の描画距離を短くしています。速度が落ちれば戻ります。
`/storia budget` で各プレイヤーの速度を確認できます。立っている・歩いているだけの人は制限されません。オフにするには `player-budget.enabled: false` にします。

### 普段のプレイ中のチャンク生成が遅い

`/storia pregen` で事前生成するか（[[pregeneration]] を参照）、`config/paper-global.yml` の `chunk-system.worker-threads` を増やすか、[[cluster]] で複数のマシンに分けてください。

## Storia Cluster

### ワーカーが「Cannot reach the cluster coordinator」で止まる

- Relay は起動していますか？ワーカーから 25590 番ポートに届きますか？（`nc -zv relay-host 25590`）
- ワーカーと Relay の **合言葉は同じ** ですか？違うと最初のメッセージで拒否されます。
- 両方とも **同じ Storia のリリース** ですか？プロトコルのバージョンが違うと、その旨のメッセージとともに拒否されます。

### Relay に「an old Storia asked for terrain offload」と出る

26.2-2-beta 以前の `offload:` 設定を持つサーバーが接続してきました。地形生成の分担は Cluster に置き換わりました。
そのマシンの Storia を更新し、代わりに `cluster:` を設定してください（[[worker]] を参照）。

### ワーカー間の移動で一瞬読み込み画面が出る

読み込み画面なしの移動は Minecraft 26.1・26.2 のクライアントが対象です。ViaVersion 経由の古いクライアントでは、
普通のサーバー移動になります。

## Storia Proxy

### プレースホルダーが `{name}` のまま表示される

その名前が存在しません。`/storiaproxy placeholders` で綴りを確認してください。サーバー用のプレースホルダーでは、`<server>` が
`velocity.toml` の `[servers]` にある名前と完全に一致している必要があります。

### MOTD でプレイヤーのプレースホルダーが空になる

サーバーリストはプレイヤーが参加する前に表示されるので、表示する対象のプレイヤーがいません。MOTD ではプロキシやサーバーのプレースホルダーを使ってください。

## 困ったときは

[GitHub]({{GITHUB}}/issues) に Issue を作成してください。Storia のバージョン（`/storia status`）、`logs/latest.log` の該当部分、
**合言葉を消した** `storia.yml` を添えてもらえると助かります。
