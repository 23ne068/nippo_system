import cv2
import numpy as np
import time
import os
import json
from ocr_engine_v2 import ProductionOCRBaseline

def load_img_robust(path):
    return cv2.imdecode(np.fromfile(path, dtype=np.uint8), cv2.IMREAD_COLOR)

def calculate_cer(reference, hypothesis):
    # Clean up whitespace for comparison
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

def parse_spec_blocks(spec_path):
    blocks = []
    if not os.path.exists(spec_path): return blocks
    with open(spec_path, "r", encoding="utf-8") as f:
        curr = None
        collecting = False
        content = ""
        for line in f:
            l = line.strip()
            if l.startswith("BLOCK"):
                if curr: 
                    curr["gt"] = content
                    blocks.append(curr)
                parts = [p.strip() for p in l.split("|")]
                curr = {"id": len(blocks)+1, "rect": (int(parts[1]), int(parts[2]), int(parts[3]), 500), "font": parts[4], "gt": ""}
                content = ""
                collecting = False
            elif l.startswith("CONTENT:"): collecting = True
            elif l.startswith("META") or l.startswith("BLOCK"): collecting = False
            elif collecting: content += l
        if curr:
            curr["gt"] = content
            blocks.append(curr)
    return blocks

def run_final_showcase():
    img_path = r"c:/Users/y86as/Nippo/ocr_lab/data/test_raw/02_dense_content.png"
    spec_path = r"c:/Users/y86as/Nippo/ocr_lab/data/test_raw/layout_spec.txt"
    out_img_path = r"c:/Users/y86as/Nippo/ocr_lab/data/results/final_showcase_overlay.png"
    
    img = load_img_robust(img_path)
    spec_blocks = parse_spec_blocks(spec_path)
    
    engine = ProductionOCRBaseline(data_dir=r"c:/Users/y86as/Nippo/nippo_system/data")
    engine.update_params(target_char_height=45) # Final Gold Standard
    
    # 1. Total Processing
    start = time.time()
    prev = np.zeros_like(img)
    canvas, p_lines = engine.process_frames(prev, img)
    ocr_out = engine.run_ocr(canvas, p_lines)
    total_time = time.time() - start
    
    # 2. Results Analysis
    print("\n" + "="*50)
    print("      SMART SCALER FINAL PERFORMANCE AUDIT")
    print("="*50)
    print(f"Total Processing Time: {total_time:.3f} seconds")
    print(f"Total Words Detected: {len(ocr_out['items'])}")
    print("-"*50)
    
    # Block Accuracy Analysis
    ih, iw = img.shape[:2]
    final_text_blocks = []
    
    for sb in spec_blocks:
        sx, sy, sw, sh = sb["rect"]
        block_text_parts = []
        for item in ocr_out.get("items", []):
            ymin, xmin, ymax, xmax = item["box_2d"]
            px, py = (xmin/1000)*iw, (ymin/1000)*ih
            if px >= sx and px <= sx + sw and py >= sy and py <= sy + sh:
                block_text_parts.append(item["description"])
        
        hyp = "".join(block_text_parts)
        cer = calculate_cer(sb["gt"], hyp)
        acc = max(0, 1 - cer)
        
        print(f"BLOCK {sb['id']} ({sb['font']}px): Accuracy {acc:.1%}")
        final_text_blocks.append(f"--- Block {sb['id']} ---\n" + " ".join(block_text_parts))

    print("-"*50)
    print("FINAL EXTRACTED OUTPUT (TOP 200 CHARS):")
    full_output = "\n\n".join(final_text_blocks)
    print(full_output[:200] + "...")
    
    # 3. Save Visual Proof
    engine.visualize_results(img, ocr_out, out_img_path)
    print(f"\nVisual proof saved to: {out_img_path}")

if __name__ == "__main__":
    run_final_showcase()
