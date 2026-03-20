
import os
import cv2
import numpy as np

# Use the same frames for consistency
IMG1_PATH = "c:/Users/y86as/Nippo/ocr_lab/data/session_20260220_034220/ocr_20260220_034225_context.png"
IMG2_PATH = "c:/Users/y86as/Nippo/ocr_lab/data/session_20260220_034220/ocr_20260220_034230_context.png"
OUTPUT_DIR = "c:/Users/y86as/Nippo/ocr_lab/debug_target/visualization_merging_proof"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def visualize_merging_logic():
    f2 = cv2.imread(IMG2_PATH)
    f1 = cv2.imread(IMG1_PATH)
    if f1 is None or f2 is None: return

    g1 = cv2.cvtColor(f1, cv2.COLOR_BGR2GRAY)
    g2 = cv2.cvtColor(f2, cv2.COLOR_BGR2GRAY)
    diff = cv2.absdiff(g1, g2)
    _, thresh = cv2.threshold(diff, 30, 255, cv2.THRESH_BINARY)
    
    # 1. INDIVIDUAL DETECTIONS (No grouping yet)
    kernel_small = np.ones((3, 3), np.uint8)
    mask_small = cv2.dilate(thresh, kernel_small, iterations=1)
    contours_s, _ = cv2.findContours(mask_small, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    rects_s = [cv2.boundingRect(cnt) for cnt in contours_s if cv2.contourArea(cnt) > 10]

    # 2. GROUPED LINES (Production logic)
    kernel_large = np.ones((5, 5), np.uint8)
    mask_large = cv2.dilate(thresh, kernel_large, iterations=2)
    contours_l, _ = cv2.findContours(mask_large, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    rects_l = [cv2.boundingRect(cnt) for cnt in contours_l if cv2.contourArea(cnt) > 20]

    # Visual: [Initial Detections] -> [Grouped into Line]
    viz_individual = f2.copy()
    for r in rects_s:
        cv2.rectangle(viz_individual, (r[0], r[1]), (r[0]+r[2], r[1]+r[3]), (255, 0, 0), 2)
    cv2.imwrite(os.path.join(OUTPUT_DIR, "step1_individual_detections.png"), viz_individual)

    viz_grouped = f2.copy()
    for r in rects_l:
        cv2.rectangle(viz_grouped, (r[0], r[1]), (r[0]+r[2], r[1]+r[3]), (0, 255, 0), 3)
    cv2.imwrite(os.path.join(OUTPUT_DIR, "step2_grouped_lines.png"), viz_grouped)

    # 3. Canvas Construction
    margin_w = 40
    line_spacing = 80
    
    # Extract only the grouped line
    line_crops = []
    for r in rects_l:
        line_crops.append(f2[r[1]:r[1]+r[3], r[0]:r[0]+r[2]])

    if not line_crops: return
    max_w = max(p.shape[1] for p in line_crops) + 2 * margin_w
    total_h = sum(p.shape[0] for p in line_crops) + (len(line_crops) + 1) * line_spacing
    canvas = np.zeros((total_h, max_w, 3), dtype=np.uint8)
    curr_y = line_spacing
    for p in line_crops:
        canvas[curr_y:curr_y+p.shape[0], margin_w:margin_w+p.shape[1]] = p
        curr_y += p.shape[0] + line_spacing

    cv2.imwrite(os.path.join(OUTPUT_DIR, "step3_final_canvas.png"), canvas)
    print(f"Merging proof: {len(rects_s)} small boxes -> {len(rects_l)} lines.")

if __name__ == "__main__":
    visualize_merging_logic()
