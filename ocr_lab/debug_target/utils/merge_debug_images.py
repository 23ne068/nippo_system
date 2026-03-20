
import cv2
import numpy as np
import os

def main():
    base_dir = os.path.dirname(__file__)
    merged_dir = os.path.join(base_dir, "merged")
    
    if not os.path.exists(merged_dir):
        os.makedirs(merged_dir)

    roi_path = os.path.join(base_dir, "ocr_20260220_034236_roi.png")
    vis_path = os.path.join(base_dir, "ocr_reconstructed_raw.png")
    output_path = os.path.join(merged_dir, "merged_debug_view.png")
    
    # 1. Load images
    roi_img = cv2.imread(roi_path)
    vis_img = cv2.imread(vis_path)
    
    if roi_img is None or vis_img is None:
        print("Error: Could not load one or both images.")
        return

    # 2. Create Base Canvas (Black 1920x1080)
    # vis_img is already 1920x1080 (from previous script)
    h, w = vis_img.shape[:2]
    canvas = np.zeros((h, w, 3), dtype=np.uint8)
    
    # 3. Place ROI at offset (735, 376)
    # This offset must match what was used in run_single_image.py
    offset_x = 735
    offset_y = 376
    
    roi_h, roi_w = roi_img.shape[:2]
    
    # Boundary checks
    end_y = min(offset_y + roi_h, h)
    end_x = min(offset_x + roi_w, w)
    
    # Calculate actual placement dimensions (in case of clipping)
    place_h = end_y - offset_y
    place_w = end_x - offset_x
    
    if place_h > 0 and place_w > 0:
        canvas[offset_y:end_y, offset_x:end_x] = roi_img[:place_h, :place_w]
    
    # 4. Overlay Visualization
    # vis_img is black background with colored boxes/text.
    # We want to overlay non-black pixels from vis_img onto canvas.
    
    # Create mask of non-black pixels in visualization
    gray_vis = cv2.cvtColor(vis_img, cv2.COLOR_BGR2GRAY)
    _, mask = cv2.threshold(gray_vis, 1, 255, cv2.THRESH_BINARY)
    
    # Copy vis_img pixels where mask is set
    # Using bitwise operations
    canvas_bg = cv2.bitwise_and(canvas, canvas, mask=cv2.bitwise_not(mask))
    vis_fg = cv2.bitwise_and(vis_img, vis_img, mask=mask)
    
    combined = cv2.add(canvas_bg, vis_fg)
    
    # 5. Save
    cv2.imwrite(output_path, combined)
    print(f"Saved merged image to: {output_path}")

if __name__ == "__main__":
    main()
