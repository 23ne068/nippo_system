import time
import cv2
import threading
import logging
import numpy as np
from ultralytics import YOLO

# 相対インポート
try:
    from ..core.config import USER_STATE_INTERVAL, YOLO_MODEL_PATH, DATA_DIR
    USER_STATE_INTERVAL = 1.0 # Force override for verification
except ImportError:
    USER_STATE_INTERVAL = 1.0
    DATA_DIR = os.path.expanduser("~/Documents/Nippo_OCR/raw_streams/data")
    YOLO_MODEL_PATH = "yolov8n-pose.pt"

class UserStateMonitor:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.model_path = YOLO_MODEL_PATH
        self.cap = None
        self.is_running = False
        self.thread = None
        
        try:
            # Load model (auto-download if missing)
            self.model = YOLO(self.model_path)
            self.logger.info("YOLOv8-pose model loaded.")
        except Exception as e:
            self.logger.error(f"Failed to load YOLO model: {e}")
            self.model = None

    def start(self):
        if self.is_running or not self.model:
            return
        self.is_running = True
        self.thread = threading.Thread(target=self._run_loop)
        self.thread.daemon = True
        self.thread.start()
        self.logger.info("UserStateMonitor started.")

    def stop(self):
        self.is_running = False
        if self.cap:
            self.cap.release()
        self.logger.info("UserStateMonitor stopped.")

    def _run_loop(self):
        # カメラは必要な時だけ開くか、開きっぱなしにするか。
        # 開きっぱなしの方が安定するが、リソースを食う。
        # ここではループ内でOpen/Closeは遅いので開きっぱなしにするが
        # intervalの間はsleepする。
        # Revert to default backend (CAP_ANY/MSMF)
        self.cap = cv2.VideoCapture(0)
        
        while self.is_running:
            try:
                if not self.cap.isOpened():
                    self.cap.open(0)
                    if not self.cap.isOpened():
                        self.logger.warning("Camera not found/busy. Retrying in 60s...")
                        time.sleep(60)
                        continue

                # バッファがたまらないように数回空読みする
                for _ in range(3):
                    self.cap.grab()
                
                ret, frame = self.cap.read()
                if not ret:
                    self.logger.warning("Failed to grab frame. Retrying in 10s...")
                    self.cap.release() # Release to reset
                    time.sleep(10)
                    continue

                # Inference
                results = self.model(frame, verbose=False)
                
                # Visualize the results on the frame
                annotated_frame = results[0].plot()

                # Display the resulting frame
                cv2.imshow('YOLO State Monitor', annotated_frame)
                
                # Save latest skeleton for user verification
                cv2.imwrite("latest_pose.jpg", annotated_frame)
                
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    pass
                
                # Analyze
                state_label = self._analyze_results(results)
                self.on_state_detected(state_label, results)
                
                # Sleep
                time.sleep(USER_STATE_INTERVAL)
                
            except Exception as e:
                self.logger.error(f"UserStateMonitor error: {e}")
                time.sleep(5)
        
        self.cap.release()

    def _analyze_results(self, results):
        if not results:
            return "Unknown"
        
        # 1人目の検出結果を取得
        r = results[0]
        if not r.keypoints:
            return "No Person"

        # keypoints: (17, 3) -> x, y, conf
        # 0: Nose, 5: Shoulder L, 6: Shoulder R, 9: Wrist L, 10: Wrist R
        # 信頼度が低い点は無視
        kpts = r.keypoints.data[0].cpu().numpy()
        
        nose = kpts[0]
        wrist_l = kpts[9]
        wrist_r = kpts[10]
        
        # 簡易判定ロジック
        current_state = "Sitting"
        
        # 手が顔（鼻）に近いか？ (ピクセル距離で簡易判定)
        # 座標が正規化されていない場合は画像の大きさ依存だが、
        # 大まかな閾値（例: 150px）で判定してみる。
        if nose[2] > 0.5: # 鼻が見えている
            dist_l = np.linalg.norm(nose[:2] - wrist_l[:2]) if wrist_l[2] > 0.5 else 9999
            dist_r = np.linalg.norm(nose[:2] - wrist_r[:2]) if wrist_r[2] > 0.5 else 9999
            
            if dist_l < 150 or dist_r < 150:
                current_state = "Thinking (Hand near face)"
        
        return current_state

    def on_state_detected(self, state, results=None):
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        print(f"STATE: {state}", flush=True)
        self.logger.info(f"User State: {state}")
        
        # Log to disk as requested (using DATA_DIR)
        output_path = os.path.join(DATA_DIR, "state_results.txt")
        with open(output_path, "a", encoding="utf-8") as f:
            log_msg = f"[{timestamp}] State: {state}"
            if results and results[0].keypoints:
                kpts = results[0].keypoints.data[0].cpu().numpy()
                # Nose ID is 0
                nose_x, nose_y, conf = kpts[0]
                log_msg += f" | Nose: (x:{int(nose_x)}, y:{int(nose_y)}, conf:{conf:.2f})"
            f.write(log_msg + "\n")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    monitor = UserStateMonitor()
    monitor.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        monitor.stop()
