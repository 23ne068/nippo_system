import time
import threading
import logging
from pynput import keyboard, mouse

try:
    import win32gui
    import win32process
except ImportError:
    win32gui = None
    win32process = None

# 相対インポートの問題を避けるため、単体実行時とモジュール実行時で切り替え
try:
    from ..core.config import SENSITIVE_APP_NAMES
except ImportError:
    # デバッグ用デフォルト値
    SENSITIVE_APP_NAMES = ["password", "private", "bank", "login", "secret"]

class InputMonitor:
    def __init__(self):
        self.key_count = 0
        self.mouse_distance = 0
        self.active_window_title = ""
        self.is_running = False
        self._lock = threading.Lock()
        self.logger = logging.getLogger(__name__)
        self.event_queue = [] # バッファ用のイベントリスト

    def start(self):
        """監視を開始する"""
        if self.is_running:
            return

        self.is_running = True
        
        # キーボードリスナー
        self.k_listener = keyboard.Listener(on_press=self._on_press)
        self.k_listener.start()
        
        # マウスリスナー (移動、クリックの両方を監視するように拡張可能)
        self.m_listener = mouse.Listener(on_move=self._on_move, on_click=self._on_click)
        self.m_listener.start()
        
        # ウィンドウ監視スレッド
        self.w_thread = threading.Thread(target=self._monitor_window)
        self.w_thread.daemon = True
        self.w_thread.start()
        
        self.logger.info("InputMonitor started.")

    def stop(self):
        """監視を停止する"""
        self.is_running = False
        if hasattr(self, 'k_listener'):
            self.k_listener.stop()
        if hasattr(self, 'm_listener'):
            self.m_listener.stop()
        self.logger.info("InputMonitor stopped.")

    def _on_press(self, key):
        with self._lock:
            self.key_count += 1
            try:
                k = key.char  # 普通の文字
            except AttributeError:
                k = str(key)  # 特殊キー (Key.ctrl等)
            
            self.event_queue.append({
                "type": "key",
                "val": k,
                "window": self.active_window_title,
                "time": time.time()
            })

    def _on_move(self, x, y):
        with self._lock:
            self.mouse_distance += 1

    def _on_click(self, x, y, button, pressed):
        if pressed:
            with self._lock:
                self.event_queue.append({
                    "type": "click",
                    "val": f"{button}",
                    "pos": (x, y),
                    "window": self.active_window_title,
                    "time": time.time()
                })

    def _monitor_window(self):
        while self.is_running:
            try:
                if win32gui:
                    hwnd = win32gui.GetForegroundWindow()
                    title = win32gui.GetWindowText(hwnd)
                else:
                    title = "Unknown (win32gui not installed)"

                # プライバシーチェック
                try:
                    from ..utils.privacy import is_sensitive_window
                    is_sensitive = is_sensitive_window(title)
                except ImportError:
                     # フォールバック
                    is_sensitive = any(s.lower() in title.lower() for s in SENSITIVE_APP_NAMES)
                
                with self._lock:
                    if is_sensitive:
                        self.active_window_title = "[REDACTED]"
                    else:
                        self.active_window_title = title
            except Exception as e:
                self.logger.error(f"Error getting window title: {e}")
            
            time.sleep(1.0) # 1秒ごとにポーリング

    def get_stats(self):
        """現在の統計情報と詳細イベントを取得し、カウンタをリセットする"""
        with self._lock:
            stats = {
                "keys": self.key_count,
                "mouse": self.mouse_distance,
                "window": self.active_window_title,
                "timestamp": time.time(),
                "events": list(self.event_queue) # 現在のキューをコピー
            }
            # カウンタとバッファをリセット
            self.key_count = 0
            self.mouse_distance = 0
            self.event_queue = []
            return stats

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    monitor = InputMonitor()
    monitor.start()
    
    try:
        while True:
            time.sleep(5)
            stats = monitor.get_stats()
            print(f"Stats: {stats}")
    except KeyboardInterrupt:
        monitor.stop()
