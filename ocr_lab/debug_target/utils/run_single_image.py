
import cv2
import sys
import os
import json
import logging
import pytesseract
import time

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from nippo_system.modules.screen_ocr import ScreenOCR, DATA_DIR

def main():
    # Setup paths
    target_dir = os.path.dirname(__file__)
    image_path = os.path.join(target_dir, "ocr_20260220_034236_roi.png")
    output_json_path = os.path.join(target_dir, "ocr_output_roi.json")

    print(f"Loading image from: {image_path}")

    if not os.path.exists(image_path):
        print("Error: Image file not found.")
        return

    # Load image
    img_bgr = cv2.imread(image_path)
    if img_bgr is None:
        print("Error: Failed to load image.")
        return
    
    # Initialize OCR
    ocr = ScreenOCR(output_dir=target_dir)
    
    # We want to use the EXACT logic from ScreenOCR, but capture the result instead of writing to a timeline file.
    # We will subclass to override _perform_ocr but copy the logic faithfully.
    
    class FaithfulSingleImageOCR(ScreenOCR):
        def _perform_ocr_faithful(self, img_bgr, offset=(0, 0), roi_size=(0, 0), screen_size=None):
            # Copied and adapted from ScreenOCR._perform_ocr to return the log_entry
            try:
                # BGR -> RGB
                img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
                
                config = r'--psm 6' 
                # Note: self.OCR_LANG might not be set if we didn't import config correctly, 
                # but ScreenOCR usually handles imports. Let's force "jpn" if needed or rely on parent.
                lang = "jpn" 
                
                data = pytesseract.image_to_data(img_rgb, lang=lang, config=config, output_type=pytesseract.Output.DICT)
                
                # 1. Collect & Filter raw words
                raw_words = []
                off_x, off_y = offset
                num_boxes = len(data['text'])
                
                for i in range(num_boxes):
                    text = data['text'][i].strip()
                    if not text: continue
                        
                    conf = int(data['conf'][i])
                    if conf < 75: continue
                    if len(text) == 1 and ord(text) < 128: continue

                    word = {
                        "description": text,
                        "confidence": conf,
                        "boundingPoly": {
                            "vertices": [
                                {"x": data['left'][i] + off_x, "y": data['top'][i] + off_y}, 
                                {"x": data['left'][i] + data['width'][i] + off_x, "y": data['top'][i] + off_y}, 
                                {"x": data['left'][i] + data['width'][i] + off_x, "y": data['top'][i] + data['height'][i] + off_y}, 
                                {"x": data['left'][i] + off_x, "y": data['top'][i] + data['height'][i] + off_y} 
                            ]
                        }
                    }
                    raw_words.append(word)

                if not raw_words:
                    print("No text detected (Stage 1).")
                    return None
                
                # --- NEW: Save RAW words for visualization ---
                raw_log_items = []
                if screen_size:
                    fw, fh = screen_size
                else:
                    fw, fh = roi_size if roi_size[0] > 0 else (1920, 1080)

                for w in raw_words:
                    vs = w['boundingPoly']['vertices']
                    xs = [v['x'] for v in vs]
                    ys = [v['y'] for v in vs]
                    min_x, max_x = min(xs), max(xs)
                    min_y, max_y = min(ys), max(ys)
                    
                    n_ymin = int(min(1000, max(0, (min_y / fh) * 1000)))
                    n_xmin = int(min(1000, max(0, (min_x / fw) * 1000)))
                    n_ymax = int(min(1000, max(0, (max_y / fh) * 1000)))
                    n_xmax = int(min(1000, max(0, (max_x / fw) * 1000)))
                    
                    raw_log_items.append({
                        "description": w['description'],
                        "box_2d": [n_ymin, n_xmin, n_ymax, n_xmax]
                    })
                
                raw_json_path = os.path.join(self.output_dir, "ocr_output_roi_raw.json")
                with open(raw_json_path, 'w', encoding='utf-8') as f:
                    json.dump({"items": raw_log_items}, f, indent=2, ensure_ascii=False)
                print(f"Saved RAW output to: {raw_json_path}")
                # ---------------------------------------------

                # 2. Group words into Lines (Google Format)
                # We use the PARENT method for this
                lines = self._group_words_into_lines_google_format(raw_words)
                
                # 3. Deduplicate (IoU + Levenshtein) & Filter (Blacklist/Garbage)
                # We use the PARENT method for this.
                # Since this is a fresh instance, self.prev_lines is empty, so it behaves like the "First Frame".
                # This ensures Blacklist and Garbage filters are applied.
                roi_rect = (off_x, off_y, roi_size[0], roi_size[1])
                new_lines = self._filter_duplicate_lines_iou(lines, roi_rect)

                if new_lines:
                    # Get frame dimensions for normalization
                    if screen_size:
                        frame_w, frame_h = screen_size
                    else:
                        frame_w, frame_h = roi_size # Fallback if no screen size
                    
                    if frame_w == 0 or frame_h == 0: 
                         frame_w, frame_h = 1920, 1080 

                    # Group all detected items into a single log entry
                    log_items = []
                    for line in new_lines:
                        # boundingPoly is absolute
                        vs = line['boundingPoly']['vertices']
                        xs = [v['x'] for v in vs]
                        ys = [v['y'] for v in vs]
                        
                        min_x, max_x = min(xs), max(xs)
                        min_y, max_y = min(ys), max(ys)
                        
                        # Normalize 0-1000
                        n_ymin = int(min(1000, max(0, (min_y / frame_h) * 1000)))
                        n_xmin = int(min(1000, max(0, (min_x / frame_w) * 1000)))
                        n_ymax = int(min(1000, max(0, (max_y / frame_h) * 1000)))
                        n_xmax = int(min(1000, max(0, (max_x / frame_w) * 1000)))

                        log_items.append({
                            "description": line['description'],
                            "box_2d": [n_ymin, n_xmin, n_ymax, n_xmax]
                        })
                    
                    # Structure the grouped log entry
                    # Using a fixed fake timestamp for consistency
                    log_entry = {
                        "time": "00:00:00", 
                        "items": log_items
                    }
                    return log_entry
                else:
                    print("No lines remaining after deduplication/filtering.")
                    return None

            except Exception as e:
                print(f"OCR logic error: {e}")
                import traceback
                traceback.print_exc()
                return None

    ocr_runner = FaithfulSingleImageOCR(output_dir=target_dir)
    
    # Offset from analysis: "Region: 822x376 at (735,376)"
    # Context image size: 1920x1080 (assuming 1080p from previous logs "1679x1042" captures?)
    # Wait, the logs showed "Captured frame ... 1679x1042" (from user diff lines earlier?)
    # Let's assume standard full screen or use the dimensions found in previous logs if critical.
    # For normalization (0-1000), using the correct screen size is crucial.
    # Looking at the roi offset (735, 376), a 1920x1080 screen is a safe default assumption for "Desktop".
    # User's previous logs showed "1679x1042" sometimes? No, that was ROI size?
    # Let's stick to 1920x1080 as generic Full HD or just use ROI relative if we want 0-1000 within the ROI?
    # NO, production code normalizes against `screen_size`.
    # If we pass `roi_size` as `screen_size`, it normalizes to the ROI.
    # The production code uses `monitor['width']` and `monitor['height']`.
    # Let's use 1920x1080 as a reasonable mock for the full screen.
    
    # Updated Offset from detect_offset.py (Red Box detection)
    # Red Box: x=35, y=230. ROI content inside (centered/padded).
    # Calculated Content Offset: x=40, y=244
    offset_x = 40
    offset_y = 244
    screen_w = 1920
    screen_h = 1080
    
    h, w = img_bgr.shape[:2]
    print(f"Running OCR on image size: {w}x{h} with desktop offset ({offset_x},{offset_y})")
    
    result = ocr_runner._perform_ocr_faithful(
        img_bgr, 
        offset=(offset_x, offset_y), 
        roi_size=(w, h),
        screen_size=(screen_w, screen_h)
    )
    
    if result:
        # Save results matching production format
        with open(output_json_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=None, ensure_ascii=False) # Production usages no indent for lines usually, but indent for debug is nice. Let's use 2.
            
        print(f"Saved faithful OCR output to: {output_json_path}")
        
        # Check against blacklist/garbage locally to show what passed
        print("--- Detected Text (Filtered & Normalized) ---")
        for item in result['items']:
            print(f"Text: {item['description']} | Box: {item['box_2d']}")
    else:
        print("No result produced.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}")
