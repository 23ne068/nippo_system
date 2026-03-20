
import os
import cv2
import numpy as np
import pytesseract
import json

# Paths
IMG1_PATH = "c:/Users/y86as/Nippo/ocr_lab/data/session_20260220_034220/ocr_20260220_034225_context.png"
IMG2_PATH = "c:/Users/y86as/Nippo/ocr_lab/data/session_20260220_034220/ocr_20260220_034230_context.png"
TESSDATA_PATH = "c:/Users/y86as/Nippo/nippo_system/data/tessdata"
OUTPUT_DIR = "c:/Users/y86as/Nippo/ocr_lab/debug_target/mapping_viz"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def visualize_mapping_overlay():
    f1 = cv2.imread(IMG1_PATH)
    f2 = cv2.imread(IMG2_PATH)
    if f1 is None or f2 is None: return

    # 1. Pipeline: Detect Changes
    g1 = cv2.cvtColor(f1, cv2.COLOR_BGR2GRAY)
    g2 = cv2.cvtColor(f2, cv2.COLOR_BGR2GRAY)
    diff = cv2.absdiff(g1, g2)
    _, thresh = cv2.threshold(diff, 30, 255, cv2.THRESH_BINARY)
    kernel = np.ones((5, 5), np.uint8)
    dilated = cv2.dilate(thresh, kernel, iterations=2)
    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    rects = sorted([cv2.boundingRect(cnt) for cnt in contours if cv2.contourArea(cnt) > 20], key=lambda r: r[1])

    # 2. Pipeline: Group into Lines
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

    # 3. Pipeline: Build Composite Canvas
    margin_w = 40
    line_spacing = 80
    processed_lines = []
    
    crops = []
    for l_rects in lines:
        lx1 = min(r[0] for r in l_rects)
        ly1 = min(r[1] for r in l_rects)
        lx2 = max(r[0] + r[2] for r in l_rects)
        ly2 = max(r[1] + r[3] for r in l_rects)
        crop = f2[ly1:ly2, lx1:lx2]
        crops.append(crop)
        processed_lines.append({
            'img': crop,
            'orig_rect': (lx1, ly1, lx2-lx1, ly2-ly1)
        })

    if not crops: return

    max_w = max(p.shape[1] for p in crops) + 2 * margin_w
    total_h = sum(p.shape[0] for p in crops) + (len(crops) + 1) * line_spacing
    canvas = np.zeros((total_h, max_w, 3), dtype=np.uint8)
    
    curr_y = line_spacing
    for i, p in enumerate(crops):
        ph, pw = p.shape[:2]
        canvas[curr_y:curr_y+ph, margin_w:margin_w+pw] = p
        processed_lines[i]['canvas_y'] = curr_y
        curr_y += ph + line_spacing

    # 4. Pipeline: OCR & Mapping Back
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    norm_tessdata = os.path.normpath(TESSDATA_PATH)
    # Using the exact same config logic as screen_ocr.py (no quotes)
    config = f'--psm 6 --tessdata-dir {norm_tessdata}'
    os.environ["TESSDATA_PREFIX"] = norm_tessdata

    data = pytesseract.image_to_data(canvas, lang='jpn', config=config, output_type=pytesseract.Output.DICT)

    # Visualization Setup
    overlay_img = f2.copy()
    
    for i in range(len(data['text'])):
        text = data['text'][i].strip()
        conf = int(data['conf'][i])
        if not text or conf < 75: continue
        
        # Word coords on CANVAS
        cx, cy, cw, ch = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
        
        # Map back to ORIGINAL
        mapped_x, mapped_y = -1, -1
        for p in processed_lines:
            line_y_min = p['canvas_y']
            line_y_max = line_y_min + p['img'].shape[0]
            if cy >= line_y_min and cy < line_y_max:
                ox, oy, _, _ = p['orig_rect']
                mapped_x = ox + (cx - margin_w)
                mapped_y = oy + (cy - p['canvas_y'])
                break
        
        if mapped_x == -1: continue

        # Draw on original frame - Green word box
        cv2.rectangle(overlay_img, (mapped_x, mapped_y), (mapped_x + cw, mapped_y + ch), (0, 255, 0), 2)
        # Red text label
        cv2.putText(overlay_img, text, (mapped_x, mapped_y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

    cv2.imwrite(os.path.join(OUTPUT_DIR, "ocr_overlay_on_original.png"), overlay_img)
    print("Overlay visualization saved correctly.")

if __name__ == "__main__":
    visualize_mapping_overlay()
