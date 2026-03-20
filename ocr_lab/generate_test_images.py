import cv2
import numpy as np
import os
from PIL import Image, ImageDraw, ImageFont

def generate_black_image(output_path):
    # 1920x1080 solid black
    img = np.zeros((1080, 1920, 3), dtype=np.uint8)
    cv2.imwrite(output_path, img)
    print(f"Generated: {output_path}")

def generate_dense_image(output_path, spec_path):
    # 1920x1080 black background
    canvas = Image.new('RGB', (1920, 1080), color=(0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    
    font_paths = [
        "C:\\Windows\\Fonts\\msgothic.ttc",
        "C:\\Windows\\Fonts\\meiryo.ttc",
        "C:\\Windows\\Fonts\\arial.ttf"
    ]
    
    def get_font(size):
        for p in font_paths:
            if os.path.exists(p):
                return ImageFont.truetype(p, size)
        return ImageFont.load_default()

    # Simple Parser
    if not os.path.exists(spec_path):
        print(f"Spec not found: {spec_path}")
        return

    with open(spec_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    blocks = []
    current_block = None
    collecting_content = False

    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"): continue
        
        if line.startswith("BLOCK"):
            collecting_content = False
            parts = [p.strip() for p in line.split("|")]
            # BLOCK | X | Y | Width | Font_Size | Paragraphs | Border
            current_block = {
                "x": int(parts[1]),
                "y": int(parts[2]),
                "w": int(parts[3]),
                "size": int(parts[4]),
                "border": int(parts[6]) if len(parts) > 6 else 0,
                "content": []
            }
            blocks.append(current_block)
        elif line.startswith("CONTENT:"):
            collecting_content = True
        elif collecting_content and current_block:
            current_block["content"].append(line)

    # Render Blocks
    for b in blocks:
        font = get_font(b["size"])
        curr_y = b["y"]
        
        # Calculate block height for border
        start_y = curr_y
        
        # Dry run or just draw border around the specified area
        if b["border"]:
            # Draw a simple box around the block
            # We estimate the height or just draw a fixed box if content is known
            # For simplicity, let's draw it based on content rendering
            pass

        padding = 10
        inner_x = b["x"] + (padding if b["border"] else 0)
        inner_y = b["y"] + (padding if b["border"] else 0)
        curr_y = inner_y
        max_w = b["w"] - (padding * 2 if b["border"] else 0)

        with open("c:/Users/y86as/Nippo/ocr_lab/debug_layout.txt", "a", encoding="utf-8") as df:
            df.write(f"\n--- Block ID: {blocks.index(b)+1} (Font {b['size']}px) ---\n")
            for paragraph in b["content"]:
                words = list(paragraph) if any(ord(c) > 128 for c in paragraph) else paragraph.split()
                line_str = ""
                for word in words:
                    test_line = line_str + word + ("" if any(ord(c) > 128 for c in word) else " ")
                    w = draw.textlength(test_line, font=font)
                    if w > max_w:
                        draw.text((inner_x, curr_y), line_str, fill=(255, 255, 255), font=font)
                        df.write(f"LINE: {line_str}\n")
                        curr_y += b["size"] + 5
                        line_str = word + ("" if any(ord(c) > 128 for c in word) else " ")
                    else:
                        line_str = test_line
                
                if line_str:
                    draw.text((inner_x, curr_y), line_str, fill=(255, 255, 255), font=font)
                    df.write(f"LINE: {line_str}\n")
                    curr_y += b["size"] + 15

        if b["border"]:
            # Draw rectangle after rendering to know height
            draw.rectangle([b["x"], b["y"], b["x"] + b["w"], curr_y], outline=(255, 255, 255), width=2)

    canvas.save(output_path)
    print(f"Generated: {output_path}")

if __name__ == "__main__":
    out_dir = r"c:/Users/y86as/Nippo/ocr_lab/data/test_raw"
    spec_file = os.path.join(out_dir, "layout_spec.txt")
    os.makedirs(out_dir, exist_ok=True)
    
    generate_black_image(os.path.join(out_dir, "01_all_black.png"))
    generate_dense_image(os.path.join(out_dir, "02_dense_content.png"), spec_file)
