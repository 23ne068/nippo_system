
import os
import cv2
import numpy as np

# Paths
IMG2 = "c:/Users/y86as/Nippo/ocr_lab/data/session_20260220_034220/ocr_20260220_034230_context.png"
OUTPUT_DIR = "c:/Users/y86as/Nippo/ocr_lab/debug_target/visualization_spacing_final"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def visualize_clean_transformation():
    raw = cv2.imread(IMG2)
    gray = cv2.cvtColor(raw, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 30, 255, cv2.THRESH_BINARY)
    kernel = np.ones((5, 5), np.uint8) 
    dilated = cv2.dilate(thresh, kernel, iterations=2)

    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    rects = [cv2.boundingRect(cnt) for cnt in contours]
    rects.sort(key=lambda r: r[1])
    
    # Group into lines
    lines = []
    if rects:
        current_line = [rects[0]]
        last_y2 = rects[0][1] + rects[0][3]
        for r in rects[1:]:
            if r[1] < last_y2 + 20:
                current_line.append(r)
                last_y2 = max(last_y2, r[1] + r[3])
            else:
                lines.append(current_line)
                current_line = [r]
                last_y2 = r[1] + r[3]
        lines.append(current_line)

    margin_w = 40
    line_spacing = 80
    
    # 1. Show ONE specific line crop (explicitly showing it's a small piece)
    if len(lines) > 0:
        line_idx = min(1, len(lines) - 1) 
        l_rects = lines[line_idx]
        lx1 = min(r[0] for r in l_rects)
        ly1 = min(r[1] for r in l_rects)
        lx2 = max(r[0] + r[2] for r in l_rects)
        ly2 = max(r[1] + r[3] for r in l_rects)
        
        line_crop = raw[ly1:ly2, lx1:lx2]
        # Add fake "black background" around it to show it was extracted
        demo_bg = np.zeros((line_crop.shape[0] + 40, line_crop.shape[1] + 80, 3), dtype=np.uint8)
        demo_bg[20:20+line_crop.shape[0], 40:40+line_crop.shape[1]] = line_crop
        cv2.imwrite(os.path.join(OUTPUT_DIR, "single_line_extraction_demo.png"), demo_bg)
    else:
        print("No lines detected in this frame.")
        return

    # 2. Show the "Black-out" canvas reconstruction
    # We'll take first 8 lines to show the structure
    subset = lines[:min(8, len(lines))]
    processed_crops = []
    for l_rects in subset:
        lx1 = min(r[0] for r in l_rects)
        ly1 = min(r[1] for r in l_rects)
        lx2 = max(r[0] + r[2] for r in l_rects)
        ly2 = max(r[1] + r[3] for r in l_rects)
        processed_crops.append(raw[ly1:ly2, lx1:lx2])

    max_w = max(p.shape[1] for p in processed_crops) + 2 * margin_w
    total_h = sum(p.shape[0] for p in processed_crops) + (len(processed_crops) + 1) * line_spacing
    
    canvas = np.zeros((total_h, max_w, 3), dtype=np.uint8)
    curr_y = line_spacing
    for p in processed_crops:
        canvas[curr_y:curr_y+p.shape[0], margin_w:margin_w+p.shape[1]] = p
        curr_y += p.shape[0] + line_spacing

    cv2.imwrite(os.path.join(OUTPUT_DIR, "final_spaced_composite_blackout.png"), canvas)

if __name__ == "__main__":
    visualize_clean_transformation()
