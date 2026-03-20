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

# Relative Import
try:
    from ..core.config import SCREEN_CAPTURE_INTERVAL, OCR_DIFF_THRESHOLD, OCR_LANG, OCR_STREAM_DIR, DATA_DIR, THROTTLE_OCR_INTERVAL, ENABLE_YIELD_MODE, ACTIVITY_THRESHOLD_SEC, PENDING_FRAMES_DIR, INPUT_STREAM_DIR
except ImportError:
    SCREEN_CAPTURE_INTERVAL = 5.0
    OCR_DIFF_THRESHOLD = 5000
    OCR_LANG = "jpn+eng"
    OCR_STREAM_DIR = os.path.expanduser("~/Documents/Nippo_OCR/raw_streams/ocr")
    DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
    ENABLE_YIELD_MODE = False

# Import Pluggable OCR Engine
import sys
import platform
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(script_dir))
nippo_ocr_path = os.path.join(project_root, "nippo-ocr", "src")
if nippo_ocr_path not in sys.path:
    sys.path.append(nippo_ocr_path)

try:
    from nippo_ocr import create_ocr_engine
except ImportError as e:
    logging.error(f"Failed to import nippo_ocr package: {e}")
    create_ocr_engine = None

class ScreenOCR:
    def __init__(self, output_dir=None, save_debug_images=False):
        self.logger = logging.getLogger(__name__)
        
        self.output_dir = output_dir if output_dir else OCR_STREAM_DIR
        self.save_debug_images = save_debug_images
        self.prev_gray = None
        self.prev_gray_bgr = None
        self.is_running = False
        self.thread = None
        
        if create_ocr_engine:
            if platform.system() == "Windows":
                self.engine = create_ocr_engine("winrt")
                self.logger.info("Initialized high-speed WinRT OCR Engine for Windows.")
            else:
                self.engine = create_ocr_engine("tesseract", data_dir=DATA_DIR)
                self.engine.update_params(target_char_height=45)
                self.logger.info("Initialized Tesseract OCR Engine for Linux/Mac.")
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
        # 1. 整理: 撮影スレッド (Producer) と解析スレッド (Consumer) を分離
        producer_thread = threading.Thread(target=self._producer_loop, daemon=True)
        consumer_thread = threading.Thread(target=self._consumer_loop, daemon=True)
        
        producer_thread.start()
        consumer_thread.start()
        
        while self.is_running:
            time.sleep(1)

    def _producer_loop(self):
        """[Producer] 5秒おきに撮影し、変化があれば即座に保存する (漏らさない)"""
        self.logger.info("OCR Producer started (Capture only).")
        with mss.mss() as sct:
            monitor = sct.monitors[1]
            while self.is_running:
                try:
                    start_time = time.time()
                    sct_img = sct.grab(monitor)
                    frame = np.array(sct_img)
                    frame_bgr = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                    gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)

                    if self.prev_gray is not None:
                        diff = cv2.absdiff(self.prev_gray, gray)
                        _, thresh = cv2.threshold(diff, 30, 255, cv2.THRESH_BINARY)
                        count = cv2.countNonZero(thresh)
                        
                        if count > OCR_DIFF_THRESHOLD:
                            # 変化あり: pending_frames に保存
                            ts = time.strftime('%H%M%S')
                            now_ms = int((time.time() % 1) * 1000)
                            filename = f"frame_{ts}_{now_ms:03d}.jpg"
                            filepath = os.path.join(PENDING_FRAMES_DIR, filename)
                            cv2.imwrite(filepath, frame_bgr)
                            print(f"[Producer] Capture saved (diff={count}): {filename}", flush=True)

                    self.prev_gray = gray
                    self.prev_gray_bgr = frame_bgr.copy()
                    
                    elapsed = time.time() - start_time
                    time.sleep(max(0.1, SCREEN_CAPTURE_INTERVAL - elapsed))
                except Exception as e:
                    self.logger.error(f"Producer error: {e}")
                    time.sleep(1)

    def _consumer_loop(self):
        """[Consumer] 保存された画像を順次OCRする (OSの暇を見てバックログを消化)"""
        self.logger.info("OCR Consumer started (Processing only).")
        last_consumed_gray = None
        
        while self.is_running:
            try:
                # pending_frames 内の古い順に1枚取得
                files = sorted([f for f in os.listdir(PENDING_FRAMES_DIR) if f.endswith('.jpg')])
                if not files:
                    time.sleep(2)
                    continue
                
                target_file = files[0]
                target_path = os.path.join(PENDING_FRAMES_DIR, target_file)
                
                # OCR実行
                frame_bgr = cv2.imread(target_path)
                if frame_bgr is None:
                    try: os.remove(target_path)
                    except: pass
                    continue

                curr_gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
                
                # v2エンジンに「どこが文字か」を教えるための比較
                # バックログの場合、1つ前の画像と比較するか、初回は真っ黒な画像と比較して全部出す
                if last_consumed_gray is None:
                    ref_frame = np.zeros_like(frame_bgr)
                else:
                    ref_frame = cv2.cvtColor(last_consumed_gray, cv2.COLOR_GRAY2BGR)

                ocr_start = time.time()
                # モニタサイズを画像から取得
                h, w = frame_bgr.shape[:2]
                canvas, p_lines = self.engine.process_frames(ref_frame, frame_bgr)
                
                if canvas is not None and p_lines:
                    # 正しい解像度を渡して正規化 (0-1000) を行わせる
                    ocr_out = self.engine.run_ocr(canvas, p_lines, screen_size=(w, h))
                    ocr_dur = time.time() - ocr_start
                    print(f"[Consumer] Processed: {target_file} (dur={ocr_dur:.1f}s). Remaining: {len(files)-1}", flush=True)
                    if ocr_out:
                        self._save_and_broadcast(ocr_out, frame_w=w, frame_h=h)
                else:
                    # テキストが見つからなかった場合もログを出す
                    print(f"[Consumer] No text found in {target_file}. Skipping.", flush=True)
                
                last_consumed_gray = curr_gray

                # 処理完了したら削除
                try:
                    os.remove(target_path)
                except: pass
                
                time.sleep(0.5) 
                
            except Exception as e:
                self.logger.error(f"Consumer error: {e}")
                time.sleep(2)

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
    ocr = ScreenOCR()
    ocr.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        ocr.stop()
