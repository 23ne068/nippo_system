# Project Directory Structure

Nippoシステムのディレクトリ構成定義書です。
開発資産、ビルドツール、研究資料、ドキュメントの場所を明確に定義し、長期的な保守性を確保します。

## ディレクトリ全体像

```text
Nippo/
├── nippo_system/        # メインアプリケーション・ソースコード
│   ├── core/            # 設定・共通クラス
│   ├── gui_app.py       # GUIエントリーポイント
│   ├── ocr/             # OCRエンジンのラッパー
│   ├── input_monitor/   # 入力監視モジュール
│   ├── transformer/     # データ抽出・意味付け・日報生成ロジック
│   ├── reporter/        # 集計・レポート出力
│   └── user_state/      # ユーザー状態（サボり等）判定ロジック
│
├── nippo-ocr/           # OCRコアエンジン（サブパッケージ）
├── packaging/           # ビルド・配布用スクリプト
│   ├── build_exe.py     # PyInstallerビルド用スクリプト
│   ├── build_installer.iss # インストーラー定義
│   └── create_shortcut.ps1 # スタートアップ登録支援スクリプト
│
├── docs/                # 設計書・ロードマップ・レポート
│   ├── structure.md     # 本ファイル（構成定義書）
│   ├── future_roadmap.md # 今後の展望
│   └── system_structure.md # システム設計詳細
│
├── labs/                # 研究・デバッグ・実験用スクリプト
│   ├── audio_debug/     # 音声レベル・録音の実験
│   ├── camera_debug/    # YOLO・姿勢推定の実験
│   └── ocr_lab/         # OCRエンジンの比較・検証
│
├── README.md            # プロジェクト概要・セットアップ
└── .gitignore           # Git管理対象から巨大ファイルを除外
```

## 各ディレクトリの役割

### `nippo_system/` (Source Code)
システムの本体です。`gui_app.py` から起動し、トレイアイコン常駐や各種マネージャー（OCR, Input, Transformer）の制御を行います。

### `nippo-ocr/` (Core Module)
高度なOCR処理（領域抽出や特定コンテキストへの最適化など）を担当する独立性の高いモジュールです。

### `packaging/` (Build Tools)
`.exe`化やインストーラー作成のためのツール・設定ファイル群です。
配布版を作成する際は、この中の `build_exe.py` を実行します。

### `docs/` (Documentation)
プロジェクトの「なぜ（Why）」や「どのように（How）」を記録する場所です。
開発の履歴や、将来の目標（ロードマップ）が格納されています。

### `labs/` (Research & Debug)
新機能の開発中に発生した使い捨ての検証スクリプトや、特定のハードウェア（マイク、カメラ）との相性テスト用スクリプトなどを格納します。ここにあるファイルは本番の `.exe` には含まれません。
