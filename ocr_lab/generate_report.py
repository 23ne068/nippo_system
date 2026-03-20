import cv2
import numpy as np
import os
import difflib
from ocr_engine_v2 import ProductionOCRBaseline

def calculate_cer(reference, hypothesis):
    # Strip spaces for comparison to focus on content accuracy
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

def parse_spec_blocks_v3(spec_path):
    blocks = []
    if not os.path.exists(spec_path): return blocks
    with open(spec_path, "r", encoding="utf-8") as f:
        curr = None
        collecting = False
        lines = []
        for line in f:
            l = line.strip()
            if l.startswith("BLOCK"):
                if curr: 
                    curr["gt_lines"] = [ln for ln in lines if ln.strip()]
                    blocks.append(curr)
                parts = [p.strip() for p in l.split("|")]
                curr = {"id": len(blocks)+1, "name": f"Block {len(blocks)+1}", "rect": (int(parts[1]), int(parts[2]), int(parts[3])), "font": int(parts[4]), "gt_lines": []}
                lines = []
                collecting = False
            elif l.startswith("CONTENT:"):
                collecting = True
            elif l.startswith("META") or l.startswith("#"):
                collecting = False
            elif collecting:
                lines.append(line.rstrip())
        if curr:
            curr["gt_lines"] = [ln for ln in lines if ln.strip()]
            blocks.append(curr)
    return blocks

def generate_report():
    img_path = r"c:/Users/y86as/Nippo/ocr_lab/data/test_raw/02_dense_content.png"
    spec_path = r"c:/Users/y86as/Nippo/ocr_lab/data/test_raw/layout_spec.txt"
    report_path = r"c:/Users/y86as/Nippo/ocr_lab/data/results/accuracy_report.txt"
    
    img = cv2.imdecode(np.fromfile(img_path, dtype=np.uint8), cv2.IMREAD_COLOR)
    spec_blocks = parse_spec_blocks_v3(spec_path)
    engine = ProductionOCRBaseline(data_dir=r"c:/Users/y86as/Nippo/nippo_system/data")
    engine.update_params(target_char_height=45)
    
    prev = np.zeros_like(img)
    canvas, p_lines = engine.process_frames(prev, img)
    ocr_out = engine.run_ocr(canvas, p_lines)
    
    # Map OCR blocks to Spec blocks
    # We use spatial proximity of the block origins
    id_map = {} # ocr_block_id -> spec_block_id (1-indexed)
    for idx, p in enumerate(p_lines):
        ox, oy, _, _ = p["orig_rect"]
        best_spec_id = -1
        min_dist = 9999
        for sb in spec_blocks:
            sx, sy, _ = sb["rect"]
            dist = ((ox-sx)**2 + (oy-sy)**2)**0.5
            if dist < min_dist:
                min_dist = dist
                best_spec_id = sb["id"]
        if min_dist < 150:
            id_map[idx] = best_spec_id

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("=== OCR PHASE 3 ACCURACY REPORT (STRUCTURAL ISOLATION) ===\n")
        f.write(f"Total Processing Time: {ocr_out.get('duration', 0.0):.2f}s\n\n")
        
        for sb in spec_blocks:
            # Find detected lines for this specific block using id_map
            detected_lines = []
            for item in ocr_out.get("items", []):
                if id_map.get(item.get("block_id")) == sb["id"]:
                    detected_lines.append(item["description"])
            
            # Find adaptive scale used for this block
            used_scale = 1.0
            for idx, spec_id in id_map.items():
                if spec_id == sb["id"]:
                    used_scale = p_lines[idx]["scale_applied"]
                    break

            f.write(f"[{sb['name']} - Font: {sb['font']}px - Scale: {used_scale:.2f}x]\n")
            f.write(f"{'Detected (Hypothesis)':<50} | {'CER':>6} | {'Target (Ground Truth)':<50}\n")
            f.write("-" * 115 + "\n")
            
            gt_lines = sb["gt_lines"]
            matcher = difflib.SequenceMatcher(None, gt_lines, detected_lines)
            total_cer = 0
            
            for tag, i1, i2, j1, j2 in matcher.get_opcodes():
                if tag == 'equal':
                    for i in range(i1, i2):
                        gt, hyp = gt_lines[i], detected_lines[j1 + (i - i1)]
                        cer = calculate_cer(gt, hyp)
                        total_cer += cer
                        f.write(f"{hyp[:50]:<50} | {cer:5.1%} | {gt[:50]:<50}\n")
                elif tag == 'replace':
                    for i in range(i1, i2):
                        gt = gt_lines[i]
                        hyp = detected_lines[j1 + (i - i1)] if (j1 + (i - i1)) < j2 else "[MISSING]"
                        cer = calculate_cer(gt, hyp) if hyp != "[MISSING]" else 1.0
                        total_cer += cer
                        f.write(f"{hyp[:50]:<50} | {cer:5.1%} | {gt[:50]:<50}\n")
                    if j2 - j1 > i2 - i1:
                        for j in range(j1 + (i2 - i1), j2):
                            f.write(f"{detected_lines[j][:50]:<50} |  EXTRA | {'[EXTRA]':<50}\n")
                elif tag == 'delete':
                    for i in range(i1, i2):
                        total_cer += 1.0
                        f.write(f"{'[MISSING]':<50} | 100.0% | {gt_lines[i][:50]:<50}\n")
                elif tag == 'insert':
                    for j in range(j1, j2):
                        f.write(f"{detected_lines[j][:50]:<50} |  EXTRA | {'[EXTRA]':<50}\n")
            
            avg_acc = max(0, 1 - (total_cer / len(gt_lines))) if gt_lines else 0
            f.write(f"\n>> BLOCK AVERAGE ACCURACY: {avg_acc:.2%}\n")
            f.write("=" * 115 + "\n\n")

if __name__ == "__main__":
    generate_report()
