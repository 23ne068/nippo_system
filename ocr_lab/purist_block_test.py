import cv2
import numpy as np
import os
import sys
import io
from ocr_engine_v2 import ProductionOCRBaseline

# Force UTF-8 output for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def load_img_robust(path):
    return cv2.imdecode(np.fromfile(path, dtype=np.uint8), cv2.IMREAD_COLOR)

def purist_block_test():
    img_path = r"c:/Users/y86as/Nippo/ocr_lab/data/test_raw/02_dense_content.png"
    img = load_img_robust(img_path)
    engine = ProductionOCRBaseline(data_dir=r"c:/Users/y86as/Nippo/nippo_system/data")
    engine.update_params(target_char_height=45)
    
    # 1. Detect blocks
    prev = np.zeros_like(img)
    canvas, p_lines = engine.process_frames(prev, img)
    # p_lines contains the blocks we found and scaled
    
    print("\n--- Purist Block-Based Test Results ---")
    print(f"| Block | Original Size | Adaptive Scale | Detected Text Sample |")
    print(f"| :--- | :--- | :--- | :--- |")
    
    for i, p in enumerate(p_lines):
        # Run OCR on ONLY THIS SINGLE BLOCK canvas
        # We'll create a tiny canvas for just this block
        block_img = p['img']
        # We need p_lines format for run_ocr
        temp_p_line = p.copy()
        temp_p_line['canvas_y'] = 80 # dummy spacing
        temp_canvas = np.zeros((block_img.shape[0]+160, block_img.shape[1], 3), dtype=np.uint8)
        temp_canvas[80:80+block_img.shape[0], :] = block_img
        
        ocr_out = engine.run_ocr(temp_canvas, [temp_p_line])
        items = ocr_out.get("items", [])
        text = " ".join([it["description"] for it in items])
        
        rect = p["orig_rect"]
        scale = p["scale_applied"]
        
        print(f"| {i+1} | {rect[2]}x{rect[3]} | {scale:.2f}x | {text[:50]}... |")

if __name__ == "__main__":
    purist_block_test()
