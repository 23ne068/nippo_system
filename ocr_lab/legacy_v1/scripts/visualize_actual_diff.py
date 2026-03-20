
import os
import cv2
import numpy as np

# Paths
IMG1 = "c:/Users/y86as/Nippo/ocr_lab/data/session_20260220_034220/ocr_20260220_034225_context.png"
IMG2 = "c:/Users/y86as/Nippo/ocr_lab/data/session_20260220_034220/ocr_20260220_034230_context.png"
OUTPUT_DIR = "c:/Users/y86as/Nippo/ocr_lab/debug_target/visualization_diff"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def visualize_real_diff():
    # 1. Load two consecutive frames
    f1 = cv2.imread(IMG1)
    f2 = cv2.imread(IMG2)
    if f1 is None or f2 is None:
        print("Error: Images not found.")
        return

    g1 = cv2.cvtColor(f1, cv2.COLOR_BGR2GRAY)
    g2 = cv2.cvtColor(f2, cv2.COLOR_BGR2GRAY)

    # 2. Real absdiff (Same logic as screen_ocr.py)
    diff = cv2.absdiff(g1, g2)
    _, thresh = cv2.threshold(diff, 30, 255, cv2.THRESH_BINARY)
    
    # 3. Dilation (To connect components)
    kernel = np.ones((5, 5), np.uint8) 
    dilated = cv2.dilate(thresh, kernel, iterations=2)

    # 4. Save results
    cv2.imwrite(os.path.join(OUTPUT_DIR, "frame1.png"), f1)
    cv2.imwrite(os.path.join(OUTPUT_DIR, "frame2.png"), f2)
    cv2.imwrite(os.path.join(OUTPUT_DIR, "real_absdiff_map.png"), diff)
    cv2.imwrite(os.path.join(OUTPUT_DIR, "real_threshold_mask.png"), thresh)
    cv2.imwrite(os.path.join(OUTPUT_DIR, "real_dilated_mask.png"), dilated)

    # 5. Highlight on frame2
    viz = f2.copy()
    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        cv2.rectangle(viz, (x, y), (x + w, y + h), (0, 0, 255), 2)
    
    cv2.imwrite(os.path.join(OUTPUT_DIR, "diff_highlighted_on_frame.png"), viz)
    print("Real diff visualization steps saved to:", OUTPUT_DIR)

if __name__ == "__main__":
    visualize_real_diff()
