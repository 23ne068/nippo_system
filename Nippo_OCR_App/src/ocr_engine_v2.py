import cv2
import numpy as np
import pytesseract
import os
import sys
import time
import json
import logging

# Production-like configuration
OCR_LANG = "jpn+eng"  # Use jpn+eng to support mixed text
OCR_DIFF_THRESHOLD = 5000

class ProductionOCRBaseline:
    """
    A standalone class that mirrors the production ScreenOCR logic 
    for use in experimental environments (ocr_lab).
    """
    def __init__(self, tesseract_path=None, data_dir=None):
        self.data_dir = data_dir or "raw_streams/ocr"
        
        # Determine the base path for bundled resources
        if getattr(sys, 'frozen', False):
            # PyInstaller extraction root
            base_path = sys._MEIPASS
        else:
            # Script directory
            script_dir = os.path.dirname(os.path.abspath(__file__))
            base_path = os.path.dirname(script_dir)
            
        bundled_tessdata = os.path.join(base_path, "resources", "tesseract", "tessdata")
        
        if os.path.exists(bundled_tessdata):
            self.tessdata_path = bundled_tessdata
        else:
            # Fallback path (could be in Documents/Nippo_OCR/data/tessdata)
            self.tessdata_path = os.path.abspath(os.path.join(self.data_dir, "tessdata"))
            
        # TESSDATA_PREFIX should be the directory CONTAINING the 'tessdata' folder
        if os.path.exists(self.tessdata_path):
            os.environ["TESSDATA_PREFIX"] = os.path.dirname(self.tessdata_path)
            
        self.setup_tesseract(tesseract_path)
        
        # Default optimization parameters
        self.params = {
            "scale_factor": 2.5,     # Global fallback
            "line_spacing": 80,       # Vertical gap on canvas
            "margin_w": 40,           # Horizontal padding
            "group_v_dist": 15,       # Vertical grouping threshold
            "group_h_dist": 20,       # Horizontal grouping threshold (Tightened)
            "dilation_iterations": 1, 
            "dilation_kernel_size": 3,
            "target_char_height": 45  # Gold standard height for Tesseract
        }

        # TESSDATA_PREFIX is already set above if path exists

    def setup_tesseract(self, path=None):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        bundled_tesseract = os.path.join(project_root, "resources", "tesseract", "tesseract.exe")
        
        if path and os.path.exists(path):
            pytesseract.pytesseract.tesseract_cmd = path
        elif os.path.exists(bundled_tesseract):
            pytesseract.pytesseract.tesseract_cmd = bundled_tesseract
        else:
            paths = [
                r"C:\Program Files\Tesseract-OCR\tesseract.exe",
                r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
                os.path.expanduser(r"~\AppData\Local\Tesseract-OCR\tesseract.exe")
            ]
            for p in paths:
                if os.path.exists(p):
                    pytesseract.pytesseract.tesseract_cmd = p
                    break

    def update_params(self, **kwargs):
        self.params.update(kwargs)

    def process_frames(self, prev_img, curr_img, return_debug=False):
        """
        Production logic: Diff -> Group -> Composite
        If return_debug is True, returns (canvas, processed_lines, debug_info)
        """
        scale = self.params["scale_factor"]
        line_spacing = self.params.get("line_spacing", 80)
        margin_w = self.params.get("margin_w", 40)
        v_dist = self.params.get("group_v_dist", 15)

        gray_prev = cv2.cvtColor(prev_img, cv2.COLOR_BGR2GRAY)
        gray_curr = cv2.cvtColor(curr_img, cv2.COLOR_BGR2GRAY)
        
        diff = cv2.absdiff(gray_prev, gray_curr)
        _, thresh = cv2.threshold(diff, 30, 255, cv2.THRESH_BINARY)
        
        debug_info = {}
        if return_debug:
            debug_info["diff"] = diff
            debug_info["thresh"] = thresh

        # Pass 1: Fine-grained detection for metric estimation
        kernel_fine = np.ones((3, 3), np.uint8)
        dilated_fine = cv2.dilate(thresh, kernel_fine, iterations=1)
        cnts_fine, _ = cv2.findContours(dilated_fine, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        rects_fine = [cv2.boundingRect(c) for c in cnts_fine if cv2.contourArea(c) > 5] # Filter noise

        if return_debug:
            debug_info["dilated_fine"] = dilated_fine
            debug_info["raw_rects_fine"] = rects_fine

        if not rects_fine:
            return (None, [], debug_info) if return_debug else (None, [])

        # Pass 2: Analysis-driven grouping
        # Calculate global median height for baseline
        all_heights = [r[3] for r in rects_fine]
        med_h = np.median(all_heights) if all_heights else 15
        
        # Sort for grouping
        rects_fine.sort(key=lambda r: (r[1], r[0]))
        
        # Group into lines/blocks manually (avoiding heavy dilation that merges columns)
        v_dist_limit = self.params.get("group_v_dist", 15)
        h_dist_limit = self.params.get("group_h_dist", 50) # Reduced to prevent column merging
        
        # Simple clustering
        blocks = []
        visited = [False] * len(rects_fine)
        
        for i in range(len(rects_fine)):
            if visited[i]: continue
            
            # Start a new block
            curr_block = [rects_fine[i]]
            visited[i] = True
            
            # BFS-like expansion
            queue = [rects_fine[i]]
            while queue:
                r1 = queue.pop(0)
                for j in range(len(rects_fine)):
                    if visited[j]: continue
                    r2 = rects_fine[j]
                    
                    # Vertical check: near-equal Y (same line) or within v_dist
                    # Horizontal check: within h_dist
                    v_overlap = max(0, min(r1[1]+r1[3], r2[1]+r2[3]) - max(r1[1], r2[1]))
                    h_gap = max(0, r2[0] - (r1[0]+r1[2])) if r2[0] > r1[0] else max(0, r1[0] - (r2[0]+r2[2]))
                    v_gap = max(0, r2[1] - (r1[1]+r1[3])) if r2[1] > r1[1] else max(0, r1[1] - (r2[1]+r2[3]))
                    
                    if (v_overlap > 0 and h_gap < h_dist_limit) or (h_gap < h_dist_limit and v_gap < v_dist_limit):
                        visited[j] = True
                        curr_block.append(r2)
                        queue.append(r2)
            blocks.append(curr_block)
        
        print(f"DEBUG: Found {len(blocks)} raw blocks after clustering (h_limit={h_dist_limit})")

        if return_debug:
            debug_info["raw_blocks"] = blocks
            
        # --- NEW: SORT BLOCKS BY READING ORDER ---
        # 1. Group blocks into columns
        # Calculate bounding box for each block
        block_meta = []
        for line_rects in blocks:
            lx1 = min(r[0] for r in line_rects)
            ly1 = min(r[1] for r in line_rects)
            lx2 = max(r[0] + r[2] for r in line_rects)
            ly2 = max(r[1] + r[3] for r in line_rects)
            block_meta.append({"rect": (lx1, ly1, lx2-lx1, ly2-ly1), "rects": line_rects})
            
        # Sort by X to group into columns
        block_meta.sort(key=lambda b: b["rect"][0])
        
        logical_columns = []
        if block_meta:
            curr_col = [block_meta[0]]
            prev_x2 = block_meta[0]["rect"][0] + block_meta[0]["rect"][2]
            for b in block_meta[1:]:
                # If gap between blocks is > 100px, it's a new column
                if b["rect"][0] > prev_x2 + 100:
                    logical_columns.append(curr_col)
                    curr_col = [b]
                else:
                    curr_col.append(b)
                prev_x2 = max(prev_x2, b["rect"][0] + b["rect"][2])
            logical_columns.append(curr_col)
            
        # 2. Sort within columns by Y and flatten
        sorted_blocks = []
        for col in logical_columns:
            col.sort(key=lambda b: b["rect"][1])
            for b in col:
                sorted_blocks.append(b["rects"])
                
        # Use sorted_blocks for processing
        processed_lines = []
        for line_rects in sorted_blocks:
            lx1 = min(r[0] for r in line_rects)
            ly1 = min(r[1] for r in line_rects)
            lx2 = max(r[0] + r[2] for r in line_rects)
            ly2 = max(r[1] + r[3] for r in line_rects)
            bw, bh = lx2-lx1, ly2-ly1
            
            # Estimate metrics for this block
            # Shift rects to block-local coordinates for easier processing
            local_rects = [(r[0]-lx1, r[1]-ly1, r[2], r[3]) for r in line_rects]
            metrics = self._estimate_metrics(local_rects, bw, bh)
            
            processed_lines.append({
                "orig_rect": (lx1, ly1, bw, bh),
                "img": curr_img[ly1:ly2, lx1:lx2],
                "metrics": metrics,
                "is_bordered": metrics.get("is_bordered", False)
            })

        if not processed_lines:
            return (None, [], debug_info) if return_debug else (None, [])

        # --- ADAPTIVE MEASUREMENT PASS ---
        target_h = self.params.get("target_char_height", 0)
        line_spacing = self.params.get("line_spacing", 80)
        margin_w = 40
        
        total_canvas_h = line_spacing
        max_canvas_w = 0
        for p in processed_lines:
            metrics = p["metrics"]
            avg_h = metrics.get("avg_font_height", 15)
            
            # Adaptive scaling: Normalize to target_h if enabled
            adaptive_scale = 1.0
            if target_h > 0 and avg_h > 0:
                adaptive_scale = target_h / avg_h
                # Clamp scale to reasonable limits (1.0 to 6.0x)
                adaptive_scale = max(1.0, min(6.0, adaptive_scale))
            
            p["scale_applied"] = adaptive_scale
            
            # Re-calculate size for this block
            lx1, ly1, lw_orig, lh_orig = p["orig_rect"]
            h_new = int(lh_orig * adaptive_scale)
            w_new = int(lw_orig * adaptive_scale)
            
            p["scaled_size"] = (w_new, h_new)
            total_canvas_h += h_new + line_spacing
            max_canvas_w = max(max_canvas_w, w_new + 2*margin_w)

        # Create canvas with finalized dimensions
        canvas = np.zeros((total_canvas_h, max_canvas_w, 3), dtype=np.uint8)
        
        # --- COMPOSITION PASS ---
        curr_y = line_spacing
        for p in processed_lines:
            adaptive_scale = p["scale_applied"]
            lx1, ly1, lw_orig, lh_orig = p["orig_rect"]
            w_new, h_new = p["scaled_size"]
            
            line_crop = p["img"] # Use the stored original crop
            if adaptive_scale != 1.0:
                line_crop = cv2.resize(line_crop, (w_new, h_new), interpolation=cv2.INTER_CUBIC)
            
            # Paste into canvas with margins
            canvas[curr_y:curr_y+h_new, margin_w:margin_w+w_new] = line_crop
            p['canvas_y'] = curr_y
            curr_y += h_new + line_spacing

        if return_debug:
            return canvas, processed_lines, debug_info
        return canvas, processed_lines

    def run_ocr(self, canvas, processed_lines, screen_size=(1920, 1080)):
        """
        Refactored: Block-by-Block isolated OCR for structural stability.
        """
        import time
        start_time = time.time()
        
        all_raw_words = []
        margin_w = 40
        
        for idx, p in enumerate(processed_lines):
            # Extract block from canvas
            w_new, h_new = p["scaled_size"]
            c_y = p["canvas_y"]
            block_img = canvas[c_y : c_y + h_new, margin_w : margin_w + w_new].copy() # .copy() to ensure it's writable
            
            # --- PHASE 3 PRE-PROCESSING ---
            # 1. Border Cleansing (Remove border pixels to avoid being seen as 'I' or 'l')
            if p.get("is_bordered", False):
                # Dynamically crop inward based on detected border thickness and block size
                crop_px = p.get("border_thickness", 4)
                
                # Ensure we don't over-crop small blocks
                max_crop_h = int(h_new * 0.2)
                max_crop_w = int(w_new * 0.2)
                crop_px_y = min(crop_px, max_crop_h)
                crop_px_x = min(crop_px, max_crop_w)

                if block_img.shape[0] > crop_px_y * 2 and block_img.shape[1] > crop_px_x * 2:
                    # Apply crop
                    block_img = block_img[crop_px_y:-crop_px_y, crop_px_x:-crop_px_x]
                    p["border_offset_x"] = crop_px_x
                    p["border_offset_y"] = crop_px_y
                else:
                    p["border_offset_x"] = 0
                    p["border_offset_y"] = 0
            else:
                p["border_offset_x"] = 0
                p["border_offset_y"] = 0
            
            # 2. CJK Horizontal Gluing
            # Determine if Japanese (CJK) text density
            # Simple heuristic: if any char in estimated text was CJK, or just apply widely
            # For now, we'll apply if OCR_LANG is jpn
            is_cjk = (OCR_LANG == "jpn") # Simplified heuristic for lab
            scale = p.get('scale_applied', 1.0)
            
            if is_cjk and block_img.size > 0 and h_new > 20:
                # Apply horizontal morphological closing to unify fragmented chars
                # Gentle kernel to avoid blurring characters into lines
                k_width = max(2, int(scale * 1.5))
                k_height = 1
                kernel = np.ones((k_height, k_width), np.uint8) 
                
                block_img = cv2.morphologyEx(block_img, cv2.MORPH_CLOSE, kernel, iterations=1)
            
            # --- ISOLATED OCR CALL ---
            if block_img.size == 0:
                continue

            img_rgb = cv2.cvtColor(block_img, cv2.COLOR_BGR2RGB)
            # Use PSM 3 (Automatic) for Japanese to let it find lines better
            psm = 3 if is_cjk else 6
            config = f'--psm {psm} --tessdata-dir {self.tessdata_path}'
            data = pytesseract.image_to_data(img_rgb, lang=OCR_LANG, config=config, output_type=pytesseract.Output.DICT)
            
            num_boxes = len(data['text'])
            ox, oy, _, _ = p['orig_rect']
            scale = p.get('scale_applied', 1.0)
            
            for i in range(num_boxes):
                text = data['text'][i].strip()
                if not text or int(data['conf'][i]) < 45: continue
                
                # For Japanese, strip extraneous spaces that Tesseract often adds between ideographs
                # We only do this if the word actually contains CJK characters.
                has_cjk = any("\u4e00" <= c <= "\u9fff" or "\u3040" <= c <= "\u30ff" for c in text)
                if has_cjk:
                    text = "".join(text.split())
                    if not text: continue
                
                if len(text) == 1 and ord(text) < 128 and not text.isalnum(): continue
                
                cx, cy = data['left'][i], data['top'][i]
                cw, ch = data['width'][i], data['height'][i]
                
                # Back-mapping (Local Block -> Screen)
                # Local scaled X = cx + border_offset_x
                # Local original (unscaled) X = (cx + border_offset_x) / scale
                # Screen X = ox + Local original X
                b_off_x = p.get("border_offset_x", 0)
                b_off_y = p.get("border_offset_y", 0)
                
                # Correct order of operations for unscaling:
                mapped_x = ox + ((cx + b_off_x) / scale)
                mapped_y = oy + ((cy + b_off_y) / scale)
                cw_orig = cw / scale
                ch_orig = ch / scale
                
                # DEBUG PRINT: Verify mapped coordinate bounds
                # Enable debugging to trace low accuracy
                # print(f"DEBUG MAP Block {idx}: text='{text}', ox={ox} oy={oy} -> mapped=({mapped_x:.1f}, {mapped_y:.1f})")
                
                all_raw_words.append({
                    "description": text,
                    "confidence": int(data['conf'][i]),
                    "block_id": idx,
                    "boundingPoly": {
                        "vertices": [
                            {"x": mapped_x, "y": mapped_y},
                            {"x": mapped_x + cw_orig, "y": mapped_y},
                            {"x": mapped_x + cw_orig, "y": mapped_y + ch_orig},
                            {"x": mapped_x, "y": mapped_y + ch_orig}
                        ]
                    }
                })

        if not all_raw_words:
            return {"time": time.strftime('%H:%M:%S'), "duration": time.time()-start_time, "items": []}

        # 1. Group into Lines (Global grouping of isolated words)
        lines = self._group_words_into_lines_google_format(all_raw_words)
        
        # 2. Deduplicate (Pass dummy ROI for lab environment)
        # In real logic, ROI filtering is complex, but here we just want the line consolidation
        unique_lines = self._filter_duplicate_lines_iou(lines, roi_rect=(0,0,0,0))

        # 3. Normalize to 0-1000 (Production Format)
        sw, sh = screen_size
        log_items = []
        for line in unique_lines:
            vs = line['boundingPoly']['vertices']
            n_ymin = int(min(1000, max(0, (vs[0]['y'] / sh) * 1000)))
            n_xmin = int(min(1000, max(0, (vs[0]['x'] / sw) * 1000)))
            n_ymax = int(min(1000, max(0, (vs[2]['y'] / sh) * 1000)))
            n_xmax = int(min(1000, max(0, (vs[2]['x'] / sw) * 1000)))

            log_items.append({
                "description": line['description'],
                "box_2d": [n_ymin, n_xmin, n_ymax, n_xmax],
                "block_id": line.get("block_id", 0)
            })

        # We trust the processing order from `process_frames` which sorts blocks logically.
        # Global coordinate sorting breaks the careful block isolation structure and merges
        # unrelated columns, so we keep `log_items` as is, sorted by `block_id` and then Y.

        return {
            "time": time.strftime('%H:%M:%S'),
            "duration": time.time() - start_time,
            "items": log_items,
            "_raw_for_viz": unique_lines # Internal use for visualization
        }

    def sort_items_reading_order(self, items):
        """
        Sort OCR items into a logical reading order (Column-first, then Top-down).
        Useful for multi-column layouts.
        """
        if not items:
            return []
            
        # 1. Cluster into columns based on X coordinate
        # Using a simple heuristic: if X centroids are far apart, they are different columns.
        sorted_by_x = sorted(items, key=lambda x: x["box_2d"][1]) # Sort by xmin
        
        columns = []
        if sorted_by_x:
            curr_column = [sorted_by_x[0]]
            prev_xmax = sorted_by_x[0]["box_2d"][3]
            
            for item in sorted_by_x[1:]:
                xmin = item["box_2d"][1]
                # If these overlap horizontally or are very close, they belong to the same 'logical column group'
                # But for a strict 2-column layout, we look for a significant gap.
                # Threshold: 10% of screen width (100 units in 0-1000 scale)
                if xmin > prev_xmax + 50: 
                    columns.append(curr_column)
                    curr_column = [item]
                else:
                    curr_column.append(item)
                prev_xmax = max(prev_xmax, item["box_2d"][3])
            columns.append(curr_column)
            
        # 2. Sort each column by Y
        final_items = []
        for col in columns:
            col.sort(key=lambda x: x["box_2d"][0]) # Sort by ymin
            final_items.extend(col)
            
        return final_items

    def _group_words_into_lines_google_format(self, words):
        # Group words by block_id first (Strict isolation)
        from collections import defaultdict
        block_groups = defaultdict(list)
        for w in words:
            block_groups[w.get("block_id", 0)].append(w)
            
        all_lines = []
        for b_id, b_words in block_groups.items():
            def get_cy(w):
                vs = w['boundingPoly']['vertices']
                return (vs[0]['y'] + vs[2]['y']) / 2
            def get_lx(w):
                return w['boundingPoly']['vertices'][0]['x']
            def get_h(w):
                vs = w['boundingPoly']['vertices']
                return vs[2]['y'] - vs[0]['y']

            # Estimate average height
            avg_h = np.median([get_h(w) for w in b_words]) if b_words else 15
            y_tolerance = max(10, avg_h * 0.6) # Words within 60% of height belong to the same line

            # 1. Sort primarily by Y
            b_words.sort(key=get_cy)
            
            # 2. Cluster into physical lines by Y
            y_lines = []
            current_y_line = []
            for word in b_words:
                if not current_y_line:
                    current_y_line.append(word)
                else:
                    # Compare with the average Y of the current line to be stable
                    line_cy = np.mean([get_cy(w) for w in current_y_line])
                    if abs(get_cy(word) - line_cy) < y_tolerance:
                        current_y_line.append(word)
                    else:
                        y_lines.append(current_y_line)
                        current_y_line = [word]
            if current_y_line:
                y_lines.append(current_y_line)
                
            # 3. Process each physical line: sort by X, then merge horizontally
            for y_line in y_lines:
                y_line.sort(key=get_lx)
                
                current_line = []
                for word in y_line:
                    if not current_line:
                        current_line.append(word)
                        continue
                    
                    last = current_line[-1]
                    rx1 = last['boundingPoly']['vertices'][1]['x']
                    lx2 = word['boundingPoly']['vertices'][0]['x']
                    ch_h = get_h(last)
                    
                    h_gap_tolerance = max(20, ch_h * 1.5)
                    
                    if (lx2 - rx1) < h_gap_tolerance:
                        current_line.append(word)
                    else:
                        merged = self._merge_line_words_google(current_line)
                        merged["block_id"] = b_id
                        all_lines.append(merged)
                        current_line = [word]
                
                if current_line:
                    merged = self._merge_line_words_google(current_line)
                    merged["block_id"] = b_id
                    all_lines.append(merged)
                
        return all_lines

    def _merge_line_words_google(self, words):
        full_text = ""
        for i, w in enumerate(words):
            if i > 0:
                # Add space if previous or current word is primarily alphanumeric/latin
                prev_txt = words[i-1]['description']
                curr_txt = w['description']
                if prev_txt[-1].isalnum() or curr_txt[0].isalnum():
                    full_text += " "
            full_text += w['description']
        all_xs = [v['x'] for w in words for v in w['boundingPoly']['vertices']]
        all_ys = [v['y'] for w in words for v in w['boundingPoly']['vertices']]
        min_x, max_x = min(all_xs), max(all_xs)
        min_y, max_y = min(all_ys), max(all_ys)
        return {
            "description": full_text,
            "boundingPoly": {
                "vertices": [
                    {"x": min_x, "y": min_y}, {"x": max_x, "y": min_y},
                    {"x": max_x, "y": max_y}, {"x": min_x, "y": max_y}
                ]
            }
        }

    def _filter_duplicate_lines_iou(self, new_lines, roi_rect):
        # Simplified for lab: removes only immediate duplicates/overlaps within same frame results
        # Production has temporal cache, but for single-frame test, we just prune internal overlaps
        pruned = []
        for line in new_lines:
            is_dup = False
            vs = line['boundingPoly']['vertices']
            box_curr = [vs[0]['x'], vs[0]['y'], vs[2]['x'], vs[2]['y']]
            for p in pruned:
                pvs = p['boundingPoly']['vertices']
                box_p = [pvs[0]['x'], pvs[0]['y'], pvs[2]['x'], pvs[2]['y']]
                # Simple IoU
                inter = max(0, min(box_curr[2], box_p[2]) - max(box_curr[0], box_p[0])) * \
                        max(0, min(box_curr[3], box_p[3]) - max(box_curr[1], box_p[1]))
                area1 = (box_curr[2]-box_curr[0])*(box_curr[3]-box_curr[1])
                area2 = (box_p[2]-box_p[0])*(box_p[3]-box_p[1])
                iou = inter / float(area1 + area2 - inter + 1e-6)
                if iou > 0.8: # Very high overlap
                    is_dup = True; break
            if not is_dup: pruned.append(line)
        return pruned

    def _estimate_metrics(self, rects, bw, bh):
        """
        Estimate font size and line count from a collection of rectangles.
        Also checks for border-like structures.
        """
        if not rects:
            return {"avg_font_height": 0, "line_count": 0, "is_bordered": False}
            
        # 1. Detect Border
        # A component is likely a border if it spans most of the block's width and height
        # AND its thickness is small relative to its size
        is_bordered = False
        border_thickness = 0
        for r in rects:
            if r[2] > bw * 0.8 and r[3] > bh * 0.8:
                is_bordered = True
                # Heuristic: If it's a large rect, the border thickness is likely 
                # related to the difference between its outer and inner bounding box,
                # but Tesseract bounding rects for borders are just the outer box.
                # Default to 4px crop for borders (on scaled image)
                border_thickness = 4
                break
        
        # 2. Initial Average Font Height
        # Filter out "border-like" rectangles before calculating median font size
        non_border_rects = [r for r in rects if not (r[2] > bw * 0.8 and r[3] > bh * 0.8)]
        if not non_border_rects: non_border_rects = rects # Fallback
        
        heights = [r[3] for r in non_border_rects]
        raw_med_h = np.median(heights) if heights else 0
        
        char_heights = [h for h in heights if h < raw_med_h * 2.5 and h > 5]
        if not char_heights:
            char_heights = [raw_med_h] if raw_med_h > 0 else [15]
            
        avg_h = np.median(char_heights)
        
        # 3. Line Count Estimation
        sorted_rects = sorted(non_border_rects, key=lambda r: r[1])
        curr_line_count = 0
        if sorted_rects:
            curr_line_y2 = -100
            for r in sorted_rects:
                if r[1] > curr_line_y2 - (avg_h * 0.3):
                    curr_line_count += 1
                    curr_line_y2 = r[1] + r[3]
                else:
                    curr_line_y2 = max(curr_line_y2, r[1] + r[3])
            
        return {
            "avg_font_height": float(avg_h),
            "line_count": int(curr_line_count),
            "is_bordered": is_bordered,
            "border_thickness": border_thickness
        }

    def visualize_results(self, original_img, results_dict, output_path):
        """
        Create an overlay image using the raw lines (internal format).
        """
        viz = original_img.copy()
        # results_dict is the production-style dict, we use the internal '_raw_for_viz'
        for line in results_dict.get('_raw_for_viz', []):
            vs = line['boundingPoly']['vertices']
            x, y = vs[0]['x'], vs[0]['y']
            w, h = vs[2]['x'] - x, vs[2]['y'] - y
            cv2.rectangle(viz, (int(x), int(y)), (int(x + w), int(y + h)), (0, 255, 0), 2)
        
        cv2.imwrite(output_path, viz)
        return output_path

if __name__ == "__main__":
    # Example usage for lab testing
    import sys
    if len(sys.argv) < 3:
        print("Usage: ocr_engine_v2.py <prev_img> <curr_img>")
        sys.exit(1)

    p_path = sys.argv[1]
    c_path = sys.argv[2]
    
    prev = cv2.imread(p_path)
    curr = cv2.imread(c_path)
    
    if prev is None or curr is None:
        print("Error: Could not load images.")
        sys.exit(1)

    engine = ProductionOCRBaseline(data_dir=r"c:/Users/y86as/Nippo/nippo_system/data")
    canvas, p_lines = engine.process_frames(prev, curr)
    
    if canvas is not None:
        cv2.imwrite("debug_canvas.png", canvas)
        print(f"Canvas created. Size: {canvas.shape}")
        
        results = engine.run_ocr(canvas, p_lines)
        print(f"Found {len(results)} items.")
        
        # Print JSON-like output
        log_entry = {
            "time": time.strftime('%H:%M:%S'),
            "items": [{"description": r['text'], "box_2d_mapped": r['rect']} for r in results]
        }
        print(json.dumps(log_entry, ensure_ascii=False, indent=2))
        
        # Visualize
        engine.visualize_results(curr, results, "result_overlay.png")
        print("Visualization saved to result_overlay.png")
    else:
        print("No significant difference detected.")
