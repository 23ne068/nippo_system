import os
import json
import yaml
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# 実行ファイルのディレクトリを取得 (nippo_system/reporter/)
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# nippo_system/ フォルダ (親)
NIPPO_SYSTEM_DIR = os.path.dirname(CURRENT_DIR)
# Nippo/ ルートフォルダ (さらにその親)
ROOT_DIR = os.path.dirname(NIPPO_SYSTEM_DIR)

SEMANTIC_DIR = os.path.join(NIPPO_SYSTEM_DIR, "transformer", "semantic_data")
REPORTS_DIR = os.path.join(NIPPO_SYSTEM_DIR, "reports")

class StoryAggregator:
    def __init__(self, date_str=None):
        self.date_str = date_str or datetime.now().strftime("%Y-%m-%d")
        os.makedirs(REPORTS_DIR, exist_ok=True)

    def _load_json(self, prefix):
        path = os.path.join(SEMANTIC_DIR, f"{prefix}_{self.date_str}.json")
        if not os.path.exists(path):
            logger.warning(f"File not found: {path}")
            return []
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def aggregate(self):
        logger.info(f"Aggregating story (including idle analysis) for {self.date_str}")
        
        clicks = self._load_json("semantic_clicks")
        typing = self._load_json("semantic_typing")
        context = self._load_json("semantic_context")

        ctx_map = {item["window"]: item["activity"] for item in context}

        # 全イベントを統合
        events = []
        for c in clicks:
            events.append({
                "time": c["time"],
                "type": "click",
                "window": c["window"],
                "target": c["target"],
                "ocr_context": c.get("ocr_context", "")
            })
        for t in typing:
            events.append({
                "time": t.get("time", "00:00:00"), 
                "type": "writing",
                "window": t["window"],
                "content": t.get("content", ""),
                "stats": t.get("edit_stats", {}),
                "ocr_context": t.get("ocr_context", "")
            })

        events.sort(key=lambda x: x["time"])

        total_idle_sec = 0
        IDLE_THRESHOLD_SEC = 300 # 5分以上の空きを[IDLE]とする

        story = {
            "date": self.date_str,
            "summary": {
                "total_clicks": len(clicks),
                "total_writing_sessions": len(typing),
                "total_idle_time_min": 0,
                "active_time_ratio": 0
            },
            "chronicle": []
        }

        # 時間ごとにグループ化してchronicleを作成
        def time_to_sec(t_str):
            try:
                parts = t_str.split(':')
                return float(parts[0])*3600 + float(parts[1])*60 + float(parts[2])
            except: return 0

        hourly_sessions = {}
        for ev in events:
            win = ev["window"]
            category = ctx_map.get(win, "Other Activity")
            curr_time_sec = time_to_sec(ev["time"])
            hour_str = ev["time"].split(':')[0] + ":00"

            if hour_str not in hourly_sessions:
                hourly_sessions[hour_str] = {
                    "hour": hour_str,
                    "activities": []
                }
            
            # 同じウィンドウでの連続した活動をセッションとしてまとめる
            activities = hourly_sessions[hour_str]["activities"]
            if not activities or activities[-1]["window"] != win:
                activities.append({
                    "start_time": ev["time"],
                    "window": win,
                    "category": category,
                    "ocr_context": "",
                    "events": []
                })
            
            curr_activity = activities[-1]
            # ocr_context の結合（文字数制限つきで、新しい情報を後ろに追加）
            if ev.get("ocr_context") and ev["ocr_context"] not in curr_activity["ocr_context"]:
                if len(curr_activity["ocr_context"]) < 500:
                    curr_activity["ocr_context"] += (" " + ev["ocr_context"])

            if ev["type"] == "click":
                curr_activity["events"].append({
                    "time": ev["time"],
                    "action": f"Clicked '{ev['target']}'"
                })
            elif ev["type"] == "writing":
                curr_activity["events"].append({
                    "time": ev["time"],
                    "action": "Typed text",
                    "content": ev.get("content", ""),
                    "metrics": ev["stats"]
                })
            prev_event_time_sec = curr_time_sec

        story["chronicle"] = list(hourly_sessions.values())

        # 全体のサマリー更新
        story["summary"]["total_idle_time_min"] = round(total_idle_sec / 60, 1)
        if events:
            total_dur = time_to_sec(events[-1]["time"]) - time_to_sec(events[0]["time"])
            if total_dur > 0:
                story["summary"]["active_time_ratio"] = round((total_dur - total_idle_sec) / total_dur, 2)

        return story

    def save_yaml(self, story):
        output_path = os.path.join(REPORTS_DIR, f"nsl_story_{self.date_str}.yaml")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(f"# Nippo Work Story - Generated on {datetime.now().isoformat()}\n")
            yaml.dump(story, f, allow_unicode=True, sort_keys=False, default_flow_style=False)
        logger.info(f"Work Story YAML saved to: {output_path}")
        return output_path

if __name__ == "__main__":
    aggregator = StoryAggregator()
    story = aggregator.aggregate()
    aggregator.save_yaml(story)
