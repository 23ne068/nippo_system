
import os
import cv2
import numpy as np

# Paths
IMG_PATH = "c:/Users/y86as/Nippo/ocr_lab/data/session_20260220_034220/ocr_20260220_034230_context.png"
OUTPUT_DIR = "c:/Users/y86as/Nippo/ocr_lab/debug_target/visualization_comparison"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def create_definitive_comparison():
    raw = cv2.imread(IMG_PATH)
    gray = cv2.cvtColor(raw, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 30, 255, cv2.THRESH_BINARY)
    kernel = np.ones((5, 5), np.uint8) 
    dilated = cv2.dilate(thresh, kernel, iterations=2)

    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    rects = [cv2.boundingRect(cnt) for cnt in contours]
    rects.sort(key=lambda r: r[1])
    
    # Simple line grouping
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

    # Prepare Canvas (Actual Production Logic)
    margin_w = 40
    line_spacing = 80
    processed_crops = []
    for line_rects in lines:
        lx1 = min(r[0] for r in line_rects)
        ly1 = min(r[1] for r in line_rects)
        lx2 = max(r[0] + r[2] for r in line_rects)
        ly2 = max(r[1] + r[3] for r in line_rects)
        
        crop = raw[ly1:ly2, lx1:lx2]
        processed_crops.append(crop)

    if not processed_crops:
        return

    max_w = max(p.shape[1] for p in processed_crops) + 2 * margin_w
    total_h = sum(p.shape[0] for p in processed_crops) + (len(processed_crops) + 1) * line_spacing
    canvas = np.zeros((total_h, max_w, 3), dtype=np.uint8)
    
    curr_y = line_spacing
    for p in processed_crops:
        canvas[curr_y:curr_y+p.shape[0], margin_w:margin_w+p.shape[1]] = p
        curr_y += p.shape[0] + line_spacing

    # --- Visualization Synthesis ---
    # Draw original with detected boxes labeled
    raw_boxes = raw.copy()
    for i, line_rects in enumerate(lines):
        lx1 = min(r[0] for r in line_rects)
        ly1 = min(r[1] for r in line_rects)
        lx2 = max(r[0] + r[2] for r in line_rects)
        ly2 = max(r[1] + r[3] for r in line_rects)
        cv2.rectangle(raw_boxes, (lx1, ly1), (lx2, ly2), (0, 0, 255), 2)
        cv2.putText(raw_boxes, f"ID:{i}", (lx1, ly1-5), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2)

    # Resize raw_boxes to fit a comparison view if it's too large
    disp_raw = cv2.resize(raw_boxes, (0,0), fx=0.4, fy=0.4)
    # Resize canvas similarly
    disp_canvas = cv2.resize(canvas, (0,0), fx=0.4, fy=0.4) if canvas.size > 0 else np.zeros((100,100,3))

    # Create a layout: [Raw with Boxes] [Actual OCR Canvas]
    h_r, w_r = disp_raw.shape[:2]
    h_c, w_c = disp_canvas.shape[:2]
    
    # Scale canvas to match raw height for side-by-side or just save side-by-side with padding
    final_h = max(h_r, h_c)
    comparison = np.zeros((final_h, w_r + w_c + 50, 3), dtype=np.uint8)
    comparison[:h_r, :w_r] = disp_raw
    comparison[:h_c, w_r+50:w_r+50+w_c] = disp_canvas
    
    # Add text
    cv2.putText(comparison, "Source Image (Red = Crops)", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255,255,255), 2)
    cv2.putText(comparison, "OCR Canvas (Processed)", (w_r + 60, 30), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255,255,255), 2)

    cv2.imwrite(os.path.join(OUTPUT_DIR, "definitive_blackout_comparison.png"), comparison)
    cv2.imwrite(os.path.join(OUTPUT_DIR, "ocr_canvas_raw.png"), canvas)
    print("Definitive comparison saved to:", OUTPUT_DIR)

if __name__ == "__main__":
    create_definitive_comparison()
