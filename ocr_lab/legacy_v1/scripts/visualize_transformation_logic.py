
import os
import cv2
import numpy as np

# Paths (Using the same frame as before for consistency)
IMG2 = "c:/Users/y86as/Nippo/ocr_lab/data/session_20260220_034220/ocr_20260220_034230_context.png"
OUTPUT_DIR = "c:/Users/y86as/Nippo/ocr_lab/debug_target/visualization_spacing_detail"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def visualize_transformation_detail():
    raw = cv2.imread(IMG2)
    gray = cv2.cvtColor(raw, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 30, 255, cv2.THRESH_BINARY)
    kernel = np.ones((5, 5), np.uint8) 
    dilated = cv2.dilate(thresh, kernel, iterations=2)

    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    rects = [cv2.boundingRect(cnt) for cnt in contours]
    rects.sort(key=lambda r: r[1])
    
    # 1. Group into lines
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

    # 2. Extract and Save individual lines with padding
    margin_w = 40
    line_spacing = 80
    extracted_imgs = []
    
    for i, line_rects in enumerate(lines[:5]): # Show first 5 lines
        lx1 = min(r[0] for r in line_rects)
        ly1 = min(r[1] for r in line_rects)
        lx2 = max(r[0] + r[2] for r in line_rects)
        ly2 = max(r[1] + r[3] for r in line_rects)
        
        crop = raw[ly1:ly2, lx1:lx2]
        ch, cw = crop.shape[:2]
        
        # Add side padding visualize
        padded = np.zeros((ch, cw + 2*margin_w, 3), dtype=np.uint8)
        padded[:, margin_w:margin_w+cw] = crop
        
        # Add border only for visualization
        cv2.rectangle(padded, (0, 0), (padded.shape[1]-1, padded.shape[0]-1), (255, 255, 255), 1)
        
        cv2.imwrite(os.path.join(OUTPUT_DIR, f"line_{i}_extracted.png"), padded)
        extracted_imgs.append(padded)

    # 3. Create Annotated Composite
    canvas_w = max(p.shape[1] for p in extracted_imgs) + 200 # Extra space for labels
    canvas_h = sum(p.shape[0] for p in extracted_imgs) + (len(extracted_imgs) + 1) * line_spacing
    canvas = np.zeros((canvas_h, canvas_w, 3), dtype=np.uint8)
    
    curr_y = line_spacing
    for i, p in enumerate(extracted_imgs):
        lh, lw = p.shape[:2]
        canvas[curr_y:curr_y+lh, 20:20+lw] = p
        
        # Annotate spacing
        if i > 0:
            # Draw arrow for gap
            gap_y = curr_y - line_spacing
            cv2.arrowedLine(canvas, (lw + 50, gap_y), (lw + 50, curr_y), (0, 0, 255), 2)
            cv2.arrowedLine(canvas, (lw + 50, curr_y), (lw + 50, gap_y), (0, 0, 255), 2)
            cv2.putText(canvas, f"{line_spacing}px GAP", (lw + 70, gap_y + line_spacing//2), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 1)
            
        curr_y += lh + line_spacing

    cv2.imwrite(os.path.join(OUTPUT_DIR, "annotated_composite_logic.png"), canvas)
    print("Detailed spacing transformation saved to:", OUTPUT_DIR)

if __name__ == "__main__":
    visualize_transformation_detail()
