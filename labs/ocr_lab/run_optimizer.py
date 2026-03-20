import cv2
import os
import json
import time
import itertools
from ocr_engine_v2 import ProductionOCRBaseline

def load_img_robust(path):
    if not os.path.exists(path): return None
    import numpy as np
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

def run_experiment():
    prev_path = r"c:/Users/y86as/Nippo/ocr_lab/data/test_raw/01_all_black.png"
    curr_path = r"c:/Users/y86as/Nippo/ocr_lab/data/test_raw/02_dense_content.png"
    spec_path = r"c:/Users/y86as/Nippo/ocr_lab/data/test_raw/layout_spec.txt"
    
    prev = load_img_robust(prev_path)
    curr = load_img_robust(curr_path)
    gt_text = get_ground_truth(spec_path)

    if prev is None or curr is None:
        print("Error: Could not load stress test images.")
        return

    # Super-Grid (Phase 2 Extreme)
    grid = {
        "scale_factor": [2.3, 2.5, 2.7],
        "line_spacing": [80, 85],
        "group_v_dist": [14, 16],
        "group_h_dist": [13, 15],
        "dilation_iterations": [1, 2]
    }

    # Generate all combinations
    keys, values = zip(*grid.items())
    combinations = [dict(zip(keys, v)) for v in itertools.product(*values)]
    
    # Create results directory at start
    os.makedirs("data/experiments", exist_ok=True)
    
    engine = ProductionOCRBaseline(data_dir=r"c:/Users/y86as/Nippo/nippo_system/data")
    
    results = []
    print(f"Starting Super-Grid Search: {len(combinations)} combinations...", flush=True)
    
    start_all = time.time()
    for i, params in enumerate(combinations):
        print(f"[{i+1}/{len(combinations)}] Testing: {params}", end=" ", flush=True)
        engine.update_params(**params)
        
        start_t = time.time()
        canvas, p_lines = engine.process_frames(prev, curr)
        if canvas is not None:
            # 2. Run OCR
            h, w = curr.shape[:2]
            ocr_out = engine.run_ocr(canvas, p_lines, screen_size=(w, h))
            end_t = time.time()
            
            # 3. Analyze Results
            items = ocr_out.get("items", [])
            hyp_text = "".join([it["description"] for it in items])
            hyp_clean = "".join(hyp_text.split())
            
            cer = calculate_cer(gt_text, hyp_clean)
            accuracy = max(0, 1 - cer)
            
            results.append({
                "id": i + 1,
                "params": params,
                "word_count": len(items),
                "accuracy": accuracy,
                "duration": end_t - start_t
            })
            print(f"-> Accuracy: {accuracy:.2%} | Words: {len(items)}", flush=True)
        else:
            print("-> FAILED", flush=True)

    end_all = time.time()
    
    # Sort results by accuracy descending, then word_count
    sorted_results = sorted(results, key=lambda x: (x["accuracy"], x["word_count"]), reverse=True)
    
    # Save results to JSON
    os.makedirs("data/experiments", exist_ok=True)
    with open("data/experiments/super_optimization_results.json", "w", encoding="utf-8") as f:
        json.dump({
            "summary": {
                "total_combinations": len(combinations),
                "duration_sec": end_all - start_all,
                "best_params": sorted_results[0]["params"] if sorted_results else {}
            },
            "best_results": sorted_results[:10]
        }, f, ensure_ascii=False, indent=2)

    print(f"\nOptimization Finished in {end_all - start_all:.1f}s")
    print("-" * 30)
    print("TOP 3 RESULTS (By Accuracy):")
    for res in sorted_results[:3]:
        print(f"Acc: {res['accuracy']:.2%} | Words: {res['word_count']} | Params: {res['params']}")
    print("-" * 30)
    print(f"Detailed report saved to: data/experiments/super_optimization_results.json")

if __name__ == "__main__":
    run_experiment()
