
import json
import os
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

def main():
    target_dir = os.path.dirname(__file__)
    json_path = os.path.join(target_dir, "ocr_output_roi.json")
    output_image_path = os.path.join(target_dir, "ocr_reconstructed.png")
    
    # Canvas settings (Screen size assumed in previous step)
    SCREEN_W = 1920
    SCREEN_H = 1080
    
    # Create black canvas
    canvas = np.zeros((SCREEN_H, SCREEN_W, 3), dtype=np.uint8)
    
    # Load JSON
    if not os.path.exists(json_path):
        print(f"Error: {json_path} not found.")
        return

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    items = data.get('items', [])
    print(f"Found {len(items)} items to visualize.")
    
    # Convert to PIL for Japanese text drawing
    img_pil = Image.fromarray(canvas)
    draw = ImageDraw.Draw(img_pil)
    
    # Load Font
    font_path = "C:/Windows/Fonts/msgothic.ttc"
    try:
        font = ImageFont.truetype(font_path, 20)
    except IOError:
        # Fallback
        font = ImageFont.load_default()
        print("Warning: Japanese font not found, using default.")

    for item in items:
        # box_2d: [ymin, xmin, ymax, xmax] (0-1000 normalized)
        ymin_n, xmin_n, ymax_n, xmax_n = item['box_2d']
        text = item['description']
        
        # Denormalize
        x1 = int(xmin_n / 1000 * SCREEN_W)
        y1 = int(ymin_n / 1000 * SCREEN_H)
        x2 = int(xmax_n / 1000 * SCREEN_W)
        y2 = int(ymax_n / 1000 * SCREEN_H)
        
        # Draw box (Green)
        # Using PIL rectangle: [x0, y0, x1, y1]
        draw.rectangle([x1, y1, x2, y2], outline=(0, 255, 0), width=1)
        
        # Draw text (Red, exactly at top-left of box)
        draw.text((x1, y1), text, font=font, fill=(255, 0, 0))

    # Save
    img_pil.save(output_image_path)
    print(f"Saved visualization to: {output_image_path}")

if __name__ == "__main__":
    main()
