# 🏗️ Nippo OCR: モジュール型データパイプライン (Modular Data Pipeline)

システムの拡張性（将来的に音声やYOLO、入力ログなどを統合する）を考慮した、完全に独立した「データストリーム型」の設計を定義します。

---

## 🚀 フォルダ構成の役割分担
データを「源泉（ストリーム）」ごとに完全に分離して保存します。これにより、OCRエンジンを修正せずに新しいデータ源を追加できます。

```text
nippo_data/
├── raw_streams/           # Stage 1: 未加工データの保存場所
│   ├── ocr/               # OCR結果 (TSV形式)
│   ├── ui_meta/           # ウィンドウ構造、UI部品の位置 (JSON/TSV)
│   └── audio/             # 音声テキスト (S2T後のテキストログ)
│
├── transformer/           # Stage 2: 変換エンジンのロジック
│   └── joiner.py          # 複数のストリームを時刻で結合する関数
│
└── semantic_logs/         # Stage 3: LLM用の最終成果物
    └── nsl_2026-02-21.yml # Nippo Semantic Log (NSL)
```

---

## 1. Stage 1: ストリームごとの保存 (Recording)

データを「源泉（ストリーム）」ごとに完全に分離して保存します。

### ソースコードの構成 (`nippo_system/`)
- `main.py`: 全プロセスを統合管理・起動
- `core/`: 共通設定 (`config.py`)、永続化 (`storage.py`)
- `ocr/`: 画面解析、テキスト抽出
- `audio/`: 音声録音、文字起こし
- `input_monitor/`: キーボード、マウス活動監視

### データストリームの保存場所 (`Documents/Nippo_OCR/raw_streams/`)
- **OCR ストリーム**: `ocr/ocr_stream_YYYY-MM-DD.tsv`
  - `Timestamp | block_id | box_2d | text`
- **音声ストリーム**: `audio/audio_stream_YYYY-MM-DD.tsv`
  - `Timestamp | transcribed_text`
- **入力活動ストリーム**: `input/input_stream_YYYY-MM-DD.tsv`
  - `Timestamp | window_title | key_count | mouse_count`
- **UI Metadata ストリーム**: `ui_meta/` (計画中)
  - `Timestamp | process_name | area_label | box_2d`

---

## 2. Stage 2: Transformer Function (結合・意味付与)
変換関数（Transformer）は、保存された複数のファイルを読み込み、**時刻が近いもの同士をガッチャンコ（JOIN）**します。

### 結合(Join)の仕組み
1.  ある時刻の OCRテキスト の座標を取得。
2.  同じ時刻の UI Meta から、その座標を「含んでいる」エリアラベルを探す。
3.  座標(x,y) を 「エリア名 ([Editor])」に変換して NSL に書き出す。

**メリット:**
- **疎結合**: OCRプログラムはウィンドウ構造を知らなくていい。UIメタデータ取得プログラムは文字を知らなくていい。
- **後付け**: あとから「PCの負荷情報ストリーム」を足しても、変換関数(Transformer)を少し書き換えるだけで日報に反映できます。

---

## 3. Stage 3: Nippo Semantic Log (NSL)
結合後の最終形式です。LLMに「どのストリームから来た情報か」が伝わるようにします。

```yaml
--- [22:45:05] ---
[UI_CONTEXT]: Visual Studio Code (Active)
[ACTIVITY]:
  - AREA: [Editor] (via UI_Meta)
    TEXT: "def process_data(src):" (via OCR)
  - AREA: [Terminal] (via UI_Meta)
    TEXT: "Success!" (via OCR)
[AUDIO_MEMO]: "よし、データ処理の関数はこれで完璧だ。" (via Audio_Stream)
```

---

## 💡 今後の展望
OCR以外のデータが増えても、この「ストリーム分離 ＋ Transformer結合」の構造なら、システム全体を壊さずに機能を追加し続けることが可能です。
