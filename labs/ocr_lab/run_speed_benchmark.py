import cv2
import time
import os
import numpy as np
from ocr_engine_v2 import ProductionOCRBaseline

def load_img_robust(path):
    return cv2.imdecode(np.fromfile(path, dtype=np.uint8), cv2.IMREAD_COLOR)

def benchmark_speed():
    prev_img = r"c:/Users/y86as/Nippo/ocr_lab/data/raw/スクリーンショット 2026-02-20 192914.png"
    curr_img = r"c:/Users/y86as/Nippo/ocr_lab/data/raw/スクリーンショット 2026-02-20 192938.png"
    prev = load_img_robust(prev_img)
    curr = load_img_robust(curr_img)
    
    engine = ProductionOCRBaseline(data_dir=r"c:/Users/y86as/Nippo/nippo_system/data")
    
    # Test cases: (Scale, Spacing)
    tests = [
        (1.0, 80),
        (2.0, 80),
        (2.6, 80),
        (2.6, 40),
        (2.6, 120),
    ]
    
    print("| Scale | Spacing | Duration (s) | Canvas Size |", flush=True)
    print("| :--- | :--- | :--- | :--- |", flush=True)
    
    for s, sp in tests:
        engine.update_params(scale_factor=s, line_spacing=sp)
        
        start = time.time()
        canvas, p_lines = engine.process_frames(prev, curr)
        if canvas is not None:
            results = engine.run_ocr(canvas, p_lines)
            end = time.time()
            duration = end - start
            h, w = canvas.shape[:2]
            print(f"| {s}x | {sp}px | {duration:.2f}s | {w}x{h} |", flush=True)
        else:
            print(f"| {s}x | {sp}px | Failed | - |", flush=True)

if __name__ == "__main__":
    benchmark_speed()
