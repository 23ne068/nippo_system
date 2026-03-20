import sqlite3
import time
import json
import threading
import logging
import os

# 相対インポート
try:
    from .config import LOG_DB_PATH, TTL_HOURS
except ImportError:
    LOG_DB_PATH = "logs.db"
    TTL_HOURS = 24

class StorageManager:
    def __init__(self, db_path=None):
        self.logger = logging.getLogger(__name__)
        self.db_path = db_path if db_path else LOG_DB_PATH
        self._lock = threading.Lock()
        self._init_db()

    def _init_db(self):
        try:
            # ディレクトリ作成
            db_dir = os.path.dirname(self.db_path)
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir)

            with self._lock:
                conn = sqlite3.connect(self.db_path, check_same_thread=False)
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp REAL,
                        log_type TEXT,
                        content TEXT,
                        metadata TEXT
                    )
                ''')
                # インデックス: タイムスタンプ検索用
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON logs (timestamp)')
                conn.commit()
                conn.close()
        except Exception as e:
            self.logger.error(f"Storage init failed: {e}")

    def save_log(self, log_type, content, metadata=None):
        """ログをデータベースに保存する"""
        ts = time.time()
        # metadataが辞書ならJSON文字列化
        if isinstance(metadata, dict):
            meta_str = json.dumps(metadata, ensure_ascii=False)
        else:
            meta_str = str(metadata) if metadata else "{}"
        
        try:
            with self._lock:
                conn = sqlite3.connect(self.db_path, check_same_thread=False)
                cursor = conn.cursor()
                cursor.execute(
                    'INSERT INTO logs (timestamp, log_type, content, metadata) VALUES (?, ?, ?, ?)',
                    (ts, log_type, content, meta_str)
                )
                conn.commit()
                conn.close()
        except Exception as e:
            self.logger.error(f"Failed to save log ({log_type}): {e}")

    def get_recent_logs(self, limit=10):
        """直近のログを取得（デバッグ用）"""
        try:
            with self._lock:
                conn = sqlite3.connect(self.db_path, check_same_thread=False)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM logs ORDER BY timestamp DESC LIMIT ?', (limit,))
                rows = [dict(row) for row in cursor.fetchall()]
                conn.close()
            return rows
        except Exception as e:
            self.logger.error(f"Failed to get recent logs: {e}")
            return []

    def cleanup_old_data(self):
        """TTL以前のデータを削除する"""
        cutoff = time.time() - (TTL_HOURS * 3600)
        try:
            with self._lock:
                conn = sqlite3.connect(self.db_path, check_same_thread=False)
                cursor = conn.cursor()
                cursor.execute('DELETE FROM logs WHERE timestamp < ?', (cutoff,))
                deleted = cursor.rowcount
                if deleted > 0:
                    self.logger.info(f"Deleted {deleted} old log records.")
                    # データ量が減ったのでVACUUMでファイルサイズ圧縮（重いので頻度は要検討）
                    # cursor.execute('VACUUM') 
                conn.commit()
                conn.close()
        except Exception as e:
            self.logger.error(f"Cleanup failed: {e}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    store = StorageManager("test.db")
    store.save_log("test", "hello world", {"source": "manual"})
    print(store.get_recent_logs())
    store.cleanup_old_data()
