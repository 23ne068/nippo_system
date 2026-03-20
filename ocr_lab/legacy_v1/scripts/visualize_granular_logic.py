
import os
import cv2
import numpy as np

# Use two REAL consecutive frames
IMG1_PATH = "c:/Users/y86as/Nippo/ocr_lab/data/session_20260220_034220/ocr_20260220_034225_context.png"
IMG2_PATH = "c:/Users/y86as/Nippo/ocr_lab/data/session_20260220_034220/ocr_20260220_034230_context.png"
OUTPUT_DIR = "c:/Users/y86as/Nippo/ocr_lab/debug_target/visualization_granular"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def visualize_granular_logic():
    f1 = cv2.imread(IMG1_PATH)
    f2 = cv2.imread(IMG2_PATH)
    if f1 is None or f2 is None: return

    g1 = cv2.cvtColor(f1, cv2.COLOR_BGR2GRAY)
    g2 = cv2.cvtColor(f2, cv2.COLOR_BGR2GRAY)

    diff = cv2.absdiff(g1, g2)
    _, thresh = cv2.threshold(diff, 30, 255, cv2.THRESH_BINARY)
    
    # 1. Granular Detection (Small kernel, 1 iteration)
    # This shows the "raw" changes before grouping.
    kernel_small = np.ones((3, 3), np.uint8)
    granular_mask = cv2.dilate(thresh, kernel_small, iterations=1)
    
    contours_g, _ = cv2.findContours(granular_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    rects_g = [cv2.boundingRect(cnt) for cnt in contours_g if cv2.contourArea(cnt) > 5]
    
    # 2. Production Grouping (Same as screen_ocr.py)
    kernel_prod = np.ones((5, 5), np.uint8)
    dilated_prod = cv2.dilate(thresh, kernel_prod, iterations=2)
    contours_p, _ = cv2.findContours(dilated_prod, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    rects_p = [cv2.boundingRect(cnt) for cnt in contours_p if cv2.contourArea(cnt) > 20]
    
    # Sort and group into lines
    rects_p.sort(key=lambda r: r[1])
    lines = []
    if rects_p:
        curr = [rects_p[0]]
        last_y2 = rects_p[0][1] + rects_p[0][3]
        for r in rects_p[1:]:
            if r[1] < last_y2 + 15:
                curr.append(r)
                last_y2 = max(last_y2, r[1] + r[3])
            else:
                lines.append(curr)
                curr = [r]
                last_y2 = r[1] + r[3]
        lines.append(curr)

    # VISUALIZATION A: Granular boxes (Blue) vs Grouped Lines (Red)
    viz_src = f2.copy()
    # Draw individual "granular" changes in Blue
    for r in rects_g:
        cv2.rectangle(viz_src, (r[0], r[1]), (r[0]+r[2], r[1]+r[3]), (255, 0, 0), 1)
    
    # Draw final "Line Crops" in Red - Tight Crops
    for l_rects in lines:
        lx1 = min(r[0] for r in l_rects)
        ly1 = min(r[1] for r in l_rects)
        lx2 = max(r[0] + r[2] for r in l_rects)
        ly2 = max(r[1] + r[3] for r in l_rects)
        cv2.rectangle(viz_src, (lx1, ly1), (lx2, ly2), (0, 0, 255), 2)

    cv2.imwrite(os.path.join(OUTPUT_DIR, "granular_vs_grouped_detection.png"), viz_src)

    # VISUALIZATION B: Zoom into ONE line to show tightness
    if lines:
        # Pick a line with text
        l = lines[len(lines)//2]
        lx1 = min(r[0] for r in l)
        ly1 = min(r[1] for r in l)
        lx2 = max(r[0] + r[2] for r in l)
        ly2 = max(r[1] + r[3] for r in l)
        
        # Show the crop itself with zero margins first
        tight_crop = f2[ly1:ly2, lx1:lx2]
        cv2.imwrite(os.path.join(OUTPUT_DIR, "tight_line_crop_only.png"), tight_crop)

    print("Granular visualization saved to:", OUTPUT_DIR)

if __name__ == "__main__":
    visualize_granular_logic()
