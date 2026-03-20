import json
import os
import difflib

def calculate_cer(reference, hypothesis):
    """
    Calculate Character Error Rate (CER) using Levenshtein distance.
    """
    if not reference:
        return 1.0 if hypothesis else 0.0
    
    # Simple edit distance
    s = difflib.SequenceMatcher(None, reference, hypothesis)
    # distance = sum of deletes, inserts, and substitutes
    # Actually, difflib doesn't give Levenshtein directly easily in terms of count
    # But we can approximate or use a simple Levenshtein implementation
    
    # Basic Levenshtein distance
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
    
    edit_dist = dp[m][n]
    return edit_dist / m

def evaluate_accuracy(results_json_path, spec_path):
    # Load Specification (Ground Truth)
    if not os.path.exists(spec_path):
        print(f"Spec not found: {spec_path}")
        return

    ground_truth = ""
    with open(spec_path, "r", encoding="utf-8") as f:
        collecting = False
        for line in f:
            line = line.strip()
            if line.startswith("CONTENT:"):
                collecting = True
            elif line.startswith("BLOCK"):
                collecting = False
            elif collecting and line:
                ground_truth += line

    # Cleanup GT (remove spaces for CER if preferred, or keep)
    gt_clean = "".join(ground_truth.split())

    # Load Results
    if not os.path.exists(results_json_path):
        print(f"Results not found: {results_json_path}")
        return

    with open(results_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"| Rank | Params | Words | CER (Lower is better) | Accuracy |")
    print(f"| :--- | :--- | :--- | :--- | :--- |")
    
    for i, res in enumerate(data.get("best_results", [])):
        hyp = "".join(res.get("chars_preview", "").split())
        # Re-run a full char collection from all_results if needed, 
        # but for now let's assume word-based recovery for the preview
        
        cer = calculate_cer(gt_clean, hyp)
        accuracy = max(0, 1 - cer)
        print(f"| {i+1} | {res['params']} | {res['word_count']} | {cer:.4f} | {accuracy:.2%} |")

if __name__ == "__main__":
    results_path = r"c:/Users/y86as/Nippo/ocr_lab/data/experiments/super_optimization_results.json"
    spec_path = r"c:/Users/y86as/Nippo/ocr_lab/data/test_raw/layout_spec.txt"
    evaluate_accuracy(results_path, spec_path)
