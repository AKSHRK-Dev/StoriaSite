---
summary: Java を入れ、Storia をダウンロードして最初のサーバーを起動する。Paper や Folia からの乗り換えも。
---
## 必要なもの

- **Java 25** 以上。ディストリビューションは何でもかまいません。迷ったら [Eclipse Temurin](https://adoptium.net) がおすすめです。
- 64 ビットの OS：Linux（推奨）、Windows、macOS。
- [[ram-world]] を使う場合：Java のヒープとは **別に**、ワールドフォルダ以上の空き RAM。

Java のバージョンを確認します。

```bash
java -version
```

## インストール

1. サーバー用の空のフォルダを作ります。
2. [ダウンロードページ](/en-us/downloads/) から `storia-{{VERSION}}.jar` をそこに保存します。
3. 一度起動します。

    ```bash
    java -Xms4G -Xmx8G -jar storia-{{VERSION}}.jar nogui
    ```

4. サーバーが止まり、[Minecraft EULA](https://aka.ms/MinecraftEULA) への同意を求められます。同意する場合は
   `eula.txt` を開き、`eula=true` に書き換えます。
5. もう一度起動します。`Done` と表示されたら、ポート 25565 で準備完了です。

初回起動時には、Paper や Folia と同じファイル（`server.properties`、`config/paper-global.yml`、
`config/paper-world-defaults.yml`）に加えて **`storia.yml`** が作られます。内容は [[configuration]] で説明しています。

!!! tip "ヒープのサイズ"
    `-Xmx` にはできるだけ多くのメモリを割り当ててください。ただし RAM ワールド（ヒープの外の `/dev/shm` に置かれます）と
    OS のための分は残しておきましょう。

## 起動スクリプト

Linux・macOS の場合：

```bash
#!/bin/sh
cd "$(dirname "$0")"
exec java -Xms4G -Xmx8G -jar storia-{{VERSION}}.jar nogui
```

`start.sh` という名前で保存し、`chmod +x start.sh` のあと `./start.sh` で起動します。

Windows の場合は `start.bat` として保存します。

```bat
@echo off
java -Xms4G -Xmx8G -jar storia-{{VERSION}}.jar nogui
pause
```

## Paper や Folia からの乗り換え

Storia は同じワールド形式と設定ファイルを読むので、そのまま入れ替えられます。

1. **サーバーフォルダをバックアップします。**
2. サーバーを止め、Paper や Folia の jar を Storia の jar に置き換えます。
3. すべてのプラグインが Folia に対応しているか確認します（`plugin.yml` に `folia-supported: true`）。
   対応していないプラグインは起動時に読み込まれません。[[plugins]] を参照してください。
4. サーバーを起動します。`storia.yml` が作られ、ワールドが RAM にコピーされます。

元に戻すのも簡単です。Storia を `stop` で止め（RAM 上のワールドがディスクに書き込まれます）、前の jar で起動するだけです。

## 起動したら最初に

```text
/storia status              RAM ワールドの状態と最後の同期
/storia pregen start 3000   スポーンの周り 3000 ブロックを事前生成
/storia budget              ティックスレッドの混み具合をプレイヤーごとに表示
```

次に読むとよいページ：

- [[configuration]]：`storia.yml` のすべての項目
- [[pregeneration]]：プレイヤーが来る前に地形を作っておく
- [[cluster]]：プレイヤーが 1 台に収まらなくなったら
- [[proxy]]：複数のサーバーを 1 つのアドレスにまとめるなら
