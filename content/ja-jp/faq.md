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
2 回目以降は `26.2-2`、`26.2-3` … となります。サーバー・ワーカー・リレーは必ず **同じバージョン** にそろえてください。

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

`/storia pregen` で事前生成するか（[[pregeneration]] を参照）、`config/paper-global.yml` の `chunk-system.worker-threads` を増やすか、[[worker]] を追加してください。

## 処理の分担

### `/storia offload` に「disconnected」と出る

- ワーカーは起動していますか？サーバーからそのポートに届きますか？（`nc -zv worker-host 25590`。ポートは自分の設定に合わせて）
- 合言葉は **両方で同じ** ですか？違う合言葉は最初のメッセージで拒否され、ログに出ます。
- 両方とも **同じ Storia のリリース** ですか？プロトコルのバージョンが違うと、その旨のメッセージとともに拒否されます。

### ワーカーがディメンションを断る：「terrain differs」

ワーカーの `level.dat`・データパック・Storia のバージョンが、サーバーと一致していません。`level.dat` と `datapacks/` をコピーし直し、
同じ Storia のリリースを使ってください。[[worker#keeping-the-worker-in-sync|ワーカーを同じ状態に保つ]] を参照してください。

### ワーカーがディメンションを断る：「no such dimension here」

サーバーにはあるのに、ワーカーにはないディメンション（データパックやプラグインで作ったワールドなど）です。その中のチャンクはサーバーが自分で生成します。

### ほとんどのチャンクが「generated locally (workers busy)」になる

ワーカーが手いっぱいです。ワーカーを増やすか、スレッドを増やすか、`offload.max-in-flight` を大きくしてください。

## Storia Proxy

### プレースホルダーが `{name}` のまま表示される

その名前が存在しません。`/storiaproxy placeholders` で綴りを確認してください。サーバー用のプレースホルダーでは、`<server>` が
`velocity.toml` の `[servers]` にある名前と完全に一致している必要があります。

### MOTD でプレイヤーのプレースホルダーが空になる

サーバーリストはプレイヤーが参加する前に表示されるので、表示する対象のプレイヤーがいません。MOTD ではプロキシやサーバーのプレースホルダーを使ってください。

## 困ったときは

[GitHub]({{GITHUB}}/issues) に Issue を作成してください。Storia のバージョン（`/storia status`）、`logs/latest.log` の該当部分、
**合言葉を消した** `storia.yml` を添えてもらえると助かります。
