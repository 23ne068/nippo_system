
import os
import cv2
import numpy as np

# Use two REAL consecutive frames from the session
IMG1_PATH = "c:/Users/y86as/Nippo/ocr_lab/data/session_20260220_034220/ocr_20260220_034225_context.png"
IMG2_PATH = "c:/Users/y86as/Nippo/ocr_lab/data/session_20260220_034220/ocr_20260220_034230_context.png"
OUTPUT_DIR = "c:/Users/y86as/Nippo/ocr_lab/debug_target/visualization_real_logic"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def visualize_real_extraction():
    # 1. Load two frames
    f1 = cv2.imread(IMG1_PATH)
    f2 = cv2.imread(IMG2_PATH)
    if f1 is None or f2 is None: return

    g1 = cv2.cvtColor(f1, cv2.COLOR_BGR2GRAY)
    g2 = cv2.cvtColor(f2, cv2.COLOR_BGR2GRAY)

    # 2. Real absdiff (The core detection logic)
    diff = cv2.absdiff(g1, g2)
    _, thresh = cv2.threshold(diff, 30, 255, cv2.THRESH_BINARY)
    kernel = np.ones((5, 5), np.uint8) 
    dilated = cv2.dilate(thresh, kernel, iterations=2)

    # 3. Find contours of ACTUAL CHANGES
    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    rects = [cv2.boundingRect(cnt) for cnt in contours]
    
    # 4. Filter tiny noise and group into lines
    rects = [r for r in rects if r[2]*r[3] > 20] # Filter specks
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

    # 5. Extraction & Reconstruction
    margin_w = 40
    line_spacing = 80
    extracted_data = []
    
    for l_rects in lines:
        lx1 = min(r[0] for r in l_rects)
        ly1 = min(r[1] for r in l_rects)
        lx2 = max(r[0] + r[2] for r in l_rects)
        ly2 = max(r[1] + r[3] for r in l_rects)
        
        # CROP ONLY THE CHANGED AREA
        crop = f2[ly1:ly2, lx1:lx2]
        extracted_data.append({"img": crop, "rect": (lx1, ly1, lx2-lx1, ly2-ly1)})

    # Calculate canvas
    if not extracted_data: return
    max_w = max(d['img'].shape[1] for d in extracted_data) + 2 * margin_w
    total_h = sum(d['img'].shape[0] for d in extracted_data) + (len(extracted_data) + 1) * line_spacing
    
    canvas = np.zeros((total_h, max_w, 3), dtype=np.uint8)
    curr_y = line_spacing
    for d in extracted_data:
        h, w = d['img'].shape[:2]
        canvas[curr_y:curr_y+h, margin_w:margin_w+w] = d['img']
        curr_y += h + line_spacing

    # --- SAVE VISUAL PROOF ---
    # A) Show changes highlighted on original (Red boxes around changes)
    viz_src = f2.copy()
    for d in extracted_data:
        x, y, w, h = d['rect']
        cv2.rectangle(viz_src, (x, y), (x + w, y + h), (0, 0, 255), 3)
    cv2.imwrite(os.path.join(OUTPUT_DIR, "src_with_real_diff_boxes.png"), viz_src)

    # B) Show ONE isolated crop vs a "black hole"
    d0 = extracted_data[0]
    isolated = np.zeros((d0['img'].shape[0] + 100, d0['img'].shape[1] + 100, 3), dtype=np.uint8)
    isolated[50:50+d0['img'].shape[0], 50:50+d0['img'].shape[1]] = d0['img']
    cv2.imwrite(os.path.join(OUTPUT_DIR, "isolated_line_crop.png"), isolated)

    # C) Final Spaced Canvas (The real thing)
    cv2.imwrite(os.path.join(OUTPUT_DIR, "final_real_spacing_canvas.png"), canvas)
    
    print("Real-diff logic visualization saved to:", OUTPUT_DIR)

if __name__ == "__main__":
    visualize_real_extraction()
