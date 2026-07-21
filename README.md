# エルデンリング自動レベリング

PS5をchiaki-ngのリモートプレイで操作し、参考元XMLの入力を仮想DS4コントローラーから送るマクロです。

詳しい手順は、同梱の `手順書.html` を上から順に読んでください。

## まずダウンロードするもの

### 1. Python 3.12.x

- [Python公式 Windowsダウンロード](https://www.python.org/downloads/windows/)
- 動作保証対象は **Python 3.12.x** です。
- Python 3.13以降は、この公開版では未検証です。
- インストーラーの最初の画面で `Add python.exe to PATH` をオンにしてください。

### 2. chiaki-ng

- [chiaki-ngの案内・ダウンロードページ](https://chiaki-ng.com/)
- [chiaki-ngのWindowsダウンロードページ](https://chiaki-ng.com/download/)
- [chiaki-ng上流GitHub Releases](https://github.com/streetpea/chiaki-ng/releases)

Windows x64のportable版をダウンロードし、展開後に `chiaki.exe` が次の場所にある状態にしてください。

```text
%LOCALAPPDATA%\eldenring_auto_leveling\chiaki-ng\chiaki-ng-Win\chiaki.exe
```

`chiaki-ng.com` は独立した案内・ミラーサイトです。上流の配布元を確認したい場合は、上記の `streetpea/chiaki-ng` GitHub Releasesを使ってください。

### 3. ViGEmBus

- [ViGEmBus公式サイトのダウンロード](https://vigembus.com/download/)
- [ViGEmBus公式GitHub Releases](https://github.com/nefarius/ViGEmBus/releases/latest)

ViGEmBusはWindows上に仮想ゲームパッドを作る第三者製のシステムドライバーです。このマクロのPythonコードは `vgamepad` を使ってDS4入力を作るため、Windows側へのインストールが必要です。

ダウンロードした公式インストーラーを実行し、画面の指示に従ってインストールしてください。ViGEmBusはシステムドライバーであり、マクロのフォルダへコピーするものではありません。また、ViGEmBusはCodex製ではないため、この公開ZIPには同梱していません。

### 4. 参考元の `eldenring.xml`

- [参考元記事から `eldenring.xml` を取得](https://note.com/psycho_tanshio/n/n03ae7bf7275a)

ダウンロードしたファイル名を `eldenring.xml` にし、次の場所へ保存してください。

```text
%USERPROFILE%\Downloads\eldenring.xml
```

参考元の `eldenring.xml` は、Marked One様の次の記事を利用させていただきました。配布いただきありがとうございます。

## この公開ZIPに含まれないもの

次のものは、上記リンクから利用者側で準備します。

- Python本体
- Pythonの仮想環境 `.venv`
- chiaki-ng本体
- ViGEmBusインストーラー
- 参考元の `eldenring.xml`

公開ZIPを展開したフォルダで、初回だけPython環境を作ります。エクスプローラーで展開先フォルダを開き、アドレスバーに `cmd` と入力してから、次を実行してください。

```bat
cd /d "macro"
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install vgamepad
```

## 重要な前提

- この仕組みは、自分のPS5をリモートプレイで操作します。
- 公式PS Remote Playではなく、`chiaki-ng` を使います。
- 入力の流れは `PCの仮想DS4 -> chiaki-ng -> PS5 -> エルデンリング` です。
- chiaki-ngの画面にPS5の映像が出ている状態で実行してください。
- エルデンリングはオフラインで起動してください。

## 通常使うファイル

```text
start_chiaki.cmd                              chiaki-ngを起動
check_virtual_gamepad.cmd                     仮想コントローラー確認
dry_run_macro.cmd                              入力なしでマクロ内容だけ確認
test_one_loop.cmd                              1ループだけ実行
loop_xml_prefix_touch_grace_until_stop.cmd     止めるまでループ実行
```

通常のループ実行は `loop_xml_prefix_touch_grace_until_stop.cmd` です。

## 現在の操作フロー

```text
XML再生
-> 黄金波1回目
-> XML後半の移動/待機
-> 黄金波2回目
-> タッチパッド
-> 三角
-> ×
-> ×
-> 即ニュートラル復帰
-> ニュートラル状態を3秒維持
-> 次ループ
```

## エルデンリング側の設定

- 祝福: `王朝に至る崖路`
- 武器: `神の遺剣`
- 戦技: `黄金波`
- カメラ感度: `5`
- 初期位置: `images\initial_position_guide.png` を参照

初期位置は、崖・落下側が画面左、祝福が画面右に見える向きにします。

## 停止方法

マクロの黒い画面で `Ctrl+C` を押します。Ctrl+C後は、仮想DS4をニュートラル状態で3秒維持してから終了します。

cmd右上の `×` で閉じると、この終了処理が走らない可能性があります。

## よくある詰まりどころ

- `PSN Login` 後にredirect画面になったら、ブラウザのアドレスバーのURLを丸ごとchiaki-ngへ貼り付けます。
- PS5側の決定キーは `×` です。マクロ上では `Cross / ×` として送ります。
- タッチパッドや×が反応しない場合は、chiaki-ngを再起動してPS5へ再接続します。
- 停止後も上入力が残る場合は、物理コントローラーの左スティックを一度動かして離し、chiaki-ngを再接続します。
