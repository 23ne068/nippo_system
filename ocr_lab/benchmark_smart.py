import cv2
import numpy as np
import time
import os
import json
from ocr_engine_v2 import ProductionOCRBaseline

def load_img_robust(path):
    return cv2.imdecode(np.fromfile(path, dtype=np.uint8), cv2.IMREAD_COLOR)

def calculate_cer(reference, hypothesis):
    if not reference: return 1.0 if hypothesis else 0.0
    m, n = len(reference), len(hypothesis)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m + 1): dp[i][0] = i
    for j in range(n + 1): dp[0][j] = j
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if reference[i-1] == hypothesis[j-1]:
                dp[i][j] = dp[i-1][j-1]
            else:
                dp[i][j] = 1 + min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1])
    return dp[m][n] / m

def get_ground_truth(spec_path):
    gt = ""
    if not os.path.exists(spec_path): return ""
    with open(spec_path, "r", encoding="utf-8") as f:
        collecting = False
        for line in f:
            line = line.strip()
            if line.startswith("CONTENT:"): collecting = True
            elif line.startswith("BLOCK"): collecting = False
            elif collecting and line: gt += line
    return "".join(gt.split())

def benchmark():
    prev_path = r"c:/Users/y86as/Nippo/ocr_lab/data/test_raw/01_all_black.png"
    curr_path = r"c:/Users/y86as/Nippo/ocr_lab/data/test_raw/02_dense_content.png"
    spec_path = r"c:/Users/y86as/Nippo/ocr_lab/data/test_raw/layout_spec.txt"
    
    prev = load_img_robust(prev_path)
    curr = load_img_robust(curr_path)
    gt_text = get_ground_truth(spec_path)
    
    engine = ProductionOCRBaseline(data_dir=r"c:/Users/y86as/Nippo/nippo_system/data")
    
    scenarios = [
        {"name": "Baseline (1.0x)", "params": {"scale_factor": 1.0, "target_char_height": 0}}, # 0 triggers "dumb" 1.0x if we modify engine or just use scale
        {"name": "Best Static (2.5x)", "params": {"scale_factor": 2.5, "target_char_height": 0}},
        {"name": "Smart Scaler (Adaptive)", "params": {"target_char_height": 45}}
    ]
    
    # We need to ensure engine respects target_char_height=0 as "disable adaptive"
    # Actually I'll just temporarily patch engine or set a very low target
    
    print(f"| Scenario | Words | Accuracy | Proc Time | CER |")
    print(f"| :--- | :--- | :--- | :--- | :--- |")
    
    for s in scenarios:
        engine.update_params(**s["params"])
        
        start = time.time()
        canvas, p_lines = engine.process_frames(prev, curr)
        if canvas is not None:
            ocr_out = engine.run_ocr(canvas, p_lines)
            end = time.time()
            
            items = ocr_out.get("items", [])
            hyp_text = "".join([it["description"] for it in items])
            hyp_clean = "".join(hyp_text.split())
            
            if s["name"] == "Smart Scaler (Adaptive)":
                print(f"\n[DEBUG GT] {gt_text[:100]}...")
                print(f"[DEBUG HY] {hyp_clean[:100]}...")
            
            cer = calculate_cer(gt_text, hyp_clean)
            acc = max(0, 1 - cer)
            
            print(f"| {s['name']} | {len(items)} | {acc:.2%} | {end-start:.2f}s | {cer:.4f} |")
        else:
            print(f"| {s['name']} | FAILED | - | - | - |")

if __name__ == "__main__":
    benchmark()
