import os
import sys

# 基本設定
if getattr(sys, 'frozen', False):
    # PyInstaller化されたexeとして実行されている場合
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # 通常のPythonスクリプトとして実行されている場合
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

APP_ROOT = BASE_DIR

# モジュール型ストリーム構成 (Stage 1 & 2)
STREAM_ROOT = os.path.join(APP_ROOT, "raw_streams")
OCR_STREAM_DIR = os.path.join(STREAM_ROOT, "ocr")
UI_META_STREAM_DIR = os.path.join(STREAM_ROOT, "ui_meta")
AUDIO_STREAM_DIR = os.path.join(STREAM_ROOT, "audio")
INPUT_STREAM_DIR = os.path.join(STREAM_ROOT, "input")
TRANSFORMER_DIR = os.path.join(BASE_DIR, "transformer") # Stage 2 中間データ保存先
PENDING_FRAMES_DIR = os.path.join(STREAM_ROOT, "pending_frames") # 高負荷時の待避先

# 互換性のための既存変数
# [重要] システムデータ（モデル、DB）は開発フォルダ内の data/ に保持
DATA_DIR = os.path.join(BASE_DIR, "data") 
LOG_DB_PATH = os.path.join(DATA_DIR, "logs.db")
TESSDATA_PATH = os.path.join(DATA_DIR, "tessdata")

# 必要ディレクトリの作成
for d in [OCR_STREAM_DIR, UI_META_STREAM_DIR, AUDIO_STREAM_DIR, INPUT_STREAM_DIR, DATA_DIR, TESSDATA_PATH, TRANSFORMER_DIR, PENDING_FRAMES_DIR]:
    os.makedirs(d, exist_ok=True)
TTL_HOURS = 24  # データの保存期間

# モジュール有効化フラグ
ENABLE_INPUT_MONITOR = True
ENABLE_AUDIO = False
ENABLE_SCREEN_OCR = True
ENABLE_USER_STATE = True

# Yield Mode (リソース譲渡設定)
ENABLE_YIELD_MODE = True
THROTTLE_OCR_INTERVAL = 30.0  # 作業検出時のOCR間隔
ACTIVITY_THRESHOLD_SEC = 10.0 # 「作業中」とみなす直近の活動秒数

# 画面OCR設定
SCREEN_CAPTURE_INTERVAL = 5.0  # 秒
OCR_DIFF_THRESHOLD = 5000      # 差分検知の閾値（ピクセル数等の指標、要調整）
OCR_LANG = "jpn+eng"       # Tesseract用

# 音声設定
AUDIO_SAMPLE_RATE = 16000
VAD_MODE = 3                   # 0-3 (3が最も攻撃的/厳格)

# ユーザー状態（YOLO）設定
USER_STATE_INTERVAL = 15.0     # 秒
YOLO_MODEL_PATH = os.path.join(DATA_DIR, "models", "yolov8n-pose.pt")

# プライバシー設定
# ウィンドウタイトルに含まれていた場合、監視を一時停止するキーワード
SENSITIVE_APP_NAMES = [
    "password", "1password", "lastpass", "bitwarden",
    "bank", "credit", "card", "login", "signin",
    "private", "incognito", "inprivate",
    "パスワード", "銀行", "クレジットカード", "ログイン"
]
