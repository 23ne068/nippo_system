import os
import json
import logging
from datetime import datetime
from nippo_system.core.config import TRANSFORMER_DIR, OCR_STREAM_DIR, INPUT_STREAM_DIR

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

class MainTransformer:
    def __init__(self, date_str=None):
        self.date_str = date_str or datetime.now().strftime("%Y-%m-%d")
        self.semantic_dir = os.path.join(TRANSFORMER_DIR, "semantic_data")
        os.makedirs(self.semantic_dir, exist_ok=True)
        
        # 画面解像度の取得 (デフォルト 1920x1080)
        try:
            import tkinter
            root = tkinter.Tk()
            self.screen_width = root.winfo_screenwidth()
            self.screen_height = root.winfo_screenheight()
            root.destroy()
        except:
            self.screen_width, self.screen_height = 1920, 1080
            
        logger.info(f"Screen resolution detected: {self.screen_width}x{self.screen_height}")
        
        # モジュール群の遅延インポート等
        self.raw_ocr_path = os.path.join(OCR_STREAM_DIR, f"ocr_stream_{self.date_str}.tsv")
        self.raw_input_path = os.path.join(INPUT_STREAM_DIR, f"input_stream_{self.date_str}.tsv")
        self.mouse_path = os.path.join(INPUT_STREAM_DIR, f"mouse_events_{self.date_str}.tsv")
        self.keyboard_path = os.path.join(INPUT_STREAM_DIR, f"keyboard_events_{self.date_str}.tsv")

    def _load_mouse_data(self):
        data = []
        if not os.path.exists(self.mouse_path): return data
        import csv
        csv.field_size_limit(10**7) # 追加: フィールド長制限を緩和
        with open(self.mouse_path, "r", encoding="utf-8") as f:
            logger.info(f"Loading mouse data from {self.mouse_path}")
            reader = csv.reader(f, delimiter="\t")
            for row in reader:
                if len(row) >= 5:
                    data.append({
                        "time": row[0],
                        "window": row[1],
                        "x": int(row[2]),
                        "y": int(row[3]),
                        "button": row[4]
                    })
        return data

    def run(self):
        logger.info(f"Starting Transformer for {self.date_str}")
        
        # 1. データの読み込み
        ocr_data = self._load_ocr_data()
        mouse_data = self._load_mouse_data()
        keyboard_data = self._load_event_tsv(self.keyboard_path)
        
        if not ocr_data and not mouse_data and not keyboard_data:
            logger.warning("No data found for this date.")
            return

        # 2. 意味付け (Semantic Annotation)
        from nippo_system.transformer.annotators.click_map import find_click_target
        from nippo_system.transformer.annotators.key_logic import reconstruct_typing, identify_language
        from nippo_system.transformer.annotators.context import resolve_activity

        # --- A. Clicks (Meaningful Mouse) ---
        click_results = []
        ocr_sorted = sorted(ocr_data, key=lambda x: x["time"])
        
        for click in mouse_data:
            # 入力側の時刻は HH:MM:SS.mmm なので、秒単位に丸めて比較
            click_time_full = click["time"]
            click_time_sec = click_time_full.split('.')[0] 
            
            # 直前の最も近い時刻のOCRデータ「全ブロック」を取得
            past_ocrs = [o for o in ocr_sorted if o["time"] <= click_time_sec]
            target = None
            ocr_text_joined = ""
            
            if past_ocrs:
                latest_time = past_ocrs[-1]["time"]
                # 最新フレームの全OCRブロックを取得
                latest_frame_ocrs = [o for o in past_ocrs if o["time"] == latest_time]
                
                # 座標の正規化 (OCRの 0-1000 スケールに合わせる)
                norm_x = int((click["x"] / self.screen_width) * 1000)
                norm_y = int((click["y"] / self.screen_height) * 1000)
                
                # 最新フレーム内からクリック対象を探す
                target = find_click_target(
                    norm_x, norm_y, 
                    [{"box_2d": o["box_2d"], "description": o["text"]} for o in latest_frame_ocrs]
                )
                
                # その瞬間のOCR全体文字列をコンテキストとして保持
                ocr_text_joined = " ".join([o.get("description", o.get("text", "")) for o in latest_frame_ocrs])

            click_results.append({
                "time": click["time"],
                "window": click["window"],
                "target": target if target and target.strip() else "Background",
                "button": click.get("button", "left"),
                "ocr_context": ocr_text_joined[:200]
            })
        self._save_semantic_file("semantic_clicks", click_results)

        # --- B. Typing (Meaningful Keys) ---
        typing_results = []
        if keyboard_data:
            from collections import defaultdict
            win_keys = defaultdict(list)
            for k in keyboard_data:
                try:
                    content = k["content"]
                    k_info = json.loads(content) if content.startswith("{") else content
                    win_keys[k["window"]].append(k_info)
                except: pass
            
            for win, events in win_keys.items():
                # そのウィンドウでの最初の入力時刻をセッション時刻とする
                session_time = "00:00:00"
                # keyboard_data からこのウィンドウの最初のイベントを探す
                for k in keyboard_data:
                    if k["window"] == win:
                        session_time = k["time"]
                        break
                
                # session_time 以降のOCRを取得すべきだが、簡単のため session_time 直前のOCRをとる
                session_time_sec = session_time.split('.')[0]
                
                # 直前の最も近い時刻のOCRデータをすべて取得する
                past_ocrs = [o for o in ocr_sorted if o["time"] <= session_time_sec]
                ocr_text_joined = ""
                if past_ocrs:
                    latest_time = past_ocrs[-1]["time"]
                    latest_frame_ocrs = [o for o in past_ocrs if o["time"] == latest_time]
                    ocr_text_joined = " ".join([o.get("description", o.get("text", "")) for o in latest_frame_ocrs])

                res = reconstruct_typing(events)
                typed_text = res["text"]
                if typed_text.strip():
                    typing_results.append({
                        "time": session_time,
                        "window": win,
                        "content": typed_text,
                        "edit_stats": res["stats"],
                        "lang": identify_language(typed_text),
                        "ocr_context": ocr_text_joined[:500]
                    })
        self._save_semantic_file("semantic_typing", typing_results)

        # ウィンドウタイトルとOCRから活動を推測
        all_windows = set([i["window"] for i in mouse_data] + [i["window"] for i in keyboard_data])
        context_results = []
        
        for w in all_windows:
            # そのウィンドウが表示されている間のOCRテキストを収集
            # 簡易版: 全OCRからそのウィンドウタイトルに関連しそうなものを探す
            # 実際には時刻でフィルタするのが理想だが、ここではウィンドウごとの「傾向」を掴む
            related_text = " ".join([o["text"] for o in ocr_data if len(o["text"]) > 2])
            # キーワード抽出（簡易版: 出現頻度の高い単語）
            # FIXME: 本来はウィンドウごとの時間帯で区切るべき
            
            context_results.append({
                "window": w,
                "activity": resolve_activity(w)
            })
        self._save_semantic_file("semantic_context", context_results)

    def _save_semantic_file(self, prefix, data):
        output_path = os.path.join(self.semantic_dir, f"{prefix}_{self.date_str}.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"Generated: {output_path}")

    def _load_ocr_stream(self, path):
        data = []
        if not os.path.exists(path): return data
        import csv
        csv.field_size_limit(10**7) # 追加: フィールド長制限を緩和
        with open(path, "r", encoding="utf-8") as f:
            logger.info(f"Loading OCR stream from {path}")
            reader = csv.reader(f, delimiter="\t")
            for row in reader:
                if len(row) >= 4:
                    data.append({
                        "time": row[0],
                        "box_2d": json.loads(row[2]),
                        "text": row[3]
                    })
        return data

    def _load_event_tsv(self, path):
        data = []
        if not os.path.exists(path): return data
        import csv
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.reader(f, delimiter="\t")
            for row in reader:
                if len(row) >= 3:
                    data.append({"time": row[0], "window": row[1], "content": row[2]})
        return data

    def _load_ocr_data(self): return self._load_ocr_stream(self.raw_ocr_path)
    def _load_input_data(self):
        path = self.raw_input_path
        data = []
        if not os.path.exists(path): return data
        import csv
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.reader(f, delimiter="\t")
            for row in reader:
                if len(row) >= 4:
                    data.append({"time": row[0], "window": row[1], "keys": row[2], "mouse": row[3]})
        return data

    def _annotate(self, ocr_data, input_data, mouse_data, keyboard_data):
        from nippo_system.transformer.annotators.click_map import find_click_target
        from nippo_system.transformer.annotators.key_logic import reconstruct_typing, identify_language
        from nippo_system.transformer.annotators.context import resolve_activity
        
        results = []
        
        # マスククリックの解析 (意味付け)
        for click in mouse_data:
            try:
                # 単純にクリック座標と時刻で近いOCRを探す
                target = find_click_target(
                    click["x"], click["y"], 
                    [{"box_2d": o["box_2d"], "description": o["text"]} for o in ocr_data]
                )
                
                results.append({
                    "time": click["time"],
                    "type": "click",
                    "window": click["window"],
                    "category": resolve_activity(click["window"]),
                    "target": target or "Background",
                    "button": click.get("button", "left")
                })
            except Exception as e:
                logger.error(f"Click annotation error: {e}")

        # キー入力の解析
        if keyboard_data:
            # ウィンドウごとにグループ化して文章復元
            from collections import defaultdict
            win_keys = defaultdict(list)
            for k in keyboard_data:
                content = k["content"]
                try:
                    # JSONとして解析を試みる
                    k_info = json.loads(content)
                    win_keys[k["window"]].append(k_info)
                except json.JSONDecodeError:
                    # JSONでない場合は生文字列として扱う
                    win_keys[k["window"]].append(content)
                except: pass
            
            for win, events in win_keys.items():
                typed_text = reconstruct_typing(events)
                if typed_text.strip():
                    results.append({
                        "time": keyboard_data[0]["time"], # 最初の入力時刻
                        "type": "typing",
                        "window": win,
                        "category": resolve_activity(win),
                        "content": typed_text,
                        "language": identify_language(typed_text)
                    })

        return sorted(results, key=lambda x: x["time"])

if __name__ == "__main__":
    transformer = MainTransformer()
    transformer.run()
