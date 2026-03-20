
import os
import cv2
import numpy as np

# Use two REAL consecutive frames
IMG1_PATH = "c:/Users/y86as/Nippo/ocr_lab/data/session_20260220_034220/ocr_20260220_034225_context.png"
IMG2_PATH = "c:/Users/y86as/Nippo/ocr_lab/data/session_20260220_034220/ocr_20260220_034230_context.png"
OUTPUT_DIR = "c:/Users/y86as/Nippo/ocr_lab/debug_target/visualization_final_mapping"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def visualize_final_mapping():
    f2 = cv2.imread(IMG2_PATH)
    f1 = cv2.imread(IMG1_PATH)
    if f1 is None or f2 is None: return
    
    # Simple logic to get the same green boxes as before
    g1 = cv2.cvtColor(f1, cv2.COLOR_BGR2GRAY)
    g2 = cv2.cvtColor(f2, cv2.COLOR_BGR2GRAY)
    diff = cv2.absdiff(g1, g2)
    _, thresh = cv2.threshold(diff, 30, 255, cv2.THRESH_BINARY)
    kernel = np.ones((5, 5), np.uint8)
    dilated = cv2.dilate(thresh, kernel, iterations=2)
    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    rects = sorted([cv2.boundingRect(cnt) for cnt in contours if cv2.contourArea(cnt) > 20], key=lambda r: r[1])

    # Grouping
    lines = []
    if rects:
        curr = [rects[0]]
        last_y2 = rects[0][1] + rects[0][3]
        for r in rects[1:]:
            if r[1] < last_y2 + 15:
                curr.append(r)
                last_y2 = max(last_y2, r[1] + r[3])
            else:
                lines.append(curr)
                curr = [r]
                last_y2 = r[1] + r[3]
        lines.append(curr)

    # 1. Source with Green Boxes
    src_viz = f2.copy()
    line_crops = []
    for i, l_rects in enumerate(lines):
        lx1 = min(r[0] for r in l_rects)
        ly1 = min(r[1] for r in l_rects)
        lx2 = max(r[0] + r[2] for r in l_rects)
        ly2 = max(r[1] + r[3] for r in l_rects)
        cv2.rectangle(src_viz, (lx1, ly1), (lx2, ly2), (0, 255, 0), 3)
        cv2.putText(src_viz, f"#{i}", (lx1, ly1-5), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        line_crops.append(f2[ly1:ly2, lx1:lx2])

    cv2.imwrite(os.path.join(OUTPUT_DIR, "step1_source_green_boxes.png"), src_viz)

    # 2. Final Canvas (Mapping from green boxes)
    line_spacing = 80
    margin_w = 40
    max_w = max(p.shape[1] for p in line_crops) + 2 * margin_w
    total_h = sum(p.shape[0] for p in line_crops) + (len(line_crops) + 1) * line_spacing
    canvas = np.zeros((total_h, max_w, 3), dtype=np.uint8)
    
    curr_y = line_spacing
    for i, p in enumerate(line_crops):
        ph, pw = p.shape[:2]
        canvas[curr_y:curr_y+ph, margin_w:margin_w+pw] = p
        # Add label for verification
        cv2.putText(canvas, f"#{i}", (margin_w - 35, curr_y + ph//2), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        curr_y += ph + line_spacing

    cv2.imwrite(os.path.join(OUTPUT_DIR, "step2_final_canvas_mapped.png"), canvas)
    print("Final mapping visualization saved.")

if __name__ == "__main__":
    visualize_final_mapping()
