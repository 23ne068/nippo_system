import sys
import json
import time
import asyncio
import numpy as np
import cv2
import mss
import threading
import logging
import pytesseract
import os

# Import Config
try:
    import config
except ImportError:
    try:
        from . import config
    except ImportError:
        config = None

if config:
    SCREEN_CAPTURE_INTERVAL = getattr(config, 'SCREEN_CAPTURE_INTERVAL', 5.0)
    OCR_DIFF_THRESHOLD = getattr(config, 'OCR_DIFF_THRESHOLD', 5000)
    OCR_LANG = getattr(config, 'OCR_LANG', 'jpn+eng')
    DATA_DIR = getattr(config, 'DATA_DIR', 'data')
else:
    SCREEN_CAPTURE_INTERVAL = 5.0
    OCR_DIFF_THRESHOLD = 5000
    OCR_LANG = "jpn+eng"
    DATA_DIR = "data"

# Import V2 Engine
try:
    from ocr_engine_v2 import ProductionOCRBaseline
except ImportError as e:
    logging.error(f"Failed to import OCR Engine v2: {e}")
    ProductionOCRBaseline = None

class ScreenOCR:
    def __init__(self, output_dir=None, save_debug_images=False, monitor_id=1):
        self.monitor_id = monitor_id
        self.logger = logging.getLogger(__name__)
        
        # Define stable data directory in user's Documents
        user_docs = os.path.expanduser("~/Documents/Nippo_OCR/data")
        global DATA_DIR
        DATA_DIR = user_docs

        # Ensure target directory exists
        os.makedirs(DATA_DIR, exist_ok=True)

        self.output_dir = output_dir if output_dir else DATA_DIR
        self.save_debug_images = save_debug_images
        self.prev_gray = None
        self.prev_gray_bgr = None
        self.is_running = False
        self.thread = None
        
        if ProductionOCRBaseline:
            self.engine = ProductionOCRBaseline(data_dir=DATA_DIR)
            # Use Smart Scaler Settings (Phase 3 Defaults)
            self.engine.update_params(target_char_height=45)
        else:
            self.engine = None
            self.logger.error("ScreenOCR initialized without engine backend.")

        # Stateful Deduplication Cache
        self.prev_lines = []

    def start(self):
        if self.is_running or not self.engine:
            return
        self.is_running = True
        self.thread = threading.Thread(target=self._run_loop)
        self.thread.daemon = True
        self.thread.start()
        self.logger.info("ScreenOCR started (v2 engine).")

    def stop(self):
        self.is_running = False
        self.logger.info("ScreenOCR stopped.")

    def _run_loop(self):
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except AttributeError:
            pass

        with mss.mss() as sct:
            try:
                monitor = sct.monitors[self.monitor_id]
            except IndexError:
                self.logger.warning(f"Monitor {self.monitor_id} not found. Falling back to monitor 1.")
                monitor = sct.monitors[1]
                
            while self.is_running:
                try:
                    start_time = time.time()
                    
                    sct_img = sct.grab(monitor)
                    frame = np.array(sct_img)
                    frame_bgr = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                    gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
                
                    if self.prev_gray is not None and self.prev_gray_bgr is not None:
                        diff = cv2.absdiff(self.prev_gray, gray)
                        _, thresh = cv2.threshold(diff, 30, 255, cv2.THRESH_BINARY)
                        count = cv2.countNonZero(thresh)
                        
                        if count > OCR_DIFF_THRESHOLD:
                            # 1. Image Processing & Layout extraction (v2)
                            canvas, p_lines = self.engine.process_frames(self.prev_gray_bgr, frame_bgr)
                            
                            if canvas is not None and p_lines:
                                # 2. Isolated OCR Pipeline (v2)
                                ocr_start = time.time()
                                ocr_out = self.engine.run_ocr(canvas, p_lines)
                                print(f"[OCR] Processed in: {time.time() - ocr_start:.4f}s", flush=True)
                                
                                if ocr_out:
                                    self._save_and_broadcast(ocr_out, frame_w=monitor['width'], frame_h=monitor['height'])
                            
                    self.prev_gray = gray
                    self.prev_gray_bgr = frame_bgr.copy()
                    
                    elapsed = time.time() - start_time
                    wait = max(0.1, SCREEN_CAPTURE_INTERVAL - elapsed)
                    time.sleep(wait)
                
                except Exception as e:
                    self.logger.error(f"ScreenOCR error: {e}")
                    time.sleep(5)

    def _save_and_broadcast(self, ocr_out, frame_w, frame_h):
        try:
            now = time.localtime()
            date_str = time.strftime('%Y-%m-%d', now)
            time_str = time.strftime('%H:%M:%S', now)
            
            # TSV (.tsv) 形式で保存
            output_filename = f"ocr_stream_{date_str}.tsv"
            output_path = os.path.join(self.output_dir, output_filename)
            
            unique_items = self._filter_duplicates(ocr_out.get("items", []))
            if not unique_items: 
                return

            with open(output_path, "a", encoding="utf-8") as f:
                for item in unique_items:
                    # [時刻] | [ID] | [座標] | [テキスト]
                    # テキスト内の改行やタブは前処理でエスケープ
                    clean_text = item.get('description', '').replace('\n', '\\n').replace('\t', ' ')
                    box = json.dumps(item.get('box_2d', []))
                    block_id = item.get('id', '0')
                    
                    f.write(f"{time_str}\t{block_id}\t{box}\t{clean_text}\n")
            
            full_text = " ".join([i['description'] for i in unique_items])
            self.on_text_detected(full_text)
            
        except Exception as e:
            self.logger.error(f"Saving OCR results (TSV) failed: {e}")

    def _filter_duplicates(self, new_items):
        return new_items

    def on_text_detected(self, text):
        preview = text[:50].replace('\n', ' ')
        print(f"[OCR] (Saved to file): {preview}...", flush=True)
        self.logger.info(f"OCR: {preview}...")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Parse monitor_id from command line arguments if provided
    import sys
    monitor_id = 1
    if len(sys.argv) > 1:
        try:
            monitor_id = int(sys.argv[1])
        except ValueError:
            pass

    ocr = ScreenOCR(monitor_id=monitor_id)
    ocr.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        ocr.stop()
