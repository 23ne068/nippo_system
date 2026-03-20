import os
import sys
import queue
import json
import threading
import logging
import zipfile
import urllib.request
import sounddevice as sd
import vosk

# 相対インポート対応
try:
    from ..core.config import DATA_DIR, AUDIO_SAMPLE_RATE, VAD_MODE
except ImportError:
    DATA_DIR = os.path.expanduser("~/Documents/Nippo_OCR/raw_streams/data")
    AUDIO_SAMPLE_RATE = 16000
    VAD_MODE = 3

MODEL_NAME = "vosk-model-small-ja-0.22"
MODEL_URL = f"https://alphacephei.com/vosk/models/{MODEL_NAME}.zip"

class AudioListener:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.model_path = os.path.join(DATA_DIR, MODEL_NAME)
        self.q = queue.Queue()
        self.is_running = False
        self.thread = None
        
        # モデル準備
        self._ensure_model()
        try:
            vosk.SetLogLevel(-1) # ログ抑制
            self.model = vosk.Model(self.model_path)
            self.logger.info("Vosk model loaded.")
        except Exception as e:
            self.logger.error(f"Failed to load Vosk model: {e}")
            raise

    def _ensure_model(self):
        if not os.path.exists(self.model_path):
            self.logger.info(f"Downloading Vosk model from {MODEL_URL}...")
            if not os.path.exists(DATA_DIR):
                os.makedirs(DATA_DIR)
            
            zip_path = os.path.join(DATA_DIR, f"{MODEL_NAME}.zip")
            urllib.request.urlretrieve(MODEL_URL, zip_path)
            
            self.logger.info("Extracting model...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(DATA_DIR)
            
            os.remove(zip_path)
            self.logger.info("Model ready.")

    def _callback(self, indata, frames, time, status):
        if status:
            self.logger.warning(f"Audio status: {status}")
        self.q.put(bytes(indata))

    def start(self):
        if self.is_running:
            return
        self.is_running = True
        self.thread = threading.Thread(target=self._run_loop)
        self.thread.daemon = True
        self.thread.start()
        self.logger.info("AudioListener started.")

    def stop(self):
        self.is_running = False
        self.logger.info("AudioListener stopped.")

    def _run_loop(self):
        try:
            with sd.RawInputStream(samplerate=AUDIO_SAMPLE_RATE, blocksize=8000, dtype='int16',
                                   channels=1, callback=self._callback):
                rec = vosk.KaldiRecognizer(self.model, AUDIO_SAMPLE_RATE)
                
                while self.is_running:
                    try:
                        data = self.q.get(timeout=1.0)
                        if rec.AcceptWaveform(data):
                            res = json.loads(rec.Result())
                            text = res.get("text", "").strip()
                            if text:
                                # Safe encoding for Windows terminal
                                safe_text = text.encode('cp932', errors='ignore').decode('cp932')
                                print(f"(Audio Module): {safe_text}", flush=True)
                                self.on_speech_recognized(text)
                        else:
                            partial = json.loads(rec.PartialResult())
                            if partial.get("partial"):
                                print(f" > {partial['partial']}", end='\r', flush=True)
                    except queue.Empty:
                        continue
        except Exception as e:
            self.logger.error(f"Audio stream error: {e}")
            self.is_running = False

    def on_speech_recognized(self, text):
        # 外部からオーバーライドまたはコールバック設定することを想定
        self.logger.info(f"Recognized: {text}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        listener = AudioListener()
        listener.start()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        listener.stop()
