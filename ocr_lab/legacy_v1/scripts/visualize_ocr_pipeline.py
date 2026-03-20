
import os
import cv2
import numpy as np

# Paths
INPUT_IMAGE = "c:/Users/y86as/Nippo/ocr_lab/data/session_20260220_034220/ocr_20260220_034225_context.png"
OUTPUT_DIR = "c:/Users/y86as/Nippo/ocr_lab/debug_target/visualization_steps"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def visualize_pipeline():
    # 1. Raw Input
    raw = cv2.imread(INPUT_IMAGE)
    if raw is None:
        print("Error: Input image not found.")
        return
    cv2.imwrite(os.path.join(OUTPUT_DIR, "step1_raw.png"), raw)
    print("Step 1: Raw image saved.")

    # 2. Mask Generation (Simulate detection)
    gray = cv2.cvtColor(raw, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 30, 255, cv2.THRESH_BINARY)
    kernel = np.ones((5, 5), np.uint8) 
    dilated_mask = cv2.dilate(thresh, kernel, iterations=2)
    cv2.imwrite(os.path.join(OUTPUT_DIR, "step2_mask.png"), dilated_mask)
    print("Step 2: Mask generation saved.")

    # 3. Line Detection & Visualization
    contours, _ = cv2.findContours(dilated_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    rects = [cv2.boundingRect(cnt) for cnt in contours]
    
    # Group into lines
    rects.sort(key=lambda r: r[1])
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

    viz_detection = raw.copy()
    processed_lines = []
    for i, line_rects in enumerate(lines):
        lx1 = min(r[0] for r in line_rects)
        ly1 = min(r[1] for r in line_rects)
        lx2 = max(r[0] + r[2] for r in line_rects)
        ly2 = max(r[1] + r[3] for r in line_rects)
        
        cv2.rectangle(viz_detection, (lx1, ly1), (lx2, ly2), (0, 255, 0), 2)
        cv2.putText(viz_detection, f"Line {i}", (lx1, ly1-5), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        line_crop = raw[ly1:ly2, lx1:lx2]
        if line_crop.size > 0:
            processed_lines.append(line_crop)

    cv2.imwrite(os.path.join(OUTPUT_DIR, "step3_detection.png"), viz_detection)
    print("Step 3: Line detection visualization saved.")

    # 4. Final Composite (Step that Tesseract sees)
    line_spacing = 80
    margin_w = 40
    
    if not processed_lines:
        return

    canvas_w = max(p.shape[1] for p in processed_lines) + 2 * margin_w
    canvas_h = sum(p.shape[0] for p in processed_lines) + (len(processed_lines) + 1) * line_spacing
    canvas = np.zeros((canvas_h, canvas_w, 3), dtype=np.uint8)
    
    curr_y = line_spacing
    for p in processed_lines:
        lh, lw = p.shape[:2]
        canvas[curr_y:curr_y+lh, margin_w:margin_w+lw] = p
        curr_y += lh + line_spacing

    cv2.imwrite(os.path.join(OUTPUT_DIR, "step4_composite.png"), canvas)
    print("Step 4: Final composite (with huge spacing) saved.")

if __name__ == "__main__":
    visualize_pipeline()
