import time
import subprocess
import sys
import os

import io

# Force UTF-8 for Windows console output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Try to set chcp 65001 for proper display
try:
    os.system("chcp 65001")
except Exception:
    pass

# Define scenarios
SCENARIOS = [
    {
        "name": "1_Static",
        "desc": "【静止画】マウスやキーボードを操作せず、画面を静止させてください。",
        "duration": 30
    },
    {
        "name": "2_Typing",
        "desc": "【タイピング】メモ帳などで、ゆっくり文字を入力し続けてください。",
        "duration": 30
    },
    {
        "name": "3_Scroll",
        "desc": "【スクロール】Webページやドキュメントをスクロールし続けてください。",
        "duration": 30
    },
    {
        "name": "4_Mixed",
        "desc": "【通常作業】アプリの切り替えや、マウス移動を行ってください。",
        "duration": 30
    }
]

def main():
    print("=== OCR Data Collection Sequence ===")
    print("4つのシナリオでデータを収集します。")
    print("各シナリオの前に3秒間のカウントダウンがあります。")
    print("----------------------------------------")

    python_exe = sys.executable
    script_path = os.path.join(os.path.dirname(__file__), "run_ocr_test.py")

    for i, scenario in enumerate(SCENARIOS, 1):
        print(f"\n[{i}/4] シナリオ: {scenario['name']}")
        print(f"指示: {scenario['desc']}")
        print("準備ができたら Enter キーを押してください...", end="")
        input()
        
        print("3秒後に開始します...")
        time.sleep(1)
        print("2...")
        time.sleep(1)
        print("1...")
        time.sleep(1)
        print("START!", flush=True)

        # Run the collector script
        try:
            subprocess.run([python_exe, script_path, str(scenario['duration'])], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error executing scenario {scenario['name']}: {e}")
            return
        except KeyboardInterrupt:
            print("\nAborted by user.")
            return

    print("\n========================================")
    print("すべてのデータ収集が完了しました。")
    print("ocr_lab/data/ フォルダを確認してください。")

if __name__ == "__main__":
    main()
