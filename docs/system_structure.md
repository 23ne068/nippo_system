# Nippo システム構成と状態
*(2026-02-20 現在)*

## 📂 ディレクトリ構成

```graphql
Nippo/
├── nippo_system/               # メインアプリケーションパッケージ
│   ├── main.py                 # 🚀 エントリーポイント。サブプロセス管理とゾンビプロセス除去。
│   ├── config.py               # ⚙️ 設定ファイル (ここでモジュールの有効/無効を切り替えます)。
│   ├── modules/                # コアロジック (機能) モジュール
│   │   ├── screen_ocr.py       # 👁️ OCR: 画面の文字を読み取り、日次JSONログを生成。
│   │   ├── reporter.py         # 📝 レポート作成: ログを解析し、Markdown形式の日報を生成。
│   │   ├── run_ocr.py          # screen_ocr.py を単独でテスト実行するためのラッパー。
│   │   ├── run_state.py        # 📷 カメラ/ユーザー状態監視 (現在「無効化」中)。
│   │   ├── run_audio.py        # 🎤 音声認識 (Vosk) モジュール。
│   │   ├── run_input.py        # ⌨️ キーボード/マウス入力の監視。
│   └── data/                   # 💾 データ保存場所
│       ├── ocr_results_YYYY-MM-DD.txt # 日次OCRログファイル (稼働中)
│       ├── report_YYYY-MM-DD.md       # 生成された日報ファイル
│       ├── logs.db                    # SQLiteデータベース (その他のモジュール用)
│       └── vosk-model-small-ja-0.22/  # ローカル音声認識モデル
│
├── driver_debug/               # 🔧 診断ツール (カメラ問題の調査用)
│   ├── diagnose_camera.py      # カメラIDとWindows PnP状態を確認するスクリプト。
│   └── verification_plan.md    # ドライバー問題のデバッグ計画書。
│
└── .gemini/                    # 🧠 AIブレイン & 成果物 (無視してください)
```

## 📷 カメラ機能のステータス (フェーズ 5 - 一時停止中)

- **現在の状態:** `nippo_system/main.py` にて **無効化 (DISABLED)** されています。
- **理由:** ドライバ/ハードウェアの不具合により、「不明なエラー」が多発し、システム不安定化と大量のエラーログ発生の原因となっていたため。
- **ログへの影響:** 以前はエラーログが画面に表示され、それをOCRが読み取って無限ループしていましたが、モジュール停止により解決しました。
- **今後のアクションプラン:**
    1.  `driver_debug/diagnose_camera.py` を使用して、根本原因（ハードウェア故障かドライバ不良か）を特定する。
    2.  安定動作が確認でき次第、`nippo_system/config.py` の `ENABLE_USER_STATE` を有効化する。

## 📝 日報生成ワークフロー (フェーズ 6 - 稼働中)

1.  **OCR ログ記録:** `screen_ocr.py` が画面上のテキスト変化を検知し、`nippo_system/data/ocr_results_YYYY-MM-DD.txt` に保存します。
    *   *フォーマット:* JSON形式 (`time`, `description` (テキスト), `box_2d` (座標))。
2.  **レポート生成:** `reporter.py` が日次ログを読み込み、ノイズやシステムメッセージを除去し、時間ごとにグルーピングして `report_YYYY-MM-DD.md` を生成します。
