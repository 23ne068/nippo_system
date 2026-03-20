
import cv2
import sys
import os
import json
import logging
import pytesseract
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from nippo_system.modules.screen_ocr import ScreenOCR

def main():
    base_dir = os.path.dirname(__file__)
    roi_img_path = os.path.join(base_dir, "ocr_20260220_034236_roi.png")
    roi_json_path = os.path.join(base_dir, "ocr_output_roi_raw.json")
    output_image_path = os.path.join(base_dir, "padding_40px_result.png")
    
    if not os.path.exists(roi_img_path) or not os.path.exists(roi_json_path):
        print("Error: Files not found.")
        return

    # Initialize ScreenOCR to handle Tesseract configuration automatically
    ocr_runner = ScreenOCR()

    # Load ROI Image
    roi_img = cv2.imread(roi_img_path)
    rh, rw = roi_img.shape[:2]
    
    # Load JSON to find content bounds (same logic as experiment)
    with open(roi_json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    items = data.get('items', [])
    if not items:
        return
        
    SCREEN_W, SCREEN_H = 1920, 1080
    OFFSET_X, OFFSET_Y = 40, 244
    
    min_rx, min_ry = float('inf'), float('inf')
    max_rx, max_ry = float('-inf'), float('-inf')
    
    for item in items:
        ymin_n, xmin_n, ymax_n, xmax_n = item['box_2d']
        sx1 = xmin_n / 1000 * SCREEN_W
        sy1 = ymin_n / 1000 * SCREEN_H
        sx2 = xmax_n / 1000 * SCREEN_W
        sy2 = ymax_n / 1000 * SCREEN_H
        rx1 = sx1 - OFFSET_X
        ry1 = sy1 - OFFSET_Y
        rx2 = sx2 - OFFSET_X
        ry2 = sy2 - OFFSET_Y
        min_rx = min(min_rx, rx1)
        min_ry = min(min_ry, ry1)
        max_rx = max(max_rx, rx2)
        max_ry = max(max_ry, ry2)
        
    min_rx = max(0, int(min_rx))
    min_ry = max(0, int(min_ry))
    max_rx = min(rw, int(max_rx))
    max_ry = min(rh, int(max_ry))
    
    # Crop with 40px Padding
    pad = 40
    cx1 = max(0, min_rx - pad)
    cy1 = max(0, min_ry - pad)
    cx2 = min(rw, max_rx + pad)
    cy2 = min(rh, max_ry + pad)
    
    crop_img = roi_img[cy1:cy2, cx1:cx2]
    print(f"Cropped to: {cx2-cx1}x{cy2-cy1} (Padding {pad}px)")
    
    # Run OCR (Standard Config)
    img_rgb = cv2.cvtColor(crop_img, cv2.COLOR_BGR2RGB)
    config = r'--psm 6'
    data = pytesseract.image_to_data(img_rgb, lang="jpn", config=config, output_type=pytesseract.Output.DICT)
    
    # Visualize
    pil_img = Image.fromarray(img_rgb)
    draw = ImageDraw.Draw(pil_img)
    try:
        font_path = "C:/Windows/Fonts/msgothic.ttc"
        font_base = ImageFont.truetype(font_path, 20)
    except:
        font_base = ImageFont.load_default()

    count = 0
    num_boxes = len(data['text'])
    for i in range(num_boxes):
        text = data['text'][i].strip()
        if not text: continue
        conf = int(data['conf'][i])
        if conf < 50: continue
        if len(text) == 1 and ord(text) < 128: continue
        
        count += 1
        x = data['left'][i]
        y = data['top'][i]
        w = data['width'][i]
        h = data['height'][i]
        
        # Dynamic font
        font_size = max(8, int(h * 0.8))
        try:
             font = ImageFont.truetype(font_path, font_size)
        except:
             font = font_base

        draw.rectangle([x, y, x+w, y+h], outline=(255, 255, 0), width=1)
        draw.text((x, y), text, font=font, fill=(255, 0, 0))

    pil_img.save(output_image_path)
    print(f"Saved visualization to: {output_image_path}")
    print(f"Word Count: {count}")

if __name__ == "__main__":
    main()
