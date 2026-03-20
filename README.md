# Nippo System

個人のPC作業を自動で記録し、AI（LLM）が日報を生成するための統合システムです。
OCR、入力監視、音声、ウィンドウコンテキストの抽出を行い、一日の活動を構造化されたデータとして集計します。

## 🚀 クイックスタート

### 1. セットアップ
```bash
# 仮想環境の有効化 (Windows)
.\.venv\Scripts\activate

# 依存ライブラリのインストール
pip install -r requirements.txt
```

### 2. 実行
```bash
# メインアプリケーションの起動
python -m nippo_system.main
```

### 3. パッケージ化 (EXE作成)
```bash
# PyInstallerを使用して配布用EXEを作成
python packaging/build_exe.py
```
作成されたEXEは `dist/NippoSystem_Release/NippoSystem.exe` に格納されます。

## 📂 ディレクトリ構成

詳細な構成定義は [docs/structure.md](docs/structure.md) を参照してください。

- **`nippo_system/`**: アプリケーション本体。
- **`nippo-ocr/`**: 高度なOCRエンジンモジュール。
- **`packaging/`**: 配布用EXE化・インストーラー作成ツール。
- **`docs/`**: 設計書・ロードマップ・研究レポート。
- **`labs/`**: 実験用デバッグスクリプト・テストコード。

## 🛠 機能一覧
- **ハイブリッドOCR**: WinRT OCR と Tesseract を状況に応じて切り替え。
- **入力監視**: キーボード入力、マウスクリックの意味付け（Semantic Tagging）。
- **日報自動生成**: 記録したデータからAI用のYAMLを生成し、プロンプトと共にコピー。
- **二重起動防止**: 常に1つのインスタンスのみが動作するよう自動管理。
- **トレイ常駐**: バックグラウンドでの静かな稼働。
