import cv2
import numpy as np
import os
import json
from ocr_engine_v2 import ProductionOCRBaseline

def load_img_robust(path):
    return cv2.imdecode(np.fromfile(path, dtype=np.uint8), cv2.IMREAD_COLOR)

def validate():
    # Use empty image as prev to treat whole curr as new content
    curr_path = r"c:/Users/y86as/Nippo/ocr_lab/data/test_raw/02_dense_content.png"
    curr = load_img_robust(curr_path)
    prev = np.zeros_like(curr)
    
    engine = ProductionOCRBaseline(data_dir=r"c:/Users/y86as/Nippo/nippo_system/data")
    
    # Top 2 Parameters from previous run
    best_params_list = [
        {"scale_factor": 2.5, "line_spacing": 82, "group_v_dist": 15, "group_h_dist": 14},
        {"scale_factor": 2.5, "line_spacing": 82, "group_v_dist": 16, "group_h_dist": 14}
    ]
    
    # Results directory for this validation
    val_dir = "data/validation_stress"
    os.makedirs(val_dir, exist_ok=True)
    
    for i, params in enumerate(best_params_list):
        print(f"\n--- Validation Run {i+1} ---")
        print(f"Params: {params}")
        
        engine.update_params(**params)
        
        canvas, p_lines = engine.process_frames(prev, curr)
        
        if canvas is not None:
            # Save the composite canvas for manual verification of border-text grouping
            cv2.imwrite(os.path.join(val_dir, f"run_{i+1}_canvas.png"), canvas)
            
            h, w = curr.shape[:2]
            ocr_out = engine.run_ocr(canvas, p_lines, screen_size=(w, h))
            
            items = ocr_out.get("items", [])
            word_count = len(items)
            total_chars = sum(len(item["description"]) for item in items)
            
            print(f"Words: {word_count}")
            print(f"Chars: {total_chars}")
            
            # Save results
            with open(os.path.join(val_dir, f"run_{i+1}_results.json"), "w", encoding="utf-8") as f:
                json.dump(ocr_out, f, ensure_ascii=False, indent=2)
                
            # Quick look at first few detected words
            top_words = [item["description"] for item in items[:5]]
            print(f"First few words: {top_words}")
        else:
            print("Failed to generate canvas.")

if __name__ == "__main__":
    validate()
