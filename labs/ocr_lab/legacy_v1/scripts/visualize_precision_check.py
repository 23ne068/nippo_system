
import os
import cv2
import numpy as np

# Use two REAL consecutive frames
IMG1_PATH = "c:/Users/y86as/Nippo/ocr_lab/data/session_20260220_034220/ocr_20260220_034225_context.png"
IMG2_PATH = "c:/Users/y86as/Nippo/ocr_lab/data/session_20260220_034220/ocr_20260220_034230_context.png"
OUTPUT_DIR = "c:/Users/y86as/Nippo/ocr_lab/debug_target/visualization_precision_check"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def visualize_precision():
    f1 = cv2.imread(IMG1_PATH)
    f2 = cv2.imread(IMG2_PATH)
    if f1 is None or f2 is None: return

    g1 = cv2.cvtColor(f1, cv2.COLOR_BGR2GRAY)
    g2 = cv2.cvtColor(f2, cv2.COLOR_BGR2GRAY)

    # Production logic
    diff = cv2.absdiff(g1, g2)
    _, thresh = cv2.threshold(diff, 30, 255, cv2.THRESH_BINARY)
    
    # 1. Heatmap of changes (to see where pixels actually differ)
    heatmap = cv2.applyColorMap(diff, cv2.COLORMAP_JET)
    # Binary mask overlay (Red where pixels differ > 30)
    overlay = f2.copy()
    overlay[thresh > 0] = [0, 0, 255] # Paint actual diff pixels Red
    
    # 2. Re-detect boxes
    kernel = np.ones((5, 5), np.uint8)
    dilated = cv2.dilate(thresh, kernel, iterations=2)
    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    rects = [cv2.boundingRect(cnt) for cnt in contours if cv2.contourArea(cnt) > 20]

    # Save individual steps for user review
    cv2.imwrite(os.path.join(OUTPUT_DIR, "step1_absdiff_heatmap.png"), heatmap)
    cv2.imwrite(os.path.join(OUTPUT_DIR, "step2_pixel_level_diff_overlay.png"), overlay)
    
    # Final verification image
    viz = f2.copy()
    # Draw actual diff pixels in low-alpha red
    mask_indices = np.where(thresh > 0)
    viz[mask_indices] = [0, 0, 255]
    # Draw the resulting boxes
    for x, y, w, h in rects:
        cv2.rectangle(viz, (x, y), (x + w, y + h), (0, 255, 0), 2)
    
    cv2.imwrite(os.path.join(OUTPUT_DIR, "step3_final_box_alignment_check.png"), viz)
    print("Precision check files saved to:", OUTPUT_DIR)

if __name__ == "__main__":
    visualize_precision()
