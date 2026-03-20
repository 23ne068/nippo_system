import cv2
import numpy as np
import os
from ocr_engine_v2 import ProductionOCRBaseline

def load_img_robust(path):
    return cv2.imdecode(np.fromfile(path, dtype=np.uint8), cv2.IMREAD_COLOR)

def verify_estimation():
    curr_path = r"c:/Users/y86as/Nippo/ocr_lab/data/test_raw/02_dense_content.png"
    curr = load_img_robust(curr_path)
    # Treat whole image as new for this test
    prev = np.zeros_like(curr)
    
    engine = ProductionOCRBaseline(data_dir=r"c:/Users/y86as/Nippo/nippo_system/data")
    # Use baseline params for measurement (1.0x scale to see original metrics)
    engine.update_params(scale_factor=1.0, group_v_dist=15)
    
    canvas, processed_lines = engine.process_frames(prev, curr)
    
    print("\n--- Estimation Verification Results ---")
    print(f"| Block | Box (X,Y,W,H) | Est. Font Size | Est. Line Count | Adaptive Scale |")
    print(f"| :--- | :--- | :--- | :--- | :--- |")
    
    for i, p in enumerate(processed_lines):
        rect = p["orig_rect"]
        m = p["metrics"]
        scale = p["scale_applied"]
        print(f"| {i+1} | {rect} | {m['avg_font_height']:.1f}px | {m['line_count']} | {scale:.2f}x |")

    print("\n--- Ground Truth (from layout_spec.txt) ---")
    print("| Block | Real Font Size | Real Line Count |")
    print("| :--- | :--- | :--- |")
    print("| 1 (Main) | 20px | 10 |")
    print("| 2 (Sidebar) | 16px | 8 |")
    print("| 3 (Footer) | 12px | 2 |")
    print("| 4 (Tab) | 18px | 2 |")

if __name__ == "__main__":
    verify_estimation()
