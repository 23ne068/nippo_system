import json

def find_click_target(x, y, ocr_items):
    """
    座標(x, y)がOCRで読み取られたどのBoxの中にあるかを判定し、
    そのテキスト（意味）を返す。
    """
    for item in ocr_items:
        # OCR Box の形式: [[y1, x1, y2, x2]] またはそのままのリスト
        box = item.get("box_2d", [])
        if not box or len(box) < 4:
            continue
        
        y1, x1, y2, x2 = box
        if x1 <= x <= x2 and y1 <= y <= y2:
            return item.get("description", "")
            
    return None
