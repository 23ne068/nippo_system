import cv2
import numpy as np
import json
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "nippo-ocr", "src")))
from nippo_ocr.factory import create_ocr_engine

def test():
    print("Testing WinRTEngine Plugin Architecture...")
    img = np.zeros((1080, 1920, 3), dtype=np.uint8)
    img.fill(255)
    cv2.putText(img, "Nippo OCR Windows Native API Factory Test!", (100, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
    
    cv2.imwrite("test_curr.png", img)
    prev = np.zeros_like(img)
    
    engine = create_ocr_engine("winrt")
    canvas, lines = engine.process_frames(prev, img)
    res = engine.run_ocr(canvas, lines, screen_size=(1920, 1080))
    print(json.dumps(res, indent=2, ensure_ascii=False))
    print("Test passed successfully!")

if __name__ == "__main__":
    test()
