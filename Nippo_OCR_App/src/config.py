import os

# 基本設定
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# 保存先はユーザーフォルダに固定
USER_DOCS = os.path.join(os.environ.get('USERPROFILE', ''), 'Documents')
APP_ROOT = os.path.join(USER_DOCS, "Nippo_OCR")

# モジュール型ストリーム構成 (Stage 1)
STREAM_ROOT = os.path.join(APP_ROOT, "raw_streams")
OCR_STREAM_DIR = os.path.join(STREAM_ROOT, "ocr")
UI_META_STREAM_DIR = os.path.join(STREAM_ROOT, "ui_meta")
AUDIO_STREAM_DIR = os.path.join(STREAM_ROOT, "audio")

# 互換性のための既存変数 (OCRエンジン用)
DATA_DIR = OCR_STREAM_DIR

# 必要ディレクトリの作成
for d in [OCR_STREAM_DIR, UI_META_STREAM_DIR, AUDIO_STREAM_DIR]:
    os.makedirs(d, exist_ok=True)

# モジュール有効化フラグ (Standalone OCR app)
ENABLE_SCREEN_OCR = True

# 画面OCR設定
SCREEN_CAPTURE_INTERVAL = 5.0  # 秒
OCR_DIFF_THRESHOLD = 5000      # 差分検知の閾値（ピクセル数等の指標、要調整）
OCR_LANG = "jpn+eng"       # Tesseract用

# プライバシー設定
# ウィンドウタイトルに含まれていた場合、監視を一時停止するキーワード
SENSITIVE_APP_NAMES = [
    "password", "1password", "lastpass", "bitwarden",
    "bank", "credit", "card", "login", "signin",
    "private", "incognito", "inprivate",
    "パスワード", "銀行", "クレジットカード", "ログイン"
]
