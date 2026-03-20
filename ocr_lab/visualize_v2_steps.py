import cv2
import numpy as np
import os
import sys
import json
from ocr_engine_v2 import ProductionOCRBaseline

def load_img_robust(path):
    # Support Japanese filenames on Windows
    return cv2.imdecode(np.fromfile(path, dtype=np.uint8), cv2.IMREAD_COLOR)

def visualize_steps(prev_path, curr_path, output_dir="data/results"):
    # Clean and recreate directory
    if os.path.exists(output_dir):
        import shutil
        shutil.rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)
    
    # Load images
    prev = load_img_robust(prev_path)
    curr = load_img_robust(curr_path)
    if prev is None or curr is None:
        print("Error: Could not load images.")
        return

    engine = ProductionOCRBaseline(data_dir=r"c:/Users/y86as/Nippo/nippo_system/data")
    
    # --- Execute Engine with Debug Info ---
    canvas, processed_lines, debug_info = engine.process_frames(prev, curr, return_debug=True)
    
    if canvas is not None:
        # 01: Binary Mask (Raw intermediate)
        cv2.imwrite(os.path.join(output_dir, "01_binary_mask.png"), debug_info["thresh"])
        
        # 02: Dilated Mask (Raw intermediate)
        if "dilated_fine" in debug_info:
            cv2.imwrite(os.path.join(output_dir, "02_dilated_mask.png"), debug_info["dilated_fine"])
        
        # 03: Grouped Lines Data (JSON)
        # Store the raw rects as a list of lists [ [x,y,w,h], ... ] for each line
        lines_data = []
        if "raw_blocks" in debug_info:
            for line_rects in debug_info["raw_blocks"]:
                lines_data.append([list(r) for r in line_rects])
            with open(os.path.join(output_dir, "03_grouped_lines_data.json"), "w", encoding="utf-8") as f:
                json.dump(lines_data, f, ensure_ascii=False, indent=2)
        
        # 04: Composite Canvas (Raw input to Tesseract)
        cv2.imwrite(os.path.join(output_dir, "04_composite_canvas.png"), canvas)
        
        # 05: Final OCR Results (JSON)
        h, w = curr.shape[:2]
        results_dict = engine.run_ocr(canvas, processed_lines, screen_size=(w, h))
        output_dict = {k: v for k, v in results_dict.items() if k != "_raw_for_viz"}
        with open(os.path.join(output_dir, "05_ocr_results.json"), "w", encoding="utf-8") as f:
            f.write("{\n")
            f.write(f'  "time": "{output_dict["time"]}",\n')
            f.write('  "items": [\n')
            for i, item in enumerate(output_dict["items"]):
                comma = "," if i < len(output_dict["items"]) - 1 else ""
                item_json = json.dumps(item, ensure_ascii=False)
                f.write(f'    {item_json}{comma}\n')
            f.write('  ]\n')
            f.write("}\n")
        
        print(f"Extraction complete (Raw Data Only). Files saved in: {output_dir}")
        
        # --- Generate Detailed Mapping Documentation ---
        mapping_path = os.path.join(output_dir, "00_pipeline_mapping.md")
        with open(mapping_path, "w", encoding="utf-8") as f:
            f.write("# OCR パイプライン： 生成データとコードの対応詳細\n\n")
            f.write("このディレクトリのファイルは `visualize_v2_steps.py` によって生成されました。\n")
            f.write("「加工なしの生データ」がプログラム内部のどの変数・関数に対応しているかを示します。\n\n")
            f.write("## 🧪 処理フローと対応表\n\n")
            f.write("| ファイル名 | 役割 | 担当関数・変数 | 解説 |\n")
            f.write("| :--- | :--- | :--- | :--- |\n")
            f.write("| **01_binary_mask.png** | 二値化 | `engine.process_frames` / `thresh` | 差分検知後のピクセルマスク |\n")
            f.write("| **02_dilated_mask.png** | 膨張 | `engine.process_frames` / `dilated_mask` | 文字を塊にするための太らせ処理 |\n")
            f.write("| **03_grouped_lines_data.json** | 行データ | `engine.process_frames` / `lines` | **[OCR投入前]** 行として切り出す前の矩形座標のリスト |\n")
            f.write("| **04_composite_canvas.png** | 合成画像 | `engine.process_frames` / `canvas` | **[OCR投入直前]** Tesseractに実際に渡される画像そのもの |\n")
            f.write("| **05_ocr_results.json** | OCR結果 | `engine.run_ocr` / `output_dict` | **[OCR完了後]** 文字認識を終え、画面座標に直した最終データ |\n\n")
            f.write("--- \n")
            f.write("### 🔍 特筆事項\n")
            f.write("- **04_composite_canvas.png** が「本当にOCRに投げている手前のファイル」です。\n")
            f.write("- これを作成しているのは `ocr_engine_v2.py` の `process_frames` 関数の後半部分（L100-111）です。\n")
            f.write("- **05_ocr_results.json** は、`run_ocr` 関数が **04** の画像を受け取って処理した結果です。\n")
    else:
        print("No significant difference detected between frames.")

if __name__ == "__main__":
    prev_img = r"c:/Users/y86as/Nippo/ocr_lab/data/raw/スクリーンショット 2026-02-20 192914.png"
    curr_img = r"c:/Users/y86as/Nippo/ocr_lab/data/raw/スクリーンショット 2026-02-20 192938.png"
    visualize_steps(prev_img, curr_img)
