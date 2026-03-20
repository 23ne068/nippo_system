import cv2
import numpy as np
import os
import json
import difflib
from ocr_engine_v2 import ProductionOCRBaseline

import sys
if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def calculate_cer(reference, hypothesis):
    if not reference: return 1.0 if hypothesis else 0.0
    reference = "".join(reference.split())
    hypothesis = "".join(hypothesis.split())
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

def parse_spec_v2(spec_path):
    blocks = []
    if not os.path.exists(spec_path): return blocks
    
    with open(spec_path, "r", encoding="utf-8") as f:
        curr_block = None
        collecting = False
        content = ""
        for line in f:
            line = line.strip()
            if line.startswith("BLOCK"):
                if curr_block:
                    curr_block["gt"] = content
                    blocks.append(curr_block)
                parts = [p.strip() for p in line.split("|")]
                curr_block = {
                    "rect": (int(parts[1]), int(parts[2]), int(parts[3]), 0), # Height computed later or ignored
                    "font_size": int(parts[4]),
                    "id": len(blocks) + 1
                }
                content = ""
                collecting = False
            elif line.startswith("CONTENT:"):
                collecting = True
            elif line.startswith("BLOCK") or line.startswith("META") or line.startswith("#"):
                collecting = False
            elif collecting:
                content += line
        if curr_block:
            curr_block["gt"] = content
            blocks.append(curr_block)
    return blocks

def evaluate_block_by_block():
    img_path = r"c:/Users/y86as/Nippo/ocr_lab/data/test_raw/02_dense_content.png"
    spec_path = r"c:/Users/y86as/Nippo/ocr_lab/data/test_raw/layout_spec.txt"
    
    img = cv2.imdecode(np.fromfile(img_path, dtype=np.uint8), cv2.IMREAD_COLOR)
    spec_blocks = parse_spec_v2(spec_path)
    
    engine = ProductionOCRBaseline(data_dir=r"c:/Users/y86as/Nippo/nippo_system/data")
    
    # 1. Evaluate with Baseline (1.0x)
    # 2. Evaluate with Smart Scaler (Adaptive)
    
    modes = [
        {"name": "Static 1.0x", "params": {"scale_factor": 1.0, "target_char_height": 0}},
        {"name": "Smart Scaler", "params": {"target_char_height": 45}}
    ]
    
    results = {}
    
    for mode in modes:
        print(f"\n--- Testing Mode: {mode['name']} ---")
        engine.update_params(**mode['params'])
        mode_results = []
        
        for sb in spec_blocks:
            # We want to see how well our engine detects THIS block specifically
            # To simulate production, we'll run the full process_frames on the WHOLE image
            # then look for detections inside this block's region.
            
            # Run engine
            prev = np.zeros_like(img)
            canvas, p_lines = engine.process_frames(prev, img)
            ocr_out = engine.run_ocr(canvas, p_lines)
            
            # Filter words falling into this spec block
            sx, sy, sw, _ = sb["rect"]
            # To ensure we capture the whole block, use a sufficiently large height or parse it.
            # Using 500 to ensure we capture all 10+ lines of these test blocks since they don't overlap vertically.
            sh = 500
            
            block_words = []
            for item in ocr_out.get("items", []):
                # box_2d is [ymin, xmin, ymax, xmax] in 0-1000 scale
                ymin, xmin, ymax, xmax = item["box_2d"]
                # Convert back to pixel
                ih, iw = img.shape[:2]
                px_xmin, px_ymin = (xmin/1000.0)*iw, (ymin/1000.0)*ih
                px_xmax, px_ymax = (xmax/1000.0)*iw, (ymax/1000.0)*ih
                
                # Check overlap: center point of the detected word must be inside the block
                cx = (px_xmin + px_xmax) / 2
                cy = (px_ymin + px_ymax) / 2
                
                if cx >= sx and cx <= sx + sw and cy >= sy and cy <= sy + sh:
                    block_words.append(item["description"])
            
            hyp = "".join(block_words)
            print(f"  [DEBUG GT] {repr(sb['gt'][:50])}...")
            print(f"  [DEBUG HY] {repr(hyp[:50])}...")
            if block_words:
                print(f"  [Sample Words] {block_words[:5]}")
            
            cer = calculate_cer(sb["gt"], hyp)
            acc = max(0, 1 - cer)
            
            mode_results.append({
                "block_id": sb["id"],
                "font_size": sb["font_size"],
                "cer": cer,
                "accuracy": acc,
                "words": len(block_words)
            })
            print(f"Block {sb['id']} ({sb['font_size']}px): Acc {acc:.2%} (Words: {len(block_words)})")
            
        results[mode["name"]] = mode_results

    # Final Summary Table
    print("\n--- Final Adaptive Accuracy Report ---")
    print(f"| Mode | Block 1 (20px) | Block 2 (16px) | Block 3 (12px) | Block 4 (Tab) | Average |")
    print(f"| :--- | :--- | :--- | :--- | :--- | :--- |")
    for mode_name, res in results.items():
        accs = [r["accuracy"] for r in res]
        avg = sum(accs)/len(accs)
        print(f"| {mode_name} | {res[0]['accuracy']:.1%} | {res[1]['accuracy']:.1%} | {res[2]['accuracy']:.1%} | {res[3]['accuracy']:.1%} | **{avg:.1%}** |")

if __name__ == "__main__":
    evaluate_block_by_block()
