# エルデンリング自動レベリング

詳しい手順は `手順書.html` を開いてください。こちらは現在仕様の要約です。

## 重要な前提

- この仕組みは、自分のPS5をリモートプレイで操作します。
- 公式PS Remote Playではなく、`chiaki-ng` を使います。
- 入力の流れは `PCの仮想DS4 -> chiaki-ng -> PS5 -> エルデンリング` です。
- エルデンリングはオフラインで起動してください。

## 公開版の前提

この公開版は、設定済み環境を丸ごと配布するものではありません。次のものはZIPに含まれないため、利用者側で用意してください。

- Python 3.12（Windows）
- ViGEmBus（仮想コントローラー用ドライバー）
- chiaki-ng（PS5リモートプレイ用）
- 参考元の `eldenring.xml`

ZIPを展開した後、初回だけ次を実行してPython環境を作ります。コマンドは展開先フォルダで実行してください。

```bat
cd /d "macro"
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install vgamepad
```

`eldenring.xml` は `%USERPROFILE%\Downloads\eldenring.xml` に置いてください。詳しい登録・初期位置・実行手順は `手順書.html` を開いて確認します。

## 通常使うファイル

```text
start_chiaki.cmd                         chiaki-ngを起動
check_virtual_gamepad.cmd                仮想コントローラー確認
dry_run_macro.cmd                        入力なしでマクロ内容だけ確認
test_one_loop.cmd                        1ループだけ実行
loop_xml_prefix_touch_grace_until_stop.cmd  止めるまでループ実行
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

マクロの黒い画面で `Ctrl+C` を押します。

Ctrl+C後は、仮想DS4をニュートラル状態で3秒維持してから終了します。

cmd右上の `×` で閉じると、この終了処理が走らない可能性があります。

## よくある詰まりどころ

- `PSN Login` 後にredirect画面になったら、ブラウザのアドレスバーのURLを丸ごとchiaki-ngへ貼り付けます。
- PS5側の決定キーは `×` です。マクロ上では `Cross / ×` として送ります。
- タッチパッドや×が反応しない場合は、chiaki-ngを再起動してPS5へ再接続します。
- 停止後も上入力が残る場合は、物理コントローラーの左スティックを一度動かして離し、chiaki-ngを再接続します。
