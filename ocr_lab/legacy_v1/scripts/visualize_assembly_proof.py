
import os
import cv2
import numpy as np

# Use frames with confirmed multiple changes
IMG1_PATH = "c:/Users/y86as/Nippo/ocr_lab/data/session_20260220_034220/ocr_20260220_034225_context.png"
IMG2_PATH = "c:/Users/y86as/Nippo/ocr_lab/data/session_20260220_034220/ocr_20260220_034230_context.png"
OUTPUT_DIR = "c:/Users/y86as/Nippo/ocr_lab/debug_target/visualization_assembly_proof"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def visualize_assembly_proof():
    f1 = cv2.imread(IMG1_PATH)
    f2 = cv2.imread(IMG2_PATH)
    if f1 is None or f2 is None: return

    g1 = cv2.cvtColor(f1, cv2.COLOR_BGR2GRAY)
    g2 = cv2.cvtColor(f2, cv2.COLOR_BGR2GRAY)
    diff = cv2.absdiff(g1, g2)
    _, thresh = cv2.threshold(diff, 20, 255, cv2.THRESH_BINARY)
    
    # REDUCE DILATION to avoid merging separate lines
    kernel = np.ones((3, 3), np.uint8)
    dilated = cv2.dilate(thresh, kernel, iterations=1)
    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Sort detected boxes by Y position
    rects = sorted([cv2.boundingRect(cnt) for cnt in contours if cv2.contourArea(cnt) > 5], key=lambda r: r[1])

    # TIGHT GROUPING for visualization proof
    lines = []
    if rects:
        curr = [rects[0]]
        last_y2 = rects[0][1] + rects[0][3]
        for r in rects[1:]:
            if r[1] < last_y2 + 2: # Very tight to show more lines
                curr.append(r)
                last_y2 = max(last_y2, r[1] + r[3])
            else:
                lines.append(curr)
                curr = [r]
                last_y2 = r[1] + r[3]
        lines.append(curr)

    # Extraction
    line_spacing = 60
    margin_w = 40
    line_crops = []
    line_origins = []
    for l_rects in lines:
        lx1 = min(r[0] for r in l_rects)
        ly1 = min(r[1] for r in l_rects)
        lx2 = max(r[0] + r[2] for r in l_rects)
        ly2 = max(r[1] + r[3] for r in l_rects)
        line_crops.append(f2[ly1:ly2, lx1:lx2])
        line_origins.append((lx1, ly1, lx2-lx1, ly2-ly1))

    # Canvas
    max_w_crop = max(p.shape[1] for p in line_crops)
    canvas_w = max_w_crop + 2 * margin_w
    canvas_h = sum(p.shape[0] for p in line_crops) + (len(line_crops) + 1) * line_spacing
    canvas = np.zeros((canvas_h, canvas_w, 3), dtype=np.uint8)
    
    line_y_on_canvas = []
    curr_y = line_spacing
    for p in line_crops:
        ph, pw = p.shape[:2]
        canvas[curr_y:curr_y+ph, margin_w:margin_w+pw] = p
        line_y_on_canvas.append(curr_y)
        curr_y += ph + line_spacing

    # Layout
    h_src, w_src = f2.shape[:2]
    total_h = max(h_src, canvas.shape[0])
    master = np.zeros((total_h, w_src + canvas.shape[1] + 300, 3), dtype=np.uint8)
    master[:h_src, :w_src] = f2
    master[:canvas.shape[0], w_src+300:] = canvas
    
    # Colors
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255)]
    for i, (orig_rect, can_y) in enumerate(zip(line_origins, line_y_on_canvas)):
        ox, oy, ow, oh = orig_rect
        color = colors[i % len(colors)]
        cv2.rectangle(master, (ox, oy), (ox+ow, oy+oh), color, 4)
        c_start = w_src + 300 + margin_w
        cv2.rectangle(master, (c_start, can_y), (c_start + ow, can_y + oh), color, 4)
        cv2.line(master, (ox + ow, oy + oh//2), (w_src + 300, can_y + oh//2), color, 2)

    cv2.putText(master, f"Mapped {len(lines)} lines", (w_src + 20, 150), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255,255,255), 4)

    final_resize = cv2.resize(master, (0,0), fx=0.4, fy=0.4)
    cv2.imwrite(os.path.join(OUTPUT_DIR, "master_assembly_proof.png"), final_resize)
    print(f"Assembly proof with {len(lines)} lines saved.")

if __name__ == "__main__":
    visualize_assembly_proof()
